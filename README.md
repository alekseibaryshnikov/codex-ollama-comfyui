# Codex and ComfyUI on Windows

A recoverable harness with Codex as the interface. Sol coordinates, native
`terra_coder` implements routine bounded code changes, and a separate fresh
`terra` session reviews every patch and repair. Astra handles difficult work.
ComfyUI makes the media. Coding uses signed-in Codex access and no local GPU.
See the [HTML routing and verification report](docs/terra-coding-routing.html).

This repository contains source, workflows, custom skills, pinned references to
installed upstream skills, model download references and Windows dependency locks.
It does **not** contain model weights, credentials,
machine configuration, generated media or old job histories.

## What it restores

| Task | Route |
|---|---|
| Coordination and complex work | `gpt-6.1-sol`, high reasoning |
| Routine coding | Native `terra_coder`, `gpt-6.1-terra`, medium |
| Difficult work | Native `astra`, `gpt-6-astra`, high |
| Independent code review | Native `terra`, `gpt-6.1-terra`, high |
| Images | Juggernaut XL |
| Image editing | Qwen Image Edit 2511 INT8 with four-step Lightning |
| Video generation | LTX-2.5 distilled NVFP4, text or first-frame image |
| Existing-video regeneration | LTX-2.5 full-source-frame guidance, experimental |
| Music / sound effects / speech | ACE-Step 1.0 / Stable Audio Open 1.0 / Kokoro |

OpenAI models use signed-in Codex access. No separately billed OpenAI API client
is added. Your Codex account must provide the configured models and subagents.

## Fresh Windows setup

### One script

Download [setup.ps1](https://raw.githubusercontent.com/alekseibaryshnikov/codex-ollama-comfyui/main/setup.ps1)
and run it in a normal **64-bit Windows PowerShell** window:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\setup.ps1"
```

It installs Git, Python 3.12 x64, Codex desktop and CLI, the managed
ComfyUI environment, model weights, your 131 skills, the native agents and your
recorded plugins. It starts the local services and checks CUDA and service
readiness. Account sign-in and model terms still need your participation.
Allow about **200 GB free**, a compatible NVIDIA driver and Windows App Installer.

Use `-Plan` for a read-only preview. Rerun the same command to resume; existing
content is rechecked, not blindly skipped. [The full installer guide](docs/windows-setup.md)
covers custom paths, unattended runs, reports and the final routing activation
after destination smoke checks. The individual commands below remain available.

Start with Windows x86-64, Git, 64-bit Python 3.12, the Codex app and CLI,
and a compatible NVIDIA driver. The reference GPU is an RTX 5080 with 16 GB VRAM;
the reference machine has about 64 GB RAM. This is not a CPU-only installation.

The active download catalog is about **87.81 GB**, with the Python/CUDA environment
separate. Ollama and the Qwen coding weights aren't installed by default. See
[the catalog](manifests/catalog.json) for every size, SHA-256, source and license.
The exact known Python build is recorded in [the runtime lock](locks/runtime.json).

```powershell
git clone https://github.com/alekseibaryshnikov/codex-ollama-comfyui.git
cd codex-ollama-comfyui

# Preview and restore standalone skills. This doesn't require ComfyUI or Ollama.
py -3.12 restore_skills.py
py -3.12 restore_skills.py --approved

# Choose any local installation directory. Nothing downloads in this step.
py -3.12 bootstrap.py configure --comfy-root "$env:USERPROFILE\AI\ComfyUI"

# Inspect the generated manifest and upstream model terms before approving.
Get-Content work\download-manifest.json

# Create a new, owned ComfyUI checkout and Python environment.
py -3.12 bootstrap.py comfy --approved
```

If `py -3.12` isn't available, use the full path to a 64-bit Python 3.12
interpreter. Configuration generation and the runner itself support Python 3.11+;
the pinned ComfyUI wheels require Python 3.12 on Windows x86-64.

The selected directory will contain `app` and `python` siblings. `comfy` refuses
an unrelated existing checkout or environment. To reuse a separately installed
ComfyUI instead, configure its parent directory, ensure its Python is at the
generated decoder path, and skip `comfy`. Keep using that installation's own
trusted launcher. The strict `run-comfy` command below is for the managed,
locked checkout and refuses unknown source edits or extra custom nodes.
The bootstrap does not upgrade an unrelated installation.

### Your installed skills and plugins

The [skill catalog](manifests/skills.json) restores **131 standalone skills**:
126 from eight pinned public repositories and five bundled custom skills.
Supporting scripts, references, templates and Video Shotcraft assets are included.
The 15 duplicate copies in the reference profile are consolidated; their content
matches after line-ending normalization. See [the inventory](docs/skills-inventory.md)
for names, provenance and license links.
Open the [HTML setup and verification report](docs/skills-setup.html) locally for
the full skill list, restore commands and tested limits.

The destination is the selected profile's `.agents/skills`. A matching existing
skill is left alone. Any differing skill, including a copy in `.codex/skills`,
stops restoration before publishing the batch; move or reconcile that copy
explicitly. No existing skills are overwritten or deleted. Preview is read-only.
The approved restore uses Git and verifies every recorded file's SHA-256 before
installation. Skills' own runtime tools and dependencies aren't installed by this
command. The generated `local-harness` skill is installed by `install.py stage`
below so it points to your actual checkout, giving 132 standalone skills in total.

Plugin skills are restored through Codex, separately from those file snapshots:

```powershell
py -3.12 restore_skills.py --plugins            # Preview 14 enabled plugins.
py -3.12 restore_skills.py --plugins --approved

# Optional isolated profile for either command, without changing your real profile.
py -3.12 restore_skills.py --approved --codex-home .\test-profile\.codex
```

For a new Ponytail marketplace registration, the plugin command requests the
recorded revision and calls `codex plugin add` for missing plugins. Existing
matching marketplace registrations are preserved, including an unpinned one.
Existing enabled plugins stay enabled and aren't reinstalled.
Host-provided marketplaces are resolved by the destination
Codex installation; old machine paths and cache files aren't copied. Plugin
versions are chosen by Codex's available marketplace, not byte-pinned like the
standalone catalog. Errors are returned individually and an incomplete restore
exits with status 1. If a host-only plugin isn't available in the CLI, install it
through the app's Plugins directory. Sign in and reconnect account-backed apps
there as needed. [OpenAI's plugin documentation](https://developers.openai.com/plugins/build/plugins)
describes marketplace setup and account connection requirements.

Open a new Codex chat after restoring. Confirm the restored skills appear in the
skill picker before using them. System skills bundled with Codex are supplied by
the destination app rather than copied into this repository.

### Model access and downloads

Accept the required access terms on the destination account:

- [LTX-2.5](https://huggingface.co/Lightricks/LTX-2.5)
- [Stable Audio Open 1.0](https://huggingface.co/stabilityai/stable-audio-open-1.0)

Review the other model licenses linked in the catalog too. Upstream terms apply
to model use; this repository does not redistribute the weights or grant rights
to them. Log in locally, using the environment created above:

```powershell
$Comfy = "$env:USERPROFILE\AI\ComfyUI"  # Use the directory chosen earlier.
& "$Comfy\python\Scripts\hf.exe" auth login

py -3.12 bootstrap.py models --approved
```

Don't put tokens in this repository or command arguments. `HF_TOKEN` or the
local Hugging Face token cache can supply authentication. All gated access is
checked before weight downloads. Existing files must match their pinned size and
hash; divergent files and package versions are preserved with an error.

Start ComfyUI in a second terminal and leave it running:

```powershell
py -3.12 bootstrap.py run-comfy
```

The launcher uses loopback port `8189`, offline mode and a 3.5 GB VRAM reserve.
It does not create a startup service or expose ComfyUI to the LAN.

### Native Codex integration

Verify the media environment, then stage the native roles:

```powershell
py -3.12 bootstrap.py verify

# Prepare native roles and the skill without changing root model or routing.
py -3.12 install.py stage
```

`verify` checks decoder imports and media service/model/workflow readiness. Its
native coding section describes the configured agents; it does not make a model
call or prove account access. In a fresh signed-in chat, verify both `terra_coder`
implementation and a separate `terra` review. The coding worker never calls
Ollama, acquires the media GPU lease or delegates recursively.

Sign into Codex, choose Sol, and open a fresh chat so the native roles can be
discovered. The skill is rendered for this checkout and installed under the
selected profile's `.agents/skills`; roles go under `.codex/agents`.
`--codex-home <profile>\.codex` supports an explicit profile for staging,
activation and isolated checks.

Follow [the verification checklist](docs/verification.md), then record actual
results in a private evidence file copied from the example:

```powershell
Copy-Item examples\activation-evidence.json work\activation-evidence.json
# Change a capability to true only after its check really passed here.
py -3.12 install.py activate --evidence work\activation-evidence.json
```

Activation refuses incomplete evidence. It backs up every changed global file,
sets Sol/OpenAI as the root provider, installs the native roles and rendered
skill, and adds a marked routing section to global `AGENTS.md`. Unrelated
settings and instructions are preserved. Open a fresh Codex chat afterward.
Staging alone does not enable coordinator routing.

The profile locations follow the official [skills](https://learn.chatgpt.com/docs/build-skills)
and [subagent](https://learn.chatgpt.com/docs/agent-configuration/subagents) documentation.

For an already activated installation, `py -3.12 install.py refresh` updates the
owned routing block, roles and skill with a rollback backup. It preserves root
configuration and instructions outside the block. It isn't initial activation
and doesn't certify account/model availability. Existing legacy skill locations
are retained; duplicate harness skills must be reconciled before updating.

## Everyday commands

```powershell
py -3.12 harness.py doctor
py -3.12 harness.py asset start --request examples\image.json --workspace .
py -3.12 harness.py status <job-id>
py -3.12 harness.py cancel <job-id>
```

Ask Sol to delegate routine coding to `terra_coder` with owned files, a behavioral
contract, observed failing tests and check commands. Use a separate fresh `terra`
reviewer for the exact current patch. At most two focused repairs are allowed;
difficult remaining work goes to Sol or Astra. The old local `code start` route
is retired and refuses new or replayed Qwen work. Historical job status, review
and cancellation remain inspectable. No automatic Ollama fallback is configured.

Jobs return IDs immediately and save requests, logs, graphs and outputs under
`.runtime`. Projects call one installed runner and share its GPU lease. The
runner waits for unrelated ComfyUI work, unloads the other engine before GPU
handoff, and cancels only owned work. Normal limits are ten minutes for coding,
images and audio, and thirty minutes for video. Larger jobs need an explicit
limit increase. Technical success requires retrieved, fully decoded files.

Native coding and review sessions follow their separate bounded role
instructions and inherit the signed-in Codex provider. Normal filesystem
permissions and Codex sandbox rules still apply. Reviewer instructions are not
a filesystem sandbox or proof of model diversity.

## Video and context limits

LTX defaults are 512 square, 24fps and eight distilled steps. Five seconds maps
to 121 frames; six to 145; fifteen to 361. Video edits need a staged source with
the exact native frame count, constant 24fps and matching displayed aspect.
Rotation metadata is checked. Reference filenames are relative to ComfyUI input.

`video_edit` is **experimental source-guided regeneration**, not a validated
precise instruction editor or masked Retake workflow. Tested retention values
0.40 and 0.20 both kept a brown pot instead of making it white. Generated audio
replaces the soundtrack. The earlier robot-ear artifact has not been certified
fixed. Do not treat readable files as artistic acceptance.

For the former local coding worker, a 262,144-token allocation was confirmed.
A 98,637-token retrieval test passed in about 235 seconds; the calibrated
near-full request hit its 600-second limit. Full-window quality remains unverified.
Ollama reported a 76% CPU / 24% GPU split. These are reference observations, not
promises for another machine. These historical results aren't Terra benchmarks.
Installed Ollama software and weights are preserved. `bootstrap.py ollama
--approved` remains an explicit legacy maintenance command, not a coding route.

## Recovery

Both `stage` and `activate` print a backup path:

```powershell
py -3.12 install.py rollback <printed-backup-path>
```

Rollback checks installed hashes first and refuses to overwrite later edits.
Restore layered changes newest-first. It does not remove weights, environments
or Ollama models. See [recovery notes](docs/recovery.md) for uncertain HTTP
submissions and the separate Ollama alias backup.

## Tests and evidence

```powershell
py -3.12 -m unittest discover -s tests -v
```

Core tests use temporary files and simulated services. Optional native tests
need `COMFY_PYTHON` pointing to the Comfy interpreter and `COMFY_ROOT` pointing
to its `app` directory. They do not run model inference. The reference workflows
have real prior image/audio/video smoke evidence; a new machine must run its own
checks. A completely clean Windows installation has not been exercised.

The runner uses Python's standard library. ComfyUI and speech dependencies are
installed only into the selected environment. No agent framework or dashboard
is required. [TDD evidence](TDD_EVIDENCE.md) records the publication checks.
