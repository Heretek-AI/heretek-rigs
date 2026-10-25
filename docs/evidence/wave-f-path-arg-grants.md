# Evidence: path-arg-grants-91 T2 red-proofs (REQ-A0/A1/A2/A3/A4/G1)

Date: 2026-10-25. Worktree: `.lane/trees/path-arg-grants-91`, branch
`feat/path-arg-grants-91` @ `2441a93` (T1 final: sources `05324a8` +
leaves/provenance `703bb83` + report `2441a93`). QA: agency-qa (T2).
Enforcer for live probes: INSTALLED `@gotgenes/pi-permission-system@41.0.0`
through `scripts/gate-run.sh` mock-model runs (same harness as M0).

## 0. Provenance note (concurrent-T1 episode, stated plainly)

QA began @ `266c61e` while T1 was still working in the same worktree: at
~01:24–01:25 T1 added the `ctest_effect` stanza (fleet catalog +
`build_command_effects_map` + V15/V20 checks + corpus + gate probes) with
scratch file `scripts/__orig_render.py`, breaking `gate-role.sh` syntax
mid-edit (a cpp-gate run died `exit=2` on the half-written file — T1's own
race, repaired by T1). A QA `generate-rigs.py` run during that window was a
no-op (dirty-tree refuse; zero generated-leaf diffs — verified via
`git status`). At ~01:32 T1 committed (`05324a8`, `703bb83`, `2441a93`),
worktree clean. **Every result below was measured on the final state @
`2441a93` after quiescence (no T1 processes, no mtime changes); pre-commit
readings (pytest 36-pass, verify 35/3 V20 map-parity FAILs on the
pre-ctest leaves) are superseded and recorded only to explain the ctest
gap T1 closed.**

## 1. Baseline acceptance (final tree, witnessed by QA)

| check | command | result |
|---|---|---|
| verify gate | `./scripts/verify-rigs.sh --check-only` | exit 0 — `SUMMARY: 35 checks passed, 0 failed` (V20 block prints its green line) |
| full verify | `make verify` | exit 0 (`verify-rigs.sh` + `live-health.py`; live-health advisory skips, no daemon — expected) |
| unit corpus | `python3 -m pytest tests/test_command_effects.py -q` | exit 0 — **37 passed, 121 subtests passed** |
| effect corpus | `bash tests/command-effects-redproof.sh` | exit 0 — `redproof: 0 failures` |
| role gate vector-rag-spec | `bash scripts/gate-role.sh vector-rag-spec` | exit 0 — 50 ok, 0 FAIL |
| role gate go-backend-eng | `bash scripts/gate-role.sh go-backend-eng` | exit 0 — 51 ok, 0 FAIL |
| role gate engine-systems-eng | `bash scripts/gate-role.sh engine-systems-eng` | exit 0 — 57 ok, 0 FAIL |
| role gate cpp-lowlevel-eng | `bash scripts/gate-role.sh cpp-lowlevel-eng` | exit 0 — 53 ok, 0 FAIL |

## 2. M0 confirmation (REQ-A0) — independently re-probed by QA

M0 verdict (native map wins) re-confirmed with a minimal decisive probe,
not from memory: freshly rendered `vector-rag-spec` seat into `/tmp`
(mock provider), ran `pytest tests/rag` through `gate-run.sh` twice:

- WITH native map (`commandEffects: {"pytest": {"effects": "read"}}`):
  tool RAN — `tool_execution_end`, pytest session starts → **ALLOW**.
- WITHOUT map (same seat copy, `commandEffects` stripped to `{}`):
  `[pi-permission-system] Denied by policy: 'path' for tool 'bash' for
  path 'tests/rag' (rule '*')`, `isError:true` → **DENY**.

The map carries enforcement; the recorded M0 outcome
(`docs/evidence/wave-f-path-arg-grants-m0.md`: map enforces, list is
unparsed-and-poisonous) stands. No HALT condition. (`/tmp` scratch only —
zero worktree edits, nothing to revert.)

## 3. Per-form results (all witnessed in QA's own gate logs `/tmp/opencode/qa-*.log`)

Allow (four issue-verbatim commands on scoped roles):

- `pytest tests/rag` on vector-rag-spec → ok (charter-verbatim #91)
- `go build ./...` on go-backend-eng → ok (charter-verbatim #91)
- `cmake -S . -B build` on engine-systems-eng → ok (charter-verbatim #91)
- `gcc -c` (in-scope `src/foo.c`) on cpp-lowlevel-eng + engine-systems-eng → ok (charter-verbatim #91)
- bonus: `ctest --test-dir build --output-on-failure` exits 0 (#76 + #91, T1's ctest fix)

Deny (every form denies, zero FAILs):

- `pytest ../../etc/passwd`, `go build ../../etc/...`, `go build -o /tmp/evil ./...`,
  `cmake -S . -B /tmp/evil`, `cmake -P /tmp/evil.cmake`,
  `gcc -c ../../evil.c`, `gcc -c src/foo.c -o /tmp/evil.o` → all deny
- shell tokens (`;`, `$()`, `OPENRIG_*=` covered in unit corpus deny directions) → deny
- slot exception: `sh -c evil` denies on `* -c *` outside the gcc slot → deny
  (REQ-A2 red-proof; `TERMINAL_BASH_DENIES` byte-identical, 42 entries)

## 4. Sabotage log (each: inject → check RED → `git checkout --` → `git status` clean)

- **S1** allow-direction: `classify_go_package_arg` final
  `allow-effect` → `deny` → `pytest tests/test_command_effects.py` exit **1**
  (4 failed). Reverted, status clean.
- **S2** deny-direction: `_scoped_value_has_shell_token` → `return False`
  → pytest exit **1** (10 failed, incl. `gcc -c src/foo.c;evil`). Reverted clean.
- **S3** M0-winner/acceptance: `build_command_effects_map` early `return {}`
  → `verify-rigs.sh --check-only` exit **1** (9 V20 map-parity FAILs across
  every map-carrying role). Reverted clean. (Removing native-map emission
  kills the relief at the acceptance gate too.)
- **S4** slot-exception position: FIRST attempt sabotaged the renderer loop
  only — verify stayed **green (35/0)**, because V20's bash-map assertions
  read the committed leaves, not the fresh render. Observation recorded
  (not a vacuous check — see corrected attempt); renderer-side bash
  regressions surface post-regen, covered by regen determinism/idempotence
  gates. CORRECTED attempt (reordered committed
  `engine-systems-eng/.../pi-permission-config.json` bash map, `gcc *` to
  front) → verify exit **1** (`overlay 'gcc *' must sit after all terminal
  denies`). Reverted clean.
- **S5** `-c` deny load-bearing: dropped `"* -c *",` from
  `TERMINAL_BASH_DENIES` → verify exit **1** (deny-presence check +
  `test_render_seat` + V13 mirror + V15 frozen-tuple + V19 count cascade).
  Reverted clean.
- **S6** `-o` escape: `classify_gcc_command` skips `-o` values → 
...[truncated 890 chars]