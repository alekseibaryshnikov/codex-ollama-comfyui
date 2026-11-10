"""SUBMIT-1/MEDIA-OWNERSHIP: real durable job/GPU metadata, simulated Comfy.

The service records exact POST bodies. Late enqueue and lost replies are
simulated, and no inference engine, production state or GPU is touched.
"""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from uuid import UUID, uuid4

import harness
import media


class SubmissionOwnershipTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / 'work')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.store = harness.JobStore(self.root/'jobs-a')
        self.gpu = self.root/'gpu'
        self.marker = self.gpu/'unconfirmed-prompt.json'
        self.job = self.store.create('asset', {'preset': 'image', 'prompt': 'x'}, self.root)
        self.config = {'model': 'test', 'comfy_url': 'http://localhost:8189', 'ollama_url': 'http://localhost:11434'}
        self.calls = []
        self.at_post = None
        self.post = lambda data: {'prompt_id': data.get('prompt_id'), 'node_errors': {}}
        self.enterContext(patch('harness.GPU_ROOT', self.gpu))
        self.handoff = self.enterContext(patch('harness.prepare_gpu'))
        self.other_engine = self.enterContext(patch('harness.http_json'))
        self.enterContext(patch('media.prepare', return_value={'kind': 'image', 'prompt': {}, 'output_nodes': ['save']}))
        self.enterContext(patch('media.poll', return_value={'state': 'succeeded', 'outputs': [{'type': 'output'}]}))
        self.enterContext(patch('media.retrieve', return_value=['decoded.png']))
        self.enterContext(patch('media.api', side_effect=self.service))

    def service(self, url, path, data=None):
        self.calls.append((path, data))
        if path == '/prompt':
            self.at_post = (self.store.read(self.job['id']), harness.read_json(self.marker) if self.marker.is_file() else {})
            return self.post(data)
        return {}

    def execute(self):
        harness.execute_job(self.store, self.job['id'], self.config)
        return self.store.read(self.job['id'])

    def test_request_and_shared_guard_own_id_before_post_and_clear_on_echo(self):
        """An immediate echo must name the UUID already on disk before enqueue."""
        result = self.execute()
        sent = self.calls[0][1].get('prompt_id')
        self.assertIsInstance(sent, str)
        self.assertEqual(str(UUID(sent)), sent)
        state, marker = self.at_post
        self.assertEqual(state['prompt_id'], sent)
        self.assertEqual(marker['prompt_id'], sent)
        self.assertEqual(marker['job_id'], self.job['id'])
        self.assertEqual(result['state'], 'succeeded')
        self.assertFalse(result.get('operator_check_required'))
        self.assertFalse(self.marker.exists())

    def test_lost_ack_cancels_once_and_late_enqueue_cannot_race_next_gpu_handoff(self):
        """Deletion before delayed validation finishes cannot prove non-acceptance."""
        validating = []
        def delayed(data):
            validating.append(data.get('prompt_id'))
            raise TimeoutError('lost acknowledgement')
        self.post = delayed
        result = self.execute()
        self.assertTrue(result.get('operator_check_required'))
        owned = result['prompt_id']
        self.assertEqual(validating, [owned])
        harness.cancel_job(self.store, self.job['id'], self.config)
        harness.cancel_job(self.store, self.job['id'], self.config)
        self.assertEqual(self.calls[1:], [('/queue', {'delete': [owned]}), ('/interrupt', {'prompt_id': owned})])
        self.assertEqual(harness.read_json(self.marker)['prompt_id'], owned)
        # The new job sees an empty queue; the prior POST can still enqueue later.
        other = harness.JobStore(self.root/'jobs-b')
        job = other.create('code', {'task': 'x', 'checks': [['unused']]}, self.root)
        self.handoff.reset_mock()
        with patch('harness.run_command') as worker:
            harness.execute_job(other, job['id'], self.config)
        self.assertEqual(other.read(job['id'])['state'], 'failed')
        self.assertIn(str(self.marker), other.read(job['id'])['error'])
        self.handoff.assert_not_called()
        self.other_engine.assert_not_called()
        worker.assert_not_called()
        self.assertEqual(validating.pop(), owned)
        self.assertTrue(self.marker.exists())

    def test_mismatched_ack_never_targets_foreign_id(self):
        """A successful HTTP response for a different UUID leaves ownership uncertain."""
        foreign = str(uuid4())
        self.post = lambda data: {'prompt_id': foreign, 'node_errors': {}}
        result = self.execute()
        self.assertEqual(result['state'], 'failed')
        self.assertTrue(result.get('operator_check_required'))
        self.assertTrue(self.marker.exists())
        owned = result['prompt_id']
        self.assertNotEqual(owned, foreign)
        self.assertEqual(self.calls[1:], [('/queue', {'delete': [owned]}), ('/interrupt', {'prompt_id': owned})])

    def test_supervisor_exit_during_submission_leaves_guard_and_recoverable_id(self):
        """A vanished worker cannot release uncertainty by releasing the OS lock."""
        def disappear(data):
            raise SystemExit('worker crash')
        self.post = disappear
        with self.assertRaises(SystemExit):
            self.execute()
        self.assertTrue(self.marker.exists())
        stored = self.store.read(self.job['id'])
        self.assertEqual(stored['prompt_id'], harness.read_json(self.marker)['prompt_id'])
        self.store.update(self.job['id'], created_at=0)
        with patch('media.cancel', wraps=media.cancel) as cancel:
            result = harness.cancel_job(self.store, self.job['id'], {**self.config, 'comfy_url': 'http://localhost:9000'})
        cancel.assert_called_once_with(stored['prompt_id'], self.config['comfy_url'])
        self.assertTrue(result['operator_check_required'])
        self.assertTrue(self.marker.exists())
        self.assertEqual(self.calls[-1], ('/interrupt', {'prompt_id': stored['prompt_id']}))

    def test_known_prequeue_http_validation_rejection_clears_guard(self):
        """Installed Comfy returns a typed 400 before enqueue for invalid graphs."""
        payload = {'error': {'type': 'prompt_outputs_failed_validation', 'message': 'invalid graph'}, 'node_errors': {}}
        def reject(request, timeout):
            raise HTTPError(request.full_url, 400, 'Bad Request', {}, io.BytesIO(json.dumps(payload).encode()))
        with patch('media.api', REAL_API), patch('media.urlopen', side_effect=reject):
            result = self.execute()
        self.assertEqual(result['state'], 'failed')
        self.assertIn('invalid graph', result['error'])
        self.assertFalse(result.get('operator_check_required'))
        self.assertFalse(self.marker.exists())


REAL_API = media.api
