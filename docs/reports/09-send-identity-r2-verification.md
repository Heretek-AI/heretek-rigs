# 09-send-identity-r2 — independent adversarial verification (drift-guard, rework cycle 2)

Wave: `09-send-identity-r2` (branch `fix/09-send-identity-r2`, tip `ca3990b` at audit start; cycle base `5bbb846`).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/09-send-identity-r2`.
Auditor: independent (no production code changed; no commits; no pushes; this report is the only file written).
Files read from disk (nothing trusted summarized): `AGENTS.md`,
`openspec/specs/send-identity/spec.md` (REQ-S1…S4 normative),
`docs/reports/09-send-identity-rework-2.md`, `docs/reports/09-send-identity-r2-qa.md`,
`docs/reports/09-send-identity-r1-verification.md` (prior PASS — revalidated, not inherited),
`docs/evidence/09-send-identity/red-proofs.log`, `scripts/send_identity.py` (full read),
`scripts/seed-rig.py` (redaction choke point + `parse_issued_token`, read),
`tests/test_send_identity.py` (harness + cycle hunk, read),
cycle diff `git diff 5bbb846..HEAD`, `git log 5bbb846..HEAD`.

## 1. Cycle-diff analysis

- Commits in scope (all `Refs #9`, zero `Closes`/`Fixes`/`Resolves`): `7932e80` (fix),
  `cb3ba9a` (report), `8bbde89` (provenance regen), `a570bf1` + `ca3990b` (report/QA records). PASS.
- `--name-only` (21 files): `scripts/send_identity.py`, `tests/test_send_identity.py`,
  `docs/evidence/09-send-identity/red-proofs.log`, 2 reports, 16 `registry/` leaves.
  **Zero files under `openspec/`** (empty diff confirmed), zero under `specs/`, `rigs/`,
  `rosters/`, `fleet/`, zero daemon/upstream/fleet-host paths. PASS.
- Functional changes only in the two claimed files. `scripts/send_identity.py` hunk:
  `_session_log`/`_binding_log` precomputed via `_redact`, 7 log interpolations rerouted
  (mismatch warn, symlink warn, reuse ok, missing warn, unparseable error, store-OSError
  error, issued ok) plus the 2 pre-existing `_fail` call-site lines that already carried
  raw `{session}` (degraded-warn, fatal-error) — 9 session sites total, all redacted now.
  No logic touched (no branch, return-code, scope, or MAC change). `tests/` hunk: fixture
  `0o644` → `0o640` + one new test `test_reuse_path_emits_no_token_material`. PASS.
- `scripts/verify-rigs.sh`: **zero diff in cycle** — V28 text untouched, V1–V27 untouched. PASS.
- Registry diff: every changed line is a `resolvedCommit` re-bake (`2aff663…` → `cb3ba9a…`)
  plus `canonicalUrl` embeds in behaviour.json views; zero other diff lines (auditor read
  the full `git diff -- registry/` head and the stat: 16 files, 2/4 lines each).
  Provenance re-lag only, sanctioned per AGENTS.md. PASS.
- Rework-2 report §Commits omits the two later record commits (`a570bf1`, `ca3990b`) from
  its list but they are docs/evidence-only and `Refs #9`; report-accuracy nit, not a finding.

## 2. Leak-trace verdict (the core question)

(a) **Mint path traced end to end.** The issued token flows exactly
`proc.stdout → parse_issued_token → fh.write(token)` (`send_identity.py:207,222`).
`parse_issued_token` (`seed-rig.py:147-161`) returns `lines[1]` or `None`, prints nothing.
Grep confirms the `token` variable is never interpolated into any `print`/log line —
the only `print` mentioning "token" is the static-text unparseable-output error (L211,
no token bytes). The four flagged sinks (C2 mismatch warn L154, C3 symlink warn L163,
C4 missing warn L173, C5 issued-ok L237) interpolate only `session` /
`binding_path.name`. `binding_path.name` is session-derived (`send-id-<session>.key`,
`/`+`..` refused at the `sender_binding_filename` choke point, L74-76). Every
subprocess/exception detail (`cannot list grants`, `token add failed: {e}`/`{detail}`,
revoke/store errors) flows through the redacting `_fail`; every verify-side reason
flows through the redacting `_deny`. Residual raw interpolations audited individually:
L161 `{binding_path.name}: {e}` and L187 `refusing to store … {binding_path.name}` both
flow into `_fail` → redacted; L350 raw `{e}` (`mac computation failed`) flows into
`_deny` → redacted; L60/L76 are pure name constructors, not log sinks; L75/L262/L268
`ValueError`s carry identifiers/static text only. **No token/key bytes can reach any
of the four sinks — or any other print site.** PASS.

(b) **Redaction helper is the genuine choke point.** The fix calls
`seed_mod._redact_for_log` loaded from `scripts/seed-rig.py` — byte-identical definition
at cycle base (`git show 5bbb846:scripts/seed-rig.py`, L196-201) and HEAD: same regex
`[A-Za-z0-9_-]{40,}`, same `…redacted…` substitution, same 200-char truncation. Not a
lookalike, never duplicated. Byte-identical-output claim independently re-proven:
`_redact_for_log(x) == x` for `blue-x@rig-y`, `send-id-blue-x@rig-y.key`,
`blue-x@rig-y/send-identity` (auditor ran it, all identical). PASS.

(c) **0o640 fixture triggers refusal for the right reason and holds no secret.**
Fixture content is the literal `"dummy"` (5 chars; bearer regex needs 40+ — auditor
confirmed `None`). `0o640 != 0o600` so the pre-mint gate
(`stat.S_IMODE != 0o600 → _fail("…not a 0600 regular file…")`, L183-189) refuses —
same predicate as under `0o644`; mode check, not content. Others-bits are 0
(`0o640 & 0o007 == 0` vs `0o644 & 0o007 == 4`; auditor computed both). Targeted test
`test_existing_non_0600_store_refuses_pre_mint` green on HEAD. PASS.

## 3. Anti-stub + secrets

- Stub scan over the cycle diff (`TODO|FIXME|XXX|NotImplemented|pass #||| true|skipTest|
  @unittest.skip|assert True`): zero matches. `except` audit: `FileNotFoundError` sets
  a sentinel (not swallowed — `_st = None` flows to the mint path); `(OSError,
  TimeoutExpired)` → `_fail`; inner `OSError` bare-`pass` is tmp-cleanup only before
  `raise`; `Exception` → `_deny("unverified")`. No swallowed errors, no dummy passes. PASS.
- Secrets grep re-run by auditor over both evidence files:
  `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md
  docs/evidence/09-send-identity-rotation.md` → no output, exit 1. PASS.
- `git diff 5bbb846..HEAD -- scripts/` added lines contain zero 40+ token-shaped runs
  (grep-clean). Test constants (`fakesendidentitytoken%06d`-shaped fakes, `dummy…`
  `FOR-TEST-ONLY` secrets) are short/dummy-marked. PASS.

## 4. QA spot-check (auditor sabotage, reverted, tree clean)

- SPOT-R2 (H2 live): sabotaged reuse-ok line back to raw
  `f"ok {session}: … (reuse {binding_path.name})"`, drove issue→reuse with `"A"*45`
  session via the committed fake-rig harness → RED (`ok AAA…(45)…: sender binding
  already issued (reuse send-id-AAA….key)`, bearer regex HIT). Restored from backup →
  GREEN (`ok …redacted…: sender binding already issued (reuse …redacted….key)`, no
  40+ run on stdout/stderr). `git diff --stat` on both code/test paths empty after
  restore. The sink is live and the helper is what stops it — matches RP-R2-C2C5 /
  QA-R3b verbatim. PASS.
- Baseline re-runs on the clean tree: `python3 -m unittest tests.test_send_identity`
  → `Ran 27 tests … OK`; `python3 scripts/audit_loop.py --self-test` → `SELF-TEST
  PASSED`. Full `make test` (532) and `verify-rigs.sh` (36/0) were green per the QA
  report at `a570bf1`; tip `ca3990b` adds only log/report records, and the auditor's
  27-test corpus + self-test re-runs confirm no regression from the cycle diff (which
  touches no verify logic). `git status --short` clean apart from this report. PASS.
- `red-proofs.log` RP-R2-C1 / RP-R2-C2C5 / RP-R2-H3 + QA-R3a/b/c entries match the
  rework-2 and QA reports' verbatim claims and the auditor's independent SPOT-R2
  reproduction (same sabotage shape, same RED signature, same GREEN restore).
  Failure signatures non-vacuous in both directions. PASS.

## 5. Scope

- Zero daemon/upstream/fleet-host changes (name-only list §1). All 5 cycle commits
  `Refs #9`; no `Closes`/`Fixes`/`Resolves` anywhere in `5bbb846..HEAD` bodies. Linear
  local history, no `--force` in reflog (only worktree-setup `reset: moving to HEAD`
  at base). No push performed (auditor wrote only this report). PASS.

## 6. Prior-PASS revalidation (r1, not inherited)

- R1's F5 fix (`expected_sender` keyword-only + `sender != expected_sender` → `unverified`,
  `send_identity.py:342-346`) still present and reached before MAC computation. V28 gate,
  REQ-S1/S2 corpus, and rotation evidence untouched by this cycle. No regression. PASS.

## Findings

None. F1…: none raised.

VERDICT: PASS
