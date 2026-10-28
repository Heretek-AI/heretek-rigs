# 09-send-identity — sender-binding revoke + rotation runbook (REQ-S4, Refs #9)

Date: 2026-10-28. Worktree: `.lane/trees/09-send-identity`
(branch `feat/09-send-identity`).

`rig mcp token` offers no expiry/audience flags (its mint form always scopes
the grant: `rig mcp token add <name> --seat <session> --rig <managed-rig>`).
Rotation of a sender binding is therefore **revoke + mint replacement**: the old binding secret
stops verifying on its very next use, the new secret verifies. This document
is the operator runbook (§1) plus its executed-live proof in scratch (§2:
revoked-then-represented attestation refused, replacement attestation
accepted, re-key proven both directions).

Secrets discipline: the once-printed binding secret is captured straight to
a 0600 file, never pasted on a command line, in chat, or in a committed
file. Below, printed secrets appear redacted to first/last 2 chars plus
length (`or...BY (len=47, redacted)`); `grep -rE '[A-Za-z0-9_-]{40,}'` over
this file prints nothing. Every new log path in the tooling goes through
`scripts/seed-rig.py:_redact_for_log`.

## §1 Runbook (operator environment)

All commands run with the operator's real `OPENRIG_HOME` (default
`~/.openrig/`). The daemon keeps serving throughout: revocation is effective
on the next verification, no restart involved (proven §2, step 7).

1. Identify the binding (hashes only — tokens are never listed):
   `rig mcp token list --json`
   Expected: the `<session>/send-identity` entry with `"seat": "<session>"`
   and `"rigs": ["<managed-rig>"]` (the same scope the seeder mints with
   `issue_sender_binding(..., rig=<rig>)` and the same scope the reuse check
   (`_grant_scope_matches`) expects).
2. Revoke the compromised/rotated binding:
   `rig mcp token revoke <session>/send-identity --seat <session> --rig <managed-rig>`
   Expected: `Revoked <session>/send-identity: its next request is refused.
   Its rows and records stay.` (`rc=0`). Already-handed-over work stays with
   its owners. (Revoke is name-addressed; the `--seat`/`--rig` flags here
   restate the scope being retired so the operator's intent is explicit in
   shell history. The daemon resolves the grant by name.)
3. Mint the replacement (same name, same seat + rig scope):
   `rig mcp token add <session>/send-identity --seat <session> --rig <managed-rig>`
   (`<managed-rig>` is the seat's own rig — the same scope the seeder uses.
   V24-style mandate: every mint carries `--seat` AND `--rig`. Omitting
   `--rig` mints a rig-unscoped grant that the next seed treats as a scope
   mismatch and revoke-and-replaces, undoing this rotation.)
   The binding secret prints ONCE — capture it to the secrets file
   immediately, e.g. per the S1 seed path
   `$HERETEK_SECRETS/send-id-<session>.key` (mode 600, atomic mkstemp +
   fchmod + replace): never paste it on a command line, in chat, or in a
   file that is committed.
4. Redistribute: the seat picks the new file up through the existing
   `send-identity.json` `!cat` reference (no config edit — the reference
   names the file, not the secret).
5. Verify, in order: the pre-rotation attestation presented against the new
   secret verifies as `unverified` (re-key effective); a fresh attestation
   minted under the new secret verifies as `attested` with the proven
   sender (proven §2, step 7).
6. If step 3's output is unparseable (secret unrecoverable):
   `rig mcp token revoke <session>/send-identity --seat <session> --rig <managed-rig>`
   at once so no live binding grant with an unknown secret lingers, then
   repeat from step 3. The S1 seeder (`scripts/send_identity.py:
   issue_sender_binding`) does exactly this automatically
   (revoke-best-effort + fatal exit).

Failure modes (all fail closed): minting for an existing name refuses
(`'...' already has a grant; revoke it first...`, non-zero exit) — revoke
first (step 2); revoking an unknown name refuses (`No grant named ...`) —
nothing changes; binding file missing/unreadable while a grant exists fails
verification to `unverified` until the file is restored.

## §2 Executed-live evidence (scratch isolation, redacted)

Isolation: `SCRATCH=/tmp/09-rotate-scratch` (mode 700). Every `rig`
invocation below ran with `OPENRIG_HOME=$SCRATCH/home`; the live daemon and
live `~/.openrig/` were never contacted (no live daemon was running; the
scratch daemon bound `127.0.0.1:18439`, a port nothing else uses). Binding
secrets lived at `$SCRATCH/home/binding-{1,2}.key` (mode 600, scratch-only,
deleted with the scratch dir); below they appear redacted as recorded live.
Runner: `/tmp/s3-rotation-run.sh` (scratch-only, never committed). Dummy
seat `blue-probe@test-rig` / rig `test-rig` throughout.

```
S3: OPENRIG_HOME=/tmp/09-rotate-scratch/home (scratch-only; live ~/.openrig untouched)
== step 0: start scratch daemon ==
Daemon started on port 18439 (pid 3305852)
rc=0
== step 1: identify (hashes only, tokens never listed) ==
{
  "configured": false,
  "file": "/tmp/09-rotate-scratch/home/mcp-http-tokens.json",
  "grants": []
}
rc=0
== step 2: mint binding ==
Token for blue-probe@test-rig/send-identity, shown once (only its hash is kept in /tmp/09-rotate-scratch/home/mcp-http-tokens.json):
or...-w (len=47, redacted)
The client sends it as: Authorization: Bearer <token>. Revoke it with: rig mcp token revoke blue-probe@test-rig/send-identity
stored binding-1.key mode: 0o600
== step 3: list shows seat+rig scope ==
[{'name': 'blue-probe@test-rig/send-identity', 'seat': 'blue-probe@test-rig', 'rigs': ['test-rig'], 'roots': [], 'workspace': False, 'owner': False, 'createdAt': '2026-10-28T12:48:17.565Z'}]
== step 4: attestation round-trip under key 1 ==
v1.blue-probe@test-rig.test-rig.rotationproofnonce01.12...45 (len=64, redacted)
verify: attested blue-probe@test-rig
== step 5: revoke the binding ==
Revoked blue-probe@test-rig/send-identity: its next request is refused. Its rows and records stay.
rc=0
grants now: []
== step 6: re-add replacement (same name, same seat+rig scope) ==
Token for blue-probe@test-rig/send-identity, shown once (only its hash is kept in /tmp/09-rotate-scratch/home/mcp-http-tokens.json):
or...BY (len=47, redacted)
The client sends it as: Authorization: Bearer <token>. Revoke it with: rig mcp token revoke blue-probe@test-rig/send-identity
stored binding-2.key mode: 0o600
== step 7: re-key proof (old attestation fails under key 2, new verifies) ==
send-identity: unverified (bad attestation mac)
old attestation under key 2: unverified None
new attestation under key 2: attested blue-probe@test-rig
== step 8: stop scratch daemon ==
Daemon stopped
rc=0
ROTATE-OK: sender binding revoked + re-issued with --seat AND --rig; re-key proven
```

Verdict lines (verbatim): `old attestation under key 2: unverified None`
(rotation effective — key-1 material is dead) and
`new attestation under key 2: attested blue-probe@test-rig` (replacement works).
