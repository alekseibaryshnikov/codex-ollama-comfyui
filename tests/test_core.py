"""Contracts in harness.py, JOB-1/GPU-1/PROC-1/CODE-1.

Uses real disk, OS locks and child processes; no model/service calls. These tests
cannot establish live inference quality, sandbox enforcement or Terra review.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import harness

from harness import JobStore, GpuLease, validate_request, run_command, code_command


class CoreTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / 'work'
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request = {'task': 'Implement the specified function', 'checks': [[sys.executable, '-m', 'unittest']]}

    def test_request_validation_rejects_missing_task_checks_and_invalid_timeout(self):
        """JOB-1: Bad requests fail before any worker is spawned."""
        for value in [{}, {'task': 'x'}, dict(self.request, timeout_seconds=True), dict(self.request, timeout_seconds=-1), dict(self.request, checks=['python'])]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_request('code', value, self.root)

    def test_valid_request_has_bounded_default_and_requires_real_workspace(self):
        """JOB-1: Defaults are finite; an absent workspace cannot receive edits."""
        self.assertEqual(validate_request('code', self.request, self.root)['timeout_seconds'], 600)
        with self.assertRaises(ValueError):
            validate_request('code', self.request, self.root / 'missing')

    def test_job_request_survives_reload_and_terminal_state_cannot_be_changed(self):
        """JOB-1: Reload preserves evidence and no late process resurrects a job."""
        store = JobStore(self.root)
        job = store.create('code', self.request, self.root)
        again = JobStore(self.root).read(job['id'])
        self.assertEqual(again['state'], 'queued')
        self.assertEqual(json.loads((self.root / 'jobs' / job['id'] / 'request.json').read_text()), self.request)
        store.update(job['id'], state='failed', error='test failure')
        with self.assertRaises(ValueError):
            store.update(job['id'], state='running')

    def test_job_ids_cannot_escape_store(self):
        """JOB-1: An untrusted job identifier cannot read arbitrary paths."""
        for job_id in ['../config', '..', '/tmp', 'not-a-uuid']:
            with self.subTest(job_id=job_id), self.assertRaises(ValueError):
                JobStore(self.root).read(job_id)

    def test_gpu_lock_excludes_second_project_and_releases(self):
        """GPU-1: Competing jobs cannot acquire the shared GPU until release."""
        first, second = GpuLease(self.root), GpuLease(self.root)
        self.addCleanup(first.release)
        self.addCleanup(second.release)
        self.assertTrue(first.acquire())
        self.assertFalse(second.acquire())
        first.release()
        self.assertTrue(second.acquire())

    def test_process_returns_exit_code_and_real_log(self):
        """PROC-1: A failing command retains its actual output and exit code."""
        log = self.root / 'run.log'
        rc = run_command([sys.executable, '-c', 'print("evidence");raise SystemExit(7)'], self.root, log, time.monotonic()+10, lambda: False)
        self.assertEqual(rc, 7)
        self.assertIn('evidence', log.read_text())

    def test_timeout_stops_owned_process(self):
        """PROC-1: A hung child is stopped and reported as timed out."""
        with self.assertRaises(TimeoutError):
            run_command([sys.executable, '-c', 'import time;time.sleep(20)'], self.root, self.root/'run.log', time.monotonic()+0.3, lambda: False)

    def test_cancel_stops_only_owned_process(self):
        """PROC-1: Cancellation is distinct from success or deadline expiry."""
        with self.assertRaises(InterruptedError):
            run_command([sys.executable, '-c', 'import time;time.sleep(20)'], self.root, self.root/'run.log', time.monotonic()+20, lambda: True)

    def test_timeout_also_stops_grandchildren(self):
        """PROC-1: A child cannot leave a grandchild writing after timeout."""
        marker = self.root/'escaped.txt'
        child = 'import time,pathlib;time.sleep(1.5);pathlib.Path('+repr(str(marker))+').write_text("escaped")'
        parent = 'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",'+repr(child)+']);time.sleep(20)'
        real_job=harness.WindowsJob
        def delayed_assignment(process):
            time.sleep(0.15)
            return real_job(process)
        with patch('harness.WindowsJob',side_effect=delayed_assignment),self.assertRaises(TimeoutError):
            run_command([sys.executable,'-c',parent],self.root,self.root/'tree.log',time.monotonic()+0.4,lambda:False)
        time.sleep(1.8)
        self.assertFalse(marker.exists())

    def test_worker_uses_full_supported_context(self):
        """CODE-CONTEXT: local launch must expose 262144, not silently cap at 64K.

        Tests the real generated client argv without starting model inference.
        Live allocation and long-input processing require separate Ollama probes.
        """
        argv, _ = code_command({'codex': 'codex.exe', 'model': 'qwen3.8:27b-codex', 'ollama_url': 'http://127.0.0.1:11434'}, self.root)
        self.assertIn('model_context_window=262144', argv)
        self.assertNotIn('model_context_window=65536', argv)

    def test_worker_is_local_and_does_not_inherit_api_credentials(self):
        """CODE-1: Local work cannot silently bill an OpenAI model or delegate."""
        os.environ['OPENAI_API_KEY'] = 'unit-test-secret'
        os.environ['CODEX_API_KEY'] = 'unit-test-secret'
        self.addCleanup(os.environ.pop, 'OPENAI_API_KEY', None)
        self.addCleanup(os.environ.pop, 'CODEX_API_KEY', None)
        argv, env = code_command({'codex': 'codex.exe', 'model': 'qwen3.8:27b', 'ollama_url': 'http://127.0.0.1:11434'}, self.root)
        self.assertIn('--oss', argv)
        self.assertIn('--ignore-user-config', argv)
        self.assertIn('model_provider="ollama"', argv)
        self.assertIn('agents.enabled=false', argv)
        self.assertIn('skills.include_instructions=false', argv)
        self.assertIn('model_reasoning_effort="none"', argv)
        self.assertIn('qwen3.8:27b', argv)
        self.assertFalse('OPENAI_API_KEY' in env)
        self.assertFalse('CODEX_API_KEY' in env)
        self.assertFalse('TYPESAFE_API_KEY' in env)
        self.assertFalse('CODEX_APP_TOOLS_PIPE_PATH' in env)
        self.assertNotEqual(env.get('CODEX_HOME'),str(Path.home()/'.codex'))
        self.assertEqual(env['CODEX_HARNESS_WORKER'], '1')


if __name__ == '__main__':
    unittest.main()
