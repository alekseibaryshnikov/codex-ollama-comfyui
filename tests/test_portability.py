"""INSTALL/MEDIA-PORTABLE: fresh profile paths and root-preserving stage.

Real temporary files and child interpreter imports; no live services or globals.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import install

class PortabilityTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).resolve().parents[1]/'work';scratch.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.home=self.root/'Fresh Profile'/'.codex';self.home.mkdir(parents=True)
        self.source=self.root/'Another Checkout';self.source.mkdir()
        shutil.copytree(install.BASE/'integration',self.source/'integration')
        self.skill=self.home.parent/'.agents/skills/local-harness/SKILL.md'

    def test_staging_changes_only_roles_and_skill_and_rolls_back(self):
        """Fresh setup can review with native roles before enabling routing."""
        config=b'model="keep-root"\n';policy=b'Keep my own instructions.\n'
        (self.home/'config.toml').write_bytes(config);(self.home/'AGENTS.md').write_bytes(policy)
        with patch('install.BASE',self.source):backup=install.stage(self.home)
        self.assertEqual((self.home/'config.toml').read_bytes(),config)
        self.assertEqual((self.home/'AGENTS.md').read_bytes(),policy)
        self.assertTrue((self.home/'agents/astra.toml').is_file())
        self.assertTrue(self.skill.is_file())
        self.assertIn((self.source/'harness.py').as_posix(),self.skill.read_text(encoding='utf-8'))
        install.rollback(backup)
        self.assertFalse(self.skill.exists())

    def test_activation_renders_the_selected_profile_and_checkout(self):
        """Global instructions cannot point back to the author's machine."""
        with patch('install.BASE',self.source):backup=install.activate(self.home,{k:True for k in install.REQUIRED})
        policy=(self.home/'AGENTS.md').read_text(encoding='utf-8')
        self.assertIn(self.skill.as_posix(),policy)
        self.assertIn((self.source/'workflows').as_posix(),self.skill.read_text(encoding='utf-8'))
        self.assertNotIn('__HARNESS_ROOT__',self.skill.read_text(encoding='utf-8'))
        install.rollback(backup)

    def test_default_decoder_follows_the_host_interpreter(self):
        """Missing local config must not silently choose a machine-only D: path."""
        env=dict(os.environ);env.pop('COMFY_PYTHON',None)
        result=subprocess.run([sys.executable,'-c','import media;print(media.DEFAULT_DECODER)'],cwd=install.BASE,env=env,capture_output=True,text=True,check=True)
        self.assertEqual(Path(result.stdout.strip()),Path(sys.executable))

    def test_explicit_decoder_environment_override_is_used(self):
        """A selected Comfy interpreter is preserved without shell expansion."""
        env=dict(os.environ);env['COMFY_PYTHON']=str(self.root/'Python With Spaces'/'python.exe')
        result=subprocess.run([sys.executable,'-c','import media;print(media.DEFAULT_DECODER)'],cwd=install.BASE,env=env,capture_output=True,text=True,check=True)
        self.assertEqual(result.stdout.strip(),env['COMFY_PYTHON'])
