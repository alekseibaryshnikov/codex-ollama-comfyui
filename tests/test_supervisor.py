"""JOB-3 at process_identity/inspect_job, real child and disk, no model calls."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import harness


class SupervisorTests(unittest.TestCase):
    def test_dead_supervisor_becomes_failed_on_status(self):
        """JOB-3: Terminated worker cannot remain running or ignore cancellation."""
        scratch=Path(__file__).resolve().parents[1]/'work';scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            root=Path(temp);store=harness.JobStore(root/'state')
            state=store.create('asset',{'preset':'image','prompt':'test'},root)
            child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
            try:
                identity=harness.process_identity(child.pid)
                self.assertIsNotNone(identity)
                harness.write_json(store.folder(state['id'])/'owner.json',{'pid':child.pid,'identity':identity})
                child.kill();child.wait(timeout=5)
                result=harness.inspect_job(store,state['id'])
                self.assertEqual(result['state'],'failed')
                self.assertIn('supervisor',result['error'])
            finally:
                if child.poll() is None:child.kill();child.wait()

    def test_reused_pid_is_not_treated_as_owned_supervisor(self):
        """JOB-3: Changed creation identity marks failure without killing PID."""
        scratch=Path(__file__).resolve().parents[1]/'work'
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            root=Path(temp);store=harness.JobStore(root/'state')
            state=store.create('asset',{'preset':'image','prompt':'test'},root)
            import os
            harness.write_json(store.folder(state['id'])/'owner.json',{'pid':os.getpid(),'identity':'wrong-creation-time'})
            result=harness.inspect_job(store,state['id'])
            self.assertEqual(result['state'],'failed')

    def test_orphan_media_cancel_is_targeted(self):
        """JOB-3: Explicit cancel can stop the known prompt of a dead supervisor."""
        scratch=Path(__file__).resolve().parents[1]/'work'
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            root=Path(temp);store=harness.JobStore(root/'state')
            state=store.create('asset',{'preset':'image','prompt':'test'},root)
            store.update(state['id'],state='failed',prompt_id='owned-prompt',error='supervisor died')
            with patch('media.cancel') as cancel:
                result=harness.cancel_job(store,state['id'],{'comfy_url':'http://127.0.0.1:8189'})
            cancel.assert_called_once_with('owned-prompt','http://127.0.0.1:8189')
            self.assertTrue(result['cancel_requested'])


if __name__=='__main__':unittest.main()
