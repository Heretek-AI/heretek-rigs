# 09-send-identity — implementation report (wave 9, Refs #9)

Stage: `2026-10-28-09-send-identity` (branch `feat/09-send-identity`, base
`main @ 4b453a2`). Repo-side only: per-seat sender attestation extending the
#121 bearer-grant model. No daemon edits, no upstream filing, no fleet-host
live proofs. Every commit and reference uses `Refs #9` (the issue stays open
until live proof).

## What changed per milestone

### S0 — isolated-scratch spoof proof (commit `51228f3`)
- Spike `/tmp/s0-spoof-proof.sh` (scratch-only, never committed): loopback
  daemon under `/tmp/s0-09-send-identity/home` (`OPENRIG_HOME` isolated;
  live `~/.openrig` untouched), repo bundle materialized read-only
  (`rig import --materialize-only`, no seat processes), dummy keys only.
- Proof (non-vacuous — real daemon receipts, not error echoes): forged peer
  `--source red-ai-red-teamer@defensive-sec-and-red-team` recorded verbatim
  as `"sourceSession"` with `"state":"pending"` on a row owned by
  `blue-appsec-engineer@defensive-sec-and-red-team`; fully alien
  `--source red-actor@other-rig` accepted the same way. `rig queue show
  --full --json` confirmed both rows. No attestation, grant, or seat process
  required.
- Evidence `docs/evidence/09-send-identity-spoof.md` (qitem hex tails +
  daemon host ids redacted; forged-sender lines verbatim).

### S1 — grant-bound attestation + relay verify (commits `9228e81`, `d391ca1`)
- NEW `scripts/send_identity.py`: `sender_binding_filename`
  (`send-id-<session>.key`, no-`..`-`/` rule + fail-closed `ValueError` on
  hostile sessions), `sender_binding_grant_name`
  (`<session>/send-identity` — `/` cannot collide with a session name),
  `issue_sender_binding` (full mirror of `issue_seat_grant`: `--seat` +
  `--rig` scope, scope-match reuse, pre-mint 0600 validation, fail-closed
  parse via reused `parse_issued_token`, revoke-on-fail, atomic 0600
  mkstemp+replace; reuses `_list_grants`/`_grant_scope_matches`/
  `_revoke_grant`/`_redact_for_log` by import — zero duplicated discipline),
  HMAC-SHA256 `mint_attestation`/`verify_attestation` returning
  `attested`/`unverified`/`rejected` (claims ignored, replay single-acceptance
  per caller-owned `seen` set, cross-rig scope fail, missing attestation
  holds UNVERIFIED, `seen=None` fails closed; every denial logs redacted).
- `scripts/seed-rig.py`: issues the sender binding under the existing
  `_need_grant` gate (dormant for unbound roles — no role binds a
  seat-grant server today — same `--dry-run`/`--refresh-policy-only` skips).
- `scripts/render-seat.py`: renders `send-identity.json`
  (`sender` + `scope.rig` + `!cat <secrets>/send-id-<session>.key` +
  `version`) for grant-bound roles only (lazy module load; strict dies on a
  missing binding, degraded renders `enabled:false`, unbound roles render
  nothing).
- NEW `tests/test_send_identity.py` (24 tests at S1, 25 after the S3
  filename-hostility guard; dummy keys, fake stateful `rig`): all four
  REQ-S2 classes + issuance discipline + render rules + filename guard.
- `tests/test_identity_m1.py`: fixture-only update (bound-role secrets dir
  now also carries a sender binding, mirroring seed behavior).
- Red-proofs `docs/evidence/09-send-identity/red-proofs.log` (S1a–S1d: each
  sabotage turned its test RED for the right reason, then reverted).
- Regen `d391ca1` is stamp-only (render change alters zero generated leaves;
  V22 intact in fleet + leaves).

### S2 — V28 gate + corpus promotion (commits `e538f8a`, `c3a9d40`)
- `scripts/verify-rigs.sh`: appended `== V28. Send-Identity Attestation
  (09-send-identity S1) ==` (new block only). V28 asserts filename/grant-name
  rules, issuance + verify markers, `!cat` render markers with zero
  bearer-shaped runs, corpus rc=0 with a ≥20 non-vacuous floor, S0 evidence
  present with verdict lines and zero bearer-shaped runs; bears `ok()`.
- Freeze bump (mandated by V19's own bump rule + tasks S2.1): `_v19_canonical`
  35→36, post-freeze-ok addend +1→+2 (V19's own ok + V28), and the three
  live-count docs (`AGENTS.md`, `README.md`, `docs/USER_GUIDE.md`) 35→36.
  No other V1–V27 line touched.
- FAIL-ONLY recorded in `red-proofs.log`: module removed → exit 1,
  `SUMMARY: 35 checks passed, 4 failed` (V28 load/source/corpus fails +
  S1-layering cascade in V23); base-commit static check (read-only
  `git show 4b453a2:`) confirms zero markers pre-fix. Restored byte-identical.
- Hardening found by the FAIL-ONLY run: fail-closed (not traceback) paths
  for a missing `send_identity.py` in both V28 and the render block, and a
  lazy render import (unbound roles never touch the module).

### S3 — rotation runbook, docs, closeout (this report + verification)
- `docs/evidence/09-send-identity-rotation.md`: revoke + mint-replacement
  runbook (every mint with `--seat` AND `--rig`, V24-style mandate) executed
  live in scratch (`/tmp/09-rotate-scratch`, port 18439, dummy seat):
  re-key proven both directions (key-1 attestation `unverified` under key 2,
  fresh key-2 attestation `attested`). Tokens redacted first/last-2 + length.
- S3.2: the AGENTS.md docs-map line for this change already exists
  (`AGENTS.md:73`, added by the spec package `4b453a2`) — docs-map-only rule
  honored, no-op recorded.
- `openspec/changes/2026-10-28-09-send-identity/` left unarchived for the
  coordinator triad.

## Files changed (wave total vs `4b453a2`)
- `scripts/send_identity.py` (new, 334 lines), `scripts/seed-rig.py` (+22),
  `scripts/render-seat.py` (+47), `scripts/verify-rigs.sh` (+116: V28 block,
  V19 bump + addend, guarded source read).
- `tests/test_send_identity.py` (new, 25 tests),
  `tests/test_identity_m1.py` (+16 fixture lines).
- `AGENTS.md`, `README.md`, `docs/USER_GUIDE.md` (live-count 35→36, 1 line each).
- `docs/evidence/09-send-identity-spoof.md` (new),
  `docs/evidence/09-send-identity/red-proofs.log` (new),
  `docs/evidence/09-send-identity-rotation.md` (new),
  `docs/reports/09-send-identity-implementation.md` (this file),
  `docs/reports/09-send-identity-verification.md` (drift-guard).
- `registry/` (16 files, provenance stamps only — generator output, never
  hand-edited). `fleet/`, `specs/`, `rigs/`, `rosters/` untouched.

## Exact commands run with exit codes
- `bash /tmp/s0-spoof-proof.sh` → 0 (`SPOOF-OK pre-fix`, accepted-forgery line).
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md` → 1 (no output).
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 36 checks passed, 0 failed`
  (S0/S1: 35/0; S2+: 36/0 with `[PASS] V28 send-identity attestation …`).
- `make test` → `Ran 530 tests … OK` (22 suites: 505 pre-existing + 25 wave
  corpus; per-module counts recorded in S2).
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`.
- `python3 scripts/generate-rigs.py --check-idempotent` → byte-identical PASS
  (after each milestone commit; regen commits `d391ca1`, `c3a9d40` stamp-only).
- `python3 -m unittest tests.test_send_identity -v` → 25/25 OK.
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md docs/evidence/09-send-identity-rotation.md` → 1 (no output).
- S3 rotation greps: `--seat` ×7, `--rig` ×8, rig-less mint lines 0.
- FAIL-ONLY: module removed → verify rc=1, `SUMMARY: 35 checks passed, 4 failed`.

## Self-audit notes (unfinished / deferred, stated plainly)
- Daemon-side attestation persistence (`seen`-set durability) is the #127
  upstream gap — explicitly out of scope (REQ-I3 disposition stands); the
  repo-side verifier owns its set and fails closed without one.
- No fleet-host live proofs in this wave (Priority 2, deferred per proposal);
  issue #9 stays open (`Refs`, never `Closes`).
- `HANDOFF.md` (35-count lines) and `docs/IMPLEMENTATION_PROMPT.md` (35-count
  + freeze-convention lines) still state the old live count — V19 does not
  scan them; left for the coordinator's session refresh (noted, not changed,
  to avoid churning coordinator-owned state).
- `make test` baseline: HANDOFF recorded 504/21 pre-wave; the tree now runs
  530/22 (505 others + 25 wave). The +1 pre-existing delta vs HANDOFF's 504
  predates this wave (no test methods added to other suites — `test_identity_m1`
  still runs 26).
- Grant-name charset: `/`-suffixed grant names proven live in scratch
  (`token add 'blue-probe@test-rig/send-identity'` rc=0, list/revoke verified);
  `--port`/`--host`/`--materialize-only` likewise used only after `--help`
  ground truth. No CLI flags invented.
- Real secrets never left `~/.config/heretek-rigs/secrets/` (untouched; no
  live daemon was running during scratch runs); all scratch/test keys dummy
  (`/tmp`, 0600); evidence carries redacted placeholders only.
