# Publication verification

Reference date: 10 November 2026. This repository was prepared separately from
the running installation. No current global routing, model alias, application
source or package environment was changed to publish it.

## Existing behavior

The copied runner/workflow baseline passed 94 tests before portability edits.
Existing tests retain job lifecycle, deadlines, cancellation, shared GPU locking,
request validation, output decoding, source timing/aspect/rotation, native review
records, model dependency checks and targeted ComfyUI ownership coverage.

The LTX workflows remain the previously exercised eight-step distilled graphs.
Three real reference smokes produced 121-frame 512-square 24fps clips with stereo
audio. Targeted white-pot recoloring failed at two source-retention settings;
that is documented as a limitation, not a successful edit. This publication did
not repeat model inference or certify full-motion/audio quality.

## Contract-linked changes

| Requirement | Owning boundary | Tests and observed evidence |
|---|---|---|
| INSTALL-PORTABLE | `install.py` | Four new portability tests first reported three failures and one unimplemented-stage error. After rendering actual checkout/profile paths and adding root-preserving staging, all four passed. Existing seven installer tests passed. |
| MEDIA-PORTABLE | `media.py` | Real child imports first exposed the machine-only decoder path. The default now follows the host interpreter, with an explicit `COMFY_PYTHON` override. Actual decoding remains a separately configured-runtime check. |
| BOOT-1 | `bootstrap.py` | Configure resolves arbitrary roots and catalog destinations, rejects traversal before config writes, and preserves replaced config. The initial four bootstrap tests reached eight unimplemented outcomes before code. |
| BOOT-2/4 | `bootstrap.py`, `harness.GpuLease` | Tests first exposed missing approval/digest/recovery behavior. Additional delayed-promotion tests failed before the persistent alias guard. The final simulated daemon applies a delayed mutation after setup returns and subsequent jobs still refuse until reconciliation. |
| BOOT-3 | `bootstrap.py` | Temporary Git repositories exercise pinned commits, ownership receipts, tracked modifications, ignored executable overrides and known custom-node hashes. Dirty/untracked regressions failed before the source-integrity repair. |
| PROV-ACCESS | `provision.py` | A new test first received incorrect Stable Audio remediation for LTX. It now gets the actual model page and filename, without query credentials. |

The bootstrap suite has 21 passing tests. A final passing characterization uses
the real catalog's 79 destinations with tiny substitute payloads through the
real provisioner. It verifies generated first-launch file layout, not model or
package execution. It was added as characterization, not claimed as test-first
evidence for an already working path.

## Final local checks

- `python -m unittest discover -s tests -v`: **113 tests reported**, `OK
  (skipped=6)` without local native-runtime variables. Optional ComfyUI, decoder
  and voice checks are deliberately not presented as executed in this mode.
- With `COMFY_PYTHON` and `COMFY_ROOT` selecting the existing reference runtime:
  **120 tests passed**, no skips. These tests do not run generation or installers.
- `bootstrap.py configure` was exercised with the actual portable catalog in a
  temporary new path. All 73 files and six wheels resolved under their intended
  roots; the selected application directory stayed absent.
- The portable copy's `verify` command reported ready against the existing
  reference services and decoder, without changing those services.
- Temporary-profile staging preserved root configuration and instructions,
  rendered the chosen checkout path and restored its files through rollback.
  Discovery probes made no model calls. Fresh actual-user discovery is still
  a destination-machine check; a simulated Windows `USERPROFILE` is not a new
  Windows account. The actual Codex `skills/list` registry separately loaded
  the identical rendered skill as enabled at repository scope with zero parse
  errors. Prompt rendering is not the registry. Automatic user-scope discovery
  on a new account remains a destination check.
- All 12 distinct active safetensors matched pinned upstream sizes and SHA-256
  against the reference files. The published Windows wheel metadata resolved
  all required dependency edges within the lock and catalog. Metadata validation
  is not a fresh package installation.

Detailed private run logs stay in ignored `work`; they are not deployment
evidence to copy onto a new machine. The example activation evidence is all
false. Fill it only from real destination checks. GitHub Actions runs the
non-native unit suite without model downloads or stored credentials.

## Evidence limits

### Native Terra coding migration

The bounded implementation and repairs were performed by a native
`gpt-6.1-terra` implementer. A different native Terra agent independently reviewed
the patch and requested two focused repairs before approving it. Sol coordinated
the work and applied the approved deployment.

| Criterion | Contract | Behavioral evidence |
| --- | --- | --- |
| Separate implementation/review roles | `install.py`, INSTALL-NATIVE | `tests/test_install.py`, `tests/test_portability.py`: real staged profiles parse distinct coder/reviewer roles; activation and rollback cover both. |
| Fresh coder evidence | `install.py`, INSTALL-CODER-EVIDENCE | `tests/test_install.py`: missing coder evidence blocks fresh activation before writes. |
| Preserve an activated profile | `install.py`, INSTALL-REFRESH | `tests/test_native_migration.py`: root config and surrounding instruction bytes survive refresh/rollback; conflicting skills and unactivated profiles are refused. |
| Retire local coding execution | `harness.py`, NATIVE-CODE | `tests/test_native_migration.py`: old public code start and historical worker replay refuse before process/GPU work; historical status/review tests remain. |
| Independent native diagnostics | `harness.py`, NATIVE-CODE | Fresh doctor/handoff configurations need no Ollama fields; diagnostics label native availability `not_probed`. |
| Preserve owned legacy GPU handoff | `bootstrap.py`, BOOT-NATIVE | Actual historical configuration shape is represented with fake paths; consistent same-root identities retain the pair, other roots don't inherit it, malformed pairs stop before config or manifest writes. |
| No default local worker installation | `setup.ps1`, WINSETUP-NATIVE | Actual PowerShell fixture runs omit Ollama/Qwen installation and startup while retaining skills/plugins, media setup and gated routing. |

Focused tests failed for missing roles/policy and Windows local-worker routing
before implementation, then passed. Further regressions reproduced the missing
historical root identity and partial legacy ownership cases before each repair.
Actual commands/logs are retained under ignored `work/terra-coder`.

The final `python -m unittest discover -s tests -v` ran **142 tests, OK, seven
optional native/symlink checks skipped**. The final Windows `-Plan` preview lists
native coding/review and contains no Ollama/Qwen installation step.

The scoped active update copied five allowlisted runtime/integration files, then
used `install.py refresh` on the existing profile. Separate before-image backups
and a hash-guarded rollback were saved privately. Its runtime README was also
backed up and updated to point development/testing at the maintained checkout;
the earlier deployment's tests/evidence remain historical. Readback confirmed unchanged
root configuration, media configuration, media/provision sources, all workflow
files and all existing runtime/job data, including 25 terminal jobs. One existing
global harness skill remains discoverable; no duplicate was created.

Live read-only doctor checks reported all seven media presets ready and native
coding configuration separately. The old code command refused before reading
missing request/config files. Actual Codex prompt rendering parsed the distinct
coder/reviewer definitions in both a temporary profile and the real profile.
These parser/doctor checks made no model calls. They do not prove execution of a
new custom role in a fresh user chat, clean-Windows deployment, or a measured
cost/latency improvement. Open a fresh Codex chat to load the updated roles.

### One-script Windows installer

`WINSETUP-1/2/3/4` in `setup.ps1` map to
`tests/test_windows_setup.py` and `tests/windows_setup_cases.ps1`. Tests run
actual Windows PowerShell 5.1 with temporary files, replacing package managers,
authentication and most service boundaries.

- `python -m unittest discover -s tests -p test_windows_setup.py -v` ran against
  declared unimplemented boundaries first. The initial run also exposed a
  reserved PowerShell variable binding problem in five orchestration cases;
  those setup failures are not claimed as meaningful TDD red. The repaired
  lifecycle scenarios provide integration coverage, not a reconstructed TDD
  history. Initial native-command and foreign-listener checks failed at the
  missing boundaries.
- Focused regressions observed real failing outcomes before their repairs:
  omitted CUDA check, alias changes after an Ollama version failure, evidence
  path rebasing, unapproved unattended success, interactive output polluting
  command results, venv supervisor selection, absent venv-chain validation,
  case-sensitive Windows path comparison, and writes through an ignored work
  junction. Report-sentinel coverage was added for Terra's refused-root finding;
  no isolated pre-repair red is claimed for that sentinel assertion.
- The final focused suite ran **13 tests, OK**, including a real NTFS junction
  preservation fixture. The full `python -m unittest discover -s tests -v`
  ran **138 tests, OK, seven optional native/symlink checks skipped**.
- The real `powershell.exe -NoProfile -ExecutionPolicy Bypass -File setup.ps1
  -Plan` returned the expected component/path preview without invoking setup.
- A separate real Python 3.12 venv fixture showed the Windows supervisor to
  managed redirector to base-interpreter listener chain. The production guard
  then passed against actual Windows TCP/CIM information and native argv
  parsing with paths containing spaces. The tiny HTTP fixture bound an
  ephemeral loopback port; its command-line port value exercised the guard.
  This was not ComfyUI startup or GPU inference. All fixture processes exited.

Detailed red/green logs, process traces and reports remain in ignored `work`.
No prerequisite installation, real setup login, full model download or clean-OS
installation was run for this entry script. Destination checks remain required.

### Installed skill recovery addition

`SKILLS-1/2/3` in `restore_skills.py` map to
`tests/test_restore_skills.py`. The fixture suite uses real temporary profile
files and replaces Git/plugin subprocess boundaries; it doesn't prove native
installation by itself.

- `python -m unittest discover -s tests -p test_restore_skills.py -v` first
  collected nine tests against the declared, unimplemented restore boundary and
  failed there. After implementation the same tests passed, with the host's
  unsupported symlink fixture skipped.
- Two plugin tests failed against their declared unimplemented boundary, then
  passed. Further regression assertions observed useful failures for hidden
  native stderr, repeated marketplace registration, and missing fresh-profile
  `CODEX_HOME`. Each repair passed the same regression before integration.
- Final focused suite: 12 tests, OK, one symlink fixture skipped. Full
  `python -m unittest discover -s tests -v`: 125 tests, OK, seven optional
  native/symlink checks skipped. Private red/green logs remain in ignored `work`.
- Real `python restore_skills.py --approved --codex-home
  work/skills-smoke-profile/.codex` fetched the eight pinned public sources and
  installed all 131 standalone skills into an isolated profile. Independent
  readback matched the manifest's exact 1,672 file paths, sizes and SHA-256
  digests (68,476,716 bytes). No reference user skill was changed.
- Codex app-server `skills/list` discovered all 131 restored skills as enabled,
  with zero parse errors, at repository scope under that isolated profile.
  This exercises actual native parsing, not a replacement parser. Actual new
  Windows account user-scope discovery remains a destination check.
- The native plugin command registered Ponytail and installed it in a second
  isolated profile. A repeat restore returned Ponytail unchanged with no errors.
  The other 13 plugin installs and external account connections were not run.

These checks restore and discover skills. They don't exercise each skill's
workflow or install its additional runtime tools.

No clean Windows OS installation, new NVIDIA driver install, full dependency
download/install, live Ollama alias replacement, model download or gated-license
acceptance was performed for publication. The current ComfyUI source pin and
model stack were verified from a working reference environment. Accounts and
upstream availability remain external prerequisites. A new machine must perform
the verification checklist before full routing activation.
