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
