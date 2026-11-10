# Recover without overwriting unrelated work

Keep the latest printed global-integration backup. `install.py rollback` checks
every installed hash before restoring anything. If a file changed afterward,
inspect and preserve the later edit before deciding how to restore. Roll back
newest-first. Global rollback does not uninstall model weights or environments.

`configure` backs up changed local configuration under ignored `.runtime`.
`comfy` does not repair unrelated existing applications/environments in place.
A failed newly created component is retained under a unique `*-failed-*` sibling
for inspection. Fix the concrete failure and rerun the approved step; don't clear
unrelated directories to make installation proceed.

## Uncertain ComfyUI submission

The runner persists its owned prompt UUID before POST. A missing or mismatched
acknowledgement leaves `.runtime/unconfirmed-prompt.json` and an operator flag.
Further harness GPU work refuses to start. Inspect the marker's exact endpoint,
job and prompt. An empty queue alone does not prove validation cannot enqueue
later. Settle the old supervisor and outstanding request before reconciling the
owned prompt. Never clear the whole queue or interrupt unrelated jobs.

## Uncertain Ollama alias promotion

This section concerns retained legacy maintenance only. New routine coding uses
native Terra, and the default Windows installer doesn't manage Ollama. Existing
uncertainty guards are preserved so an older unsettled operation isn't bypassed.

`.runtime/unconfirmed-ollama-alias.json` protects the shared lease before the
live worker alias is replaced. It records the worker, prior digest, candidate
digest and verified backup where present. A timeout can precede a delayed copy;
one matching `/api/tags` response does not prove the request is settled.

Stop or restart the local Ollama daemon to conclusively drain the outstanding
operation, coordinating with any unrelated users of that service. Then inspect
the marker and actual tags. Keep/promote the verified candidate or restore the
verified backup as appropriate; if the worker was absent originally, restore
that absence when rolling back. Verify the final digest or absence before
removing **only** the alias uncertainty marker. Keep recovery aliases until
reconciliation is complete. Do not clear the guard to bypass the check.

Stale guards survive process restarts deliberately. These instructions do not
authorize a background agent to restart unrelated services without permission.

## Authentication and model access

Use `hf auth login` from the Comfy environment or its local token cache. Accept
both LTX-2.5 and Stable Audio Open terms on that same account. Do not paste tokens
into chats, manifests, Git URLs or issue reports. The provisioner identifies the
actual failed model; approving a download does not grant upstream access.

## Moving the checkout

Clone at the new location, rerun `configure` for the selected Comfy root, and
restage/re-activate the integration with verified destination evidence. Installed
skills contain the actual runner path, so a moved checkout needs re-rendering.
Do not run two independent harness installations against the same GPU; projects
should call one installed runner and its shared lease.

## Restoring skills

Run `py -3.12 restore_skills.py` to preview the recorded standalone catalog and
add `--approved` to fetch pinned sources and install. Use `--codex-home` to
select a separate profile. A differing skill in either `.agents/skills` or the
legacy `.codex/skills` stops the batch before publication. Compare and move that
copy yourself if you want the recorded version; recovery never overwrites it.
If publication is interrupted, already published complete skills remain valid;
rerun to finish. Unrelated skill folders aren't deleted.

Use `--plugins --approved` for recorded plugins. Existing enabled plugins and
matching registered marketplaces are retained. A same-name marketplace with a
different source or explicit revision is preserved with an error. The command
doesn't change it to force installation. Native plugin installation may update
the selected profile's config and cache; it doesn't use the harness activation
backup. Review the JSON result and retry missing plugins after resolving the
reported problem. Use Codex's plugin browser to remove a plugin if needed.

System skills and account-backed app connections come from the destination
Codex installation. Open a new chat and check discovery. Don't copy plugin
caches or authentication files from an old Windows account. Skill-specific
runtime dependencies remain separate setup tasks.

## Updating an already activated coding route

`python install.py refresh` requires an existing marked harness block and a
Sol/OpenAI root configuration. It updates the native coder/reviewer roles, skill
and only that marked block, preserving root config bytes and unrelated
instructions. It prints a backup for `python install.py rollback <backup>`.
Fresh installs still need stage, destination smoke evidence and activate.

If the existing profile uses the legacy `.codex/skills/local-harness` location,
the update retains it. If both legacy and canonical copies exist, reconcile
them explicitly before applying the update; an obsolete coding policy must not
remain discoverable. Restart Codex or open a fresh chat to reload the role files.
