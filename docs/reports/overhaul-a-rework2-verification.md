# Verification — overhaul-a rework cycle 2 re-audit (binding)

Stage: overhaul-a rework cycle 2 re-audit (prior VERDICT: PASS at 7a42a60;
rework 9ff290a + evidence 36f8461 since).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/overhaul-a`
(branch `feat/overhaul-a`, tree clean: `git status --short` empty at audit time).
Auditor: Independent Drift Guard (no code changes made, none committed).
Date (UTC): 2026-10-28.

Spec sources read from disk: `AGENTS.md`, `openspec/changes/overhaul-a/proposal.md`,
`openspec/changes/overhaul-a/design.md`,
`openspec/changes/overhaul-a/specs/p0/spec.md` (note: `openspec/changes/overhaul-a/tasks.md`
does not exist at that path; the task list lives at
`openspec/changes/overhaul-a/tasks.md` — read there),
`docs/reports/overhaul-a-implementation.md`, `docs/reports/overhaul-a-rework1.md`,
`docs/reports/overhaul-a-rework2.md`, `docs/evidence/overhaul-a-m0.md`,
`docs/evidence/overhaul-a/red-proofs.log`,
`docs/evidence/overhaul-a/rework1-red-proofs.log`,
`docs/evidence/overhaul-a/rework2-red-proofs.log`.

Scope of rework 2 under audit (`git diff 7a42a60..HEAD --name-only`): exactly 4 files —
`docs/evidence/overhaul-a/rework2-red-proofs.log`,
`docs/reports/overhaul-a-rework2.md`, `scripts/seat-sandbox.sh`,
`tests/test_seat_sandbox.py`. No other production, test, generator, workflow,
Makefile, or fleet file touched in this cycle.

## F1 — mkstemp probe fix: test-only, content/scope preserved — CONFIRMED

- Diff (`tests/test_seat_sandbox.py:475-480` post-fix): PID-predictable
  `Path("/tmp") / f"relay-scope-probe-{os.getpid()}.txt"` + `write_text` replaced by
  `tempfile.mkstemp(prefix="relay-scope-probe-", suffix=".txt", dir="/tmp")` with
  content written via the returned fd (`os.fdopen`), i.e. `O_CREAT|O_EXCL` exclusive
  creation that refuses a pre-placed symlink with `FileExistsError`.
- Test-only: no production file touched for F1; probe content
  (`dummy-probe-content\n`) and `/tmp` scope byte-identical; existing
  `addCleanup(...unlink...)` unchanged. `tempfile` was already imported — no new import.
- Red-proof in `rework2-red-proofs.log` (§F1) is non-vacuous: old pattern replicated in
  `/tmp` scratch clobbered a victim file through a pre-placed symlink (race won with
  probability 1); fixed pattern raises `FileExistsError`, victim intact. Scratch removed.

## F2 — fd-passing: fail-closed, existing checks preserved — CONFIRMED

- Fail-closed pins all present in `scripts/seat-sandbox.sh` post-fix: `O_NOFOLLOW` open
  (`os.open(v, os.O_RDONLY | os.O_NOFOLLOW)`, `:165`, ELOOP → deny
  `changed during validation (will not follow)`); identity re-check by `fstat`
  (`:168-169`: regular + same `(dev, ino)` + ≤ 256 KiB, else `os.close` + deny
  `changed during validation`); `os.set_inheritable(_fd, True)` (`:172`, required under
  PEP 446 for fd survival across `execvp`); argv rewrite to `/dev/fd/N` for both forms
  (`:173-177`, `--body-file P` via index, `--body-file=P` via prefix-preserving rewrite,
  locations recorded in new `body_locs` list `:67,80,91`).
- Existing validation checks preserved: symlink reject, single `os.stat` (folding the old
  `isfile`/`getsize` pair — same deny outcomes), size cap, secret-store containment,
  credential suffix/name, scratch/seat-workspace containment (incl. rework-1 `/`, `/tmp`,
  `/var/tmp` root exclusion), protected segments, `--source`/`-s`/`--note` parsing
  untouched. The retired "unreadable" deny string is referenced by no test
  (only unrelated suites use the word); the `OSError` path now denies as
  `not a regular file`, still fail-closed non-zero. No test in the repo asserts the old string.
- V25 markers intact: literal `os.execvp("rig", argv)` × 1 (`grep -c` = 1); all 13 relay
  deny messages present; `body_locs`/`stat` additions only.
- Enforcement class still exactly 7 methods (verified by loader introspection):
  `test_allow_valid_in_scope_matching_source_valid_note`,
  `test_deny_forged_source`, `test_deny_non_allowlisted_subcommand`,
  `test_deny_out_of_scope_body_file`, `test_deny_secret_store_body_file`,
  `test_deny_symlink_body_file`, `test_deny_unsafe_note` — 6 deny + 1 allow.
  The new TOCTOU test lives in its own class `TestRigRelayTOCTOU` (1 method), which the
  V25 gate does not count. V25 exact-7 gate still passes (`verify-rigs.sh:2898`,
  `need exactly 7`) — confirmed green in the re-run below. The report's claim that the
  class was "kept at exactly 7" is accurate, and the reason it passes is precisely the
  separate-class placement.
- Residual window honestly documented in-code and in the rework report: final
  validation-stat → `O_NOFOLLOW` open adjacency (microseconds, one synchronous block),
  down from the full validation → rig-exec span. `/dev/fd/N` feasibility against the real
  rig (`@openrig/cli` 0.7.4 `dist/commands/queue.js:540-592`, `existsSync` → `statSync` →
  `readFileSync`, no basename/shape validation, pre-daemon) proven daemon-free per the
  report; future rig shape-validation would fail loudly (non-zero), i.e. fail-closed.
- Red-proof non-vacuous (`rework2-red-proofs.log` §F2): sabotage restoring path-passing
  (5-line fd-pin block → `os.close`) makes `TestRigRelayTOCTOU` RED with
  `RIG-READ:dummy-secret-content` in both subTests (`FAILED (failures=2)`, rc=1);
  restore via `git checkout` byte-verified, GREEN (`RIG-READ:{"slice": 12}`, `/dev/fd/`
  in argv, no secret bytes). Auditor verified the TOCTOU test exists at
  `tests/test_seat_sandbox.py:549-646` and passes (see re-runs).

## F3 — shebang: test-only, PATH setup unchanged — CONFIRMED

- Diff: `tests/test_seat_sandbox.py:428` fake-rig header
  `#!/usr/bin/env python3` → `f"#!{sys.executable}\n"` + `import sys` (`:16`, the file
  lacked it). 59-byte shebang verified in report; other fake rig (escape corpus, `:358`)
  deliberately keeps `env python3` because it inherits the full runner PATH
  (`"PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}"`) — minimal scope, and the
  auditor confirms the enforcement-class env still uses
  `"PATH": f"{self.bin}:/usr/bin:/bin"` (restricted, unchanged). So the finding's
  PATH-controlled carve-out is exactly as described.
- No behavior change to production; proof is `PATH=/nonexistent` execution
  (abs-interpreter runs, env-shebang dies rc=127) in the log. Test-only.

## Scope bounded — CONFIRMED

- Rework-2 diff touches only the relay fd-pin block + two test-only threads + reports/
  evidence. No relay-semantics change beyond pinning (allowlist, source/note rules,
  containment roots identical); no generator change (`scripts/generate-rigs.py` zero diff
  since rework 1); no workflow/Dockerfile change (zero diff); no V1–V27 edits.
- `git diff 66ba80c..HEAD --name-only -- specs rigs rosters registry` is empty:
  generator rule holds (zero generated-leaf bytes changed, so no DIRTY/provenance issue
  arises in this cycle).

## V1–V27 unrenamed, SUMMARY frozen — CONFIRMED

- `grep -nE '== V[0-9]+' scripts/verify-rigs.sh` yields V1..V27 in order (27 blocks;
  V2&V3 and V4&V5 share headers as before). Zero diff to `scripts/verify-rigs.sh` since
  rework 1. V19 `passes + 1` self-inclusion block intact (`:2502` region verified).
  SUMMARY line format frozen; live `SUMMARY: 35 checks passed, 0 failed`.

## Makefile / V19 / canary untouched — CONFIRMED

- `git diff 7a42a60..HEAD --stat -- Makefile tests/test_build_canary.py fleet/fleet.yaml
  scripts/verify-rigs.sh scripts/generate-rigs.py docker/Dockerfile
  .github/workflows/docker-release.yml` is empty.

## No stubs / skips / committed secrets — CONFIRMED

- `|| true` hits in `seat-sandbox.sh` (`jail_rm`, EXIT-trap `kill`/`wait`) and
  `@unittest.skipUnless(_bwrap_works())` / root `skipTest` in `test_seat_sandbox.py`
  all pre-exist at base `66ba80c` (verified via `git show`); none introduced by rework 2.
  No `TODO`/`FIXME`/stub in the rework-2 diff.
- Secret scan of the rework-2 diff: no `ghp_`/`github_pat`/`AKIA`/private-key/Bearer
  patterns. Only dummy canary-shaped strings (`dummy-probe-content`,
  `dummy-secret-content`, `RIG-READ:...`) in test code and reports — dummy canaries only,
  consistent with the hard rules.

## Red-proof log audit — CONFIRMED non-vacuous

- `docs/evidence/overhaul-a/rework2-red-proofs.log`: baseline `make verify` 35/0 +
  check-only + `test_seat_sandbox` 34/34 + `audit_loop --self-test` PASSED recorded;
  F1 scratch RED→GREEN, F2 sabotage RED (`failures=2`, secret bytes in output) → restore
  byte-identical → GREEN, F3 direct RED counterpart (rc=127) vs GREEN. Restores via
  `git checkout` + `cmp`/byte-compare; scratch under `/tmp` removed. Failure signatures
  are output-content-based (secret bytes present/absent, victim bytes clobbered/intact),
  not exit-code-only. `git status --short` at audit time is clean (evidence file committed
  at 36f8461), matching the log's discipline.

## Re-runs (this audit, real output)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed, 0 failed`
  (V25/V26/V27 all print green). rc=0.
- `python3 -m unittest tests.test_seat_sandbox tests.test_generate_supplychain` →
  `Ran 51 tests … OK` (34 seat-sandbox incl. enforcement 7 + TOCTOU 1, plus 17
  generate-supplychain incl. rework-1 symlink test; rc=0).
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED` (rc=0).
- Canary single-test re-run ONLY (per instructions, not fixed):
  `python3 -m unittest tests.test_build_canary.CanaryCatalogPins.test_canary_scope_only` →
  `Ran 1 test … FAILED (failures=1)` — identical pre-existing signature: stale
  expected-role list, 44 additional live roles, first diff `'a11y-specialist'` vs
  `'ai-red-teamer'`. Out of scope; `fleet/fleet.yaml`, canary, Makefile untouched.

## Findings

None. All three rework threads verified minimal, fail-closed, test-pinned with
non-vacuous red proofs; gates frozen; scope bounded; tree clean.

VERDICT: PASS
