"""Acceptance scenarios for media.py contracts.

Tests replace HTTP responses, so they establish client behavior, not a live
ComfyUI execution or model quality. Decoder tests exercise a real interpreter.
"""
import base64
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

import media

TEST_TEMP = Path(__file__).resolve().parents[1] / 'work'
TEST_TEMP.mkdir(exist_ok=True)


class PrepareTests(unittest.TestCase):
    def test_video_save_format_survives_installed_comfy_normalization(self):
        """MEDIA-PREPARE: native V3 parsing retains the MP4/H.264 save settings.

        Runs installed ComfyUI schema normalization on CPU, without loading model
        weights or calling the service. Protects against a live SaveVideo TypeError.
        """
        decoder = Path(os.environ.get('COMFY_PYTHON',''))
        if not decoder.is_file() or not os.environ.get('COMFY_ROOT'):
            self.skipTest('COMFY_PYTHON and COMFY_ROOT select optional native Comfy tests')
        inputs = media.prepare('video', {'prompt': 'walk'})['prompt']['save']['inputs']
        script = (
            'import sys,json\n'
            'sys.path.insert(0,sys.argv[1]);sys.argv=["test","--cpu"]\n'
            'from comfy_extras.nodes_video import SaveVideo\n'
            'from comfy_api.latest import _io\n'
            'live=json.load(sys.stdin)\n'
            'final,hidden,data=_io.get_finalized_class_inputs(SaveVideo.INPUT_TYPES(),live)\n'
            'selected={k:v for k,v in live.items() if k in final["required"] or k in final["optional"]}\n'
            'print(json.dumps(_io.build_nested_inputs(selected,data)))\n'
        )
        result = subprocess.run([str(decoder), '-c', script, os.environ['COMFY_ROOT']], input=json.dumps(inputs), text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        nested = json.loads(result.stdout)
        self.assertEqual(nested.get('format'), {'format': 'mp4', 'codec': {'codec': 'h264'}})

    def test_music_preserves_upstream_ace_sampling(self):
        """MEDIA-MUSIC: ACE's sampler follows upstream model and CFG conditioning.

        The independent source is ComfyUI_examples/audio/ace_step_example.flac
        prompt metadata, retained in work/media-upstream-audio.json.
        """
        graph = media.prepare('music', {'prompt': 'piano'})['prompt']
        cfg_node = graph[graph['sample']['inputs']['model'][0]]
        self.assertEqual(cfg_node['class_type'], 'LatentApplyOperationCFG')
        shift_node = graph[cfg_node['inputs']['model'][0]]
        self.assertEqual(shift_node['inputs']['shift'], 5.0)
        operation = graph[cfg_node['inputs']['operation'][0]]
        self.assertEqual(operation['class_type'], 'LatentOperationTonemapReinhard')
        self.assertEqual(graph['sample']['inputs']['sampler_name'], 'euler')
        self.assertEqual(graph['sample']['inputs']['scheduler'], 'simple')

    def test_prefix_cannot_expand_a_prompt_into_an_output_path(self):
        """MEDIA-PREPARE: ComfyUI filename macros must not bypass path checks."""
        with self.assertRaises(ValueError):
            media.prepare('image', {'prompt': '../outside', 'filename_prefix': '%positive.text%'})

    def test_each_preset_binds_prompt_and_pins_an_output_node(self):
        """MEDIA-PREPARE: all five asset requests produce distinct pinned graphs."""
        for preset, kind in [('image', 'image'), ('video', 'video'), ('music', 'audio'), ('sfx', 'audio'), ('speech', 'audio')]:
            with self.subTest(preset=preset):
                request = {'prompt': 'A quiet garden'}
                if preset != 'speech':
                    request['seed'] = 7
                prepared = media.prepare(preset, request)
                self.assertEqual(prepared['kind'], kind)
                self.assertIn('A quiet garden', json.dumps(prepared['prompt']))
                self.assertTrue(prepared['output_nodes'])
                for node in prepared['output_nodes']:
                    self.assertIn(node, prepared['prompt'])

    def test_malformed_input_is_rejected_without_submitting(self):
        """MEDIA-PREPARE: reject typos, coercion, unsafe output prefixes and ranges."""
        for request in [{'prompt': ''}, {'prompt': 'x', 'width': True}, {'prompt': 'x', 'width': 513}, {'prompt': 'x', 'seed': -1}, {'prompt': 'x', 'steps': 0}, {'prompt': 'x', 'mystery': 1}, {'prompt': 'x', 'filename_prefix': '../escape'}, {'prompt': 'x', 'duration': float('nan')}]:
            with self.subTest(request=request), self.assertRaises(ValueError):
                media.prepare('image', request)

    def test_reference_image_is_a_comfy_input_name_and_only_video_supports_it(self):
        """MEDIA-PREPARE: bind an uploaded video reference without local path access."""
        prepared = media.prepare('video', {'prompt': 'walk', 'reference_image': 'ref.png'})
        self.assertIn('ref.png', json.dumps(prepared['prompt']))
        with self.assertRaises(ValueError):
            media.prepare('image', {'prompt': 'x', 'reference_image': 'ref.png'})
        with self.assertRaises(ValueError):
            media.prepare('video', {'prompt': 'x', 'reference_image': '../ref.png'})

    def test_live_schema_reports_missing_nodes_and_models(self):
        """MEDIA-VALIDATE: absent dependencies are errors before POST /prompt."""
        with patch('media.api', return_value={}):
            with self.assertRaisesRegex(ValueError, 'CheckpointLoaderSimple'):
                media.prepare('image', {'prompt': 'x'}, 'http://127.0.0.1:8189')
        prepared = media.prepare('image', {'prompt': 'x'})
        info = {node['class_type']: {'input': {'required': {}}} for node in prepared['prompt'].values()}
        info['CheckpointLoaderSimple']['input']['required']['ckpt_name'] = [['other.safetensors']]
        with patch('media.api', return_value=info):
            with self.assertRaisesRegex(ValueError, 'Juggernaut'):
                media.prepare('image', {'prompt': 'x'}, 'http://127.0.0.1:8189')


class ServiceTests(unittest.TestCase):
    def test_only_loopback_http_urls_are_allowed(self):
        """MEDIA-API: callers cannot redirect this local tool to an external host."""
        for url in ['https://example.com', 'http://127.0.0.1:8189/path', 'http://user@localhost:8189', 'http://localhost:8189/?key=x']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                media.api(url, '/queue')

    def test_submission_returns_correlated_prompt_id(self):
        """MEDIA-API/OWNERSHIP: the response must echo the submitted UUID."""
        import uuid
        def echo(url, path, payload):
            self.assertEqual(str(uuid.UUID(payload['prompt_id'])), payload['prompt_id'])
            return {'prompt_id': payload['prompt_id'], 'node_errors': {}}
        with patch('media.api', side_effect=echo) as api:
            result = media.submit({'prompt': {'1': {}}}, 'http://localhost:8189')
            self.assertEqual(result, api.call_args.args[2]['prompt_id'])
        with patch('media.api', return_value={'node_errors': {'1': 'missing'}}):
            with self.assertRaisesRegex(ValueError, 'missing'):
                media.submit({'prompt': {}}, 'http://localhost:8189')

    def test_history_requires_success_and_registered_saved_outputs(self):
        """MEDIA-API: distinguish waiting, failed generation and real output refs."""
        descriptor = {'filename': 'x.png', 'subfolder': '', 'type': 'output'}
        for history, state in [({}, 'running'), ({'id': {'status': {'status_str': 'error', 'messages': ['OOM']}}}, 'failed'), ({'id': {'status': {'status_str': 'success', 'completed': True}, 'outputs': {}}}, 'failed'), ({'id': {'status': {'status_str': 'success', 'completed': True}, 'outputs': {'9': {'images': [descriptor]}, '8': {'images': [{'filename': 'unrelated.png'}]}}}}, 'succeeded')]:
            with self.subTest(state=state), patch('media.api', return_value=history):
                result = media.poll('id', 'http://localhost:8189', ['9'])
                self.assertEqual(result['state'], state)
                if state == 'succeeded':
                    self.assertEqual(result['outputs'], [descriptor])

    def test_cancel_targets_only_the_selected_prompt(self):
        """MEDIA-CANCEL: never clear another caller's queue or globally interrupt."""
        with patch('media.api', return_value={}) as api:
            media.cancel('owned-id', 'http://localhost:8189')
        self.assertEqual([c.args[1:] for c in api.call_args_list], [('/queue', {'delete': ['owned-id']}), ('/interrupt', {'prompt_id': 'owned-id'})])


class RetrievalTests(unittest.TestCase):
    def test_reader_never_calls_stateful_cancellation_predicate(self):
        """MEDIA-DEADLINE: late reader activity cannot mutate terminal job state.

        The callback records every invocation and stands in for the harness's
        state-writing heartbeat callback. A cancelled read finishes after return.
        """
        cancelled, closed = threading.Event(), threading.Event()
        caller = threading.get_ident()
        invocations = []
        def predicate():
            invocations.append(threading.get_ident())
            return cancelled.is_set()
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): closed.set()
            def read1(self, count):
                time.sleep(0.25)
                return b'late'
        timer = threading.Timer(0.05, cancelled.set)
        with patch('media.urlopen', return_value=Response()):
            timer.start()
            try:
                with self.assertRaises(InterruptedError):
                    media.fetch('http://localhost:8189', '/view', deadline=time.monotonic() + 2, cancelled=predicate)
                calls_at_return = len(invocations)
                self.assertTrue(closed.wait(1))
                self.assertEqual(len(invocations), calls_at_return)
                self.assertTrue(all(thread == caller for thread in invocations))
            finally:
                timer.cancel()

    def test_download_allows_a_pause_longer_than_one_second_with_budget_remaining(self):
        """MEDIA-DEADLINE: a valid slow response must not be called timed out.

        Fake transport enforces the socket timeout passed to urlopen and delays
        the first chunk by 1.1 seconds, within the caller's three-second budget.
        This exercises scheduling and timeout policy, not a real HTTP server.
        """
        class Response:
            def __init__(self, timeout): self.timeout, self.sent = timeout, False
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read1(self, count):
                if self.sent: return b''
                self.sent = True
                time.sleep(min(1.1, self.timeout))
                if self.timeout < 1.1:
                    raise TimeoutError('socket timed out before a valid chunk arrived')
                return b'complete'
        with patch('media.urlopen', side_effect=lambda url, timeout: Response(timeout)):
            self.assertEqual(media.fetch('http://localhost:8189', '/view', deadline=time.monotonic() + 3), b'complete')

    def test_cancellation_returns_promptly_while_a_read_is_stalled(self):
        """MEDIA-DEADLINE: callers do not wait for a blocked response read.

        A fake read blocks for half a second; cancellation arrives after 50ms.
        The reader must stop without writing any file when that read returns.
        """
        cancelled, closed = threading.Event(), threading.Event()
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): closed.set()
            def read1(self, count):
                time.sleep(0.5)
                return b'partial'
        timer = threading.Timer(0.05, cancelled.set)
        with patch('media.urlopen', return_value=Response()):
            timer.start()
            started = time.monotonic()
            try:
                with self.assertRaises(InterruptedError):
                    media.fetch('http://localhost:8189', '/view', deadline=started + 3, cancelled=cancelled.is_set)
                self.assertLess(time.monotonic() - started, 0.35)
            finally:
                timer.cancel()
                self.assertTrue(closed.wait(1))

    def test_expired_download_does_not_start_a_request(self):
        """MEDIA-DEADLINE: a passed deadline prevents network I/O entirely."""
        with patch('media.urlopen') as request:
            with self.assertRaises(TimeoutError):
                media.fetch('http://localhost:8189', '/view', deadline=time.monotonic() - 1)
        request.assert_not_called()

    def test_download_cancellation_is_checked_between_chunks(self):
        """MEDIA-DEADLINE: cancellation after one read prevents a second read."""
        state = {'cancelled': False, 'reads': 0}
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read1(self, count):
                state['reads'] += 1
                state['cancelled'] = True
                return b'partial'
            def read(self):
                state['reads'] += 1
                state['cancelled'] = True
                return b'partial'
        with patch('media.urlopen', return_value=Response()):
            with self.assertRaises(InterruptedError):
                media.fetch('http://localhost:8189', '/view', cancelled=lambda: state['cancelled'])
        self.assertEqual(state['reads'], 1)

    def test_cancellation_stops_only_the_owned_decoder_and_removes_partial(self):
        """MEDIA-DEADLINE: a real child process is terminated during decoding.

        Replaces the decoder command with a short sleeper and HTTP with bytes;
        this establishes process cleanup, not decoder quality or network timing.
        """
        item = {'filename': 'x.png', 'subfolder': '', 'type': 'output'}
        original_popen = subprocess.Popen
        children = []
        def spawn(*args, **kwargs):
            child = original_popen([sys.executable, '-c', 'import time; time.sleep(0.35)'], **kwargs)
            children.append(child)
            return child
        with tempfile.TemporaryDirectory(dir=TEST_TEMP) as tmp:
            with patch('media.fetch', return_value=b'image'), patch('media.subprocess.Popen', side_effect=spawn):
                with self.assertRaises(InterruptedError):
                    media.retrieve([item], tmp, 'image', 'http://localhost:8189', cancelled=lambda: bool(children))
            self.assertFalse(list(Path(tmp).glob('*.part')))
            self.assertFalse(list(Path(tmp).glob('*.png')))
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].poll())

    def test_unsafe_descriptors_are_rejected_before_fetch(self):
        """MEDIA-RETRIEVE: server descriptors cannot traverse or read input files."""
        for descriptor in [{'filename': '../x.png', 'subfolder': '', 'type': 'output'}, {'filename': 'x.png', 'subfolder': '../input', 'type': 'output'}, {'filename': 'x.png', 'subfolder': '', 'type': 'input'}, {'filename': 'C:\\x.png', 'type': 'output'}]:
            with self.subTest(descriptor=descriptor), tempfile.TemporaryDirectory(dir=TEST_TEMP) as tmp:
                with self.assertRaises(ValueError):
                    media.retrieve([descriptor], tmp, 'image', 'http://localhost:8189')

    def test_output_is_saved_only_after_successful_decode(self):
        """MEDIA-RETRIEVE: real PNG decoding, HTTP replaced by known fixture bytes."""
        decoder = Path(os.environ.get('COMFY_PYTHON',''))
        if not decoder.is_file():
            self.skipTest('ComfyUI decoder interpreter is not installed')
        png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=')
        item = {'filename': 'x.png', 'subfolder': 'harness/test', 'type': 'output'}
        with tempfile.TemporaryDirectory(dir=TEST_TEMP) as tmp, patch('media.fetch', return_value=png):
            paths = media.retrieve([item], tmp, 'image', 'http://localhost:8189', str(decoder))
            self.assertEqual(len(paths), 1)
            self.assertEqual(Path(paths[0]).read_bytes(), png)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP) as tmp, patch('media.fetch', return_value=b'not png'):
            with self.assertRaises(ValueError):
                media.retrieve([item], tmp, 'image', 'http://localhost:8189', str(decoder))
            self.assertFalse(list(Path(tmp).glob('*.png')))


if __name__ == '__main__':
    unittest.main()
