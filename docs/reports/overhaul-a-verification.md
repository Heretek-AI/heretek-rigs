# Verification report — overhaul-a M0–M3 (drift-guard audit)

Stage: overhaul-a M0–M3. Worktree: `.lane/trees/overhaul-a`
(branch `feat/overhaul-a`, commits `07114e3` spec+M0, `5bbe7bd` feat,
`4dc7dfe` test evidence, tree clean).
Auditor: independent adversarial re-run from disk, 2026-10-27 UTC.
No code fixed, nothing committed.

## Spec coverage (openspec/changes/overhaul-a)

### REQ-A0 — M0 spike gates M1/M2: SATISFIED
- `docs/evidence/overhaul-a-m0.md` exists with verbatim exfiltration
  (fake-`rig` relay, rc=0 leak pre-fix, secret-store + forged-source probes)
  and `filter=` capability (`True` on Python 3.15.1) outputs on the
  unmodified tree (`66ba80c`, only untracked spec dir).
- Relay bounds recorded (`:38` if, `:47` os.execvp) match `design.md`;
  WINNER section cites the plan M1/M2 follow. M1 implementation report
  records the post-change line shift (`:52`/`:149`) explicitly — no
  unrecorded deviation.

### REQ-A1 — hardened rig relay: SATISFIED
- `scripts/seat-sandbox.sh`: relay enforces before exec — `argv[1]` in
  `{whoami, ps, queue, send, capture, transcript}`; `--source`/`-s` (space,
  `=`, attached `-sV`) equal to non-empty `$OPENRIG_SESSION_NAME`;
  `--note` (both forms) restrictive pattern + newline/CR reject;
  `--body-file` (both forms): non-symlink, regular file ≤ 256KiB, never
  inside `$HERETEK_SECRET_STORE`, credential suffix/name denials, inside
  seat workspace or scratch (`TMPDIR`/`HERETEK_JAIL_SCRATCH`), clear of
  protected segments (`.git`, `.pi`, `.agents`, `AGENTS.md`).
- 7-case corpus present (`TestRigRelayEnforcement`: 6 deny incl. symlink +
  1 allow; both `--source`/`-s` space and `=` forms exercised). Re-run:
  `Ran 49 tests ... OK` (33 seat_sandbox + 16 supplychain, combined run).
- Legacy chaining test change is correct-deny, not weakening: new
  expectation asserts rc!=0 + `subcommand not allowlisted` + marker absent;
  QA proved old code (`git show 66ba80c:...`) returns rc=0 against the fake
  rig and therefore FAILS the new assertions — behavior change is real.
- EXIT-trap intact: `trap ... EXIT` at `:168`, background-`bwrap` + `wait`
  shape unchanged (`:272`/`283`); relay still `exec`s python pre-scratch,
  never `exec bwrap`.

### REQ-A2 — hermetic regen: SATISFIED
- Filter guard real: `_tar_supports_filter()` feature-detect +
  `_safe_tar_extract` (def `:323`, call `:484`); both branches unit-proved
  (`test_guarded_branch_omits_filter_on_old_pythons` forced-negative with
  stub tf, `test_filter_branch_passes_data_filter` forced-positive,
  `test_live_interpreter_takes_filter_branch` on this host's Python 3.15.1).
- Hermetic fallback real: `build_charter` chain crew → `fleet/charters/`
  overlay → snapshot `guidance/role.md` byte-verbatim → `die()`;
  `_snapshot_for_hermetic` + `_restore_shared_skill` (tree_hash vs lock
  entry, entry reused verbatim) + `_restore_role_skill`; temp dirs
  atexit-cleaned even on `die()`.
- No regen required of the auditor, and none performed: leaves untouched
  proven — `git diff 66ba80c HEAD --stat -- specs rigs rosters registry`
  returns EMPTY; all M2 normal-path/hermetic byte-identity claims are
  backed by the implementation report + V26 gate (green in re-run), and the
  red-proofs.log sabotage/restore cycle left the tree clean.

### REQ-A3 — Docker pipeline: SATISFIED
- `docker/Dockerfile`: `bubblewrap` in slim apt list (`:94`), `bwrap
  --version` in verify step (builder `:24` deliberately untouched —
  compiler stage never runs the sandbox; documented).
- `.github/workflows/docker-release.yml`: duplicate `container:` block
  removed (exactly one remains), broken unclosed-`if` guard-profiles block
  removed in favor of the complete block, `bubblewrap` install +
  `bwrap --version` appended to verify-fleet.
- UniqueKey proof re-verified live via V27 gate (duplicate-key-rejecting
  YAML parse green; sabotage RED proven by QA).
- No full `docker build` — accepted with recorded reason (multi-arch push
  needs registry creds + network; static validation is the spec proof).

### REQ-G1 — append-only, generator rule: SATISFIED
- V25/V26/V27 appended FAIL-ONLY (no `ok()`, no renumber/reword); re-run
  prints `SUMMARY: 35 checks passed, 0 failed`.
- `git diff 66ba80c HEAD -- Makefile tests/test_build_canary.py
  scripts/verify-rigs.sh` shows ONLY the V25–27 append block in
  `verify-rigs.sh`; Makefile and `test_build_canary.py` have zero diff.
- V19 `passes + 1` at `scripts/verify-rigs.sh:2502` intact.
- `specs/` `rigs/` `rosters/` `registry/` diff vs `66ba80c` is EMPTY
  (provenance-only outcomes restored via checkout per report; no hand-edits
  — 14-file diff contains no generated leaves, only scripts/tests/docs/spec).
- No `yaml.safe_dump` on `fleet/fleet.yaml` (`fleet/` absent from diff).

## Stub / secret / vacuity scan
- No stubs: `TODO/FIXME` hits are only `verify-rigs.sh`'s own scanner
  regexes; no `NotImplementedError`, no bare `pass` in changed code.
- No swallowed errors: every new `except` path calls `die()` (fail-closed);
  pre-existing `skipUnless(bwrap)` / root `skipTest` are outside the new
  7-test relay corpus, which carries no bwrap gate.
- No secrets: only scanner regexes, the pre-existing `sk-live-123456`
  doc-vector in `verify-rigs.sh`, and `DUMMY-CANARY-NOT-A-SECRET-*` dummy
  strings in evidence/report files.
- No vacuous checks: every gate proved RED under minimal sabotage
  (M1 forged-source `failures=4`, filter else-branch `failures=1`,
  workflow dup-key UniqueKey `ValueError`, plus bonus V25/V27 live-verify
  failures during sabotage windows).

## QA non-blocking note — verdict: accepted comment drift, NOT a finding
- QA observed the relay denies with exit 1 (python `sys.exit(str)`) while
  the in-code comment at `seat-sandbox.sh:39` claims "exit 126".
  Confirmed live: denial paths use `sys.exit("seat-sandbox: ...")` → rc=1.
  Fail-closed holds (non-zero + reason on stderr), and REQ-A1's scenario
  requires only "exits non-zero naming the refusal" — the spec never pins
  126 for the relay (other wrapper paths legitimately use 126). The comment
  is aspirational drift, severity style-nit. No spec clause violated; left
  for the author to correct at their convenience.

## Re-run outputs (verbatim tails, this audit)
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed,
  0 failed` (V25/V26/V27 green, FAIL-ONLY, count frozen).
- `python3 -m unittest tests.test_seat_sandbox
  tests.test_generate_supplychain` → `Ran 49 tests ... OK`.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`.
- `python3 -m unittest
  tests.test_build_canary.CanaryCatalogPins.test_canary_scope_only` →
  `FAILED (failures=1)`, signature identical to the pre-existing failure:
  stale expected-role list, 44 additional live roles, first diff
  `a11y-specialist` vs `ai-red-teamer`. Stage touches neither `fleet/` nor
  `Makefile` nor `test_build_canary.py` (verified via stage diff
  `--name-only`), so the failure is independent of this stage. NOT fixed,
  per instructions.

## Findings
None. All required deliverables present, all gates green on re-run,
red-proofs non-vacuous, tree clean (`git status --short` empty).

VERDICT: PASS
