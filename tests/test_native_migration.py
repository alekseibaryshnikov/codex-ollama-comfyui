"""Native migration contracts in harness.py, bootstrap.py and install.py.

Real temporary files; process and HTTP boundaries mocked. No real profile or
account access is exercised.
"""
import contextlib, io, json, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
import bootstrap, harness, install

class NativeMigration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path('work').resolve()); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def test_code_refused_before_reads_or_spawn_and_replay_unchanged(self):
        """NATIVE-CODE: invalid input and historical jobs cannot start coding."""
        store=harness.JobStore(self.root/'state')
        with patch('harness.subprocess.Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'terra_coder.*terra'):
                harness.start_job(store,'code',{},self.root,self.root/'missing')
        spawn.assert_not_called(); self.assertFalse((self.root/'state').exists())
        job=store.create('code',{'task':'x','checks':[['true']]},self.root)
        before=(store.folder(job['id'])/'status.json').read_bytes()
        with patch('harness.prepare_gpu') as gpu, self.assertRaisesRegex(ValueError,'terra_coder.*terra'):
            harness.execute_job(store,job['id'],{})
        gpu.assert_not_called(); self.assertEqual((store.folder(job['id'])/'status.json').read_bytes(),before)
    def test_cli_refuses_before_missing_config(self):
        """NATIVE-CODE: CLI gives migration instruction before reading config/request."""
        p=subprocess.run([sys.executable,'harness.py','--config',str(self.root/'missing'),'code','start','--request',str(self.root/'missing'),'--workspace',str(self.root)],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0); self.assertIn('terra_coder',p.stderr)
    def test_doctor_no_ollama_and_gpu_handoff_without_legacy_pair(self):
        """NATIVE-CODE: doctor and fresh asset handoff contact only Comfy."""
        def http(url,data=None):
            self.assertNotIn('11434',url)
            if url.endswith('/queue'): return {'queue_running':[],'queue_pending':[]}
            return {'system':{'comfyui_version':'fixture'},'devices':[]}
        with patch('harness.http_json',side_effect=http):
            result=harness.doctor({'comfy_url':'http://comfy'})
            harness.prepare_gpu('asset',{'comfy_url':'http://comfy'},time.monotonic()+5,lambda:False)
        self.assertEqual(result['coding']['availability'],'not_probed'); self.assertEqual(result['coding']['model'],'gpt-6.1-terra')
        self.assertNotIn('local_worker_ready',result)
    def test_configure_fresh_and_same_root_legacy(self):
        """BOOT-NATIVE: legacy ownership survives only for the same Comfy root."""
        (self.root/'manifests').mkdir(); (self.root/'manifests/catalog.json').write_text(json.dumps({'schema_version':1,'files':[],'python_packages':[],'voice_assembly':None}))
        comfy=self.root/'comfy'; bootstrap.configure(comfy,self.root)
        path=self.root/'config.json'; config=json.loads(path.read_text())
        self.assertNotIn('model',config); self.assertNotIn('ollama_url',config); self.assertEqual(config['coding']['coder'],'terra_coder')
        config.update(model='owned',ollama_url='http://127.0.0.1:11434'); path.write_text(json.dumps(config))
        bootstrap.configure(comfy,self.root); self.assertEqual(json.loads(path.read_text())['model'],'owned')
        bootstrap.configure(self.root/'other',self.root); self.assertNotIn('model',json.loads(path.read_text()))
    def test_historical_root_identity_preserves_only_matching_pair(self):
        """BOOT-NATIVE: Old config without root retains ownership only for the same installation.

        Files are temporary; identity paths represent an old portable install.
        """
        (self.root/'manifests').mkdir(); (self.root/'manifests/catalog.json').write_text(json.dumps({'schema_version':1,'files':[],'python_packages':[],'voice_assembly':None}))
        comfy=self.root/'old-install'; path=self.root/'config.json'
        legacy={'comfy_input_dir':str(comfy/'app/input'), 'decoder_python':str(comfy/'python/Scripts/python.exe'), 'model':'owned', 'ollama_url':'http://127.0.0.1:11434'}
        path.write_text(json.dumps(legacy)); bootstrap.configure(comfy,self.root)
        self.assertEqual(json.loads(path.read_text())['model'],'owned')
        path.write_text(json.dumps(legacy)); bootstrap.configure(self.root/'different',self.root)
        self.assertNotIn('model',json.loads(path.read_text()))
        legacy['comfy_root']=str(comfy/'app'); legacy['decoder_python']=str(self.root/'different/python/Scripts/python.exe')
        path.write_text(json.dumps(legacy)); bootstrap.configure(comfy,self.root)
        self.assertNotIn('model',json.loads(path.read_text()))

    def test_reconfigure_matching_root_rejects_invalid_pair_without_writes(self):
        """BOOT-NATIVE: Invalid existing ownership cannot disappear on reconfiguration.

        Temporary files stand in for operator config and prior download manifest.
        """
        (self.root/'manifests').mkdir(); (self.root/'manifests/catalog.json').write_text(json.dumps({'schema_version':1,'files':[],'python_packages':[],'voice_assembly':None}))
        comfy=self.root/'old-install'; bootstrap.configure(comfy,self.root)
        path=self.root/'config.json'; manifest=self.root/'work/download-manifest.json'
        base=json.loads(path.read_text()); original_manifest=manifest.read_bytes()
        for pair in ({'model':'owned'}, {'ollama_url':'http://127.0.0.1:11434'}, {'model':'','ollama_url':'http://127.0.0.1:11434'}, {'model':'owned','ollama_url':''}):
            with self.subTest(pair=pair):
                path.write_text(json.dumps(dict(base,**pair))); original=path.read_bytes()
                with patch('harness.http_json') as http, self.assertRaises(ValueError):
                    bootstrap.configure(comfy,self.root)
                http.assert_not_called(); self.assertEqual(path.read_bytes(),original)
                self.assertEqual(manifest.read_bytes(),original_manifest)

    def test_partial_or_malformed_legacy_pair_refused_before_http(self):
        """NATIVE-CODE: Uncertain legacy ownership cannot silently reach Comfy or Ollama."""
        for keys in ({'model':'owned'}, {'ollama_url':'http://127.0.0.1:11434'}, {'model':'', 'ollama_url':'http://127.0.0.1:11434'}, {'model':'owned', 'ollama_url':42}):
            with self.subTest(keys=keys), patch('harness.http_json', side_effect=AssertionError('HTTP called before validation')) as http:
                with self.assertRaises(ValueError):
                    harness.prepare_gpu('asset',dict(comfy_url='http://comfy',**keys),time.monotonic()+5,lambda:False)
                http.assert_not_called()

    def test_refresh_preserves_bytes_rollback_and_refuses_ambiguous(self):
        """INSTALL-REFRESH: activated profile is refreshed without fake smoke flags."""
        home=self.root/'.codex'; home.mkdir(); config=b'model="gpt-6.1-sol"\nmodel_provider="openai"\n# keep\n'; (home/'config.toml').write_bytes(config)
        policy=b'before\r\n<!-- local-harness:start -->old<!-- local-harness:end -->\r\nafter\r\n'; (home/'AGENTS.md').write_bytes(policy)
        legacy=home/'skills/local-harness/SKILL.md'; legacy.parent.mkdir(parents=True); legacy.write_text('old')
        backup=install.refresh(home); self.assertEqual((home/'config.toml').read_bytes(),config)
        result=(home/'AGENTS.md').read_bytes(); self.assertTrue(result.startswith(b'before\r\n')); self.assertTrue(result.endswith(b'\r\nafter\r\n')); self.assertIn(b'terra_coder',result)
        self.assertTrue(legacy.exists()); self.assertFalse((home.parent/'.agents/skills/local-harness/SKILL.md').exists())
        install.rollback(backup); self.assertEqual((home/'AGENTS.md').read_bytes(),policy); self.assertEqual(legacy.read_text(),'old')
        canonical=home.parent/'.agents/skills/local-harness/SKILL.md'; canonical.parent.mkdir(parents=True); canonical.write_text('other')
        with self.assertRaises(ValueError): install.refresh(home)
        canonical.unlink(); (home/'AGENTS.md').write_text('unactivated')
        with self.assertRaises(ValueError): install.refresh(home)
