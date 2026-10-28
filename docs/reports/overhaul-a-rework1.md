# Rework report — overhaul-a cycle 1 (post-PASS review findings)

Stage: overhaul-a rework cycle 1 (cycle 1 of 3). No commit made; tree left
dirty for coordinator commit.
Worktree: `.lane/trees/overhaul-a` (branch `feat/overhaul-a`).
Rule compliance: findings verified against current code before any edit; no
V1–V27 renumber/reword, SUMMARY frozen, one-rule honored (no hand-edits to
`specs/`/`rigs/`/`rosters/`/`registry/` — regen leaves restored after the
hermetic proof runs), `yaml.safe_load` never used on `fleet/fleet.yaml`
(untouched), no secrets in commands/files/report (dummy probe content only,
`/tmp` probe files removed).

## Per-finding verdicts

- **F1 — VALID, fixed.** The no-filter fallback path let non-regular members
  through: `vendor_skill_from_clone` (`scripts/generate-rigs.py:471-476`
  pre-fix) validated only `..`/absolute names, and `_safe_tar_extract`
  (`:323-334`) took a plain `tf.extract(member, path=path)` when
  `_tar_supports_filter()` is false — a `git archive` symlink member (git
  preserves symlinks) would have been restored as a symlink. Fix (minimal,
  caller-side only, `_safe_tar_extract` untouched per the finding):
  hoisted `_no_filter = not _tar_supports_filter()` and added a conditional
  `issym()/islnk()/isdev()/isfifo()` die (exit 2) in the existing validation
  loop (`scripts/generate-rigs.py:471-486` post-fix); helper docstring
  (`:323-331`) now states the no-filter path restores only pre-validated
  regular files/dirs; caller comment (`:477-490`) notes the added
  non-regular rejection. File:line evidence: loop
  `scripts/generate-rigs.py:472-486`, docstring `:323-331`.
- **F2 — VALID, fixed.** The relay scratch-root loop
  (`scripts/seat-sandbox.sh:112-115` pre-fix) `realpath`'d `TMPDIR` /
  `HERETEK_JAIL_SCRATCH` but never excluded broad roots: with
  `TMPDIR=/tmp` (or a symlink thereto, or `/var/tmp`), any host file under
  that root entered `scratch` and passed the `--body-file` containment check
  — laundering bytes the seat could not read, since the jail masks host
  `/tmp` (`--tmpfs /tmp`, `:216`; in-jail `TMPDIR` is the per-run scratch,
  `:277`), contradicting the in-code scope note (`:46-51`). `..` escapes
  were already neutralized by `realpath`, but the resolved value was never
  checked. Fix (minimal): skip resolved `/`, `/tmp`, `/var/tmp` before
  appending (fail-closed: narrower scope ⇒ more denials; other resolved
  roots still available). File:line evidence:
  `scripts/seat-sandbox.sh:112-118` post-fix.
- **N1 — VALID, applied.** `generate_all` (`scripts/generate-rigs.py:963-964`
  pre-fix) entered hermetic mode silently. Added the one-line stderr notice
  naming the missing dir(s) (`scripts/generate-rigs.py:963-972` post-fix);
  `_snapshot_for_hermetic(root)` call unchanged. Live proof (stderr):
  `generate-rigs: crew_dir,vendor_dir missing; hermetic mode (snapshot
  restore, no live clones)`.
- **N2 — VALID, applied.** The restore test setup
  (`tests/test_generate_supplychain.py:282-284` pre-fix) copied only
  top-level files with no `shutil` import. Switched to
  `shutil.copytree(live, good, symlinks=False)` + `import shutil`
  (`tests/test_generate_supplychain.py:14`, `:279-284` post-fix).

## Red → Green evidence (behavior changes F1/F2; adversarial N2)

- F1: new `test_symlink_member_dies_on_no_filter_path`
  (`tests/test_generate_supplychain.py:133-158`) builds a synthetic git repo
  containing a symlink skill file and forces `_tar_supports_filter() ==
  False`. Pre-fix: `AssertionError: SystemExit not raised` (RED). Post-fix:
  `die(2) "refusing non-regular tar member on the no-filter fallback"` (GREEN).
- F2: new broad-root subTests folded into the existing
  `test_deny_out_of_scope_body_file` (`tests/test_seat_sandbox.py:466-487`;
  kept at 7 methods — see self-audit). Pre-fix (fix stashed):
  `AssertionError: 0 == 0 : FAKE-RIG-RAN ... /tmp/relay-scope-probe-*.txt`
  for both `TMPDIR=/tmp` and `TMPDIR=<symlink-to-/tmp>` (RED, 2 subTest
  failures). Post-fix: both deny with `outside scratch and seat workspace`,
  `TestRigRelayEnforcement` 7/7 OK (GREEN).
- N2 adversarial (`/tmp` scratch probe, removed after): synthetic skill tree
  with `nested/extra.md` — old shallow copy hash ≠ lock (lossy, proves the
  gap); `copytree` hash == lock (faithful); deleting the nested file from
  the snapshot makes `_restore_shared_skill` `die(2)` (nested deletion
  CAUGHT); re-copied snapshot restores with matching hash (GREEN).

## Acceptance

- `make verify` → rc=0: `SUMMARY: 35 checks passed, 0 failed`; V25 (7/7
  enforcement tests), V26, V27 all print green.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED` (rc=0).
- Touched suites: `tests.test_seat_sandbox + tests.test_generate_supplychain`
  → `Ran 50 tests … OK`.
- Hermetic regen proof: `HERETEK_RIGS_ALLOW_DIRTY=1 python3
  ./scripts/generate-rigs.py --check-idempotent --crew-source
  /nonexistent/crew --vendor-dir /nonexistent/vendor` → rc=0, byte-identical;
  leaves restored (`git checkout -- specs rigs registry rosters
  fleet/skills-lock.json schemas`).
- Full `make test` → `Ran 374 tests`, 1 failure:
  `test_build_canary.CanaryCatalogPins.test_canary_scope_only` — the single
  PRE-EXISTING canary failure (proven on base `07114e3` in the M1–M3 report),
  out of scope; canary, Makefile, and V19 untouched.
- `git status --porcelain` (dirty for coordinator commit):
  `M scripts/generate-rigs.py`, `M scripts/seat-sandbox.sh`,
  `M tests/test_generate_supplychain.py`, `M tests/test_seat_sandbox.py`.

## Self-audit

- No stubs/`TODO`/empty-`catch`/skipped tests; fail-closed throughout
  (relay denials, generator `die(2)`s preserved).
- V25 gate sensitivity: the first attempt added an 8th `TestRigRelayEnforcement`
  method and V25 failed loudly (`need exactly 7`) — fixed by folding the F2
  cases into the existing deny-out-of-scope method as subTests (which do not
  change the `Ran N tests` count) instead of touching the frozen gate.
- RED proofs above ran against the real wrapper/generator (fake `rig` on
  PATH, synthetic git repos in `/tmp`); no uncommitted scratch remains apart
  from the four intended file modifications.
- Unfinished / out of scope: none for this cycle — all four findings were
  valid and are addressed; the canary failure stays out of scope per
  instructions.
