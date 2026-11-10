"""WINSETUP-1/2/3 in setup.ps1, using actual Windows PowerShell 5.1.

The companion cases replace package managers, authentication and services. Real
temporary reports and evidence exercise orchestration without altering this PC.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('powershell.exe'), 'Windows PowerShell absent')
class WindowsSetupTests(unittest.TestCase):
    def case(self, scenario):
        work = BASE/'work'
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as folder:
            result = subprocess.run([
                'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-File', str(BASE/'tests/windows_setup_cases.ps1'),
                '-Scenario', scenario, '-Scratch', folder,
            ], capture_output=True, text=True, timeout=60)
            if result.returncode == 77:
                self.skipTest('Host does not permit the junction fixture')
            self.assertEqual(result.returncode, 0, result.stdout+'\n'+result.stderr)

    def test_preview_is_read_only(self):
        """WINSETUP-1: Plan needs no installers, service calls or filesystem writes."""
        self.case('preview')

    def test_unattended_without_approval_reports_action_required(self):
        """WINSETUP-1/3: No approval means no installs and a non-success exit."""
        self.case('approval')

    def test_all_components_run_in_order_without_faking_verification(self):
        """WINSETUP-1/2/3: Full simulated install stages routing, reports pending smoke."""
        self.case('lifecycle')

    def test_existing_evidence_is_preserved_and_activation_is_explicit(self):
        """WINSETUP-2: Resume preserves operator evidence, activates only on request."""
        self.case('evidence')

    def test_environment_failure_stops_dependent_execution(self):
        """WINSETUP-1/2: A refused Comfy environment cannot run provisioning or launch."""
        self.case('failure')

    def test_account_and_plugin_failures_remain_visible_while_independent_work_continues(self):
        """WINSETUP-3: No login prompt in unattended mode; report incomplete plugins."""
        self.case('accounts')

    def test_native_nonzero_status_is_not_silently_accepted(self):
        """WINSETUP-1: Real child process failure survives native command boundary."""
        self.case('native')

    def test_redirected_paths_and_foreign_comfy_listener_are_preserved(self):
        """WINSETUP-2: Owned service checks refuse another installation."""
        self.case('foreign')

    def test_failed_ollama_version_check_blocks_model_alias_changes(self):
        """WINSETUP-2: A foreign/incompatible Ollama cannot receive worker changes."""
        self.case('ollama-failure')

    def test_refused_checkout_does_not_overwrite_its_report_files(self):
        """WINSETUP-2: A rejected target keeps all bytes, including report sentinels."""
        self.case('refused-root')

    def test_windows_venv_listener_chain_and_exact_arguments(self):
        """WINSETUP-4: Measured shim/base topology passes; unrelated ancestry/argv fail."""
        self.case('ownership')

    def test_python_discovery_returns_validated_base_interpreter(self):
        """WINSETUP-4: A PATH venv must not add an unverified supervisor shim."""
        self.case('python-base')

    def test_redirected_work_folder_does_not_receive_reports_or_evidence(self):
        """WINSETUP-2: An ignored junction must not redirect installer writes."""
        self.case('redirected-work')
