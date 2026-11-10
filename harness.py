"""Local Codex worker runner. Contracts are exercised by tests/test_core.py.

JOB-1: Persist jobs atomically, reject unknown IDs and requests outside supported
boundaries, and never overwrite another job. Terminal states remain terminal.
GPU-1: A process-held lock serializes local GPU work across all projects and
releases on exit. A waiting job must respect cancellation and its deadline.
Asset handoff inspects optional worker residency before unloading it. A refused
Ollama connection permits generation; uncertain residency fails the handoff.
Each residency entry must identify its model with a nonempty string.
SUBMIT-1: Persist the owned UUID and shared unconfirmed-prompt.json before
POST while holding the GPU lease. Lost acknowledgements or supervisor death
leave further GPU handoffs blocked until operator reconciliation; a temporarily
empty Comfy queue cannot rule out a late enqueue. Automatically clear only on
matching acknowledgement or proven pre-enqueue rejection. Cancel only the
owned prompt, at most once per job. See tests/test_submission_ownership.py.
PROC-1: Execute argv without a shell, preserve logs, bound execution by a
deadline, and terminate the owned process tree on cancellation or timeout.
CODE-1: Qwen runs with a local provider, without recursive agents or inherited
OpenAI credentials; successful execution still requires checks and Terra review.
ROUTE-2: Registered video_edit jobs get the video deadline; image_edit gets the
image deadline. Asset status names its actual configured model, not the coding
worker. Doctor lists all registered presets and distinguishes optional Ollama
worker readiness from ComfyUI asset readiness. Source-required presets report
their input requirements without pretending a diagnostic placeholder is a file.
MEDIA-SOURCE: Before leasing the GPU or submitting a video edit, validate the
staged clip against the prepared frame count and output aspect, then persist
its decoded timing and dimensions in source.json. See tests/test_video_source.py.
Evidence: tests/test_routing_v2.py; real preset smokes establish service behavior.
"""

from pathlib import Path
import argparse
import contextlib
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.request

BASE = Path(__file__).resolve().parent
GPU_ROOT = BASE / '.runtime'
TERMINAL = {'succeeded', 'failed', 'cancelled', 'timed_out', 'changes_requested'}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def validate_request(kind, request, workspace):
    """JOB-1: Validate before spawning or creating any job directory."""
    if not Path(workspace).is_dir():
        raise ValueError('workspace must be an existing directory')
    if not isinstance(request, dict) or kind not in {'code', 'asset'}:
        raise ValueError('expected a code or asset request object')
    value = dict(request)
    timeout = value.setdefault('timeout_seconds', 1800 if value.get('preset') in ('video', 'video_edit') else 600)
    if type(timeout) is not int or timeout <= 0 or timeout > 86400:
        raise ValueError('timeout_seconds must be an integer between 1 and 86400')
    if kind == 'code':
        if not isinstance(value.get('task'), str) or not value['task'].strip():
            raise ValueError('code task must be nonempty text')
        checks = value.get('checks')
        if not isinstance(checks, list) or not checks or any(
            not isinstance(c, list) or not c or any(not isinstance(a, str) or not a for a in c)
            for c in checks
        ):
            raise ValueError('checks must be a nonempty list of argv lists')
    else:
        import media
        if value.get('preset') not in media.PRESETS:
            raise ValueError('unknown asset preset')
    return value


class JobStore:
    """JOB-1: One immutable request and atomically updated status per UUID job."""

    def __init__(self, root):
        self.root = Path(root)

    def create(self, kind, request, workspace):
        validate_request(kind, request, workspace)
        asset_details = {}
        if kind == 'asset':
            import media
            preset = request['preset']
            asset_details = {'preset': preset, 'model': media.workflow_model(preset)}
        job_id = str(uuid.uuid4())
        folder = self.root / 'jobs' / job_id
        folder.mkdir(parents=True)
        write_json(folder / 'request.json', request)
        state = {**asset_details, 'id': job_id, 'kind': kind, 'state': 'queued',
                 'workspace': str(Path(workspace).resolve()), 'created_at': time.time(),
                 'updated_at': time.time(), 'log': str(folder / 'worker.log')}
        write_json(folder / 'status.json', state)
        return state

    def folder(self, job_id):
        try:
            if str(uuid.UUID(job_id)) != job_id:
                raise ValueError
        except (ValueError, AttributeError, TypeError):
            raise ValueError('invalid job ID') from None
        folder = self.root / 'jobs' / job_id
        if not folder.is_dir():
            raise ValueError('unknown job ID')
        return folder

    def read(self, job_id):
        return read_json(self.folder(job_id) / 'status.json')

    def update(self, job_id, **values):
        state = self.read(job_id)
        if state['state'] in TERMINAL:
            raise ValueError('job is already terminal')
        state.update(values, updated_at=time.time())
        write_json(self.folder(job_id) / 'status.json', state)
        return state


class GpuLease:
    """GPU-1/BOOT-2: Serialize projects and block all handoffs behind either durable
    uncertainty guard. See tests/test_bootstrap_install.py for delayed alias promotion.
    """

    def __init__(self, root):
        self.path = Path(root) / 'gpu.lock'
        self.unconfirmed = Path(root) / 'unconfirmed-prompt.json'
        self.unconfirmed_alias = Path(root) / 'unconfirmed-ollama-alias.json'
        self.handle = None

    def acquire(self):
        if self.handle is not None:
            return True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open('a+b')
        try:
            if os.name == 'nt':
                import msvcrt
                if self.path.stat().st_size == 0:
                    handle.write(b'0')
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            return False
        self.handle = handle
        if os.path.lexists(self.unconfirmed):
            self.release()
            raise RuntimeError(f'GPU handoff requires operator verification of the prior submission: {self.unconfirmed}')
        if os.path.lexists(self.unconfirmed_alias):
            self.release()
            raise RuntimeError(f'GPU handoff requires operator reconciliation of the Ollama alias: {self.unconfirmed_alias}')
        return True

    def release(self):
        if self.handle is not None:
            if os.name == 'nt':
                import msvcrt
                self.handle.seek(0)
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            self.handle.close()
            self.handle = None


class WindowsJob:
    """PROC-1: Kernel job membership kills descendants even if taskkill fails.

    Evidence: CoreTests.test_timeout_also_stops_grandchildren uses real children.
    """

    def __init__(self, process):
        from ctypes import wintypes as w
        class Basic(ctypes.Structure):
            _fields_ = [('time1',ctypes.c_longlong),('time2',ctypes.c_longlong),('flags',w.DWORD),
                        ('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active',w.DWORD),
                        ('affinity',ctypes.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
        class Extended(ctypes.Structure):
            _fields_ = [('basic',Basic),('io',ctypes.c_ulonglong*6),
                        ('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),
                        ('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
        self.kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p,w.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = w.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD]
        self.kernel.AssignProcessToJobObject.argtypes = [w.HANDLE,w.HANDLE]
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.handle = self.kernel.CreateJobObjectW(None,None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)) or not self.kernel.AssignProcessToJobObject(self.handle,int(process._handle)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def resume_windows_process(pid):
    """PROC-1: Resume the suspended main thread only after job containment."""
    from ctypes import wintypes as w
    class ThreadEntry(ctypes.Structure):
        _fields_=[('size',w.DWORD),('usage',w.DWORD),('thread_id',w.DWORD),
                  ('owner_pid',w.DWORD),('priority',w.LONG),('delta',w.LONG),('flags',w.DWORD)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes=[w.DWORD,w.DWORD]
    kernel.CreateToolhelp32Snapshot.restype=w.HANDLE
    kernel.Thread32First.argtypes=[w.HANDLE,ctypes.POINTER(ThreadEntry)]
    kernel.Thread32Next.argtypes=[w.HANDLE,ctypes.POINTER(ThreadEntry)]
    kernel.OpenThread.argtypes=[w.DWORD,w.BOOL,w.DWORD]
    kernel.OpenThread.restype=w.HANDLE
    kernel.ResumeThread.argtypes=[w.HANDLE]
    kernel.ResumeThread.restype=w.DWORD
    kernel.CloseHandle.argtypes=[w.HANDLE]
    snapshot=kernel.CreateToolhelp32Snapshot(4,0)
    if snapshot == w.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry=ThreadEntry();entry.size=ctypes.sizeof(entry)
        found=kernel.Thread32First(snapshot,ctypes.byref(entry))
        while found:
            if entry.owner_pid == pid:
                thread=kernel.OpenThread(2,False,entry.thread_id)
                if not thread:raise ctypes.WinError(ctypes.get_last_error())
                try:
                    if kernel.ResumeThread(thread) == 0xffffffff:
                        raise ctypes.WinError(ctypes.get_last_error())
                finally:kernel.CloseHandle(thread)
                return
            found=kernel.Thread32Next(snapshot,ctypes.byref(entry))
        raise RuntimeError('suspended child main thread not found')
    finally:kernel.CloseHandle(snapshot)


def run_command(argv, cwd, log, deadline, cancelled, env=None, stdin_path=None):
    """PROC-1: Return exit code, or raise TimeoutError/InterruptedError after cleanup."""
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    flags = (subprocess.CREATE_NO_WINDOW | 0x4) if os.name == 'nt' else 0
    with contextlib.ExitStack() as stack:
        stream = stack.enter_context(Path(log).open('ab'))
        input_stream = stack.enter_context(Path(stdin_path).open('rb')) if stdin_path else subprocess.DEVNULL
        process = subprocess.Popen(argv, cwd=cwd, stdout=stream, stderr=stream,
                                   stdin=input_stream, env=env, creationflags=flags,
                                   start_new_session=os.name != 'nt')
        tree = None
        try:
            if os.name == 'nt':
                tree = WindowsJob(process)
                resume_windows_process(process.pid)
            while process.poll() is None:
                if cancelled():
                    raise InterruptedError('cancel requested')
                if time.monotonic() >= deadline:
                    raise TimeoutError('job deadline exceeded')
                time.sleep(0.1)
            if cancelled():
                raise InterruptedError('cancel requested')
            return process.returncode
        finally:
            if tree:
                tree.close()
            if process.poll() is None:
                if os.name != 'nt':
                    import signal
                    os.killpg(process.pid, signal.SIGKILL)
                elif tree is None:
                    process.kill()
                process.wait(timeout=10)


def code_command(config, workspace):
    """CODE-1: Build isolated local-only Codex argv and environment.

    CODE-CONTEXT: Advertise 262144 tokens to the local coding client, matching
    the Qwen worker alias allocation. tests/test_core.py checks the client;
    live Ollama probes separately verify configured and actually loaded context.
    """
    executable = config.get('codex') or shutil.which('codex') or shutil.which('codex.exe')
    if not executable:
        raise ValueError('codex executable is not on PATH')
    argv = [executable, 'exec', '--ignore-user-config', '--ephemeral', '--oss',
            '--local-provider', 'ollama', '-m', config['model'], '--json',
            '--sandbox', 'workspace-write', '-C', str(workspace),
            '-c', 'agents.enabled=false', '-c', 'features.apps=false',
            '-c', 'skills.include_instructions=false', '-c', 'skills.bundled.enabled=false',
            '-c', 'features.plugins=false', '-c', 'web_search="disabled"',
            '-c', 'model_context_window=262144', '-c', 'model_reasoning_effort="none"',
            '-c', 'model_provider="ollama"',
            '-c', 'cli_auth_credentials_store="file"',
            '-c', 'windows.sandbox="mxc"',
            '-c', 'approval_policy="never"']
    platform_vars = {'PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP',
                     'USERPROFILE','APPDATA','LOCALAPPDATA','PROGRAMDATA','SYSTEMDRIVE',
                     'HOMEDRIVE','HOMEPATH','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}
    env = {k:v for k,v in os.environ.items() if k.upper() in platform_vars}
    env['CODEX_HOME'] = str(Path(config.get('worker_home', BASE/'.runtime'/'codex-home')).resolve())
    env['CODEX_HARNESS_WORKER'] = '1'
    env['OLLAMA_HOST'] = config['ollama_url']
    env['PYTHONUTF8'] = '1'
    return argv, env


def execute_job(store, job_id, config):
    """JOB-2: Persist success/failure/cancel/timeout, release GPU in all cases.

    Code exits awaiting_review only after checks pass. Asset success requires
    fetched, decoded outputs. Evidence: tests/test_jobs.py; media.py contracts.
    """
    state = store.read(job_id)
    folder = store.folder(job_id)
    request = validate_request(state['kind'], read_json(folder/'request.json'), state['workspace'])
    deadline = time.monotonic() + max(0, state['created_at'] + request['timeout_seconds'] - time.time())
    lease = GpuLease(GPU_ROOT)
    last_heartbeat = 0

    def cancelled():
        nonlocal last_heartbeat
        if time.monotonic() - last_heartbeat > 2:
            store.update(job_id, heartbeat=time.time())
            last_heartbeat = time.monotonic()
        return (folder/'cancel').exists()

    def checkpoint():
        if cancelled():
            raise InterruptedError('cancel requested')
        if time.monotonic() >= deadline:
            raise TimeoutError('job deadline exceeded')

    prompt_id = None
    try:
        checkpoint()
        if state['kind'] == 'asset':
            import media
            model = media.workflow_model(request['preset'])
        else:
            model = config['model']
        store.update(job_id, state='waiting_gpu', worker_pid=os.getpid(), model=model)
        if state['kind'] == 'asset':
            prepared = media.prepare(request['preset'], {k:v for k,v in request.items() if k not in {'preset','timeout_seconds'}}, config['comfy_url'])
            if request['preset'] == 'video_edit':
                source = media.validate_video_source(
                    request['reference_video'], config.get('comfy_input_dir'),
                    prepared['frame_count'], config.get('decoder_python'),
                    deadline=deadline, cancelled=cancelled, expected_aspect=(prepared['width'], prepared['height']))
                write_json(folder/'source.json', source)
            write_json(folder/'workflow.json', prepared)
        while not lease.acquire():
            checkpoint()
            time.sleep(0.25)
        prepare_gpu(state['kind'], config, deadline, cancelled)
        checkpoint()
        store.update(job_id, state='running')
        if state['kind'] == 'code':
            argv, env = code_command(config, state['workspace'])
            Path(env['CODEX_HOME']).mkdir(parents=True,exist_ok=True)
            prompt = (
                'You are the local implementation worker, not the coordinator. '
                'Do not invoke the harness, delegate agents, change global configuration, '
                'commit, push, or install dependencies. Preserve existing user work. '
                'Implement the supplied contract without weakening acceptance tests. '
                'The coordinator has already established the task branch and red evidence.\n\n'
                'Do not repeat repository discovery or inspect Git history. Read the task-relevant '
                'files, implement, then run the specified checks. Stop and report concrete tool '
                'errors instead of cycling through alternative shells.\n\n'
                + request['task']
            )
            (folder/'prompt.txt').write_text(prompt, encoding='utf-8')
            rc = run_command(argv+['-'], state['workspace'], folder/'worker.log', deadline, cancelled, env, folder/'prompt.txt')
            if rc:
                raise RuntimeError(f'Qwen exited with code {rc}; see worker.log')
            store.update(job_id, state='checking')
            for index, command in enumerate(request['checks']):
                checkpoint()
                rc = run_command(command, state['workspace'], folder/f'check-{index}.log', deadline, cancelled)
                if rc:
                    raise RuntimeError(f'check {index} exited with code {rc}; see check-{index}.log')
            result = fingerprint(state['workspace'])
            checkpoint()
            store.update(job_id, state='awaiting_review', fingerprint=result,
                         checks=request['checks'], completed_at=time.time())
        else:
            # The job UUID is durable before Comfy can begin asynchronous validation.
            endpoint = config['comfy_url']
            store.update(job_id, prompt_id=job_id, comfy_url=endpoint, submission='unconfirmed', operator_check_required=True)
            write_json(lease.unconfirmed, {'job_id': job_id, 'prompt_id': job_id, 'comfy_url': endpoint,
                                          'job_directory': str(folder.resolve())})
            prompt_id = job_id
            try:
                media.submit(prepared, endpoint, prompt_id)
            except media.PromptRejected:
                prompt_id = None
                lease.unconfirmed.unlink()
                store.update(job_id, submission='rejected', operator_check_required=False)
                raise
            lease.unconfirmed.unlink()
            store.update(job_id, submission='acknowledged', operator_check_required=False)
            while True:
                checkpoint()
                result = media.poll(prompt_id, config['comfy_url'], prepared['output_nodes'])
                if result['state'] == 'failed':
                    raise RuntimeError(str(result.get('error', 'ComfyUI failed')))
                if result['state'] == 'succeeded':
                    outputs = media.retrieve(result['outputs'], folder/'outputs', prepared['kind'],
                                             config['comfy_url'], config.get('decoder_python'),
                                             deadline=deadline,cancelled=cancelled)
                    checkpoint()
                    store.update(job_id, state='succeeded', outputs=[str(p) for p in outputs], completed_at=time.time())
                    break
                time.sleep(1)
    except (Exception, KeyboardInterrupt) as error:
        if prompt_id:
            try:
                cancel_prompt_once(folder, prompt_id, config['comfy_url'])
            except Exception as cleanup_error:
                store.update(job_id, cleanup_error=str(cleanup_error))
        final = 'cancelled' if isinstance(error, (InterruptedError, KeyboardInterrupt)) else 'timed_out' if isinstance(error, TimeoutError) else 'failed'
        store.update(job_id, state=final, error=str(error), completed_at=time.time())
    finally:
        if lease.handle is not None and state['kind'] == 'code':
            try:
                http_json(config['ollama_url']+'/api/generate', {'model': config['model'], 'keep_alive': 0})
            except Exception as error:
                (folder/'cleanup-warning.txt').write_text(str(error), encoding='utf-8')
        lease.release()


def record_review(store, job_id, review):
    """REVIEW-1: Accept only Terra's explicit approval of the unchanged diff.

    This records coordinator-supplied review evidence, not reviewer identity
    authentication or a repository merge gate. Evidence: tests/test_jobs.py.
    """
    state = store.read(job_id)
    if state['state'] != 'awaiting_review':
        raise ValueError('job is not awaiting review')
    if (not isinstance(review, dict) or review.get('model') != 'gpt-6.1-terra'
            or review.get('verdict') not in {'approved', 'changes_requested'}
            or not isinstance(review.get('summary'), str) or not review['summary'].strip()):
        raise ValueError('review must name Terra, an explicit verdict, and a nonempty summary')
    if state['fingerprint'] != fingerprint(state['workspace']):
        raise ValueError('workspace changed after checks; rerun checks and review in a new job')
    write_json(store.folder(job_id)/'review.json', review)
    return store.update(job_id, state='succeeded' if review['verdict'] == 'approved' else 'changes_requested', review=review)


def fingerprint(workspace):
    """REVIEW-1: Hash tracked diff and untracked contents, including new tests."""
    digest = hashlib.sha256()
    head = subprocess.run(['git','rev-parse','HEAD'],cwd=workspace,capture_output=True,check=True).stdout
    digest.update(head)
    diff = subprocess.run(['git','diff','--binary','HEAD','--'], cwd=workspace, capture_output=True, check=True).stdout
    digest.update(diff)
    paths = subprocess.run(['git','ls-files','--others','--exclude-standard','-z'],cwd=workspace,capture_output=True,check=True).stdout
    for raw in sorted(p for p in paths.split(b'\0') if p):
        path = Path(workspace)/os.fsdecode(raw)
        if path.is_symlink():
            digest.update(raw+b'\0'+os.readlink(path).encode())
        elif path.is_file():
            digest.update(raw+b'\0'+hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def http_json(url, data=None):
    payload = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(url, data=payload, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read()
        return json.loads(body) if body.strip() else {}


def prepare_gpu(kind, config, deadline, cancelled):
    """GPU-1: Wait for Comfy's queue, unload the other engine, respect stop.

    External Comfy jobs are never interrupted to make room for a harness job.
    """
    def check():
        if cancelled():
            raise InterruptedError('cancel requested')
        if time.monotonic() >= deadline:
            raise TimeoutError('deadline while waiting for GPU')
    while True:
        check()
        queue = http_json(config['comfy_url']+'/queue')
        if not queue['queue_running'] and not queue['queue_pending']:
            break
        time.sleep(1)
    if kind == 'code':
        http_json(config['comfy_url']+'/free', {'unload_models':True, 'free_memory':True})
        while True:
            check()
            devices = http_json(config['comfy_url']+'/system_stats').get('devices', [])
            if all(d.get('torch_vram_total', 0) < 100*1024*1024 for d in devices):
                return
            time.sleep(0.5)
    else:
        unload_requested = False
        while True:
            check()
            try:
                models = http_json(config['ollama_url']+'/api/ps')['models']
            except ConnectionRefusedError:
                return
            except urllib.error.URLError as error:
                if isinstance(error.reason, ConnectionRefusedError):
                    return
                raise
            if not isinstance(models, list):
                raise ValueError('Malformed Ollama residency response')
            names = [m.get('name') if isinstance(m, dict) else None for m in models]
            if any(not isinstance(name, str) or not name.strip() for name in names):
                raise ValueError('Malformed model name in Ollama residency response')
            if config['model'] not in names:
                return
            if not unload_requested:
                http_json(config['ollama_url']+'/api/generate', {'model':config['model'], 'keep_alive':0})
                unload_requested = True
            else:
                time.sleep(0.5)


def start_job(store, kind, request, workspace, config_path):
    """CLI-1: Validate first; spawn a hidden supervisor and return a durable ID.

    Code work requires a Git task branch with an existing base commit. No
    checkout, pull, commit, or reset occurs here. Evidence: tests/test_cli.py.
    """
    request = validate_request(kind, request, workspace)
    workspace = Path(workspace).resolve()
    if kind == 'code':
        branch = subprocess.run(['git','branch','--show-current'],cwd=workspace,capture_output=True,text=True,check=True).stdout.strip()
        if not branch or branch in {'main','master'}:
            raise ValueError('create a task branch before starting code work')
        subprocess.run(['git','rev-parse','--verify','HEAD'],cwd=workspace,capture_output=True,check=True)
    else:
        import media
        media.prepare(request['preset'], {k:v for k,v in request.items() if k not in {'preset','timeout_seconds'}})
    state = store.create(kind, request, workspace)
    folder = store.folder(state['id'])
    flags = (subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == 'nt' else 0
    try:
        with (folder/'supervisor.log').open('ab') as log:
            process=subprocess.Popen([sys.executable,str(BASE/'harness.py'),'--config',str(Path(config_path).resolve()),
                              '--state-dir',str(store.root.resolve()),'_worker',state['id']],
                             cwd=BASE, stdin=subprocess.DEVNULL,stdout=log,stderr=log,
                             creationflags=flags,start_new_session=os.name != 'nt')
            write_json(folder/'owner.json',{'pid':process.pid,'identity':process_identity(process.pid)})
    except OSError as error:
        store.update(state['id'],state='failed',error=str(error))
        raise
    return state


def doctor(config):
    """CLI-1: Service failures are explicit data, never an implied ready state."""
    result = {'model':config['model']}
    for name, url in [('ollama',config['ollama_url']+'/api/tags'),('comfyui',config['comfy_url']+'/system_stats')]:
        try:
            data = http_json(url)
            if name == 'ollama':
                models = data.get('models',[])
                result[name] = {'available':True,'model_installed':any(m['name']==config['model'] for m in models),'models':models}
            else:
                result[name] = {'available':True,'version':data['system']['comfyui_version'],'devices':data['devices']}
        except Exception as error:
            result[name] = {'available':False,'error':str(error)}
    result['local_worker_ready'] = result['ollama'].get('model_installed', False)
    result['ready'] = result['comfyui']['available']
    try:
        import media
        result['presets'] = {}
        for preset in media.PRESETS:
            status = result['presets'][preset] = {'ready': False}
            try:
                required = media.workflow_template(preset).get('required_inputs', ['prompt'])
                status['required_inputs'] = required
                if not result['comfyui']['available']:
                    status['error'] = result['comfyui']['error']
                    continue
                # Dependency inspection never submits or opens these source files.
                diagnostic = {'prompt': 'readiness check', 'reference_video': 'diagnostic.mp4', 'reference_image': 'diagnostic.png'}
                media.prepare(preset, {key: diagnostic[key] for key in required}, config['comfy_url'])
                status['ready'] = True
            except Exception as error:
                status['error'] = str(error)
    except ImportError:
        result['presets'] = {'error':'media module not installed'}
    result['ready'] = result['ready'] and all(p.get('ready',False) for p in result['presets'].values() if isinstance(p,dict)) and 'error' not in result['presets']
    return result


def process_identity(pid):
    """JOB-3: Return a live process creation identity, or None after exit."""
    if os.name != 'nt':
        try:
            return Path(f'/proc/{int(pid)}/stat').read_text().rsplit(')',1)[1].split()[19]
        except FileNotFoundError:return None
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]
    kernel.OpenProcess.restype=w.HANDLE
    kernel.GetExitCodeProcess.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)]
    kernel.GetProcessTimes.argtypes=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4
    kernel.CloseHandle.argtypes=[w.HANDLE]
    handle=kernel.OpenProcess(0x1000,False,int(pid))
    if not handle:
        error=ctypes.get_last_error()
        if error==87:return None
        raise ctypes.WinError(error)
    try:
        exit_code=w.DWORD()
        if not kernel.GetExitCodeProcess(handle,ctypes.byref(exit_code)):
            raise ctypes.WinError(ctypes.get_last_error())
        if exit_code.value!=259:return None
        created,exited,kern,user=(w.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle,ctypes.byref(created),ctypes.byref(exited),ctypes.byref(kern),ctypes.byref(user)):
            raise ctypes.WinError(ctypes.get_last_error())
        return str((created.dwHighDateTime<<32)|created.dwLowDateTime)
    finally:kernel.CloseHandle(handle)


def inspect_job(store, job_id):
    """JOB-3: A vanished/reused supervisor cannot leave an active job forever.

    Detect death when status is read; never kill a PID based on stored metadata.
    Evidence: tests/test_supervisor.py uses a real terminated supervisor fixture.
    """
    state=store.read(job_id)
    if state['state'] in TERMINAL|{'awaiting_review'}:return state
    owner=store.folder(job_id)/'owner.json'
    if owner.exists():
        identity=read_json(owner)
        try:alive=process_identity(identity['pid'])
        except PermissionError:return dict(state,supervisor_visibility='unavailable from current sandbox')
        vanished=alive is None or alive!=identity['identity']
    else:
        vanished=time.time()-state['created_at']>10
    if vanished:
        state=store.update(job_id,state='cancelled' if (store.folder(job_id)/'cancel').exists() else 'failed',
                           error='supervisor exited before completing job',completed_at=time.time())
    return state


def cancel_prompt_once(folder, prompt_id, comfy_url):
    import media
    try:
        (folder/'prompt-cancel-requested').touch(exist_ok=False)
    except FileExistsError:
        return
    media.cancel(prompt_id, comfy_url)


def cancel_job(store, job_id, config):
    """JOB-3/MEDIA-CANCEL: Cancel a known prompt even after supervisor death.

    Never interrupt a queue globally or infer process ownership from a PID.
    Evidence: tests/test_supervisor.py::test_orphan_media_cancel_is_targeted.
    """
    state=inspect_job(store,job_id)
    if state['state'] in {'succeeded','awaiting_review','changes_requested'}:
        return state
    (store.folder(job_id)/'cancel').touch()
    if state['state'] in TERMINAL and state.get('prompt_id') and state.get('submission') != 'rejected':
        cancel_prompt_once(store.folder(job_id), state['prompt_id'], state.get('comfy_url', config['comfy_url']))
    return dict(state,cancel_requested=True)


def main():
    parser = argparse.ArgumentParser(description='Bounded local Qwen and ComfyUI jobs for Codex')
    parser.add_argument('--config',type=Path,default=BASE/'config.json')
    parser.add_argument('--state-dir',type=Path,default=BASE/'.runtime')
    commands = parser.add_subparsers(dest='command',required=True)
    commands.add_parser('doctor')
    for kind in ['code','asset']:
        command = commands.add_parser(kind)
        command.add_argument('action',choices=['start'])
        command.add_argument('--request',type=Path,required=True)
        command.add_argument('--workspace',type=Path,required=True)
    for name in ['status','cancel','_worker']:
        command = commands.add_parser(name)
        command.add_argument('job_id')
    review = commands.add_parser('review')
    review.add_argument('job_id')
    review.add_argument('--result',type=Path,required=True)
    args = parser.parse_args()
    try:
        config = read_json(args.config)
        store = JobStore(args.state_dir)
        if args.command == 'doctor':
            result = doctor(config)
        elif args.command in {'code','asset'}:
            result = start_job(store,args.command,read_json(args.request),args.workspace,args.config)
        elif args.command == '_worker':
            execute_job(store,args.job_id,config)
            return 0
        elif args.command == 'review':
            result = record_review(store,args.job_id,read_json(args.result))
        else:
            result = cancel_job(store,args.job_id,config) if args.command=='cancel' else inspect_job(store,args.job_id)
        print(json.dumps(result,indent=2))
        return 0
    except Exception as error:
        print(json.dumps({'error':str(error)}),file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
