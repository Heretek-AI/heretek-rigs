# Verification report — overhaul-a rework cycle 1 re-audit (prior VERDICT: PASS at e68ae57; rework 0cf3c38 + evidence ff98d32)

Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/overhaul-a` (branch `feat/overhaul-a`, tree clean).
Base: `66ba80c`. Commits since prior PASS: `0cf3c38` (rework fix) + `ff98d32` (evidence).
Auditor role: independent re-audit; no code changed, no commit made.

Read from disk: `AGENTS.md`, `openspec/changes/overhaul-a/{proposal.md,design.md,tasks.md,specs/p0/spec.md}`, `docs/reports/overhaul-a-implementation.md`, `docs/reports/overhaul-a-rework1.md`, `docs/evidence/overhaul-a-m0.md`, `docs/evidence/overhaul-a/red-proofs.log`, `docs/evidence/overhaul-a/rework1-red-proofs.log`.

## 1. Spec & deliverable audit (REQ-A0–A3, REQ-G1)

- REQ-A0: `docs/evidence/overhaul-a-m0.md` exists with verbatim fake-rig exfiltration + forged-source + `filter=` capability probes on the unmodified tree; winner recorded. SATISFIED (unchanged from prior PASS).
- REQ-A1: relay in `scripts/seat-sandbox.sh:52-153` validates before exec (allowlist, `--source`/`-s` equality, `--note` pattern, `--body-file` containment); `TestRigRelayEnforcement` 7/7 green bwrap-independent. SATISFIED (M1–M3 report + this re-audit re-run).
- REQ-A2: `_tar_supports_filter` / `_safe_tar_extract` / charter fallback / snapshot-restore + hermetic `--check-idempotent` proof. SATISFIED (unchanged behavior; rework only narrows).
- REQ-A3: Dockerfile `bubblewrap` + `bwrap --version`, workflow UniqueKey single-`container:` + verify-fleet bubblewrap. SATISFIED, untouched by rework (`git diff e68ae57..HEAD` shows zero docker/workflow files).
- REQ-G1: new coverage appended only; V1–V24 unrenamed (headers at `scripts/verify-rigs.sh:209,687,910,1076,1386,1445,1478,1513,1581,1666,1767,1999,2039,2112,2293,2341,2489,2550,2641,2691,2780,2830` intact); `git diff 66ba80c -- scripts/verify-rigs.sh` shows `+129/-0` (purely additive). SATISFIED.

## 2. Finding-by-finding verification (code read, not report trust)

- **F1 — caller-side member-type gate, fail-closed, helper/docstring accurate: CONFIRMED.**
  - Gate lives caller-side in `vendor_skill_from_clone` (`scripts/generate-rigs.py:471-486`): `_no_filter = not _tar_supports_filter()` hoisted; existing name-validation loop extended with conditional `issym()/islnk()/isdev()/is_fifo()` → `die(2)` (`:480-486`).
  - Helper `_safe_tar_extract` (`:323-336`) untouched in logic (still `filter="data"` vs plain extract); only the docstring (`:323-331`) updated to state the no-filter path "restores only pre-validated regular files/dirs" — accurate given the new caller gate. Caller comment (`:487-494`) notes the rejection. No helper-behavior change.
  - Fail-closed: `die` exit 2, raised before any `_safe_tar_extract` call in the loop. New test `test_symlink_member_dies_on_no_filter_path` (`tests/test_generate_supplychain.py:133-158`) forces `_tar_supports_filter() == False` against a synthetic git repo with a symlink skill file; expects `SystemExit` code 2.
- **F2 — exclusion covers `/`, `/tmp`, `/var/tmp` resolved incl. symlinks, legit roots intact: CONFIRMED.**
  - Fix at `scripts/seat-sandbox.sh:112-118`: each of `TMPDIR`/`HERETEK_JAIL_SCRATCH` is `realpath`'d, then skipped if the resolved value is in `("/", "/tmp", "/var/tmp")` before appending to `scratch`. Symlink-to-`/tmp` resolves to `/tmp` → skipped. `..` escapes were already neutralized by `realpath`; the resolved value is now checked (the prior gap).
  - Fail-closed direction: narrower scope ⇒ more denials. Other resolved roots still appended (legit-root allow path preserved).
  - No other relay semantics changed in rework: `git diff e68ae57..HEAD -- scripts/seat-sandbox.sh` is exactly the 5-line exclusion hunk; allowlist, source/note/body rules, symlink/size/store/credential/protected checks, `os.execvp("rig", argv)` shape all byte-identical.
  - Test-only widening: broad-root cases folded as subTests into existing `test_deny_out_of_scope_body_file` (`tests/test_seat_sandbox.py:466-487`), asserting `outside scratch and seat workspace` for both `TMPDIR=/tmp` and `TMPDIR=<symlink-to-/tmp>`. Method count stays 7 (see §5).
- **N1 — notice-only: CONFIRMED.** `generate_all` (`scripts/generate-rigs.py:974-984`) adds a one-line stderr notice naming missing dir(s) (`crew_dir,vendor_dir` join) before the unchanged `_snapshot_for_hermetic(root)` call. No behavior change beyond the notice.
- **N2 — fixture change is test-only: CONFIRMED.** `tests/test_generate_supplychain.py:14` adds `import shutil`; setup (`:279-284`) switches shallow top-level copy to `shutil.copytree(live, good, symlinks=False)`. No production code touched by N2. Adversarial nested-file probe documented in red-proofs (shallow copy lossy vs copytree faithful; nested deletion caught by tree-hash `die(2)`).

## 3. Scope bounded to the four threads: CONFIRMED

- `git diff e68ae57..HEAD --stat`: 6 files — `scripts/generate-rigs.py` (+30/-10 region), `scripts/seat-sandbox.sh` (+5/-1), `tests/test_generate_supplychain.py`, `tests/test_seat_sandbox.py`, plus the two evidence/report files. Zero docker/workflow/Makefile/fleet/spec/rig/rosters/registry changes in rework.
- No relay/semantics changes beyond the F2 exclusion; no generator behavior changes beyond the F1 gate + N1 notice; helper logic, Dockerfile, workflow, V19, Makefile, canary all byte-identical to prior PASS.

## 4. Gates frozen (V1–V27, SUMMARY, V19): CONFIRMED

- V1–V27 headers each present exactly once; V25 exact-7 floor intact (`scripts/verify-rigs.sh:2898`: `need exactly 7`); V26 `>= 7` floor; V27 UniqueKey + single smoke `container:` + bubblewrap markers. `TestRigRelayEnforcement` method count = 7 (`SeatSandboxEscapes` 26, `TestRigRelayEnforcement` 7 via AST parse); F2 cases are subTests (do not change `Ran N tests`).
- SUMMARY frozen at 35; V25/V26/V27 FAIL-ONLY (no `ok()`, no renumber/reword). V19 `passes + 1` at `scripts/verify-rigs.sh:2502` intact.
- Generator rule: `git diff 66ba80c -- specs/ rigs/ rosters/ registry/ schemas/ fleet/` is empty (zero generated-leaf bytes; stronger than empty-or-provenance-only — nothing to restore). No `yaml.safe_dump` on `fleet/fleet.yaml` (file untouched).
- Makefile / V19 / canary untouched: `git diff 66ba80c --name-only -- Makefile tests/test_build_canary.py fleet/fleet.yaml` is empty.

## 5. Stubs / skips / secrets: CLEAN

- Stub scan over the four rework files: no `TODO`/`FIXME`/`XXX`, no empty `catch`, no new `skip`/`skipTest`, no vacuous `assert True`. Observed hits are pre-existing and out of scope (`jail_rm ... || true` cleanup lines, `@unittest.skipUnless(bwrap)` for jail tests, root-mode `skipTest`, verifier's own stub-regex constants).
- Secrets: no committed secrets. Scans hit only detector regexes (`scripts/audit_sessions.py`, `scripts/verify-rigs.sh` patterns) and `DUMMY-CANARY-NOT-A-SECRET-*` / `dummy-probe-content` strings in `/tmp` probes (removed after). Real key never read/printed/copied.

## 6. Re-runs (real output, this audit)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed, 0 failed`, rc=0 (V25/V26/V27 all print green).
- `python3 -m unittest tests.test_seat_sandbox tests.test_generate_supplychain` → `Ran 50 tests ... OK`, rc=0.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`, rc=0.
- Canary (ONLY the instructed single test, no fix): `python3 -m unittest tests.test_build_canary.CanaryCatalogPins.test_canary_scope_only` → `FAILED (failures=1)`, rc=1, identical pre-existing signature: line 181, `44 additional` live roles, first diff `a11y-specialist` vs `ai-red-teamer`, `bash_deny` triple drift. `fleet/fleet.yaml`, Makefile, canary, V19 untouched — out of scope per instructions.

## 7. Red-proof evidence audit (non-vacuous, restored, clean)

- `docs/evidence/overhaul-a/red-proofs.log` (M1–M3 cycle): baseline green, relay deny/allow re-probes, legacy chaining-test behavior-change proof, three sabotages each RED with named failure (`failures=4` forged-source, `{'filter': 'data'} != {}` guard, `duplicate key: container`) then `git checkout --` restore to clean. Vacuous-check verdict recorded.
- `docs/evidence/overhaul-a/rework1-red-proofs.log` (this cycle, base `0cf3c38`, dated): baseline green (verify/check-only/50 tests/self-test); F1 sabotage (`if _no_filter and (` → `if False and (`) RED `AssertionError: SystemExit not raised`, restore byte-identical, GREEN-again OK; F2 sabotage (exclusion → `pass`) RED manual ALLOW `FAKE-RIG-RAN` + unit `FAILED (failures=2)` subTests, restore byte-identical, 7/7 GREEN-again; N1 stderr-notice + idempotence byte-identical proof with leaves restored; N2 adversarial `/tmp` probe (shallow lossy vs copytree faithful, nested deletion `die(2)`); regression = pre-existing canary only; V25 exact-7 + SUMMARY-35 + `fleet/fleet.yaml` unmodified recorded; QA verdict PASS.
- Failure signatures are non-vacuous (each RED names the re-opened hole: extraction proceeds / `FAKE-RIG-RAN` laundering / filter/target mismatches). Restores claim byte-identical with per-file clean status; final `git status --short` verified clean by this auditor (empty output).

`git status --short`: clean (empty). No uncommitted scratch remains; the two evidence/report files from `ff98d32` are committed.

VERDICT: PASS
