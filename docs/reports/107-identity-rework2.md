# 107-identity rework cycle 2 report (CodeQL py/clear-text-logging-sensitive-data 85–90)

Stage/wave: 107-identity rework cycle 2 (prior VERDICT: PASS — bounded rework, cycle 2 of 3).
Worktree: `.lane/trees/107-identity` (branch `feat/107-identity`). No commit;
worktree left dirty for coordinator commit.

## Rule compliance

Alert text treated as UNTRUSTED throughout: every flagged-class expression
was verified against current `scripts/seed-rig.py` before any change.
Established facts from code reading (not from the alert text):

- The bearer itself (`token = parse_issued_token(...)`, seed-rig.py:371) is
  never printed: its only sink is the 0600 token file (lines 388–391). No
  `print` in the file interpolates the `token` variable.
- `token_path.name` interpolations expose only the key filename
  (`mcp-http-<session>.key`); session names expose only pod/member/rig ids.
- `detail` (line 367: `proc.stderr.strip() or proc.stdout.strip()`) IS raw
  rig-subprocess output and reaches the log — the one genuinely tainted flow.
- Rig-subprocess exception strings (`OSError`/`TimeoutExpired`, line 364)
  are CodeQL-tainted as secret-bearing regardless of content.

## Per-alert verdicts (grant-path log expressions, file:line post-fix)

VALID (carried tainted external output or exception strings → fixed):

- seed-rig.py:292–295 (`_fail` degraded warn) and :297 (`_fail` strict
  error) — VALID as a class: `msg` concentrates every tainted flow below.
  Fixed once at the `_fail` choke point (line 290: `msg =
  _redact_for_log(msg)`), covering all six call sites; no per-site edits.
- seed-rig.py:370 (`_fail(f"token add failed: {detail}")`) — VALID. RED
  proof: fake rig emitting a 47-char bearer-shaped run in failure stderr
  produced it verbatim in captured stderr pre-fix
  (`... internal error bearer QQQ…Q (47)`). Fixed via the choke point.
- seed-rig.py:365 (`_fail(f"token add failed: {e}")`) — VALID-class:
  rig-subprocess `OSError`/`TimeoutExpired` string, scanner-tainted. Fixed
  via the choke point.
- seed-rig.py:319 (`_fail(f"cannot remove symlinked …: {e}")`) —
  VALID-class (exception string; local `unlink` error, low risk, redacted
  uniformly rather than renaming variables to silence the scanner). Fixed
  via the choke point.
- seed-rig.py:400–403 (store-path `OSError` print) — VALID-class
  (exception string in a direct print outside `_fail`). Fixed directly:
  `{_redact_for_log(e)}`. The bearer-shaped-run risk here is nil (local
  file error), but the redaction is semantic and uniform.
- seed-rig.py:303 (`cannot list grants via {rig_bin}`), :335
  (`cannot revoke stale grant {session}`), :349–352 (refusing-to-store),
  :407 (did-not-converge) — benign content (paths/names/static text) but
  routed through the same `_fail` choke point at zero cost.

BENIGN, unchanged (pure name/session/filename/static interpolations, no
external-output content — recorded with reason, not renamed):

- seed-rig.py:309–312 metadata-mismatch warn — `{session}` + static text
  only; the listed-grant metadata dict itself is never interpolated.
- seed-rig.py:320–323 symlink-removed warn — `{session}` +
  `{token_path.name}` only.
- seed-rig.py:325–327 reuse-ok line — `{session}` + `{token_path.name}` only.
- seed-rig.py:330–333 grant-exists-file-missing warn — same two names only.
- seed-rig.py:374–377 unparseable-output error — `{session}` + static text;
  note the unparseable stdout is deliberately NOT logged (fail-closed
  design already avoids that leak — the scanner flag here, if any, is a
  taint-through-`proc` false positive).
- seed-rig.py:405 issued-ok line — `{session}` + `{token_path.name}` only.
- `die()` (:47) and `main()` progress prints — outside the grant path;
  untouched. Stage-time gate warn (:482, yaml-load exception) is outside
  the flagged grant path (~200–390); untouched per minimal scope.

## Fix (semantic, minimal)

- Added `_redact_for_log()` (seed-rig.py:255–274): replaces every
  `[A-Za-z0-9_-]{40,}` run with `…redacted…` and truncates to ~200 chars.
  The 40-char floor matches the task spec and stays clear of session names
  (segments split on `@`/`.` are all short — verified: no existing test
  output changed shape).
- Routed ALL grant-path external-output logging through it: centrally in
  `_fail` (covers `detail`, both exception strings, all msg call sites)
  plus the one direct store-error print. No variable renames; the fix is
  semantic redaction, not scanner appeasement.

## Tests (red-first)

- RED: extended the fake rig with `FAKE_RIG_LEAK_ADD=1` (failure stderr
  carries a 47-char `Q…Q` bearer-shaped run) plus two tests asserting the
  captured log contains the failure reason but no `[A-Za-z0-9_-]{40,}`
  run. Pre-fix: 25 ran, 2 failures showing the verbatim bearer in stderr
  (both strict and degraded paths leaked).
- GREEN post-fix: `python3 -m unittest tests/test_identity_m1.py` →
  `Ran 25 tests ... OK`. New tests:
  `test_add_failure_output_bearer_is_redacted_in_log` (strict, rc≠0, reason
  kept, bearer gone, no file stored) and
  `test_add_failure_output_bearer_redacted_when_degraded` (allow-missing,
  rc=0, warn kept, bearer gone, no grant minted).
- Regression: `tests/test_render_seat.py tests/test_seed_rig.py` →
  `Ran 27 tests ... OK`. All 23 prior tests green unmodified.

## Files changed

- `scripts/seed-rig.py` (+22/−1): `_redact_for_log` helper +
  `_BEARER_RUN_RE`, one-line choke point in `_fail`, one direct
  redaction in the store-error print.
- `tests/test_identity_m1.py` (23 → 25 tests): `FAKE_RIG_LEAK_ADD` mode +
  2 redaction tests.
- This report (new file).

Untouched per standing rules: `specs/`, `rigs/`, `rosters/`, `registry/`
(no regen — no generator inputs changed: no `.key`/role/binding/catalog
edits); SUMMARY frozen at 35; V23 block unrenumbered and floor untouched
(`>= 15` still holds at 25 — checked the block, no update required);
`yaml.safe_load` only; dummy tokens in `/tmp` 0600 scratch only.

## Exact commands + exit codes

| Command | Result |
|---|---|
| `python3 -m unittest tests/test_identity_m1.py` (RED, pre-fix) | 25 ran, 2 failures (verbatim 47-Q bearer in stderr, strict + degraded) |
| `python3 -m unittest tests/test_identity_m1.py` (GREEN) | `Ran 25 tests ... OK` (exit 0) |
| `python3 -m unittest tests/test_render_seat.py tests/test_seed_rig.py` | `Ran 27 tests ... OK` (exit 0) |
| `make verify` | exit 0 — `SUMMARY: 35 checks passed, 0 failed`; `V23/107-identity M1 green ... 25 corpus tests pass (FAIL-ONLY, SUMMARY frozen)`; live-health `[SKIP]`s are the normal no-daemon data-source skips |
| Stub scan (`TODO`/`NotImplementedError`/`test.skip`/`\|\| true`/`set +e`) over both touched files | clean (grep exit 1, no hits) |

## Self-audit notes (stated plainly)

- All six flagged-class expressions were verified VALID in the taint-flow
  sense (or VALID-class for exception strings) — none dismissed as
  scanner noise without evidence; the RED test proves the `detail` flow
  really reached the log pre-fix.
- Benign lines were deliberately NOT touched: renaming variables to
  silence the scanner without changing content would be appeasement, per
  the stage rule; each carries a recorded reason above.
- Truncation (~200 chars) could clip very long failure details; the
  failure reason (`token add failed: …`) is front-loaded so it survives —
  asserted by the `assertIn("token add failed", err)` in both new tests.
- Not done (out of scope): binding any fleet role to `rig-mcp-http`,
  upstream queue filing, T2 sabotage, any regen.
