# Verify this machine before activation

Start with `bootstrap.py verify`. A ready diagnostic is service/configuration
evidence, not an inference, review or quality result.

1. Run `python -m unittest discover -s tests -v`. Record the real count and any
   skipped native tests. Set `COMFY_PYTHON` and `COMFY_ROOT` for installed-runtime
   checks, then run those checks when the dependencies are available.
2. Stage the roles with `install.py stage`. In a fresh signed-in Sol chat, call
   native Astra on a bounded question, `terra_coder` on a bounded implementation,
   and a separate fresh `terra` agent on that patch's review. Confirm
   role discovery and actual responses. The root must use the OpenAI provider.
   From an unrelated project after restarting Codex, check `/skills` for an
   enabled user-scoped `local-harness` at the rendered profile path. The registry
   can also be checked with app-server `skills/list` and `forceReload`. Prompt
   rendering alone is not the skill registry. Activation's `AGENTS.md` entry
   additionally tells Sol to load the skill through its explicit absolute path.
3. Run one bounded native Terra code task on an isolated repository branch, with
   a behavioral contract and failing tests first. Require passing acceptance
   checks and a separate Terra review of the exact unchanged patch. Record coder
   and reviewer session IDs separately. Native coding never leases the media GPU
   or calls Ollama. Set `terra_coder` evidence only after the real task passes.
4. Generate a short image, image edit, T2V, I2V, source-video regeneration,
   music, SFX and speech sample through the public runner. Request schemas and
   exposed controls are in `workflows/*.json`. Stage real authorized references
   in ComfyUI input first. An edit clip must meet the 24fps/count/aspect guard.
5. Confirm retrieved outputs decode fully. Inspect the requested change, unwanted
   changes and full-speed motion separately; audition generated audio. Record a
   failed artistic result honestly even if the technical smoke passed.
6. Exercise cancellation with two isolated projects. Cancel only the selected
   owned job and confirm the unrelated job remains intact. Keep the actual job
   IDs and logs under ignored `.runtime` or `work`.
7. Fill the private activation-evidence copy from observed capability checks.
   `video_edit: true` means the registered experimental regeneration route ran
   technically. It does not certify precise recoloring or masked editing.
8. Run `install.py activate --evidence <private-file>`, retain its backup path,
   and open a fresh Sol chat. Confirm the rendered runner path, role names,
   OpenAI provider and LTX routing. Keep evidence from this destination machine.

The example evidence file is deliberately all false. Do not copy a previous
machine's successful evidence as proof of this installation.

On the original machine, the three current LTX routes produced fully decoded
121-frame 512-square videos at 24fps with stereo 48kHz audio. Pot recoloring
failed at retention 0.40 and 0.20. The model migration did not establish full
playback quality or fix the earlier ear artifact.
