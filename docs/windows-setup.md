# One-script Windows installation

Download [setup.ps1](https://raw.githubusercontent.com/alekseibaryshnikov/codex-ollama-comfyui/main/setup.ps1)
to your Downloads folder, then run this in a normal 64-bit Windows PowerShell
terminal. Git and Python do not need to be installed first.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\setup.ps1"
```

This execution-policy override applies only to this process. The script asks
once before installing packages and accepting their WinGet package/source terms.
It does not change the machine's permanent execution policy. Run as the account
that will use Codex, not as SYSTEM or a different administrator account. Windows
or an installer may still show a UAC or Microsoft Store prompt.

## What it does

1. Checks Windows x86-64 and an installed NVIDIA driver. Windows App Installer
   must provide `winget`; the script gives its official Store link if missing.
   Install a compatible NVIDIA display driver and reboot if needed. The locked
   CUDA 13 wheels need driver branch 580 or newer. A separate CUDA Toolkit isn't
   required. The reference hardware is RTX 5080 16 GB with about 64 GB RAM.
2. Installs missing Git, Python 3.12 x64, Codex CLI and Codex desktop.
   Existing tools aren't silently upgraded or downgraded. Ollama and Qwen coding
   weights aren't installed, started or downloaded by this script. Existing
   Ollama software, services and weights are left in place.
   WinGet currently supplies CPython 3.12.10; this is compatible with the locked
   CPython 3.12 x64 wheels. The older reference inventory records 3.12.13.
3. Clones this repository, or verifies an existing clean checkout with the
   expected origin. It preserves unrelated/edited repositories and doesn't
   pull over an existing checkout. To update a previous installer checkout,
   pull its reviewed update yourself before rerunning.
4. Generates local configuration, installs the locked ComfyUI source and Python
   environment, then executes a small real PyTorch CUDA operation. Refused or
   incompatible environments cannot proceed to provisioning.
5. Restores the 131 standalone skills and stages native `astra`, `terra_coder`
   and `terra` agents
   and rendered harness skill for the selected profile. Existing skill edits
   cause the skill restorer to stop before publishing its batch.
6. Checks ChatGPT login, asks for browser login if necessary, and restores the
   14 recorded plugins through Codex's native installer. Available versions and
   host-only plugin support depend on the destination Codex installation. It
   reports failures without treating a partial restore as complete.
7. Checks Hugging Face authentication. If needed, runs the managed environment's
   `hf auth login` directly in your terminal. Accept
   [LTX-2.5 terms](https://huggingface.co/Lightricks/LTX-2.5) and
   [Stable Audio Open terms](https://huggingface.co/stabilityai/stable-audio-open-1.0)
   on that same account. The provisioner checks gated access before downloading
   any weights. Login does not itself accept model terms.
8. Downloads and verifies the media weights and speech dependencies. It starts
   managed ComfyUI in the background, then runs service/decoder verification.
   Long-running service processes clear common credential environment variables.
9. Writes `work/windows-setup/report.html`, `report.json` and command/service
   logs. If the checkout is refused or its work directory is redirected, a new
   sibling report directory keeps the refused directory untouched.

The media catalog is about 87.81 GB, with CUDA/Python packages
and temporary files separate. Allow around 200 GB free. Downloads can take hours
depending on bandwidth. These are installation steps, not asset generation jobs.

## Paths, preview and resume

Defaults are `%USERPROFILE%\Documents\Codex\codex-ollama-comfyui` for the checkout,
`%USERPROFILE%\AI\ComfyUI` for the managed app and environment, and `CODEX_HOME`
or `%USERPROFILE%\.codex` for the Codex profile. Skills use its sibling
`.agents\skills` folder. Use absolute local paths without junctions/symlinks.

```powershell
# No downloads, installations, service starts or file writes.
.\setup.ps1 -Plan

# Custom directories, retaining interactive account sign-in.
.\setup.ps1 -Approved -InstallRoot D:\AI\codex-harness -ComfyRoot D:\AI\ComfyUI

# No account prompts. Missing access is reported with exit code 2.
.\setup.ps1 -Approved -NonInteractive

# Select one profile consistently for plugins, login, roles and routing.
.\setup.ps1 -Approved -CodexHome C:\Profiles\MyCodex\.codex
```

Rerun with the same paths after resolving a reported problem. Completed files
are revalidated by the existing provisioners. An interrupted large file may need
to download again; this isn't HTTP byte-range resume. Old model/environment
content and changed skills aren't overwritten to force progress. A partial
installation isn't rolled back automatically, so completed downloads remain.

Exit code `0` means preview completed or an explicitly requested activation
completed. `2` means approval, account access, a component or verification still
needs attention. `1` means a critical dependency failed. Check the JSON/HTML
report and the actual console error. Login prompts aren't copied into command
logs. Tokens belong in local login caches or the local environment, not arguments,
the repository or a chat.

The installer starts hidden service processes, not Windows startup services.
They remain running after setup and may need starting again after a reboot.
Rerunning the script rechecks them. ComfyUI must belong to this installation's
recorded supervisor and exact managed Python process chain, bound to loopback.
An unrelated listener on `8189` is preserved. The script doesn't manage Ollama
or port `11434`. Startup failure logs
remain inspectable; the installer doesn't clear queues or kill unrelated work.

## Enable routing after verification

Installation leaves routing staged. It creates `work/activation-evidence.json`
from the all-false template only when absent, preserving any existing edits.
Service readiness does not prove model inference, native Astra/Terra responses,
user-scope skill discovery, output quality or cancellation behavior.

Follow [the destination verification checklist](verification.md), recording only
observed results. Then use the same script to invoke the existing activation gate:

```powershell
.\setup.ps1 -Approved -Evidence .\work\activation-evidence.json
```

The supplied evidence path is resolved against your terminal's directory before
the script enters the checkout. All required evidence flags must pass, and no
installer component can remain failed. The `terra_coder` evidence flag requires
an actual native coder task, separate from the `terra` review check.
Activation backs up global files through
`install.py`; its printed backup can be restored using the documented rollback.
Open a new signed-in Codex chat and reconnect any account-backed apps afterward.

## Verified boundaries

The automated installer tests execute actual Windows PowerShell 5.1 and real
temporary reports/evidence, replacing package installation, accounts and most
services. A separate real Python 3.12 venv fixture verified the production
listener ownership guard against native Windows process/TCP information and
quoted paths containing spaces. The fixture used a tiny local HTTP app on an
ephemeral port, not ComfyUI or the GPU, and all fixture processes exited.

No clean Windows installation, desktop/driver installation, full model download,
real installer login or complete ComfyUI startup was performed to validate this
entry script. The existing individual components have their separate evidence.

Package IDs and command behavior were checked against
[OpenAI's Windows deployment instructions](https://learn.chatgpt.com/docs/enterprise/windows-deployment),
[Microsoft's WinGet documentation](https://learn.microsoft.com/windows/package-manager/winget/install),
the official Microsoft manifests for
[Git](https://github.com/microsoft/winget-pkgs/tree/master/manifests/g/Git/Git),
[Python](https://github.com/microsoft/winget-pkgs/tree/master/manifests/p/Python/Python/3/12),
[Codex CLI](https://github.com/microsoft/winget-pkgs/tree/master/manifests/o/OpenAI/Codex),
and [NVIDIA's CUDA 13 release notes](https://docs.nvidia.com/cuda/archive/13.0.1/cuda-toolkit-release-notes/index.html).
