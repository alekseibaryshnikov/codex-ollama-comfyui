"""SKILLS-1/2 in restore_skills.py: real profile files, no real user writes.

Bundled fixtures exercise verification and preservation; Git fetching is replaced
except for the separately documented full manifest restore smoke.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import restore_skills


class RestoreSkillsTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1]/'work'
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base/'profile/.codex'
        self.destination = self.home.parent/'.agents/skills'
        self.data = b'---\nname: sample\ndescription: Fixture skill\n---\n'
        payload = self.base/'skills/local/sample/SKILL.md'
        payload.parent.mkdir(parents=True)
        payload.write_bytes(self.data)
        self.row = {'sha256': hashlib.sha256(self.data).hexdigest(),
                    'size_bytes': len(self.data), 'local': 'skills/local/sample/SKILL.md'}
        self.manifest = {'sources': [], 'skills': [
            {'name': 'sample', 'files': {'SKILL.md': self.row}}]}

    def run_restore(self, approved=True):
        return restore_skills.restore(self.manifest, self.home, approved, self.base)

    def test_preview_has_no_profile_writes(self):
        """SKILLS-1: Preview lists skills but neither installs nor fetches them."""
        result = self.run_restore(False)
        self.assertEqual(result['state'], 'preview')
        self.assertEqual(result['skills'], ['sample'])
        self.assertFalse(self.home.parent.exists())

    def test_restore_keeps_support_files_and_is_idempotent(self):
        """SKILLS-1: Fresh restore includes resources; a repeat preserves bytes."""
        support = self.base/'skills/local/sample/reference.md'
        support.write_bytes(b'Supporting contract.\n')
        self.manifest['skills'][0]['files']['reference.md'] = {
            'local': support.relative_to(self.base).as_posix(), 'size_bytes': 21,
            'sha256': hashlib.sha256(support.read_bytes()).hexdigest()}
        self.assertEqual(self.run_restore()['installed'], ['sample'])
        self.assertEqual((self.destination/'sample/reference.md').read_bytes(), support.read_bytes())
        self.assertEqual(self.run_restore()['unchanged'], ['sample'])

    def test_conflict_in_last_skill_prevents_all_writes(self):
        """SKILLS-1: Batch preflight preserves an edited skill and installs none."""
        self.manifest['skills'].append({'name': 'second', 'files': {'SKILL.md': self.row}})
        target = self.destination/'second'
        target.mkdir(parents=True)
        (target/'SKILL.md').write_bytes(b'User changes')
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.run_restore()
        self.assertFalse((self.destination/'sample').exists())
        self.assertEqual((target/'SKILL.md').read_bytes(), b'User changes')

    def test_legacy_conflict_is_preserved(self):
        """SKILLS-1: A divergent legacy skill must not be shadowed by a copy."""
        target = self.home/'skills/sample'
        target.mkdir(parents=True)
        (target/'SKILL.md').write_bytes(b'Legacy edits')
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.run_restore()
        self.assertFalse(self.destination.exists())

    def test_bad_hash_prevents_profile_writes(self):
        """SKILLS-2: Corrupt bundled input fails before publication."""
        self.row['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'digest'):
            self.run_restore()
        self.assertFalse(self.home.parent.exists())

    def test_unsafe_paths_and_duplicate_names_are_rejected(self):
        """SKILLS-2: Windows aliases/traversal cannot escape or collide."""
        for invalid in ('../escape', 'C:/escape', 'foo:bar', 'CON', 'sample.', 'a\\b'):
            with self.subTest(invalid=invalid):
                self.manifest['skills'][0]['name'] = invalid
                with self.assertRaises(ValueError):
                    self.run_restore()
        self.manifest['skills'][0]['name'] = 'sample'
        self.manifest['skills'].append({'name': 'SAMPLE', 'files': {'SKILL.md': self.row}})
        with self.assertRaises(ValueError):
            self.run_restore()
        self.assertFalse(self.home.parent.exists())

    def test_unsafe_resource_and_bundle_paths_are_rejected(self):
        """SKILLS-2: A safe skill name doesn't authorize arbitrary local reads."""
        for key, value in [('resource', '../escape'), ('local', '../private')]:
            with self.subTest(key=key):
                row = dict(self.row)
                if key == 'local': row['local'] = value
                self.manifest['skills'][0]['files'] = {value if key == 'resource' else 'SKILL.md': row}
                with self.assertRaises(ValueError):
                    self.run_restore()

    def test_pinned_source_bytes_are_verified_and_line_endings_normalized(self):
        """SKILLS-2: Fake source boundary proves pins are passed and hashes checked."""
        self.manifest['sources'] = [{'id': 'upstream', 'repo': 'owner/repo', 'commit': 'a'*40}]
        skill = self.manifest['skills'][0]
        skill.update(source='upstream', path='skills/sample')
        self.row.pop('local')
        self.row['normalize_lf'] = True
        source = self.base/'upstream/skills/sample'
        source.mkdir(parents=True)
        (source/'SKILL.md').write_bytes(self.data.replace(b'\n', b'\r\n'))
        with patch('restore_skills.fetch_source', return_value=self.base/'upstream') as fetch:
            self.run_restore()
        self.assertEqual(fetch.call_args.args[0], self.manifest['sources'][0])
        self.assertEqual((self.destination/'sample/SKILL.md').read_bytes(), self.data)

    def test_redirected_destination_is_rejected(self):
        """SKILLS-2: A redirected skills folder must not write another profile."""
        outside = self.base/'outside'
        outside.mkdir()
        self.destination.parent.mkdir(parents=True)
        try:
            self.destination.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Host does not permit fixture directory symlinks')
        with self.assertRaises(ValueError):
            self.run_restore()
        self.assertFalse((outside/'sample').exists())

    def test_plugin_preview_and_restore_use_native_cli_selected_profile(self):
        """SKILLS-3: Commands are mocked; preview runs none, approval targets only the selected profile."""
        manifest = {'marketplaces': [{'name': 'market', 'source': 'owner/plugins', 'ref': 'a'*40}],
                    'plugins': ['sample@market']}
        with patch('restore_skills.subprocess.run') as run:
            self.assertEqual(restore_skills.restore_plugins(manifest, self.home)['state'], 'preview')
            run.assert_not_called()
            result = restore_skills.restore_plugins(manifest, self.home, True)
        self.assertEqual(result['installed'], ['sample@market'])
        self.assertTrue(self.home.is_dir(), 'Native CLI requires an existing CODEX_HOME')
        self.assertEqual(run.call_args.kwargs['env']['CODEX_HOME'], str(self.home))
        self.assertEqual(run.call_args.args[0], ['codex', 'plugin', 'add', 'sample@market', '--json'])

    def test_plugin_failures_are_reported_and_existing_enabled_plugins_preserved(self):
        """SKILLS-3: One failed install doesn't hide others or reinstall enabled plugins."""
        import subprocess
        self.home.mkdir(parents=True)
        (self.home/'config.toml').write_text('[plugins."existing@market"]\nenabled=true\n')
        manifest = {'marketplaces': [], 'plugins': ['existing@market', 'broken@market', 'good@market']}
        with patch('restore_skills.subprocess.run', side_effect=[
                subprocess.CalledProcessError(1, ['codex'], stderr='Plugin unavailable'), None]):
            result = restore_skills.restore_plugins(manifest, self.home, True)
        self.assertEqual(result['unchanged'], ['existing@market'])
        self.assertEqual(result['installed'], ['good@market'])
        self.assertEqual(result['failed'][0]['plugin'], 'broken@market')
        self.assertEqual(result['failed'][0]['error'], 'Plugin unavailable')
        self.assertEqual(result['state'], 'incomplete')

    def test_existing_marketplace_is_preserved_and_conflicting_source_blocks_installs(self):
        """SKILLS-3: Never repoint an operator's marketplace during recovery."""
        self.home.mkdir(parents=True)
        config = self.home/'config.toml'
        manifest = {'marketplaces': [{'name': 'market', 'source': 'owner/plugins', 'ref': 'a'*40}],
                    'plugins': ['sample@market']}
        config.write_text('[marketplaces.market]\nsource_type="git"\nsource="https://github.com/owner/plugins.git"\n')
        with patch('restore_skills.subprocess.run') as run:
            self.assertEqual(restore_skills.restore_plugins(manifest, self.home, True)['installed'], ['sample@market'])
        self.assertEqual(run.call_count, 1)
        original = '[marketplaces.market]\nsource_type="git"\nsource="https://github.com/other/repo.git"\n'
        config.write_text(original)
        with patch('restore_skills.subprocess.run') as run:
            with self.assertRaisesRegex(ValueError, 'marketplace conflict'):
                restore_skills.restore_plugins(manifest, self.home, True)
            run.assert_not_called()
        self.assertEqual(config.read_text(), original)
