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

No clean Windows OS installation, new NVIDIA driver install, full dependency
download/install, live Ollama alias replacement, model download or gated-license
acceptance was performed for publication. The current ComfyUI source pin and
model stack were verified from a working reference environment. Accounts and
upstream availability remain external prerequisites. A new machine must perform
the verification checklist before full routing activation.
