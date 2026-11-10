"""Pinned local ComfyUI workflows and output retrieval.

MEDIA-PREPARE: Render only registered graphs and exposed typed inputs; reject
unknown keys, invalid ranges and unsafe filenames before network submission.
MEDIA-VALIDATE: Report missing nodes/models using object_info; ComfyUI remains
the authority for graph validation, including links and dynamic input schemas.
MEDIA-MUSIC: Preserve ACE-Step's upstream flow shift and CFG tonemap so routine
prompt changes do not silently switch its required sampling configuration.
MEDIA-LTX: video uses the installed LTX-2.5 distilled NVFP4/eight-step recipe.
Both video routes pin 24fps and map 5..15s to 8k+1 frames (121..361); returned
frame_count is authoritative for the runner's source guard. Generation supports
text-only and optional real first-frame conditioning. video_edit guides synthesis
with every source frame, with source_strength in [0,1], default 0.40. This is
experimental regeneration, not an instruction editor or masked Retake. Text is
passed verbatim; reject H3 reference-tag protocols rather than silently wrapping
them for LTX. Keep paired video/audio lengths and the tested sigma/sampler recipe.
Evidence: tests/test_routing_v2.py plus native validation and real LTX smokes.
MEDIA-IMAGE-EDIT: image_edit requires an input image and uses Qwen Image Edit
2511 with its matching four-step Lightning LoRA. Scale reference/latent inputs
to the same native megapixel area while preserving aspect ratio.
MEDIA-MODELS: Dependency checks cover PDD/LoRA files and legacy/V3 COMBO options.
MEDIA-PATHS: Normalize Windows output-subfolder separators, then apply the same
traversal and output-only checks. Never relax basename validation.
Reject empty path components, Windows trailing-dot/space aliases and source
annotations that could redirect ComfyUI outside its input directory.
Evidence for these additions: tests/test_routing_v2.py plus live preset smokes.
MEDIA-API: Surface server errors, correlate history by prompt ID and require
saved outputs from the registered output nodes before declaring success.
MEDIA-OWNERSHIP: Submit the caller's canonical prompt UUID. Require that exact
UUID in the acknowledgement. Only a known server validation rejection before
enqueue is conclusive after POST fails. See tests/test_submission_ownership.py.
MEDIA-CANCEL: Delete/interrupt only the requested prompt, never the whole queue.
MEDIA-RETRIEVE: Fetch only output descriptors, keep filenames inside the job's
destination, and fully decode files before returning their paths.
MEDIA-PORTABLE: Default to COMFY_PYTHON when explicitly provided, otherwise this
host's Python. Machine config supplies a Comfy decoder; never assume a D: drive.
Evidence: tests/test_portability.py. Decode capability needs a separate probe.
MEDIA-DEADLINE: Download reads and the owned decoder observe the caller's
monotonic deadline and cancellation; stop that decoder and remove partial files.
The caller stays responsive during stalled reads without imposing a one-second
transfer timeout; the background reader is read-only and has bounded I/O waits.
Only the caller invokes the cancellation predicate, which may update job state;
the reader must never call it, including after the caller has already returned.
Evidence: tests/test_media.py. HTTP tests replace the service; decoder tests use
the installed ComfyUI interpreter and real media bytes, not generation models.
"""
import json
import os
from pathlib import Path
from fractions import Fraction
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


WORKFLOWS = Path(__file__).with_name('workflows')
PRESETS = ('image', 'image_edit', 'video', 'video_edit', 'music', 'sfx', 'speech')
DEFAULT_DECODER = os.environ.get('COMFY_PYTHON') or sys.executable


def _safe_relative(value, basename=False):
    if not isinstance(value, str) or not value or re.search(r'[\x00-\x1f<>:"\\|?*%]', value):
        raise ValueError('Expected a safe relative filename')
    parts = value.split('/')
    if any(not p or p.endswith(('.', ' ')) for p in parts) or (basename and len(parts) != 1):
        raise ValueError('Expected a safe relative filename')
    if value.endswith(('[input]', '[output]', '[temp]')):
        raise ValueError('ComfyUI directory annotations are not accepted')
    return value


def _url(comfy_url, path):
    u = urlsplit(comfy_url)
    if u.scheme != 'http' or u.hostname not in ('localhost', '127.0.0.1', '::1') or u.username or u.password or u.query or u.fragment or u.path not in ('', '/'):
        raise ValueError('ComfyUI must use a loopback HTTP URL')
    return comfy_url.rstrip('/') + path


def validate_video_source(name, input_directory, expected_frames, decoder_python=None, deadline=None, cancelled=None, expected_aspect=None):
    """MEDIA-SOURCE: Before GPU/submission, require an existing input-root clip
    with exactly the requested native frame count and constant 24fps timing.
    Resolve containment, reject malformed references and bound the owned PyAV
    probe by caller cancellation/deadline. Inspect frame timestamps, permitting
    container time-base quantization; average_rate alone cannot establish CFR.
    MEDIA-ASPECT: if expected_aspect is supplied, require matching decoded source
    aspect before GPU work, avoiding LTX's implicit center crop. Use the first
    frame's displayed orientation, as GetVideoComponents does. Same-aspect
    scaling is allowed. Evidence: tests/test_video_source.py.
    Return verified dimensions/count/rate/duration. Stage/resample incompatible
    sources explicitly; never silently reinterpret a 30fps or VFR video as 24fps.
    Evidence: tests/test_video_source.py and registered video-edit live smoke.
    """
    deadline = time.monotonic() + 120 if deadline is None else deadline
    _check(deadline, cancelled)
    _safe_relative(name)
    if not input_directory:
        raise ValueError('Configure comfy_input_dir to validate the source clip')
    root = Path(input_directory).resolve()
    source = (root / name).resolve()
    if not source.is_relative_to(root) or not source.is_file():
        raise ValueError('reference_video must be a file inside the configured ComfyUI input directory')
    command = [decoder_python or DEFAULT_DECODER, '-I', str(Path(__file__).resolve()),
               '_probe_video', str(source), str(expected_frames)]
    metadata = json.loads(_run_decoder(command, deadline, cancelled))
    if expected_aspect is not None:
        width, height = expected_aspect
        if metadata['width'] * height != metadata['height'] * width:
            raise ValueError(f'Stage a source clip with the requested {width}:{height} aspect ratio')
    return {'reference_video': name, **metadata}


def _probe_video(path, expected_frames):
    import av
    with av.open(path) as container:
        if not container.streams.video:
            raise ValueError('reference_video has no video stream')
        stream = container.streams.video[0]
        if stream.average_rate != 24:
            raise ValueError('Stage a constant 24fps source clip')
        frames = 0
        previous = None
        min_error = max_error = 0
        for frame in container.decode(stream):
            if frames == expected_frames:
                raise ValueError(f'Stage a source clip with exactly {expected_frames} frames')
            if frame.pts is None or not frame.time_base:
                raise ValueError('Source frame has no verifiable presentation time')
            timestamp = frame.pts * frame.time_base
            if previous is None:
                start = timestamp
                width, height = frame.width, frame.height
                if frame.rotation and (frame.rotation // 90) % 2:
                    width, height = height, width
            elif timestamp <= previous:
                raise ValueError('Stage a constant 24fps source clip with increasing timestamps')
            error = timestamp - start - Fraction(frames, 24)
            min_error = min(min_error, error)
            max_error = max(max_error, error)
            # A CFR clock rounded to container ticks has less than one tick of spread.
            if max_error - min_error >= frame.time_base:
                raise ValueError('Stage a constant 24fps source clip; variable timing detected')
            previous = timestamp
            frames += 1
        if not frames or frames != expected_frames:
            raise ValueError(f'Stage a source clip with exactly {expected_frames} frames; found {frames}')
        return {'frames': frames, 'fps': 24, 'width': width, 'height': height,
                'duration_seconds': frames / 24}


def _check(deadline, cancelled):
    if cancelled is not None and cancelled():
        raise InterruptedError('Media retrieval cancelled')
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError('Media retrieval deadline exceeded')


def _run_decoder(command, deadline, cancelled, directory=None):
    _check(deadline, cancelled)
    with tempfile.TemporaryFile(dir=directory) as errors, tempfile.TemporaryFile(dir=directory) as output:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        process = subprocess.Popen(command, stdout=output, stderr=errors, creationflags=flags)
        try:
            while process.poll() is None:
                _check(deadline, cancelled)
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
            _check(deadline, cancelled)
            if process.returncode:
                errors.seek(max(0, errors.tell() - 2000))
                raise ValueError(f'Media decode failed: {errors.read().decode(errors="replace")}')
            output.seek(0)
            return output.read()
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=0.5)


def fetch(comfy_url, path, deadline=None, cancelled=None):
    deadline = time.monotonic() + 15 if deadline is None else deadline
    _check(deadline, cancelled)
    url = _url(comfy_url, path)
    events, stop, acknowledged = queue.Queue(), threading.Event(), threading.Event()
    def read():
        try:
            _check(deadline, None)
            with urlopen(url, timeout=max(0.001, min(15, deadline - time.monotonic()))) as response:
                while not stop.is_set():
                    _check(deadline, None)
                    chunk = response.read1(64 * 1024)
                    _check(deadline, None)
                    if stop.is_set():
                        return
                    events.put(('chunk', chunk))
                    if not chunk:
                        return
                    acknowledged.wait(max(0, deadline - time.monotonic()))
                    acknowledged.clear()
        except Exception as exc:
            events.put(('error', exc))
    threading.Thread(target=read, name='comfy-output-reader', daemon=True).start()
    chunks = bytearray()
    try:
        while True:
            _check(deadline, cancelled)
            try:
                event, chunk = events.get(timeout=min(0.05, max(0.001, deadline - time.monotonic())))
            except queue.Empty:
                continue
            _check(deadline, cancelled)
            if event == 'error':
                raise chunk
            if not chunk:
                return bytes(chunks)
            chunks.extend(chunk)
            acknowledged.set()
    finally:
        stop.set()
        acknowledged.set()


class PromptRejected(ValueError):
    """ComfyUI rejected this prompt before placing it on the execution queue."""


def api(comfy_url, path, data=None):
    body = None if data is None else json.dumps(data, allow_nan=False).encode()
    request = Request(_url(comfy_url, path), data=body, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        with exc:
            details = exc.read().decode(errors='replace')
        message = f'ComfyUI HTTP {exc.code}: {details}'
        if path == '/prompt' and exc.code == 400:
            try:
                error_type = json.loads(details)['error']['type']
            except (ValueError, KeyError, TypeError):
                error_type = None
            if error_type in ('invalid_prompt_id', 'no_prompt', 'missing_node_type', 'prompt_no_outputs', 'prompt_outputs_failed_validation'):
                raise PromptRejected(message) from exc
        raise ValueError(message) from exc


def workflow_template(preset):
    if preset not in PRESETS:
        raise ValueError('Expected a registered preset')
    return json.loads((WORKFLOWS / f'{preset}.json').read_text(encoding='utf-8'))


def workflow_model(preset):
    for node in workflow_template(preset)['prompt'].values():
        for key in ('ckpt_name', 'unet_name'):
            if key in node['inputs']:
                return node['inputs'][key]
        if node['class_type'] == 'KokoroGenerator':
            return 'KokoroGenerator'
    raise ValueError(f'No configured model for {preset}')


def prepare(preset, request, comfy_url=None):
    if not isinstance(request, dict):
        raise ValueError('Expected a request object')
    template = workflow_template(preset)
    required = set(template.get('required_inputs', ['prompt']))
    missing_inputs = required - request.keys()
    if missing_inputs:
        raise ValueError(f'Missing required inputs: {sorted(missing_inputs)}')
    allowed = set(template['defaults']) | required | {'filename_prefix'}
    if preset == 'video':
        allowed.add('reference_image')
    unknown = set(request) - allowed
    if unknown:
        raise ValueError(f'Unsupported {preset} inputs: {sorted(unknown)}')
    values = template['defaults'] | request
    if not isinstance(values.get('prompt'), str) or not values['prompt'].strip() or len(values['prompt']) > 20000:
        raise ValueError('prompt must contain 1–20000 characters')
    for name, bounds in template.get('ranges', {}).items():
        value = values[name]
        low, high, step = bounds
        integer = name in ('width', 'height', 'steps', 'seed')
        if isinstance(value, bool) or not isinstance(value, (int, float)) or (integer and not isinstance(value, int)) or not low <= value <= high or (step and value % step):
            raise ValueError(f'{name} must be between {low} and {high}' + (f' in multiples of {step}' if step else ''))
    for name, value in values.items():
        default = template['defaults'].get(name)
        if isinstance(default, str) and not isinstance(value, str):
            raise ValueError(f'{name} must be text')
    for field in ('reference_image', 'reference_video'):
        if field in values:
            _safe_relative(values[field])
    values['filename_prefix'] = _safe_relative(values.get('filename_prefix', f'harness/{preset}'))
    graph = template['prompt']
    prepared = {'prompt': graph, 'output_nodes': template['output_nodes'], 'kind': template['kind'], 'preset': preset}
    if preset in ('video', 'video_edit'):
        if re.search(r'<(?:Picture|Video|Audio)\s*\d+\s*>|\[video editing\]', values['prompt'], re.IGNORECASE):
            raise ValueError('Use a plain LTX prompt without H3 reference tags')
        values['length'] = round((values['duration'] * values['fps'] - 1) / 8) * 8 + 1
        prepared.update(frame_count=values['length'], width=values['width'], height=values['height'])
    if preset == 'video' and 'reference_image' in values:
        graph.update(template['reference_image_nodes'])
        graph['image']['inputs']['image'] = values['reference_image']
        graph['av']['inputs']['video_latent'] = ['anchor', 0]
    for name, targets in template['bindings'].items():
        for node, field in targets:
            graph[node]['inputs'][field] = values[name]
    if comfy_url is not None:
        info = api(comfy_url, '/object_info')
        missing = sorted({n['class_type'] for n in graph.values()} - set(info))
        if missing:
            raise ValueError(f'Missing ComfyUI nodes: {missing}')
        for node in graph.values():
            inputs = info[node['class_type']].get('input', {})
            specs = inputs.get('required', {}) | inputs.get('optional', {})
            for key in ('ckpt_name', 'clip_name', 'vae_name', 'unet_name', 'lora_name', 'pdd_file'):
                if key not in node['inputs'] or key not in specs:
                    continue
                spec = specs[key]
                options = spec[0]
                if options == 'COMBO' and len(spec) > 1:
                    options = spec[1].get('options')
                if isinstance(options, list) and node['inputs'][key] not in options:
                    raise ValueError(f'Missing model: {node["inputs"][key]}')
    return prepared


def submit(prepared, comfy_url, prompt_id=None):
    if prompt_id is None:
        prompt_id = str(uuid.uuid4())
    if not isinstance(prompt_id, str) or str(uuid.UUID(prompt_id)) != prompt_id:
        raise ValueError('Expected a canonical prompt UUID')
    response = api(comfy_url, '/prompt', {'prompt': prepared['prompt'], 'prompt_id': prompt_id})
    if not isinstance(response, dict) or response.get('prompt_id') != prompt_id or response.get('node_errors'):
        raise ValueError(f'Invalid ComfyUI acknowledgement for {prompt_id}: {response}')
    return prompt_id


def poll(prompt_id, comfy_url, output_nodes=None):
    history = api(comfy_url, '/history/' + str(prompt_id))
    entry = history.get(prompt_id)
    if not entry:
        return {'state': 'running', 'outputs': []}
    status = entry.get('status', {})
    if status.get('status_str') == 'error':
        return {'state': 'failed', 'outputs': [], 'error': status.get('messages', [])}
    if not status.get('completed'):
        return {'state': 'running', 'outputs': []}
    outputs = []
    for node_id, ui in entry.get('outputs', {}).items():
        if output_nodes is None or node_id in output_nodes:
            for key in ('images', 'audio', 'videos'):
                outputs.extend(item for item in ui.get(key, []) if isinstance(item, dict) and item.get('type') == 'output')
    if status.get('status_str') != 'success' or not outputs:
        return {'state': 'failed', 'outputs': [], 'error': 'Completed workflow has no saved outputs from its registered output nodes'}
    return {'state': 'succeeded', 'outputs': outputs}


def cancel(prompt_id, comfy_url):
    if not isinstance(prompt_id, str) or not prompt_id:
        raise ValueError('A prompt ID is required')
    api(comfy_url, '/queue', {'delete': [prompt_id]})
    api(comfy_url, '/interrupt', {'prompt_id': prompt_id})


def retrieve(outputs, destination, kind, comfy_url, decoder_python=None, deadline=None, cancelled=None):
    deadline = time.monotonic() + 120 if deadline is None else deadline
    _check(deadline, cancelled)
    if kind not in ('image', 'video', 'audio') or not outputs:
        raise ValueError('Expected nonempty saved media outputs')
    destination = Path(destination).resolve()
    descriptors = []
    for item in outputs:
        if not isinstance(item, dict) or item.get('type') != 'output':
            raise ValueError('Only ComfyUI output files may be retrieved')
        filename = _safe_relative(item.get('filename'), basename=True)
        subfolder = item.get('subfolder', '')
        if not isinstance(subfolder, str):
            raise ValueError('Expected an output subfolder name')
        if subfolder:
            subfolder = _safe_relative(subfolder.replace('\\', '/'))
        descriptors.append({'filename': filename, 'subfolder': subfolder, 'type': 'output'})
    destination.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, item in enumerate(descriptors):
        target = destination / f'{index:02}_{item["filename"]}'
        temporary = target.with_suffix(target.suffix + '.part')
        try:
            temporary.write_bytes(fetch(comfy_url, '/view?' + urlencode(item), deadline=deadline, cancelled=cancelled))
            _check(deadline, cancelled)
            script = (
                'import sys\nfrom PIL import Image\n'
                'with Image.open(sys.argv[1]) as im:\n im.load()\n assert im.width > 0 and im.height > 0\n'
                if kind == 'image' else
                'import sys,av\n'
                'with av.open(sys.argv[1]) as container:\n'
                ' stream=next((s for s in container.streams if s.type==sys.argv[2]),None)\n'
                ' assert stream is not None,"missing media stream"\n'
                ' count=sum(1 for _ in container.decode(stream))\n'
                ' assert count>0,"empty media stream"\n'
            )
            command = [decoder_python or DEFAULT_DECODER, '-c', script, str(temporary), kind]
            _run_decoder(command, deadline, cancelled, destination)
            _check(deadline, cancelled)
            temporary.replace(target)
            paths.append(str(target))
        finally:
            temporary.unlink(missing_ok=True)
    return paths


if __name__ == '__main__' and sys.argv[1:2] == ['_probe_video']:
    print(json.dumps(_probe_video(sys.argv[2], int(sys.argv[3]))))
