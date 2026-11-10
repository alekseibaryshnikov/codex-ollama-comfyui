"""PROV-1..5 in provision.py: disk and mocked HTTP/process boundaries.

No remote weights are fetched and no package is installed. Voice assembly uses
the installed Comfy Python for a real tiny tensor/archive round trip.
"""
import hashlib
import io
import json
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
import urllib.request
from unittest.mock import patch

import provision


class ProvisionTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / 'work'
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest_path = self.root / 'manifest.json'
        self.item = {'source': 'https://huggingface.co/org/model/resolve/pinned/file',
                     'destination': str(self.root/'comfy'/'models'/'test.bin'),
                     'size_bytes': 3, 'sha256': hashlib.sha256(b'abc').hexdigest(), 'gated': False}
        self.manifest = {'comfy_root': str(self.root/'comfy'), 'files': [self.item],
                         'python_packages': [], 'voice_assembly': None}
        self.save()

    def save(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding='utf-8')

    def test_redirect_cannot_downgrade_same_host_or_change_to_other_non_https_scheme(self):
        """PROV-6: Even same-host redirect targets must retain HTTPS transport.

        This builds redirect requests without opening a network connection, so
        it tests the credential boundary independently of any server behavior.
        """
        request = urllib.request.Request('https://huggingface.co/model', headers={'Authorization':'Bearer test-token'})
        for target in ['http://huggingface.co/model', 'http://cdn.example.com/model', 'ftp://huggingface.co/model']:
            with self.subTest(target=target), self.assertRaises(ValueError):
                provision.SafeRedirect().redirect_request(request, None, 302, 'Found', {}, target)

    def test_https_redirect_keeps_auth_only_on_original_host(self):
        """PROV-6: HTTPS CDN redirects are allowed without carrying HF auth."""
        request = urllib.request.Request('https://huggingface.co/model', headers={'Authorization':'Bearer test-token'})
        handler = provision.SafeRedirect()
        same = handler.redirect_request(request, None, 302, 'Found', {}, 'https://huggingface.co/next')
        other = handler.redirect_request(request, None, 302, 'Found', {}, 'https://cdn.example.com/model')
        self.assertEqual(same.get_header('Authorization'), 'Bearer test-token')
        self.assertIsNone(other.get_header('Authorization'))

    def test_explicit_approval_required_before_any_helper(self):
        """PROV-1: A missing approval cannot download or inspect cached auth."""
        with patch('provision.helper') as call, self.assertRaises(PermissionError):
            provision.provision(self.manifest_path, python='python')
        call.assert_not_called()

    def test_destination_escape_and_plain_http_are_rejected(self):
        """PROV-1: A manifest cannot write outside its two declared roots."""
        self.item['destination'] = str(self.root/'elsewhere'/'test.bin')
        with self.assertRaises(ValueError):
            provision.validate_manifest(self.manifest, self.manifest_path)
        self.item['destination'] = str(self.root/'comfy'/'models'/'test.bin')
        self.item['source'] = 'http://example.com/model'
        with self.assertRaises(ValueError):
            provision.validate_manifest(self.manifest, self.manifest_path)

    def test_gate_failure_happens_before_all_downloads_and_installs(self):
        """PROV-2: Even an ungated file earlier in the list cannot download first."""
        gated = dict(self.item, gated=True, destination=str(self.root/'comfy'/'models'/'gated.bin'))
        self.manifest['files'].append(gated)
        self.save()
        calls = []
        def fake(python, path, mode, index=0):
            calls.append(mode)
            if mode == 'gate':
                raise PermissionError('Accept the Stable Audio license and authenticate')
            return {}
        with patch('provision.helper', side_effect=fake), self.assertRaises(PermissionError):
            provision.provision(self.manifest_path, approved=True, python='python')
        self.assertEqual(calls, ['gate'])
        self.assertFalse(Path(self.item['destination']).exists())

    def test_gated_failure_names_the_actual_model_without_query_credentials(self):
        """PROV-ACCESS: LTX access failures must not send the user to Stable Audio."""
        item=dict(self.item,filename='ltx-model.safetensors',gated=True,
                  source='https://huggingface.co/Lightricks/LTX-2.5/resolve/pin/model?token=never-report-this')
        with patch('provision.open_remote',side_effect=urllib.error.URLError('denied')):
            with self.assertRaises(PermissionError) as failure:
                provision.run_helper(dict(self.manifest,files=[item]),'gate',0)
        message=str(failure.exception)
        self.assertIn('ltx-model.safetensors',message)
        self.assertIn('https://huggingface.co/Lightricks/LTX-2.5',message)
        self.assertNotIn('never-report-this',message)
        self.assertNotIn('Stable Audio',message)

    def test_speech_subset_does_not_request_gated_sound_effect_models(self):
        """PROV-2: Explicit speech-only approval skips SFX and its gated access."""
        self.item['purpose'] = 'speech-model'
        self.manifest['files'].append(dict(self.item, purpose='sfx-model', gated=True,
            destination=str(self.root/'comfy'/'models'/'gated.bin')))
        self.save()
        calls = []
        def fake(python, path, mode, index=0, only='all'):
            calls.append(mode)
            return {} if mode == 'versions' else {'ok':True}
        with patch('provision.helper', side_effect=fake):
            provision.provision(self.manifest_path, approved=True, python='python', only='speech')
        self.assertNotIn('gate', calls)
        self.assertEqual(calls.count('fetch'), 1)

    def test_download_is_verified_and_reused_without_network(self):
        """PROV-3: Correct content is committed once; reuse verifies the same hash."""
        with patch('provision.open_remote', return_value=io.BytesIO(b'abc')):
            evidence = provision.download_file(self.item)
        self.assertEqual(Path(self.item['destination']).read_bytes(), b'abc')
        self.assertEqual(evidence['sha256'], self.item['sha256'])
        with patch('provision.open_remote') as call:
            again = provision.download_file(self.item)
        call.assert_not_called()
        self.assertTrue(again['reused'])

    def test_bad_size_or_hash_does_not_create_destination_or_leave_partial(self):
        """PROV-3: A failed transfer never becomes an installed model."""
        for body in [b'ab', b'xyz', b'abcd']:
            with self.subTest(body=body), patch('provision.open_remote', return_value=io.BytesIO(body)), self.assertRaises(ValueError):
                provision.download_file(self.item)
            self.assertFalse(Path(self.item['destination']).exists())
            self.assertEqual(list((self.root/'comfy'/'models').glob('*.part*')), [])

    def test_existing_divergent_file_is_preserved(self):
        """PROV-3: Existing user data cannot be replaced by a manifest fetch."""
        path = Path(self.item['destination']); path.parent.mkdir(parents=True)
        path.write_bytes(b'old')
        with patch('provision.open_remote') as call, self.assertRaises(ValueError):
            provision.download_file(self.item)
        call.assert_not_called()
        self.assertEqual(path.read_bytes(), b'old')

    def test_missing_upstream_hash_is_computed_and_recorded(self):
        """PROV-3: GitHub assets without hashes still get local hash evidence."""
        self.item['sha256'] = None
        with patch('provision.open_remote', return_value=io.BytesIO(b'abc')):
            evidence = provision.download_file(self.item)
        self.assertEqual(evidence['sha256'], hashlib.sha256(b'abc').hexdigest())

    def test_conflicting_package_version_fails_before_fetch(self):
        """PROV-4: An installed dependency is preserved rather than upgraded."""
        self.manifest['python_packages'] = [{'package':'test-package','version':'2.0',
            'source':'https://files.pythonhosted.org/test.whl','destination':str(self.root/'downloads'/'test.whl'),
            'size_bytes':3,'sha256':self.item['sha256']}]
        self.save()
        calls = []
        def fake(python, path, mode, index=0):
            calls.append(mode)
            return {'test-package':'1.0'}
        with patch('provision.helper', side_effect=fake), self.assertRaises(ValueError):
            provision.provision(self.manifest_path, approved=True, python='python')
        self.assertEqual(calls, ['versions'])

    def test_voice_archive_real_roundtrip_and_divergent_preservation(self):
        """PROV-5: Safe tensors produce expected archive keys; reruns are idempotent."""
        python = Path(os.environ.get('COMFY_PYTHON',''))
        if not python.is_file():
            self.skipTest('Comfy Python unavailable for real tensor roundtrip')
        code = '''import json,pathlib,sys,torch,numpy as np
sys.path.insert(0,sys.argv[1]);import provision
root=pathlib.Path(sys.argv[2]);src=root/'af_test.pt';torch.save(torch.tensor([[1.,2.]]),src)
dest=root/'voices_v1.bin'
m={'files':[{'purpose':'speech-voice-source','filename':'af_test.pt','destination':str(src)}],
   'voice_assembly':{'source_voices':['af_test'],'destination':str(dest)}}
provision.assemble_voices(m)
with np.load(dest,allow_pickle=False) as a:assert a.files==['af_test'];assert a['af_test'].tolist()==[[1.,2.]]
original=dest.read_bytes();provision.assemble_voices(m);assert dest.read_bytes()==original
torch.save(torch.tensor([[9.,9.]]),src)
try:provision.assemble_voices(m)
except ValueError:pass
else:raise AssertionError('divergent archive overwritten')
assert dest.read_bytes()==original
'''
        result = subprocess.run([str(python), '-c', code, str(Path(provision.__file__).parent), str(self.root)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_installed_speech_runtime_has_complete_dependencies_and_imports(self):
        """PROV-4: Real Comfy runtime can import the complete Kokoro speech path.

        This checks installed distributions and imports, not inference or service
        reload. It catches missing transitive packages even when wheel installs
        themselves succeeded. Optional extras and non-Windows imports are excluded.
        """
        python = Path(os.environ.get('COMFY_PYTHON',''))
        if not python.is_file():
            self.skipTest('Comfy Python unavailable for speech runtime acceptance')
        code = '''import importlib,importlib.metadata
from packaging.requirements import Requirement
pending=['kokoro-onnx'];seen=set()
while pending:
 name=pending.pop()
 if name in seen:continue
 seen.add(name)
 for text in importlib.metadata.requires(name) or []:
  requirement=Requirement(text)
  if requirement.marker and not requirement.marker.evaluate({'extra':''}):continue
  version=importlib.metadata.version(requirement.name)
  assert requirement.specifier.contains(version),f'{requirement} incompatible with {version}'
  pending.append(requirement.name)
for name in ['kokoro_onnx','phonemizer','joblib','espeakng_loader','onnxruntime']:
 importlib.import_module(name)
'''
        result = subprocess.run([str(python), '-c', code], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
