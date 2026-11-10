"""BOOT-1..3: isolated disk/transport checks, no real installs or model downloads."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import bootstrap

class BootstrapTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).resolve().parents[1]/'work';scratch.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);(self.base/'manifests').mkdir();(self.base/'locks').mkdir()
        self.catalog={'schema_version':1,'files':[{'purpose':'test-model','source':'https://huggingface.co/example/model/resolve/'+'a'*40+'/weight.bin','destination_root':'comfy','destination':'models/checkpoints/weight.bin','size_bytes':3,'sha256':'a'*64,'gated':False,'license':'example'}],'python_packages':[],'voice_assembly':None}
        self.save()
        (self.base/'locks/runtime.json').write_text(json.dumps({'ollama':{'base_model':'qwen3.8:27b','base_digest':'sha256:'+'b'*64,'worker_model':'qwen3.8:27b-codex','context_length':262144},'comfyui':{'repository':'https://github.com/Comfy-Org/ComfyUI.git','commit':'c'*40}}))

    def save(self):
        (self.base/'manifests/catalog.json').write_text(json.dumps(self.catalog),encoding='utf-8')

    def test_configure_resolves_a_fresh_root_without_writing_there(self):
        """BOOT-1: a new username/path produces real config and a confined manifest."""
        comfy=self.base/'Fresh Windows User'/'AI'/'ComfyUI'
        bootstrap.configure(comfy,base=self.base)
        config=json.loads((self.base/'config.json').read_text())
        self.assertEqual(Path(config['comfy_input_dir']),(comfy/'app/input').resolve())
        self.assertEqual(Path(config['decoder_python']),(comfy/'python/Scripts/python.exe').resolve())
        self.assertEqual(config['model'],'qwen3.8:27b-codex')
        manifest=json.loads((self.base/'work/download-manifest.json').read_text())
        self.assertEqual(Path(manifest['files'][0]['destination']),(comfy/'app/models/checkpoints/weight.bin').resolve())
        self.assertFalse(comfy.exists())

    def test_unsafe_catalog_stops_before_machine_config_is_written(self):
        """BOOT-1: model catalog cannot redirect writes outside the selected root."""
        for destination in ('../escape','/absolute','C:/outside.bin','models/../../escape'):
            self.catalog['files'][0]['destination']=destination;self.save()
            with self.subTest(destination=destination),self.assertRaises(ValueError):bootstrap.configure(self.base/'comfy',base=self.base)
        self.assertFalse((self.base/'config.json').exists())

    def test_reconfigure_keeps_a_copy_of_existing_config(self):
        """BOOT-1: changing the chosen root cannot destroy previous local settings."""
        bootstrap.configure(self.base/'first',base=self.base)
        old=(self.base/'config.json').read_bytes()
        bootstrap.configure(self.base/'second',base=self.base)
        self.assertNotEqual((self.base/'config.json').read_bytes(),old)
        self.assertTrue(any(p.read_bytes()==old for p in (self.base/'.runtime').rglob('*.json')))

    def test_install_actions_require_explicit_approval_before_network_or_processes(self):
        """BOOT-2/3: merely invoking an installer must not start a download."""
        for action in (bootstrap.setup_ollama,bootstrap.install_comfy):
            with self.subTest(action=action.__name__),self.assertRaises(PermissionError):action(base=self.base)
