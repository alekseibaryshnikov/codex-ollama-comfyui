# Codex, Ollama and ComfyUI on Windows

A recoverable local harness with Codex as the interface. Sol coordinates normal
work, Terra reviews every code patch, and Astra handles difficult work. Local
Qwen is optional and used only for suitable bounded coding tasks. ComfyUI makes
the media.

This repository contains source, workflows, model download references and
Windows dependency locks. It does **not** contain model weights, credentials,
machine configuration, generated media or old job histories.

## What it restores

| Task | Route |
|---|---|
| Coordination and normal coding | `gpt-6.1-sol`, high reasoning |
| Difficult work | Native `astra`, `gpt-6-astra`, high |
| Independent code review | Native `terra`, `gpt-6.1-terra`, high |
| Optional local coding | Ollama `qwen3.8:27b-codex`, 262,144 context tokens |
| Images | Juggernaut XL |
| Image editing | Qwen Image Edit 2511 INT8 with four-step Lightning |
| Video generation | LTX-2.5 distilled NVFP4, text or first-frame image |
| Existing-video regeneration | LTX-2.5 full-source-frame guidance, experimental |
| Music / sound effects / speech | ACE-Step 1.0 / Stable Audio Open 1.0 / Kokoro |

OpenAI models use signed-in Codex access. No separately billed OpenAI API client
is added. Your Codex account must provide the configured models and subagents.

## Fresh Windows setup

Start with Windows x86-64, Git, 64-bit Python 3.12, the Codex app and CLI, Ollama,
and a compatible NVIDIA driver. The reference GPU is an RTX 5080 with 16 GB VRAM;
the reference machine has about 64 GB RAM. This is not a CPU-only installation.

The active download catalog is about **87.81 GB**, with Qwen's roughly 17.74 GB
Ollama download and the Python/CUDA environment separate. See
[the catalog](manifests/catalog.json) for every size, SHA-256, source and license.
The exact known Python build is recorded in [the runtime lock](locks/runtime.json).

```powershell
git clone https://github.com/alekseibaryshnikov/codex-ollama-comfyui.git
cd codex-ollama-comfyui

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

### Optional Qwen and Codex integration

Start the Ollama app, then configure the local coding worker:

```powershell
py -3.12 bootstrap.py ollama --approved
py -3.12 bootstrap.py verify

# Prepare native roles and the skill without changing root model or routing.
py -3.12 install.py stage
```

The Ollama command checks the pinned base digest, prepares the worker with
`num_ctx=262144`, and preserves an existing alias before replacement. It does
not run inference. `verify` checks decoder imports and service/model/workflow
readiness; it reports the optional worker separately. It does not prove output
quality or that a full 262K prompt will finish quickly.

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

## Everyday commands

```powershell
py -3.12 harness.py doctor
py -3.12 harness.py asset start --request examples\image.json --workspace .
py -3.12 harness.py code start --request my-task.json --workspace C:\Projects\my-task
py -3.12 harness.py status <job-id>
py -3.12 harness.py cancel <job-id>
py -3.12 harness.py review <job-id> --result my-terra-review.json
```

Code requests need an existing Git base commit and a task branch. Passing Qwen
and check commands yields `awaiting_review`. Sol records Terra's real review of
the unchanged patch before acceptance. At most two focused repairs are allowed;
difficult remaining work goes to Astra. Model/tool failures return to Sol rather
than an endless shell-repair loop.

Jobs return IDs immediately and save requests, logs, graphs and outputs under
`.runtime`. Projects call one installed runner and share its GPU lease. The
runner waits for unrelated ComfyUI work, unloads the other engine before GPU
handoff, and cancels only owned work. Normal limits are ten minutes for coding,
images and audio, and thirty minutes for video. Larger jobs need an explicit
limit increase. Technical success requires retrieved, fully decoded files.

Worker sessions disable connectors, nested agents and skill injection, and
filter inherited credentials from their environment. Normal filesystem
permissions and Codex sandbox rules still apply; this is not a filesystem
secrecy boundary.

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

Qwen's loaded 262,144-token allocation was confirmed on the reference machine.
A 98,637-token retrieval test passed in about 235 seconds; the calibrated
near-full request hit its 600-second limit. Full-window quality remains unverified.
Ollama reported a 76% CPU / 24% GPU split. These are reference observations, not
promises for another machine.

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
