"""INSTALL-1 at install.py, real temporary files and TOML parsing.

No actual user configuration is changed by this suite.
"""
from pathlib import Path
import tempfile
import tomllib
import unittest
import install


class InstallTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).resolve().parents[1]/'work';scratch.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)/'codex';self.home.mkdir()
        self.original='model = "qwen3.8:27b"\nopenai_base_url="http://127.0.0.1:11434/api/codex/v1"\nmodel_catalog_json="catalog.json"\n[features]\nmemories=true\n'
        (self.home/'config.toml').write_text(self.original)
        (self.home/'AGENTS.md').write_text('Existing user instructions\n')
        self.evidence={key:True for key in ['tests','qwen','terra_coder','terra','astra','image','image_edit','video','video_edit','music','speech','sfx']}

    def test_fresh_activation_requires_separate_coder_evidence(self):
        """INSTALL-CODER-EVIDENCE: Reviewer evidence cannot prove coder access.

        Temporary profile gate only; no native account or model access is probed.
        """
        with self.assertRaisesRegex(ValueError,'terra_coder'):
            install.activate(self.home,dict(self.evidence,terra_coder=False))
        self.assertEqual((self.home/'config.toml').read_text(),self.original)

    def test_new_video_edit_smoke_is_required(self):
        """INSTALL-2: a failed source-video edit smoke blocks global activation."""
        with self.assertRaises(ValueError):
            install.activate(self.home,dict(self.evidence,video_edit=False))
        self.assertEqual((self.home/'config.toml').read_text(),self.original)

    def test_installed_routing_uses_ltx_and_names_editing_limit(self):
        """INSTALL-LTX/NATIVE: Installed policy uses LTX and delegates to distinct roles.

        Temporary profile files exercise activation, not live Codex discovery.
        """
        backup=install.activate(self.home,self.evidence)
        policy=(self.home/'AGENTS.md').read_text(encoding='utf-8')
        self.assertIn('LTX-2.5',policy)
        self.assertIn('experimental source-guided regeneration',policy)
        self.assertNotIn('with H3 for video',policy)
        self.assertIn('terra_coder',policy)
        self.assertIn('fresh',policy)
        self.assertNotIn('Qwen through Ollama',policy)
        install.rollback(backup)

    def test_new_image_edit_smoke_is_required(self):
        """INSTALL-2: a failed image-edit smoke blocks global activation."""
        with self.assertRaises(ValueError):
            install.activate(self.home,dict(self.evidence,image_edit=False))
        self.assertEqual((self.home/'config.toml').read_text(),self.original)

    def test_optional_qwen_availability_does_not_gate_activation(self):
        """INSTALL-2: unavailable optional local coding cannot capture Sol routing."""
        backup=install.activate(self.home,dict(self.evidence,qwen=False))
        self.assertEqual(tomllib.loads((self.home/'config.toml').read_text())['model'],'gpt-6.1-sol')
        install.rollback(backup)
        self.assertEqual((self.home/'config.toml').read_text(),self.original)

    def test_activation_requires_every_requested_smoke(self):
        """INSTALL-1: Missing sound effects cannot be described as full readiness."""
        self.evidence['sfx']=False
        with self.assertRaises(ValueError): install.activate(self.home,self.evidence)
        self.assertEqual((self.home/'config.toml').read_text(),self.original)

    def test_activation_restores_openai_root_and_keeps_unrelated_settings(self):
        """INSTALL-1/NATIVE: Activate distinct roles and restore the prior profile.

        Real temporary files and TOML are exercised, not native agent execution.
        """
        backup=install.activate(self.home,self.evidence)
        data=tomllib.loads((self.home/'config.toml').read_text())
        self.assertEqual(data['model'],'gpt-6.1-sol')
        self.assertEqual(data['model_provider'],'openai')
        self.assertNotIn('openai_base_url',data)
        self.assertNotIn('model_catalog_json',data)
        self.assertTrue(data['features']['memories'])
        self.assertTrue((self.home/'AGENTS.md').read_text().startswith('Existing user instructions'))
        self.assertEqual(tomllib.loads((self.home/'agents/astra.toml').read_text())['model'],'gpt-6-astra')
        coder=tomllib.loads((self.home/'agents/terra_coder.toml').read_text())
        reviewer=tomllib.loads((self.home/'agents/terra.toml').read_text())
        self.assertEqual((coder['model'],coder['model_reasoning_effort']),('gpt-6.1-terra','medium'))
        self.assertEqual((reviewer['model'],reviewer['model_reasoning_effort']),('gpt-6.1-terra','high'))
        self.assertTrue(install.skill_path(self.home).is_file())
        install.rollback(backup)
        self.assertEqual((self.home/'config.toml').read_text(),self.original)
        self.assertEqual((self.home/'AGENTS.md').read_text(),'Existing user instructions\n')
        self.assertFalse((self.home/'agents/astra.toml').exists())
        self.assertFalse((self.home/'agents/terra_coder.toml').exists())
        self.assertFalse((self.home/'agents/terra.toml').exists())

    def test_rollback_refuses_to_overwrite_later_user_edits(self):
        """INSTALL-1: A rollback cannot discard configuration edited afterward."""
        backup=install.activate(self.home,self.evidence)
        with (self.home/'config.toml').open('a') as stream:stream.write('\n# later user edit\n')
        with self.assertRaises(ValueError):install.rollback(backup)
        self.assertIn('later user edit',(self.home/'config.toml').read_text())


if __name__=='__main__':unittest.main()
