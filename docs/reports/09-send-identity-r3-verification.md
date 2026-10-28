# 09-send-identity-r3 — independent adversarial verification (drift-guard, rework cycle 3)

Wave: `09-send-identity-r3` (branch `fix/09-send-identity-r3`, tip `aafd51f` at audit start; cycle base `8ac5ca6`).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/09-send-identity-r3`.
Auditor: independent (no production code changed; no commits; no pushes; this report is the only file written).
Files read from disk (nothing trusted summarized): `AGENTS.md`,
`openspec/specs/send-identity/spec.md` (REQ-S1…S4 normative),
`docs/reports/09-send-identity-rework-3.md`, `docs/reports/09-send-identity-r3-qa.md`,
`docs/reports/09-send-identity-r2-verification.md` (prior PASS — revalidated, not inherited),
`docs/evidence/09-send-identity/red-proofs.log` (full, 465 lines),
`scripts/send_identity.py` (full, 384 lines), `scripts/seed-rig.py` (gate regions),
`scripts/render-seat.py` (`secret_ok` 780–816, `_bound09` 995–1060),
`docs/evidence/09-send-identity-rotation.md:60–95`,
cycle diff `git diff 8ac5ca6..HEAD` (name-only/stat/full for scripts+tests+evidence),
`git log 8ac5ca6..HEAD`, `git reflog`.

## 1. Cycle-diff analysis

- Commits in scope (both `Refs #9`, zero `Closes`/`Fixes`/`Resolves` in bodies):
  `849f197` (fix G1/G2/G3/G5), `aafd51f` (red-proofs + QA records). Linear local
  history; reflog shows only worktree-setup `reset: moving to HEAD` at base plus the
  two cycle commits — no `--force`. No push performed. PASS.
- `--name-only` (8 files): `docs/evidence/09-send-identity-rotation.md`,
  `docs/evidence/09-send-identity/red-proofs.log`, `docs/reports/09-send-identity-r3-qa.md`,
  `docs/reports/09-send-identity-rework-3.md`, `scripts/seed-rig.py`,
  `scripts/send_identity.py`, `tests/test_identity_m1.py`, `tests/test_send_identity.py`.
  Zero files under `openspec/` (empty diff confirmed), zero under `specs/`, `rigs/`,
  `rosters/`, `fleet/`, zero daemon/upstream/fleet-host paths, zero `registry/` files
  (registry diff empty this cycle — no regen needed, consistent with the
  no-catalog/generator-change claim). PASS.
- Functional changes confined exactly as claimed (auditor read the full diff):
  - `scripts/send_identity.py` (+17): reuse branch `elif binding_path.is_file()` gains
    `os.lstat` + `S_ISREG` + exact `0o600` guard, `_fail` closed, grant left intact
    (no revoke on this path). Nothing else in the file touched.
  - `scripts/seed-rig.py` (+48/-): new `seat_needs_sender_binding` helper
    (`:186–198` = `seat_needs_grant(..., opt_in=False)`) + gated `issue_sender_binding`
    call (`:566–588`, skip prints ok-line). Nothing else touched.
  - `tests/test_send_identity.py` (+24/-): new `test_reuse_of_non_0600_binding_file_refuses`
    (0400) + fixture mask `0o640`→`0o400` in `test_existing_non_0600_store_refuses_pre_mint`.
  - `tests/test_identity_m1.py` (+25): new `SeatNeedsSenderBindingTests` (3 tests).
  - `docs/evidence/09-send-identity-rotation.md`: G1 missing-vs-unreadable rewrite only.
  - `docs/evidence/09-send-identity/red-proofs.log` (+59 RP-R3-G2/G3/G5) + 2 reports.
  PASS.
- `scripts/verify-rigs.sh`: zero diff in cycle (`git diff -- scripts/verify-rigs.sh` empty) —
  V28 text untouched, V1–V27 untouched. PASS.
- Rework-3 report §Commits lists only the fix commit; the later record commit (`aafd51f`,
  log+QA records, `Refs #9`) postdates it — docs/evidence-only, report-accuracy nit, not a finding.

## 2. Spec-conformance verdict (the critical question: do the tightened guards break REQ-S1?)

(a) **G2 reuse refusal — no over-refusal (REQ-S1 holds for all VALID states).**
The guard narrows exactly one path: grant-exists + path-is-a-file + file is NOT a
0600 regular file → `_fail`. Every VALID state is untouched: 0600-regular reuse still
prints `ok … already issued (reuse …)` and returns 0 (`send_identity.py:184–187`);
missing file → warn + revoke + re-issue (`:188–195`); symlink → unlink + re-issue
(`:157–165`); scope mismatch → revoke + re-issue (`:152–156`); fresh mint → pre-mint
guard (`:200–206`) + token-add path unchanged. Proven live: auditor re-ran the full
corpus on the clean tree → `Ran 28 tests … OK`, including
`test_issue_reuses_matching_grant_and_file` (valid reuse) and both refusal tests.
The QA-R4a blast-radius note (full corpus under guard-removed sabotage fails ONLY the
new refusal test; valid reuse still passes) confirms the guard narrows only the unsafe
path. REQ-S1 "attested send accepted" (valid binding reusable) and "unattested held
UNVERIFIED" (no availability change — attestation/verify paths untouched) both hold. PASS.

(b) **G3 narrowed seed gate — no under-issuance (seat-set comparison, explicit).**
Render gate (`scripts/render-seat.py:1010–1015`): `_bound09 = [b for b in
role.get("mcp",[]) or [] if isinstance(b,dict) and mcp_catalog.get(b.get("server"),{}).get("seat_grant")]`;
configures `send-identity.json` iff `_bound09` non-empty, i.e. iff the role binds a
catalog server carrying `seat_grant: true`. No opt-in anywhere on the render side.
Seed gate (`scripts/seed-rig.py:186–198`): `seat_needs_sender_binding(role, catalog) =
seat_needs_grant(role, catalog, opt_in=False)`, and `seat_needs_grant` returns True iff
a dict binding hits `mcp_catalog[server].get("seat_grant")` (else `bool(opt_in)` = False).
Predicate-identical to `_bound09` (same catalog flag, same dict-guard, same
`(role or {}).get("mcp",[]) or []` shape). Seat-set comparison:
  - bound role (with or without `HERETEK_SEAT_GRANT_OPT_IN=1`): seed True, render entry —
    MATCH (issues exactly as before; auditor confirms the call site is additionally nested
    inside `_need_grant`, which is True for every bound role, and `_issue_grants` is False
    only in `dry_run`/`refresh_policy_only` where no issuance of any kind happens — pre-existing).
  - unbound role, no opt-in: seed False (skip ok-line), render no entry — MATCH.
  - unbound role WITH opt-in: seat grant still issues via `_need_grant` (opt-in honored
    there), sender binding skipped via the new gate, renderer emits no entry — MATCH
    (this was the pre-fix divergence: unusable bindings the renderer could never reference).
No seat the renderer configures is now SKIPPED at seed; REQ-S1 issuance intact, and
unattested seats stay UNVERIFIED per spec exactly as today. `SeatNeedsSenderBindingTests`
(3/3, encoding bound/unbound/opted-in-unbound) green. PASS.

(c) **G4-skip upheld: `expected_sender` + denial + callers + cross-seat test present and untouched.**
`expected_sender` required kwarg (`send_identity.py:311`), sender-mismatch denial
(`:359–363`, `unverified`, redacted), cross-seat test
`test_cross_seat_secret_cannot_authenticate_other_sender` (`tests/test_send_identity.py:347–364`)
present; all 10 in-repo `verify_attestation` call sites are in the test corpus and pass
`expected_sender=` (auditor counted 10/10); zero production callers outside tests/verify-gate
(relay is future work — matches the QA report). Cycle diff touches only the
`issue_sender_binding` reuse branch; `verify_attestation` byte-untouched. The thread
predates the rework-1 landing, as claimed. PASS.

## 3. Fail-closed assessment (G2 leaves the grant intact)

Refusal path returns `_fail(...)` with NO revoke: the live grant is preserved. The failure
is loud in both modes: strict prints `error: <session>: sender binding issuance failed:
existing <file> is not a 0600 regular file; remove it and re-seed` to stderr, rc 2 (seed
exits); degraded prints `warn: … sender binding not issued (…), continuing degraded` (rc 0,
the sanctioned degraded discipline). Recovery is documented in the message itself
("remove it and re-seed") and asserted by the new test (`0600` in err, body untouched,
single `token add` in the fake log — no re-mint, no overwrite): an operator who
`chmod 600`s the file gets reuse (rc 0) on the next seed; one who removes it gets the
grant-exists-but-missing → revoke + re-issue path. A forged/planted non-0600 file therefore
fails closed and visibly — it cannot silently or permanently strand the seat (no silent
deny, no grant destruction, no content mutation). The new `except OSError: _reuse_st = None`
is not a swallow: `None` flows straight into the refusal predicate. PASS (no finding;
residual note: degraded-mode rc 0 continues without a binding by design, surfacing later as
render-die/disabled-entry — loud, pre-existing discipline).

## 4. Anti-stub + secrets

- Stub scan over the cycle `scripts/`+`tests/` diff (`TODO|FIXME|XXX|NotImplemented|pass #|
  || true|skipTest|@unittest.skip|assert True`): zero matches. `except` audit: new guard's
  `OSError→None` fails closed (above); `FileNotFoundError→None` flows to mint;
  `(OSError, TimeoutExpired)→_fail`; tmp-cleanup bare `pass` precedes `raise`; no swallowed
  errors, no dummy passes. PASS.
- Secrets grep re-run by auditor over both evidence files:
  `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md
  docs/evidence/09-send-identity-rotation.md` → no output, exit 1. PASS.
- `git diff 8ac5ca6..HEAD -- scripts/ tests/` 40+-char matches are only long test identifiers
  (`def test_unbound_role_needs_no_sender_binding`, `def test_opted_in_unbound_…`,
  `def test_reuse_of_non_0600_binding_file_refuses`, etc.) — snake_case names, not bearer
  material; no token-shaped runs added. PASS.

## 5. QA spot-check (auditor sabotage, reverted, tree clean)

- SPOT-R3 (G3 live): replaced `seat_needs_sender_binding` body with unconditional
  `return True` (backup to `/tmp/opencode/`, scratch removed after). RED:
  `AssertionError: True is not false`, `Ran 3 tests … FAILED (failures=2)`
  (`test_unbound_role_needs_no_sender_binding`,
  `test_opted_in_unbound_role_gets_grant_but_no_sender_binding`) — the gate, not the
  caller, is what stops unusable bindings; matches RP-R3-G3 / QA-R4b verbatim.
  Restored from backup → `Ran 3 tests … OK`. `git status --short` clean and
  `git diff --stat -- scripts/seed-rig.py` empty after restore. PASS.
- Baseline re-run on the clean tree: `python3 -m unittest tests.test_send_identity` →
  `Ran 28 tests … OK`. Full `make test` (536) and `verify-rigs.sh` (36/0) were green per the
  QA report at `849f197`; tip `aafd51f` adds only log/report records (no code change), and the
  auditor's 28-test corpus re-run confirms no regression. `red-proofs.log` RP-R3-G2/G3/G5 +
  QA-R4a/b/c entries match the rework-3 and QA reports' verbatim claims and the auditor's
  independent SPOT-R3 reproduction. Failure signatures non-vacuous in both directions. PASS.

## 6. Scope

- Zero daemon/upstream/fleet-host changes (name-only list §1). Both cycle commits `Refs #9`;
  no `Closes`/`Fixes`/`Resolves` in `8ac5ca6..HEAD` bodies. Linear local history, no `--force`
  in reflog. No push performed (auditor wrote only this report). PASS.

## 7. Prior-PASS revalidation (r2, not inherited)

- R2's redaction choke point (`_session_log`/`_binding_log` via `seed_mod._redact_for_log`,
  9 session sites) intact — the G2 hunk reuses the same `_binding_log`/`_session_log` in its
  new message. R1's F5 fix (`sender != expected_sender → unverified`, `:359–363`) still present
  and before MAC computation. V28 gate, REQ-S1/S2 corpus, rotation evidence untouched by this
  cycle. No regression. PASS.

## Findings

None. F1…: none raised.

VERDICT: PASS
