"""JOB-2/REVIEW-1 at harness.execute_job/record_review.

Real job storage and Git fingerprints, replaced model/Comfy calls. This proves
runner state and evidence handling, not actual model capabilities.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import harness


class JobTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1]/'work'
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        gpu_patch=patch('harness.GPU_ROOT',self.root/'test-gpu')
        gpu_patch.start();self.addCleanup(gpu_patch.stop)
        self.repo = self.root/'repo'
        self.repo.mkdir()
        subprocess.run(['git','init','-b','test-worker',str(self.repo)], capture_output=True,check=True)
        subprocess.run(['git','-C',str(self.repo),'-c','user.name=Harness Test','-c','user.email=harness@example.invalid','commit','--allow-empty','-m','fixture'],capture_output=True,check=True)
        self.store = harness.JobStore(self.root/'state')
        self.config = {'model':'qwen3.8:27b','codex':'codex.exe','ollama_url':'http://127.0.0.1:11434','comfy_url':'http://127.0.0.1:8189'}
        self.job = self.store.create('code',{'task':'Implement x','checks':[[sys.executable,'-c','pass']]},self.repo)

    def test_code_requires_passing_checks_then_explicit_terra_approval(self):
        """JOB-2/REVIEW-1: Model exit zero alone must not report acceptance."""
        with patch('harness.prepare_gpu'), patch('harness.http_json',return_value={'models':[]}), patch('harness.run_command',return_value=0):
            harness.execute_job(self.store,self.job['id'],self.config)
        state=self.store.read(self.job['id'])
        self.assertEqual(state['state'],'awaiting_review')
        harness.record_review(self.store,self.job['id'],{'model':'gpt-6.1-terra','verdict':'approved','summary':'No actionable findings'})
        self.assertEqual(self.store.read(self.job['id'])['state'],'succeeded')

    def test_failed_checks_are_not_reported_as_success(self):
        """JOB-2: A successful model with a failing check yields failed job."""
        with patch('harness.prepare_gpu'), patch('harness.http_json',return_value={'models':[]}), patch('harness.run_command',side_effect=[0,1]):
            harness.execute_job(self.store,self.job['id'],self.config)
        self.assertEqual(self.store.read(self.job['id'])['state'],'failed')
        lease=harness.GpuLease(self.store.root)
        self.assertTrue(lease.acquire())
        lease.release()

    def test_pre_cancelled_job_never_invokes_model(self):
        """JOB-2: Cancellation before launch stops work and preserves evidence."""
        (self.store.folder(self.job['id'])/'cancel').touch()
        with patch('harness.run_command') as command:
            harness.execute_job(self.store,self.job['id'],self.config)
        command.assert_not_called()
        self.assertEqual(self.store.read(self.job['id'])['state'],'cancelled')

    def test_model_timeout_stays_distinct_from_failure_and_releases_gpu(self):
        """JOB-2: Deadlines cannot be misreported as successful completions."""
        with patch('harness.prepare_gpu'),patch('harness.http_json',return_value={'models':[]}),patch('harness.run_command',side_effect=TimeoutError('deadline')):
            harness.execute_job(self.store,self.job['id'],self.config)
        self.assertEqual(self.store.read(self.job['id'])['state'],'timed_out')

    def test_review_rejects_changed_diff_and_wrong_model(self):
        """REVIEW-1: Approval must cover current bytes and name Terra."""
        with patch('harness.prepare_gpu'),patch('harness.http_json',return_value={'models':[]}),patch('harness.run_command',return_value=0):
            harness.execute_job(self.store,self.job['id'],self.config)
        with self.assertRaises(ValueError):
            harness.record_review(self.store,self.job['id'],{'model':'qwen','verdict':'approved','summary':'ok'})
        (self.repo/'new.py').write_text('print(1)')
        with self.assertRaises(ValueError):
            harness.record_review(self.store,self.job['id'],{'model':'gpt-6.1-terra','verdict':'approved','summary':'ok'})

    def test_review_rejects_different_clean_commit(self):
        """REVIEW-1: A checkout/commit change invalidates review even with no diff."""
        with patch('harness.prepare_gpu'),patch('harness.http_json',return_value={'models':[]}),patch('harness.run_command',return_value=0):
            harness.execute_job(self.store,self.job['id'],self.config)
        (self.repo/'new.py').write_text('print(1)')
        subprocess.run(['git','add','.'],cwd=self.repo,check=True,capture_output=True)
        subprocess.run(['git','-c','user.name=Harness Test','-c','user.email=harness@example.invalid','commit','-m','different clean base'],cwd=self.repo,check=True,capture_output=True)
        with self.assertRaises(ValueError):
            harness.record_review(self.store,self.job['id'],{'model':'gpt-6.1-terra','verdict':'approved','summary':'ok'})

    def test_separate_store_cannot_bypass_installation_gpu_lock(self):
        """GPU-1: Custom job storage still uses the same installation GPU lease."""
        shared=self.root/'global-state'
        lease=harness.GpuLease(shared);self.assertTrue(lease.acquire());self.addCleanup(lease.release)
        request=harness.read_json(self.store.folder(self.job['id'])/'request.json');request['timeout_seconds']=1
        harness.write_json(self.store.folder(self.job['id'])/'request.json',request)
        with patch('harness.GPU_ROOT',shared,create=True),patch('harness.prepare_gpu'),patch('harness.http_json',return_value={'models':[]}),patch('harness.run_command',return_value=0):
            harness.execute_job(self.store,self.job['id'],self.config)
        self.assertEqual(self.store.read(self.job['id'])['state'],'timed_out')


if __name__=='__main__': unittest.main()
