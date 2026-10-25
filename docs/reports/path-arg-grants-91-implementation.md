# T1 Implementation Report: path-arg-grants-91 (Wave F, issue #91)

Stage: `path-arg-grants-91` — T1 implement only (QA + drift-guard follow).
Branch: `feat/path-arg-grants-91` (worktree `.lane/trees/path-arg-grants-91`).
Date: 2026-10-25.

## M0 live probe (REQ-A0) — ran FIRST, gated everything

Through INSTALLED pps 41.0.0, gate-role.sh-style mock runs on
`pytest tests/rag` (vector-rag-spec): **NATIVE MAP wins**.
List form is unparsed AND poisonous (whole permission layer fails closed to
ask — even explicit `git status --short` degrades). Full data:
`docs/evidence/wave-f-path-arg-grants-m0.md`. No HALT (a shape enforces).
Extended probes validated go (`*/...` path_read exception + `-o`
withdrawal), cmake (`cmake -S *` + read decl), gcc (post-deny overlay +
read/`-o` decl) — all allow/deny directions per the evidence file.

## Deliverables (REQ-A1/A2/A3/A4)

- `fleet/fleet.yaml`: `command_effects` catalog += pytest/go/cmake/gcc
  stanzas (text-surgical, no yaml.safe_dump); engine-systems-eng
  `bash_allow` += `cmake -S *`, `gcc *`, `g++ *`; `path_write` +=
  `build/*` (greenfield configure writes there — sandbox makes cwd-root
  read-only); cpp-lowlevel-eng `bash_allow` += `gcc *`, `g++ *`.
- `scripts/render-seat.py`: `build_command_effects(path_write,
  role_verbs=None)` (descriptors; verb-conditional; `([])` still
  note+body for V15); `build_command_effects_map()` (native map —
  M0 winner, incl. ctest read decl with `-S` script-mode guard);
  classifiers `classify_scoped_path_value`,
  `classify_go_package_arg` (`...` branch), `pair_cmake_flag_values`,
  `classify_gcc_command`; config.json `commandEffects` = map; new
  sidecar `command-effects.descriptors.json`; gcc overlay patterns render
  AFTER the 42 terminal denies (`*` stays first — pi drops bash otherwise,
  probed); explicit `path_read {"*/...":"allow"}` for go-verb roles only.
  `TERMINAL_BASH_DENIES` byte-identical (42).
- `scripts/gate-role.sh`: `expect_run` policy-level allow helper (tool
  RAN ⟺ policy allowed; exit codes not asserted — sandbox FS limits
  GOCACHE/build/ creation); conditional fixtures + charter-verbatim
  allow probes (pytest/go/cmake/gcc) + deny probes (traversal, /tmp,
  `-o`, `-P`, `sh -c`).
- `scripts/verify-rigs.sh`: V1 carve-out (catalog overlay patterns only
  may follow denies); V15 deliberate migration (committed leaves assert
  native map; note/body values pinned via renderer); V20 `#91` FAIL-ONLY
  block (no ok() — V19 freezes SUMMARY at 35): catalog, map parity vs
  fresh renderer (51 roles), overlay position/two-role scope, go
  exception scoping, engine `build/*`.
- `tests/test_command_effects.py`: 6 new corpus classes (TDD red→green);
  2 shape-pinning tests deliberately migrated; 3 new rendered-shape tests.
- `tests/command-effects-redproof.sh`: id-list assertion deliberately
  updated (appsec 2 ids; engine note/body/cmake/gcc); go/cmake/gcc
  corpus both directions. `redproof: 0 failures`.
- Full regen via generator (generator rule: only fleet/scripts edited
  by hand); 344 files changed, mostly permission-leaf map migration +
  integrity-digest churn.

## Verification (exact commands, exit codes)

- `python3 -m pytest tests/test_command_effects.py -q` → 36 passed,
  121 subtests passed, exit 0.
- `bash tests/command-effects-redproof.sh` → 0 failures, exit 0.
- `bash scripts/gate-role.sh vector-rag-spec` → exit 0, incl. 2× #91 probes.
- `bash scripts/gate-role.sh go-backend-eng` → exit 0, incl. 3× #91 probes.
- engine/cpp gates re-run pending (first engine run: all #91 probes green,
  pre-existing #76 ctest probe red → fixed in-wave via ctest read decl;
  first cpp run invalidated by a concurrent script edit, re-run).
- `python3 scripts/audit_loop.py --self-test` → PASS.
- `make verify` (WITH dev-regen DIRTY stamps): 32 passed / 35 failed —
  ALL 35 are DIRTY-provenance cascade (16 resolvedCommit + 16 V13 DIRTY +
  3 V19 count-cascade); V1/V15-ok/V20 all green inside the 32.
  Final clean-regen `make verify` pending commit (see below).

##Flow note (deviation risk, stated plainly)

`HERETEK_RIGS_ALLOW_DIRTY=1` regen stamps DIRTY provenance, so T1 closes
with: commit sources → clean regen (no flag) → `make verify` must read
`SUMMARY: 35 checks passed, 0 failed` → commit generated leaves.
Engine/cpp gates were still running at report time; results to be
appended by QA if they land after this commit.

## Self-audit (unfinished, stated plainly)

- `make verify` final green NOT yet observed (blocked on commit-then-clean-regen).
- engine-systems-eng + cpp-lowlevel-eng gate-role.sh runs pending at write time.
- Live post-merge proof (each charter command allows on its seat) is T3
  territory; close criterion stays Refs #91 until then.
- Known residuals (evidence file): in-tree GOCACHE prerequisite for `go
  build` exit 0 (operator env, out of scope); symlink-to-outside reads
  share the pre-existing pytest posture (not weakened by this wave).
- Zero stubs: no TODOs, no skipped tests, no pass-through mocks added.
