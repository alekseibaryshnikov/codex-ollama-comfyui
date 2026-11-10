"""BOOT-1..4 in bootstrap.py. Real temporary files, simulated Git, pip and Ollama."""

from contextlib import redirect_stdout
from io import BytesIO, StringIO
from pathlib import Path
from subprocess import CompletedProcess
import hashlib
import json
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import bootstrap


class BootstrapInstallTests(unittest.TestCase):
    def setUp(self):
        work = Path(__file__).resolve().parents[1]/'work'
        work.mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(dir=work)
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        (self.base/'locks').mkdir()
        (self.base/'work').mkdir()
        (self.base/'manifests').mkdir()
        self.root = self.base/'Comfy'
        self.app = self.root/'app'
        self.python = self.root/'python/Scripts/python.exe'
        self.config = {'comfy_root': str(self.app), 'decoder_python': str(self.python),
                       'comfy_input_dir': str(self.app/'input'), 'model': 'qwen:worker',
                       'ollama_url': 'http://127.0.0.1:11434', 'comfy_url': 'http://127.0.0.1:8189'}
        self.save('config.json', self.config)
        self.locks = {'comfyui': {'repository': 'https://github.com/Comfy-Org/ComfyUI.git',
                                  'commit': 'a'*40},
                      'ollama': {'base_model': 'qwen:base', 'worker_model': 'qwen:worker',
                                 'base_digest': 'sha256:'+'b'*64, 'context_length': 262144}}
        self.save('locks/runtime.json', self.locks)
        (self.base/'locks/comfy-requirements.txt').write_text('sample==1.0')
        self.models = {'qwen:base': 'b'*64, 'qwen:worker': 'c'*64}
        self.api_calls = []
        self.save('manifests/catalog.json', {'files': [], 'voice_assembly': None})

    def save(self, path, data):
        (self.base/path).write_text(json.dumps(data), encoding='utf-8')

    def service(self, endpoint, payload=None, method=None):
        self.api_calls.append((endpoint, payload))
        if endpoint == 'tags':
            return {'models': [{'name': key, 'digest': value} for key, value in self.models.items()]}
        if endpoint == 'pull':
            self.models[payload['model']] = 'b'*64
            return {'status': 'success'}
        if endpoint == 'copy':
            self.models[payload['destination']] = self.models[payload['source']]
            return {}
        if endpoint == 'create':
            self.assertEqual(payload['from'], 'qwen:base')
            self.assertEqual(payload['parameters'], {'num_ctx': 262144})
            self.assertIs(payload['stream'], False)
            self.models[payload['model']] = 'd'*64
            return {'status': 'success'}
        if endpoint == 'show':
            return {'parameters': 'temperature 0.6\nnum_ctx 262144\n'}
        if endpoint == 'delete':
            del self.models[payload['model']]
            return {}
        self.fail('Unexpected endpoint '+endpoint)

    def test_absent_base_is_pulled_and_old_worker_survives_as_backup(self):
        """BOOT-2: a pull verifies its digest before replacing an existing worker."""
        del self.models['qwen:base']
        with patch.object(bootstrap, 'ollama_request', self.service):
            result = bootstrap.setup_ollama(True, self.base)
        self.assertEqual(self.models['qwen:worker'], 'd'*64)
        self.assertEqual(self.models[result['backup']], 'c'*64)
        self.assertEqual(self.api_calls[1], ('pull', {'model':'qwen:base', 'stream':False}))

    def test_existing_base_drift_stops_before_any_model_mutation(self):
        """BOOT-2: a changed registry tag cannot silently substitute weights."""
        self.models['qwen:base'] = 'e'*64
        with patch.object(bootstrap, 'ollama_request', self.service), self.assertRaisesRegex(ValueError, 'digest'):
            bootstrap.setup_ollama(True, self.base)
        self.assertEqual(self.api_calls, [('tags', None)])

    def test_failed_creation_or_unverified_alias_preserves_previous_worker(self):
        """BOOT-2: even a lost final response may follow a completed mutation."""
        for failure in ('create', 'show'):
            def fail(endpoint, payload=None, method=None):
                response = self.service(endpoint, payload, method)
                if endpoint == failure:
                    raise OSError('lost response')
                return response
            with self.subTest(failure=failure), patch.object(bootstrap, 'ollama_request', fail):
                with self.assertRaisesRegex((ValueError, OSError, RuntimeError), 'lost response'):
                    bootstrap.setup_ollama(True, self.base)
                self.assertEqual(self.models['qwen:worker'], 'c'*64)

    def test_response_requires_bounded_json_except_empty_copy_ack(self):
        """BOOT-2: an empty copy ack is legal; tags and oversized bodies are errors."""
        for endpoint, body in [('tags', b''), ('tags', b'x'*4194305), ('create', b'{"error":"bad model"}')]:
            conn = Mock()
            conn.getresponse.return_value = Mock(status=200, read=BytesIO(body).read)
            with self.subTest(endpoint=endpoint), patch('http.client.HTTPConnection', return_value=conn):
                with self.assertRaisesRegex(ValueError, 'empty|exceeds|bad model'):
                    bootstrap.ollama_request(endpoint)
        conn = Mock()
        conn.getresponse.return_value = Mock(status=200, read=BytesIO().read)
        with patch('http.client.HTTPConnection', return_value=conn):
            self.assertEqual(bootstrap.ollama_request('copy', {}), {})

    def test_unowned_application_or_venv_is_refused_before_git_or_pip(self):
        """BOOT-3: even empty directories belong to the operator until claimed."""
        for child in (self.app, self.root/'python'):
            child.mkdir(parents=True)
            with self.subTest(child=child), patch('subprocess.run') as run:
                with self.assertRaisesRegex((ValueError, FileExistsError), 'existing|owned'):
                    bootstrap.install_comfy(True, self.base)
                run.assert_not_called()
            child.rmdir()

    def test_locked_install_reuses_only_matching_receipts(self):
        """BOOT-3: simulated Git/pip leave real receipts; lock drift invokes neither."""
        commands = []
        def run(argv, **kwargs):
            args = list(map(str, argv))
            commands.append(args)
            if 'venv' in args:
                self.python.parent.mkdir(parents=True)
                self.python.touch()
            if 'checkout' in args:
                (self.app/'main.py').touch()
            return CompletedProcess(args, 0, 'a'*40+'\n' if 'rev-parse' in args else '', '')
        with patch('sys.version_info', (3, 12, 8)), patch('subprocess.run', run):
            bootstrap.install_comfy(True, self.base)
            self.assertTrue(any('a'*40 in c for c in commands))
            self.assertTrue(any('--require-hashes' in c and str(self.base/'locks/comfy-requirements.txt') in c for c in commands))
            commands.clear()
            bootstrap.install_comfy(True, self.base)
            self.assertFalse(any('install' in c or 'checkout' in c for c in commands))
            (self.base/'locks/comfy-requirements.txt').write_text('sample==2')
            with self.assertRaisesRegex(ValueError, 'lock|receipt'):
                bootstrap.install_comfy(True, self.base)
            self.assertFalse(any('install' in c for c in commands))

    def test_run_uses_foreground_argv_and_verify_exposes_decoder_and_doctor(self):
        """BOOT-3/4: observable launch flags and failed media imports affect readiness."""
        self.create_core()
        real_run = subprocess.run
        def run_or_simulate(argv, **kwargs):
            if argv[0] == 'git':
                return real_run(argv, **kwargs)
            return CompletedProcess(argv, 0)
        with patch('subprocess.run', side_effect=run_or_simulate) as run:
            bootstrap.run_comfy(self.base)
        args = list(map(str, run.call_args.args[0]))
        self.assertIn('--offline', args)
        self.assertEqual(args[args.index('--listen')+1], '127.0.0.1')
        self.assertEqual(args[args.index('--port')+1], '8189')
        self.assertEqual(args[args.index('--reserve-vram')+1], '3.5')
        self.assertEqual(args[0], str(self.python))
        self.assertFalse(run.call_args.kwargs.get('shell', False))
        with patch('subprocess.run', side_effect=FileNotFoundError('missing decoder')), patch('harness.doctor', return_value={'ready':True, 'local_worker_ready': True}):
            report = bootstrap.verify(self.base)
        self.assertFalse(report['ready'])
        self.assertIn('missing decoder', report['decoder']['error'])

    def test_config_rejects_windows_paths_before_replacing_previous_config(self):
        """BOOT-1: NTFS streams, devices and backslashes cannot escape safe catalog names."""
        old = (self.base/'config.json').read_bytes()
        for bad in ('models\\evil.bin', 'weights.bin:stream', 'dir/CON.txt', 'foo./weight'):
            self.save('manifests/catalog.json', {'schema_version':1, 'python_packages':[],
                'files':[], 'voice_assembly': {'destination_root':'comfy','destination':bad}})
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                bootstrap.configure(self.root, self.base)
        self.assertEqual((self.base/'config.json').read_bytes(), old)

    def test_cli_models_requires_approval_before_provisioning(self):
        """BOOT-2: the public command gates download and passes the generated manifest."""
        with patch('provision.provision', return_value={'state':'provisioned'}) as provision, redirect_stdout(StringIO()):
            self.assertEqual(bootstrap.main(['models', '--approved'], self.base), 0)
        args, kwargs = provision.call_args
        self.assertEqual(Path(args[0]), self.base/'work/download-manifest.json')
        self.assertTrue(kwargs.get('approved', args[1] if len(args)>1 else False))


    def test_late_create_targets_only_a_private_alias(self):
        """BOOT-2: the daemon may still finish creating a model after an HTTP timeout."""
        pending = []
        def late(endpoint, payload=None, method=None):
            if endpoint == 'create':
                pending.append(payload.copy())
                raise TimeoutError('Ollama still creating')
            return self.service(endpoint, payload, method)
        with patch.object(bootstrap, 'ollama_request', late), self.assertRaisesRegex(OSError, 'still creating'):
            bootstrap.setup_ollama(True, self.base)
        self.service('create', pending[0])
        self.assertEqual(self.models['qwen:worker'], 'c'*64)

    def test_busy_harness_prevents_simultaneous_worker_replacement(self):
        """BOOT-2: a code job or another setup owns the harness lease; leave aliases as-is."""
        import harness
        lease = harness.GpuLease(self.base/'.runtime')
        self.assertTrue(lease.acquire())
        self.addCleanup(lease.release)
        with patch.object(bootstrap, 'ollama_request') as api, self.assertRaisesRegex(RuntimeError, 'busy'):
            bootstrap.setup_ollama(True, self.base)
        api.assert_not_called()

    def test_lost_or_delayed_copy_ack_requires_operator_reconciliation(self):
        """BOOT-2: late work on the daemon can outlive any client-side recovery."""
        import harness
        guard = self.base/'.runtime/unconfirmed-ollama-alias.json'
        for mode in ('delayed', 'applied'):
            self.models['qwen:worker'] = 'c'*64
            pending = []
            def fail(endpoint, payload=None, method=None):
                if endpoint == 'copy' and payload['destination'] == 'qwen:worker':
                    self.assertTrue(guard.is_file(), 'write marker before live promotion')
                    pending.append(payload.copy())
                    if mode == 'applied':
                        self.service(endpoint, payload, method)
                    raise TimeoutError('lost promotion acknowledgement')
                return self.service(endpoint, payload, method)
            with self.subTest(mode=mode), patch.object(bootstrap, 'ollama_request', fail):
                with self.assertRaisesRegex(RuntimeError, 'operator'):
                    bootstrap.setup_ollama(True, self.base)
                record = json.loads(guard.read_text())
                self.assertEqual(record['worker'], 'qwen:worker')
                self.assertEqual(self.models[record['backup']], record['previous_digest'])
                self.assertEqual(self.models[record['candidate']], record['candidate_digest'])
                if mode == 'delayed':
                    self.assertEqual(self.models['qwen:worker'], 'c'*64)
                    self.service('copy', pending[0])
                self.assertEqual(self.models['qwen:worker'], 'd'*64)
                with self.assertRaisesRegex(RuntimeError, 'unconfirmed-ollama-alias'):
                    harness.GpuLease(self.base/'.runtime').acquire()
                with self.assertRaisesRegex(RuntimeError, 'unconfirmed-ollama-alias'):
                    bootstrap.setup_ollama(True, self.base)
                guard.unlink()  # simulated operator verified the now-drained daemon
    def test_recreated_identical_model_does_not_accumulate_backups(self):
        """BOOT-2: a different daemon can produce a valid stable digest absent from the lock."""
        self.models['qwen:worker'] = 'd'*64
        with patch.object(bootstrap, 'ollama_request', self.service):
            result = bootstrap.setup_ollama(True, self.base)
        self.assertTrue(result['reused'])
        self.assertEqual(set(self.models), {'qwen:worker','qwen:base'})

    def create_core(self):
        """Real isolated tracked core and ignored files; no remote, venv or GPU."""
        self.app.mkdir(parents=True)
        def git(*args):
            return subprocess.run(['git', '-c', 'user.name=Bootstrap test',
                                   '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
                                   *args], cwd=self.app, check=True, capture_output=True, text=True).stdout.strip()
        git('init')
        (self.app/'main.py').write_text('# upstream core\n')
        (self.app/'.gitignore').write_text('custom_nodes/**\ncomfy/ignored.py\n*.pyc\n')
        git('add', 'main.py', '.gitignore')
        git('commit', '-m', 'local test core')
        self.locks['comfyui']['commit'] = git('rev-parse', 'HEAD')
        self.save('locks/runtime.json', self.locks)
        self.save(self.app.relative_to(self.base)/'.codex-comfy-bootstrap.json', self.locks['comfyui'])

    def test_dirty_tracked_source_blocks_reuse_and_launch_without_running_python(self):
        """BOOT-3: a pinned HEAD can have a modified tracked main.py. Preserve it."""
        self.create_core()
        (self.app/'main.py').write_text('# operator edits')
        git_run = subprocess.run
        def only_git(argv, **kwargs):
            self.assertEqual(argv[0], 'git', 'must detect edits before invoking Python')
            return git_run(argv, **kwargs)
        with patch('sys.version_info', (3, 12, 8)), patch('subprocess.run', only_git):
            for action, args in [(bootstrap.install_comfy, (True,self.base)), (bootstrap.run_comfy, (self.base,))]:
                with self.subTest(action=action.__name__), self.assertRaisesRegex(ValueError, 'tracked'):
                    action(*args)
        self.assertEqual((self.app/'main.py').read_text(), '# operator edits')
        self.assertFalse(self.python.exists())

    def test_ignored_executable_and_unknown_custom_node_refused(self):
        """BOOT-3: .gitignore cannot hide imported code or an unexpected custom node."""
        self.create_core()
        git_run = subprocess.run
        def only_git(argv, **kwargs):
            self.assertEqual(argv[0], 'git', 'untracked override must block launching Python')
            return git_run(argv, **kwargs)
        for relative in ('comfy/ignored.py', 'orphan.pyc', 'custom_nodes/other/package.txt',
                         'custom_nodes/evil.py', 'extra_model_paths.yaml'):
            item = self.app/relative
            item.parent.mkdir(parents=True, exist_ok=True)
            item.write_bytes(b'unapproved')
            with self.subTest(relative=relative), patch('subprocess.run', only_git), self.assertRaisesRegex(ValueError, 'untracked|unexpected'):
                bootstrap.run_comfy(self.base)
            self.assertEqual(item.read_bytes(), b'unapproved')
            item.unlink()

    def test_catalog_custom_node_source_requires_correct_digest_and_skips_model_payload(self):
        """BOOT-3: check approved node code before launching and leave model contents unread."""
        self.create_core()
        node = self.app/'custom_nodes/comfyui-kokoro'
        node.mkdir(parents=True)
        source, model = node/'__init__.py', node/'kokoro_v1.onnx'
        source.write_bytes(b'# approved')
        model.write_bytes(b'large data is checked by the provisioner')
        rows = [{'destination_root':'comfy','purpose':purpose,'destination':path.relative_to(self.app).as_posix(),
                 'size_bytes':path.stat().st_size,'sha256':sha} for purpose,path,sha in (
                     ('speech-node',source,hashlib.sha256(b'# approved').hexdigest()),
                     ('speech-model',model,'0'*64))]
        self.save('manifests/catalog.json', {'files':rows,'voice_assembly':None})
        git_run = subprocess.run
        launches = []
        def run(argv, **kwargs):
            if argv[0] == 'git':
                return git_run(argv, **kwargs)
            launches.append(argv)
            return CompletedProcess(argv, 0)
        with patch('subprocess.run', run):
            bootstrap.run_comfy(self.base)
            source.write_bytes(b'# modified')
            with self.assertRaisesRegex(ValueError, 'digest|hash'):
                bootstrap.run_comfy(self.base)
        self.assertEqual(len(launches), 1)
        self.assertEqual(source.read_bytes(), b'# modified')

    def test_first_check_after_provisioning_portable_catalog_layout(self):
        """BOOT-3/PROV-3: real downloads and Git checks, tiny fixture payloads at every catalog path.

        The completed voice archive stands in for offline synthesis. This checks layout
        and receipt behavior, not the contents of real weights, wheels or voice tensors.
        """
        import provision
        self.create_core()
        catalog_path = Path(__file__).resolve().parents[1]/'manifests/catalog.json'
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
        payloads = {}
        for row in catalog['files'] + catalog['python_packages']:
            self.assertRegex(row['sha256'], '^[a-f0-9]{64}$')
            payload = row['destination'].encode()
            payloads[row['source']] = payload
            row.update(size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        self.save('manifests/catalog.json', catalog)
        configured = bootstrap.configure(self.root, self.base)
        manifest = json.loads(Path(configured['manifest']).read_text())
        with patch.object(provision, 'open_remote', side_effect=lambda url: BytesIO(payloads[url])):
            for row in manifest['files'] + manifest['python_packages']:
                self.assertFalse(provision.download_file(row)['reused'])
        Path(manifest['voice_assembly']['destination']).write_bytes(b'assembled fixture')
        self.assertEqual(list(self.base.rglob('*.sha256')), [])
        bootstrap.check_core(self.app, self.locks['comfyui'], self.base)
