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

    def test_historical_review_requires_explicit_terra_approval(self):
        """REVIEW-1: A persisted reviewable code job remains reviewable after retirement."""
        self.store.update(self.job['id'], state='awaiting_review', fingerprint=harness.fingerprint(self.repo))
        harness.record_review(self.store,self.job['id'],{'model':'gpt-6.1-terra','verdict':'approved','summary':'No actionable findings'})
        self.assertEqual(self.store.read(self.job['id'])['state'],'succeeded')

    def test_review_rejects_changed_diff_and_wrong_model(self):
        """REVIEW-1: Approval must cover current bytes and name Terra."""
        self.store.update(self.job['id'], state='awaiting_review', fingerprint=harness.fingerprint(self.repo))
        with self.assertRaises(ValueError):
            harness.record_review(self.store,self.job['id'],{'model':'qwen','verdict':'approved','summary':'ok'})
        (self.repo/'new.py').write_text('print(1)')
        with self.assertRaises(ValueError):
            harness.record_review(self.store,self.job['id'],{'model':'gpt-6.1-terra','verdict':'approved','summary':'ok'})

    def test_review_rejects_different_clean_commit(self):
        """REVIEW-1: A checkout/commit change invalidates review even with no diff."""
        self.store.update(self.job['id'], state='awaiting_review', fingerprint=harness.fingerprint(self.repo))
        (self.repo/'new.py').write_text('print(1)')
        subprocess.run(['git','add','.'],cwd=self.repo,check=True,capture_output=True)
        subprocess.run(['git','-c','user.name=Harness Test','-c','user.email=harness@example.invalid','commit','-m','different clean base'],cwd=self.repo,check=True,capture_output=True)
        with self.assertRaises(ValueError):
            harness.record_review(self.store,self.job['id'],{'model':'gpt-6.1-terra','verdict':'approved','summary':'ok'})



if __name__=='__main__': unittest.main()
