# Wave command-effects verification (issue #106, stage command-effects, T3 drift-guard)

Worktree: `.lane/trees/command-effects`, branch `feat/command-effects` @ `f16c745`
(T1 `724799c` + T2 evidence `f16c745`). Unity binding: N/A.
Spec read from disk: `openspec/changes/command-effects/{proposal.md,design.md,tasks.md,specs/command-effects/spec.md}`
plus `AGENTS.md` one-rule. Auditor changed no source; this report file only.

## 1. Spec & architecture audit

Required deliverables per spec/tasks:
- T0 spec gate: all four spec files present on disk — PASS (read directly).
- REQ-C1 note-effect: `scripts/render-seat.py` renders `note-effect` with
  pattern `^[A-Za-z0-9 _\-/.:|]+$`, `execModel argv-not-shell`, deny tokens
  `; $ ` `` ` `` `$( OPENRIG_SESSION_NAME= OPENRIG_URL=` + newline/CR — PASS.
  Pattern byte-matches spec regex; argv positions cover create/block/update-reopen
  plus both typed-block relays.
- REQ-C2 body-file-effect: `classify_body_file` + `check_body_file_path` enforce
  realpath-in-scope (cwd incl. `.lane/trees/<stage>` worktree when cwd is there,
  `path_write`-expanded roots, pid-namespaced `/var/tmp/seatjail.<pid>.*`),
  regular-file-only, ≤256KiB (262144), no symlink/`..` escape, no absolute
  `/tmp` — PASS. Scope expressed as runtime descriptors, no baked absolute host
  paths; V14 gate still green (153 leaves, no `/.lane/` or host paths).
- REQ-C3 deny directions: `prod.env` outside scope, `/etc/passwd`,
  `../../etc/passwd`, symlink escape, oversize, missing file, absolute `/tmp`,
  and all forbidden note tokens deny fail-closed — PASS (redproof + corpus).
- REQ-G1 denies frozen: `TERMINAL_BASH_DENIES` lines 81–127 md5-identical
  main vs HEAD (`dc030871…`); mirror `verify-rigs.sh:588` md5-identical
  (`a1351d6b…`); renderer count 38 — PASS. `tests/test_render_seat.py`
  untouched (absent from diff) — PASS.
- REQ-G2 no renumber: `verify-rigs.sh` diff is +50/−0 (one appended V15 block,
  exactly one new `ok()`); `ok(f"` count 11 → 12 — PASS.
- `grep -rn commandEffects scripts/ fleet/`: 9 hits (source, not pycache) — PASS.
- AGENTS.md one-rule: non-generated changed files are `Makefile`,
  `docs/evidence/…`, `fleet/fleet.yaml`, `scripts/{generate-rigs,render-seat,verify-rigs}*`,
  `tests/command-effects-redproof.sh`, `tests/test_command_effects.py`.
  All `specs/ rigs/ rosters/ registry/` leaves carry the overlay via regeneration:
  `python3 ./scripts/generate-rigs.py` exit 0 with zero working-tree dirt after run
  (idempotent; only pre-existing vendor-pinning advisory on stderr) — PASS,
  no hand-edits to generated leaves.
- `Makefile` test target gains `tests/test_command_effects.py` (new coverage
  alongside, permitted; REQ-G2 constrains only `verify-rigs.sh`) — PASS.

## 2. Stub hunt

- `grep TODO|FIXME|XXX|pass$|NotImplemented` over `scripts/render-seat.py` additions:
  zero matches — PASS.
- Sampled generated leaf `specs/agents/qa/api-contract-tester/runtime/pi-permission-config.json`
  carries `['note-effect', 'body-file-effect']`, `maxBytes 262144` — PASS.
- V15 gate asserts all 102 permission leaves (`runtime/pi-permission-config.json`
  + `runtime/policy-enforcement.json`) carry both effects with exact pattern,
  execModel, constraints, and no `'ask'` rule — green in `make verify`.

## 3. Re-run, do not trust (auditor-executed)

- `bash tests/command-effects-redproof.sh` → 18/18 PASS lines,
  `redproof: 0 failures`, exit 0 — PASS.
- `python3 -m pytest tests/test_command_effects.py -q` → 11 passed,
  80 subtests passed — PASS.
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 31 checks passed, 0 failed`,
  incl. `[PASS] Command effects (#106) green: 102 permission leaves … denies frozen` — PASS.
  (31 vs AGENTS.md's stale "26" = prior appended V-blocks + this V15; exactly +1
  `ok()` vs main's 11, no renumber.)
- `git status --short` (working tree) → clean — PASS.

## 4. Red-proof evidence audit

`docs/evidence/wave-command-effects-redproofs.md` (T2 commit `f16c745`) records:
baseline green (redproof 18/18, corpus 23 passed/209 subtests, full 82/212,
`make verify` 31/0) plus three sabotage cycles S1 (pipe removed → allow RED,
exit 1), S2 (in-scope forced deny → allow RED, exit 1), S3 (deny tail forced
allow → 4 deny-direction REDs, exit 1), each restored via
`git checkout -- scripts/render-seat.py` with clean status and re-green.
Failure signatures are non-vacuous (targeted single-line defects flipping the
exact acceptance direction). Tree state matches: `scripts/render-seat.py`
unmodified since `724799c`, working tree clean — PASS.

## 5. Findings

None. No stubs, no vacuous checks, no failing commands, no missing deliverables,
no hand-edited generated leaves, no deny/mirror drift, no renumber.

VERDICT: PASS
