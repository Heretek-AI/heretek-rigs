# 107-identity rework cycle 1 — drift-guard re-audit (binding)

Stage/wave: 107-identity rework cycle 1 re-audit (prior `VERDICT: PASS` at
`80b88f8`; rework `82aa808` + evidence `9301af2` since).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/107-identity`
(branch `feat/107-identity`). `git status --short` at audit time: clean
(empty output). No code fixed, nothing committed by this audit.

## 1. Spec & architecture alignment (read from disk)

- `AGENTS.md` (operator + generator rules), `openspec/changes/107-identity/`
  (`proposal.md`, `design.md`, `tasks.md`, `specs/identity/spec.md`),
  `docs/reports/107-identity-implementation.md`,
  `docs/reports/107-identity-rework1.md`, `docs/evidence/107-identity-m0.md`,
  `docs/evidence/107-identity-rotation.md` (F1 step 5),
  `docs/evidence/107-identity-queue.md`, `docs/evidence/107-identity/red-proofs.log`,
  `docs/evidence/107-identity/qa-run.log`,
  `docs/evidence/107-identity/rework1-red-proofs.log` — all read.
- REQ-I0/I1/I2/I3/G1 deliverables all present: M0 log (Bearer 200 / bad 401 /
  revoked 401 / whoami + queue probe), M1 seed issuance + V23 gate, M2 runbook +
  live rotation, M3 queue upstream-blocked note, T2 + rework-1 red-proofs.

## 2. F1–F5 fixes hold and match the rework report

- F1 (runbook step 5): `docs/evidence/107-identity-rotation.md:35-45` now
  prohibits the bearer in curl arguments literally and through shell expansion
  (`$(cat file)`, `$TOK`), prescribes mode-600 header file + `curl -H
  @/path/to/auth.header` / `-H @-`. Matches rework report §F1 verbatim.
  Seat-config `!echo Bearer $(cat ...)` convention untouched, as claimed.
- F2 (grant gating): `scripts/seed-rig.py:167,170-183` (`GRANT_OPT_IN_ENV`,
  `seat_needs_grant` generic over the `seat_grant` flag) + `main()` gate at
  lines 488-511 (issues only when bound or `HERETEK_SEAT_GRANT_OPT_IN=1`,
  else `ok <session>: no seat-grant binding, ordinary seed path`;
  unknown role never mints). Matches §F2.
- F3 (metadata match): `_list_grants` (186-210, name→metadata dict) replaces
  `_list_grant_names` (zero stale refs repo-wide); `_grant_scope_matches`
  (213-232) checks seat equal, rigs == `[rig]`/`[]`, roots empty,
  workspace/owner falsy, fail-closed on non-dict. Call site 283-315
  revokes + re-issues on mismatch. Matches §F3.
- F4 (safe store): `os.lstat` pre-check before `token add` (321-331, rejects
  symlink/non-regular/non-0600 with rc=2, loud-degrade under opt-out) +
  `tempfile.mkstemp` + `os.fchmod(0600)` + `os.replace` atomic store
  (363-370) with temp unlink on failure and revoke-on-store-failure.
  `import stat` (line 35) + `import tempfile` (line 37) present. Matches §F4.
- F5 (rig scope): `issue_seat_grant(..., rig=None)` appends `--rig <rig>`
  (333-335); `main()` passes `rig=s["rig"]` (508). Live proof in
  `rework1-red-proofs.log` §F5 (scratch `:18453`/`:18457`, `--rig testrig`
  → list shows `rigs: ["testrig"]`, `-H @auth.header` → 200, bad-token 401,
  scratch cleanup + real `daemon.json` byte-identical). Matches §F5.

## 3. Scope discipline — no creep beyond the five findings

- Rework diff `80b88f8..HEAD --stat`: exactly 7 files —
  `docs/evidence/107-identity-rotation.md`, `docs/evidence/107-identity/`
  `rework1-red-proofs.log`, `docs/reports/107-identity-rework1.md`,
  `fleet/mcp-servers.yaml` (1 line), `specs/identity/spec.md` (1 line),
  `scripts/seed-rig.py`, `tests/test_identity_m1.py`.
- `scripts/render-seat.py`, `scripts/verify-rigs.sh`, `fleet/fleet.yaml`
  untouched in rework (empty diff). `openspec/` rework diff is the single
  REQ-I1 parenthetical line; `proposal.md`/`design.md`/`tasks.md` unchanged.
- Full-branch diff `51d7df1..HEAD --name-only -- specs/ rigs/ rosters/`:
  EMPTY. `registry/` delta is provenance re-stamps only (`resolvedCommit`
  `892e1a7→47e71aa` + matching `canonicalUrl`, 8 entries + 8 views) — zero
  content drift, zero `DIRTY-`.

## 4. Gates frozen, not renumbered

- `scripts/verify-rigs.sh` V headers V1,V2&V3,V4&V5,V6–V23 all present in
  order (V23 at line 2757, FAIL-ONLY, floor `>= 15` still holds at 23).
  No V1–V22 reword/renumber in the rework diff. SUMMARY frozen at 35.

## 5. Stubs / vacuous checks / secrets

- Anti-stub grep over rework diff (`TODO|FIXME|XXX|HACK||| true|SkipTest|skip`)
  in added lines: zero hits in code (single prose mention inside the rework
  report's own scan-result sentence, not a stub). `tests/test_identity_m1.py`:
  no skips, no `assert True`, no bare `pass`. No `_list_grant_names` stale refs.
- Secret scan: no bearer-shaped material committed. Evidence uses redacted
  `or...XX` + `tokenSha256` hashes + dummy probe values only (sole
  `Bearer ...` hit is the deliberately-invalid `BAD-TOKEN-VALUE-12345` in M0
  §4). No `ghp_`/`sk-`/47-char live tokens in tracked files.

## 6. Red-proof evidence audit (rework1-red-proofs.log)

- Baseline GREEN recorded (23 tests OK, verify 35/0, self-test PASSED,
  status clean). F1 gate GREEN + F5 live 200 corroborate the doc fixes.
- S1–S6 sabotage proofs each turned RED non-vacuously (F2 gate 2 failures;
  F3 metadata 2 failures; F4 inverted-check 1 failure; F5 dropped `--rig`
  1 failure; F1 runbook gate RED exit 1; V23 `seat_grant:false` → 35+2
  failed) and returned GREEN after `git checkout --` restore with
  byte-identical diffs and clean `git status --short`. No vacuous checks.

## 7. Re-run output (this audit, unmodified tree)

- `python3 -m pytest tests/test_identity_m1.py -q` → `23 passed in 1.69s`.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`
  (fleet/mcp-servers found, verify-rigs static/schema/digest/security pass,
  20 adversarial vectors pass).
- `./scripts/verify-rigs.sh --check-only` → `V23/107-identity M1 green:
  seat-grant catalog shape + filename helper + 23 corpus tests pass
  (FAIL-ONLY, SUMMARY frozen)` + `SUMMARY: 35 checks passed, 0 failed.`

Findings: none. All five rework fixes hold as reported, scope is bounded to
the five findings plus their evidence, and every gate re-runs green.

VERDICT: PASS
