# Verification: wave-f-path-arg-grants (issue #91, stage path-arg-grants-91, T3 drift-guard)

Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/path-arg-grants-91`
Branch: `feat/path-arg-grants-91` @ `5f4a530` (T1 commits + T2 evidence). Unity binding: N/A.
Spec read from disk: `openspec/changes/path-arg-grants-91/{proposal.md,design.md,tasks.md,specs/scoped-args/spec.md}` + `AGENTS.md`.
Evidence read from disk: `docs/evidence/wave-f-path-arg-grants-m0.md`, `docs/evidence/wave-f-path-arg-grants.md`,
`docs/reports/path-arg-grants-91-implementation.md`. Diff base: `git diff main...HEAD`.

## Re-run by auditor (all witnessed, exit codes real)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed, 0 failed`, exit 0 (V20 `#91` block green).
- `python3 -m pytest tests/test_command_effects.py -q` → `37 passed, 121 subtests passed`, exit 0.
- `bash tests/command-effects-redproof.sh` → `redproof: 0 failures`, exit 0
  (incl. `deny gcc ['-c', '../../evil.c']`, `deny gcc ['-c', 'src/foo.c', '-o', '/tmp/evil.o']`,
  `deny gcc ['-c', 'evil']` (the `sh -c` slot-outside deny), `deny gcc ['-c']`).
- `bash scripts/gate-role.sh vector-rag-spec` → exit 0 (all ok, zero FAIL).
- `git status --short` before report write: clean (0 lines).

## Spec-clause audit (REQ-A0/A1/A2/A3/A4/G1 + posture)

- REQ-A0 (live-proof-first): PASS. M0 file records NATIVE MAP wins (list form unparsed-and-poisonous,
  variant table with verbatim `permission_request.blocked` records). Implementation matches: renderer emits
  native-map `commandEffects` in `config.json` + descriptor sidecar; T2 independently re-probed map-ALLOW vs
  stripped-DENY; S3 sabotage (`build_command_effects_map` → `{}`) turns verify RED (9 V20 map-parity FAILs),
  proving the map carries enforcement (S3-style removal kills relief).
- REQ-A1 (scoped argv effects): PASS. `classify_go_package_arg` (`...` package-pattern branch with `..`/absolute/
  token deny-first), `pair_cmake_flag_values` (`-S`/`-B` pairing via `classify_scoped_path_value` +
  realpath-containment), `classify_gcc_command` (`-c` + source pairing, `-o` withdrawal), shell-token rejection —
  all present in `scripts/render-seat.py:390-600` and covered both directions in redproof + unit corpus (re-ran green).
- REQ-A2 (slot exception, frozen deny): PASS. `TERMINAL_BASH_DENIES` length 42 on main AND head, tuple text
  byte-identical (auditor compared `main:scripts/render-seat.py` vs worktree via regex-extracted tuple:
  identical). Overlay `gcc *`/`g++ *` renders after terminal denies (`overlay: after-terminal-denies`,
  `compileSlotOnly`), deny still fires outside the slot (`sh -c evil` deny in gate + redproof, re-ran green).
  S4-corrected (committed-leaf reorder → verify RED on overlay-position) and S5 (`-c` removal → deny-presence +
  V13/V15/V19 cascade RED) are non-vacuous.
- REQ-A3 (two-role scope): PASS. `fleet/fleet.yaml` adds are exactly: catalog stanzas + `gcc *`/`g++ *` to
  `cpp-lowlevel-eng` and `engine-systems-eng` only, `cmake -S *` + `build/*` to `engine-systems-eng` only.
  No `pytest`/`go` verb adds, no other role gains build verbs.
- REQ-A4 (probes + corpus): PASS (code side). Charter-verbatim allow probes added alongside existing
  `gate-role.sh` expects (pytest/go/cmake/gcc + traversal, /tmp, `-o`, `-P`, `sh -c` denies); redproof id-list
  deliberately updated with exact-order assertion (`note/body/cmake/gcc/ctest` + comment `#91 deliberate id-list
  update`) and per-tool both-direction corpus.
- REQ-G1 (frozen tuple, no renumber, generator rule): PASS. Tuple byte-identical (above); SUMMARY stays 35,
  V19 frozen; hand-edited files are exactly 9 (`fleet/fleet.yaml`, 3× `scripts/`, 2× `tests/`, 3× docs) with
  338 generated-leaf files under `specs/`/`rigs/`/`rosters/`/`registry/` via generator — no hand-edits there.
- Refs posture: PASS. Commits use `Refs #91`, zero `Closes #91` in commits or tree (proposal's `Closes only
  after post-merge live proof` language is the correct conditional, not a premature close). Live proof stays
  UNVERIFIED here, as stated.
- Canary 12: PASS (out-of-scope confirmed). Zero diff overlap with `tests/test_build_canary.py`
  (`git diff --name-only main...HEAD | grep test_build_canary` → 0 lines); pre-existing 12 failures untouched.

## Findings (1)

1. `docs/evidence/wave-f-path-arg-grants.md:99` — T2 red-proof evidence committed TRUNCATED (spec clause violated:
   `tasks.md` T2 "evidence `docs/evidence/wave-f-path-arg-grants.md`" + proposal acceptance 2 red-proof coverage +
   audit rule that every critical assertion's RED be recorded with a non-vacuous signature). Evidence: file is
   5907 bytes; its tail bytes are ``- **S6** `-o` escape: `classify_gcc_command` skips `-o` values → \n...[truncated
   890 chars]`` (auditor read raw tail via `pathlib.read_bytes`, not a viewer artifact) committed in `5f4a530`.
   The S6 (`-o` write-escape) sabotage RED signature, revert confirmation, and any closing sections (clean-status
   statement) are missing, so the `-o`-escape sabotage RED is UNVERIFIED here. The underlying behavior itself
   passes (`deny gcc -o /tmp/evil.o` green in the re-run redproof + gate deny probes), so this is an evidence-completeness
   defect, not a code defect — but under the severity rule (missing deliverable) it fails closed. Fix (no code change):
   QA completes the S6 entry (inject → RED signature with exit/failure counts → `git checkout --` → clean status)
   plus closing status/Refs/canary notes, commits as evidence, and requests T3 re-audit.

Method note: S4's first attempt (renderer-loop-only sabotage staying green) is documented in-evidence as committed-leaf
vs fresh-render coverage with a corrected attempt that does turn RED — recorded observation, not a vacuous check. No action.

VERDICT: FAIL