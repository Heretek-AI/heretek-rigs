# 107-identity rework cycle 2 — drift-guard re-audit (binding)

Stage/wave: 107-identity rework cycle 2 re-audit (prior VERDICT: PASS at aa72350;
rework 2b2fc12 + evidence f53e287 since).
Worktree: `.lane/trees/107-identity` (branch `feat/107-identity`). HEAD f53e287.
Tree state at audit: `git status --short` EMPTY (fully clean — rework-2 evidence committed).
Auditor changed no code and made no commits; this report is the only new file.
Read from disk: AGENTS.md, openspec/changes/107-identity/{proposal.md,specs/identity/spec.md,design.md,tasks.md},
docs/reports/107-identity-implementation.md, docs/reports/107-identity-rework1.md,
docs/reports/107-identity-rework2.md, docs/evidence/107-identity/{red-proofs.log,rework1-red-proofs.log,rework2-red-proofs.log,qa-run.log}.

## 1. Redaction fix bounded to rework-2 scope

`git diff aa72350..HEAD --stat` = 4 files, +224/−1:
`scripts/seed-rig.py` (+22/−1), `tests/test_identity_m1.py` (+20),
`docs/reports/107-identity-rework2.md` (new), `docs/evidence/107-identity/rework2-red-proofs.log` (new).
Full hunk review of the two code files (quoted in §6 of this report's working notes):

- `scripts/seed-rig.py`: adds `_BEARER_RUN_RE` + `_redact_for_log()` helper (40-char floor,
  `…redacted…` substitution, ~200-char truncation); one-line choke point `msg = _redact_for_log(msg)`
  at the top of the `_fail` closure inside `issue_seat_grant` (covers all six `_fail` call sites:
  list-fail, revoke-fail, symlink-remove fail, pre-store refusal, add-exception, add-detail,
  did-not-converge); one direct `{_redact_for_log(e)}` in the store-path `OSError` print.
  No function renamed (`_list_grants`, `_grant_scope_matches`, `_revoke_grant`, `issue_seat_grant`,
  `seat_needs_grant`, `parse_issued_token` all intact; `grep _list_grant_names` → no hits, rc=1).
  No branch/return-code change (`_fail` still returns 0 degraded / 2 strict; store-error path still
  revokes the minted grant and returns 2). No behavior change beyond redaction: the only
  observable delta is that bearer-shaped runs no longer reach stderr.
- `tests/test_identity_m1.py`: fake rig gains `FAKE_RIG_LEAK_ADD=1` mode (failure stderr carries a
  runtime-constructed `"Q" * 47` run — no literal bearer committed) + 2 redaction tests
  (strict fatal, degraded warn), both asserting `token add failed` is kept and no
  `[A-Za-z0-9_-]{40,}` run survives. All 23 prior tests unmodified.
- No scope creep vs the rework-2 intent: `git diff 2b2fc12..f53e287 --stat` = the evidence log only;
  `git diff aa72350..HEAD --stat -- specs/ rigs/ rosters/ registry/ fleet/` = EMPTY
  (no generator inputs, catalog, role, or binding touched).

## 2. V1–V23 unrenamed, SUMMARY frozen

- `scripts/verify-rigs.sh` untouched since aa72350 (absent from the diff). V23 block present at
  lines 2757–2806, FAIL-ONLY (no `ok()`), floor `need >= 15` unrenumbered (holds at 25),
  SUMMARY frozen at 35. Re-run output: `V23/107-identity M1 green: ... 25 corpus tests pass
  (FAIL-ONLY, SUMMARY frozen)` + `SUMMARY: 35 checks passed, 0 failed.`

## 3. Generator rule

- `git diff 51d7df1..HEAD --name-only -- specs/ rigs/ rosters/` → EMPTY (no hand-edits).
- `git diff 51d7df1..HEAD -- registry/` → 16 files, every +/- line a `resolvedCommit`
  `892e1a7…→47e71aa…` provenance stamp (+ matching `canonicalUrl` pins); `grep -c DIRTY` → 0.
  Provenance-only delta, zero DIRTY — compliant (accepted re-lag per AGENTS.md).

## 4. No stubs / skips

- `grep -rn 'TODO|FIXME|NotImplementedError|test\.skip|pytest\.skip|\|\| true|set +e'`
  over `scripts/seed-rig.py` + `tests/test_identity_m1.py` → no hits (rc=1).
- No `yaml.safe_dump` / bare `yaml.load(` in `scripts/seed-rig.py` (rc=1); `yaml.safe_load` only.

## 5. No committed secrets

- `grep -rnE '[A-Za-z0-9_-]{40,}'` over touched code + rework-2 report/evidence: hits are ONLY
  long snake_case test/report identifiers (underscores push them past 40 chars) — zero bearer-shaped
  literals. The single 47-char run in the repo is `"Q" * 47` constructed at test runtime.
- Token-shaped fixtures are labeled dummies only: `stalebearer FOR-TEST-ONLY-000*`,
  `attacker-planted FOR-TEST-ONLY-000*`, `dummybearer FOR-TEST-ONLY-0001`.
- Evidence logs carry redacted forms only (`or...3s`, `Q...Q (47)` descriptions, status codes +
  lengths); no `BAD-TOKEN` literal or bearer material in scripts/tests/evidence/fleet
  (`grep BAD-TOKEN` → no hits). M0/M2 live tokens lived in `/tmp` scratch only, per reports.

## 6. Six benign-with-reason lines — verified against `scripts/seed-rig.py` on disk

Each interpolates names/sessions/filenames/static text only; none touches rig-subprocess output:

- :309–312 metadata-mismatch warn — `{session}` + static text; the grant metadata dict is never interpolated. BENIGN confirmed.
- :320–323 symlink-removed warn — `{session}` + `{token_path.name}` only. BENIGN confirmed.
- :325–327 reuse-ok line — `{session}` + `{token_path.name}` only. BENIGN confirmed.
- :330–333 grant-exists-file-missing warn — same two names only. BENIGN confirmed.
- :374–377 unparseable-output error — `{session}` + static text; the unparseable stdout is deliberately NOT logged (fail-closed design). BENIGN confirmed.
- :405 issued-ok line — `{session}` + `{token_path.name}` only. BENIGN confirmed.
- `die()` (:46–48) and `main()` progress prints + stage-time gate warn (:482, outside the flagged
  grant path ~200–390): untouched, correctly out of scope. No appeasement renames anywhere.

## 7. Red-proof evidence audit (recorded by agency-qa, verified by auditor)

- `docs/evidence/107-identity/red-proofs.log` (T2, M1–M3): S1–S5 sabotage each turned its check RED
  (exit 1 with the exact failure signature) and GREEN after `git checkout --` restore; S6/S7 live
  scratch matrices (valid 200 vs tampered/missing/unknown/foreign 401; revoke → 401 → re-add → new
  200/old 401); S8 queue-detector empty-clean, trips on injection, restored. All NON-VACUOUS.
- `docs/evidence/107-identity/rework1-red-proofs.log`: baseline GREEN (23 tests OK, 35/0,
  SELF-TEST PASSED, status clean); S1–S6 sabotages each RED (exit 1) then GREEN on restore;
  regression all GREEN. No vacuous checks.
- `docs/evidence/107-identity/rework2-red-proofs.log` (this rework's proof): baseline GREEN
  (pytest 25 passed, `-k redact` 2 passed, audit self-test, verify 35/0, make verify 35/0);
  sabotage = single-line redaction bypass (`msg = _redact_for_log(msg)` → `msg = msg`) with
  `git diff --stat` proving exactly 1 insertion/1 deletion → `pytest -k redact` RED (exit 1,
  both tests fail, AssertionError shows the verbatim 47-Q run in stderr — the checks fail iff
  redaction is absent); `git checkout --` restore → clean status, 25 passed, 27 render/seed tests OK.
  Failure signatures non-vacuous. `git status --short` clean at audit time.

## 8. Re-run — real output (this audit, unmodified tree)

- `python3 -m pytest tests/test_identity_m1.py -q` → `25 passed in 1.87s` (expect 25: MET).
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED` (all `[PASS]` lines, incl.
  verify-rigs.sh static/schema/digest/security + 20-vector sentinel evaluator).
- `./scripts/verify-rigs.sh --check-only` → `V23/107-identity M1 green: ... 25 corpus tests pass
  (FAIL-ONLY, SUMMARY frozen)` + `SUMMARY: 35 checks passed, 0 failed.`

Findings: none. The rework-2 redaction fix is bounded (single helper + choke-point routing, no
renames, no behavior change beyond redaction), scope-clean, generator-compliant, stub-free,
secret-free, with non-vacuous red-proofs and all gates re-run green.

VERDICT: PASS
