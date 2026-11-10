---
name: local-harness
description: Coordinate local coding and ComfyUI assets with Sol, Terra review, Astra escalation and an optional Ollama worker for suitable coding tasks.
---

# Local harness

Sol (`gpt-6.1-sol`, high reasoning) coordinates and handles normal implementation.
Native `terra` (`gpt-6.1-terra`, high) independently reviews every implementation
and repair. Native `astra` (`gpt-6-astra`, high) handles difficult architecture,
ambiguous failures and escalations. Use signed-in Codex access.

The Ollama worker `qwen3.8:27b-codex` is **optional and coding-only**. It is a
configured alias of the installed Qwen3.8:27b weights with 262,144 context tokens.
Configured capacity is separate from verified long-input performance. Select it for a bounded,
well-specified code change with useful tests when its local tool path is suitable.
It is not a required hop before Sol can implement. Never use it for coordination,
planning, research, code review, asset prompts or asset generation. Qwen Image
Edit is a separate ComfyUI image model, not this Ollama worker.

Worker and specialist sessions perform their bounded assignment without invoking
this coordinator workflow or delegating recursively.

Runner: `__HARNESS_ROOT__/harness.py`.
Use absolute request/workspace paths. Commands return JSON; retain each job ID.
`doctor` reports asset readiness separately from optional local-worker readiness.

## Coding

Follow existing branch and SDD/TDD instructions before changing behavior. Pull
current main with fast-forward only when an upstream exists and existing work
can be preserved; create the task branch before editing. Never discard work.

Sol can implement directly or delegate difficult work to Astra. For every patch,
run acceptance checks and ask Terra to review the exact current code and evidence.
Repairs need fresh checks and review. Preserve native review evidence; passing
tests alone do not establish acceptance.

When Qwen is suitable:

1. Write JSON with `task`, a nonempty `checks` list of argv lists, and an
   appropriate `timeout_seconds` (at most 600 by default). Supply the contract,
   observed red evidence, permitted files and implementation constraints.
2. Run `python <runner> code start --request <json> --workspace <repository>`.
   The coordinator establishes the Git base/task branch first.
3. Inspect `status <id>` and actual errors. A tooling failure or timeout returns
   the assignment to Sol; do not keep cycling through shells. At most two focused
   repairs are allowed when a real patch and actionable check/review findings
   justify them. Escalate difficult remaining work to Astra.
4. After `awaiting_review`, obtain Terra's actual verdict. Save JSON with
   `model: "gpt-6.1-terra"`, `verdict: "approved"` or `"changes_requested"`, and
   a nonempty `summary`. Run `review <id> --result <json>`. Approval must cover
   unchanged current bytes. Never describe a failed Qwen job as successful
   because another agent later repaired the code.

No unattended commits, pushes or deployments are authorized by this skill.
Specialists retain parent permissions; reviewer instructions are not a sandbox.

## Assets

Use the registered presets below. The Ollama coding worker does not participate.

| Preset | Model and role |
|---|---|
| `image` | Existing Juggernaut XL image generation |
| `image_edit` | Qwen Image Edit 2511 with four-step Lightning; provisional targeted editing |
| `video` | LTX-2.5 distilled NVFP4; default text/image-to-video generation |
| `video_edit` | LTX-2.5 full-source-frame guided regeneration; experimental |
| `music` | Existing ACE-Step 1.0 |
| `sfx` | Existing Stable Audio Open 1.0 |
| `speech` | Existing Kokoro |

Write JSON with `preset`, nonempty `prompt`, and supported inputs from
`__HARNESS_ROOT__/workflows/<preset>.json`.
Run `asset start --request <json> --workspace <project>` and inspect `status <id>`.
Use `cancel <id>` to stop only that job. Keep exact graphs and actual node errors;
do not repeatedly rebuild failed workflows or install unrelated packages.

`image_edit` requires `reference_image`; `video_edit` requires `reference_video`.
`video` accepts an optional `reference_image`. These are existing safe relative
filenames inside ComfyUI's input directory, not absolute Windows paths or names
that merely describe a file. Copy/upload authorized local inputs there first.

Start LTX previews at 512 square and about five seconds. The pinned distilled
recipe uses eight steps at 24fps. Duration maps to native 8k+1 frames: 121 frames
for five seconds, 145 for six and 361 for fifteen. Video and audio lengths stay
paired. Use the exact registered graph and exposed inputs; old H3 reference tags
and the `[video editing]` marker are rejected rather than reinterpreted.

Describe the desired visible scene, action, camera and sound in natural language.
For image-conditioned generation, source pixels pass through preprocessing into
the first latent frame at strength 0.70. Reference images are resized/cropped to
the requested shape; stage the intended framing when composition matters.

For `video_edit`, stage a constant-24fps source with exactly the requested native
frame count. The runner checks count, timestamps and displayed aspect ratio
(including rotation) before GPU use. Same-aspect scaling is allowed; prepare an
incompatible segment explicitly rather than silently trimming, changing timing
or center-cropping it. Keep the staged file stable until inference completes.

The edit graph encodes every source frame. `source_strength` is retention in
[0,1], default 0.40: higher values retain more source content, lower values allow
more regeneration. This default is a starting recipe, not calibrated editing
fidelity. This is experimental source-guided regeneration. Judge the requested
change and preservation of appearance and motion separately. Specialized
instruction editing, time-window Retake and mask-local preservation are not
registered capabilities. Do not claim them or use the Ingredients adapter as a
generic editor. Never silently fall back to H3. In the local white-pot smoke,
retention 0.40 and 0.20 both left the pot brown in inspected frames. Targeted
object recoloring is not validated by this recipe. For precise edits, report the
missing validated capability instead of promising preservation or looping over
rebuilds.

Current LTX presets generate new audio. Source soundtrack preservation requires
an explicitly authorized postprocessing step and separate verification.

Depth and IP-Adapter remain deliberate controls. H3 and Wan A14B remain retained
manual alternatives; VACE remains experimental. No new weights, adapters or
custom nodes are approved by this route change. Add and validate a compatible
registered graph before routing to another recipe.

Image/audio jobs default to 600 seconds; video jobs default to 1800. A larger
limit requires the user's explicit request. Jobs share one GPU lock and wait for
unrelated ComfyUI work. Do not clear queues or stop unrelated services.

An uncertain ComfyUI submission leaves `operator_check_required` in status and
a durable shared `.runtime/unconfirmed-prompt.json` guard. Stop launching GPU
work and reconcile its stored prompt UUID and endpoint. An empty queue alone is
not enough: the previous supervisor and outstanding request must be settled.
Never automatically delete that guard or stop unrelated work to bypass it.

An uncertain Ollama worker-alias promotion leaves
`.runtime/unconfirmed-ollama-alias.json` and blocks the same shared lease.
It records the candidate, verified backup and their digests. Settle the outstanding
daemon operation before reconciling aliases; an immediate tags snapshot alone
does not prove a delayed promotion cannot apply. Follow
`__HARNESS_ROOT__/docs/recovery.md`. Never clear either uncertainty guard merely
to make another job start.

Technical success requires retrieved, decoded files. Artistic acceptance also
requires checking the requested change, unwanted changes and temporal quality.
Review full playback and audition sound when quality matters. If only sampled
frames or decoding were checked, say so and keep artistic acceptance open.
