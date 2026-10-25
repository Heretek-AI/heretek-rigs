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

- `python3 -m pytest tests/test_command_effects.py -q` → 37 passed,
  121 subtests passed, exit 0.
- `bash tests/command-effects-redproof.sh` → 0 failures, exit 0.
- `bash scripts/gate-role.sh vector-rag-spec` → exit 0, incl. 2× #91 probes.
- `bash scripts/gate-role.sh go-backend-eng` → exit 0, incl. 3× #91 probes.
- `bash scripts/gate-role.sh engine-systems-eng` → exit 0, incl. 8× #91
  probes + #76 ctest policy probe + #76 ctest exit-0 probe.
- `bash scripts/gate-role.sh cpp-lowlevel-eng` → exit 0, incl. 4× #91
  probes + #76 ctest policy probe.
- `python3 scripts/audit_loop.py --self-test` → PASS.
- `python3 scripts/audit_loop.py --self-test` → PASS.
- `make verify` (final, clean regen, real provenance): `SUMMARY: 35 checks
  passed, 0 failed`, exit 0 — acceptance GREEN (V1 carve-out, V15-ok and
  V20 green inside the 35; 42-tuple byte-identical).

## Close-out (final)

Commit → clean regen → verify-green flow completed: T1 sources
(`710b2ae`), ctest fix (`05324a8`), provenance refreshes. T1 stops here;
QA (T2) + drift-guard (T3) follow on this branch.

## Self-audit (unfinished, stated plainly)

- `make verify` final green NOT yet observed (blocked on commit-then-clean-regen).
- engine-systems-eng + cpp-lowlevel-eng gate-role.sh runs pending at write time.
- Live post-merge proof (each charter command allows on its seat) is T3
  territory; close criterion stays Refs #91 until then.
- Known residuals (evidence file): in-tree GOCACHE prerequisite for `go
  build` exit 0 (operator env, out of scope); symlink-to-outside reads
  share the pre-existing pytest posture (not weakened by this wave).
- Zero stubs: no TODOs, no skipped tests, no pass-through mocks added.
