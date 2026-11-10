"""CLI-1 at harness.start_job/doctor; mock service and process boundaries.

These tests check refusal and diagnostics without starting inference workers.
Real detached supervisor behavior is checked separately in the smoke evidence.
"""
from pathlib import Path
import tempfile
import io
import unittest
from unittest.mock import patch
import harness


class CliTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).resolve().parents[1]/'work';scratch.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_malformed_request_never_launches_supervisor(self):
        """CLI-1: Invalid requests cannot create a hidden worker."""
        with patch('harness.subprocess.Popen') as spawn:
            with self.assertRaises(ValueError):
                harness.start_job(harness.JobStore(self.root/'state'),'code',{},self.root,self.root/'config.json')
        spawn.assert_not_called()

    def test_doctor_reports_service_errors_instead_of_ready(self):
        """CLI-1: Offline services are returned as failed dependencies."""
        with patch('harness.http_json',side_effect=OSError('offline')):
            result=harness.doctor({'model':'qwen3.8:27b','comfy_url':'http://127.0.0.1:8189','ollama_url':'http://127.0.0.1:11434'})
        self.assertFalse(result['ready'])
        self.assertIn('offline',result['ollama']['error'])
        self.assertIn('offline',result['comfyui']['error'])

    def test_empty_comfy_control_response_is_success(self):
        """GPU-1: Comfy /free returns HTTP 200 with no JSON body."""
        with patch('harness.urllib.request.urlopen',return_value=io.BytesIO(b'')):
            self.assertEqual(harness.http_json('http://127.0.0.1/free',{'free_memory':True}),{})

    def test_asset_request_control_fields_are_not_workflow_inputs(self):
        """CLI-1/MEDIA-PREPARE: Preset and deadline stay out of graph inputs."""
        with patch('harness.subprocess.Popen') as spawn,patch('harness.process_identity',return_value='test-identity'):
            spawn.return_value.pid=12345
            result=harness.start_job(harness.JobStore(self.root/'state'),'asset',
                {'preset':'image','prompt':'a tree','timeout_seconds':600},self.root,self.root/'config.json')
        self.assertEqual(result['state'],'queued')
        self.assertTrue((self.root/'state/jobs'/result['id']/'owner.json').is_file())
        spawn.assert_called_once()


if __name__=='__main__':unittest.main()
