# Rework report — overhaul-a cycle 2 (post-PASS review findings; cycle 2 of 3)

Stage: overhaul-a rework cycle 2. No commit made; tree left dirty for
coordinator commit.
Worktree: `.lane/trees/overhaul-a` (branch `feat/overhaul-a`, tree was clean
at start).
Rule compliance: each finding verified against current worktree code before
any edit; no V1–V27 renumber/reword, SUMMARY frozen, one-rule honored (no
hand-edits to `specs/`/`rigs/`/`rosters/`/`registry/` — untouched;
`yaml.safe_load` never used on `fleet/fleet.yaml` (untouched); no secrets in
commands/files/report (dummy probe/secret content only, all under test temp
dirs or `/tmp` scratch since removed).

## Per-finding verdicts

- **F1 — VALID, fixed.** `tests/test_seat_sandbox.py:475-476` (pre-fix)
  built the relay-scope probe as `Path("/tmp") /
  f"relay-scope-probe-{os.getpid()}.txt"` + `write_text` — PID-predictable,
  and a pre-placed symlink at that path IS followed (`open(..., "w")`
  follows symlinks). RED proof (`/tmp` scratch, since removed): replicated
  the two verbatim lines with a victim file + pre-placed symlink → victim
  overwritten with `dummy-probe-content` (race won with probability 1).
  Fix (minimal): `tempfile.mkstemp(prefix="relay-scope-probe-",
  suffix=".txt", dir="/tmp")` (`O_CREAT|O_EXCL`), content written via the
  returned fd — exclusive creation refuses a pre-placed symlink
  (`FileExistsError`), victim untouched (GREEN proof). Probe content and
  `/tmp` scope preserved; existing `addCleanup(...unlink...)` unchanged.
  File:line evidence: `tests/test_seat_sandbox.py:475-480` post-fix
  (`tempfile` was already imported).
- **F2 — VALID, fixed with full fd-passing (re-stat fallback not needed).**
  Verified the window is real: the relay validated `--body-file` by path
  (`islink` → `realpath` → `isfile`/`getsize` → store/credential/
  containment/protected checks, `scripts/seat-sandbox.sh:124-151` pre-fix)
  then `os.execvp("rig", argv)` (`:152`) with the ORIGINAL path argument.
  RED proof (new committed `TestRigRelayTOCTOU`, no bwrap gate): a swapping
  fake rig replaces the validated path with a symlink to a dummy secret
  AFTER the validation decision (race won with probability 1 — deterministic,
  not timing-dependent), then reads the granted argument exactly as rig
  would. Pre-fix output: `RIG-READ:dummy-secret-content` for both
  `--body-file P` and `--body-file=P` (leak; both subTests RED).
  Fix (minimal, relay shape kept): the parser records each body value's
  argv location (`body_locs`); validation now stats once (`os.stat(real)`,
  capturing dev/ino/size with `S_ISREG`); after all checks pass the file is
  opened `os.open(v, O_RDONLY | O_NOFOLLOW)` (ELOOP → deny), the open file
  is re-verified by `fstat` (regular + same dev/ino + ≤ 256 KiB, else deny),
  `os.set_inheritable(fd, True)` (PEP 446 fds are non-inheritable by
  default — required for survival across `execvp`), and the argv entry is
  rewritten to `/dev/fd/N` (both `--body-file P` and `--body-file=P`
  forms). All pre-existing deny messages and markers preserved; V25's
  literal `os.execvp("rig", argv)` untouched. GREEN: same swapping test now
  serves `RIG-READ:{"slice": 12}` with `/dev/fd/` in argv and no secret
  bytes, both forms. `/dev/fd/N` feasibility proven against the REAL rig
  (`@openrig/cli` 0.7.4, `dist/commands/queue.js:540-592`): body resolution
  is `existsSync` → `statSync().isFile()` → `readFileSync` with NO
  basename/extension/shape validation, shared by queue create/update/inbox/
  outbox, and runs BEFORE daemon contact — live daemon-free proof:
  `--body-file /dev/fd/3` (empty) → local "resolved to 0 bytes, daemon was
  not contacted" (proves open+read of the fd); non-empty → proceeds past
  body resolution. Recorded constraint: `/dev/fd/N` carries no basename, so
  a FUTURE rig that shape-validates the path would fail the allow-path
  loudly (non-zero exit, fail-closed) rather than read elsewhere; the relay
  comment states this. Residual window (documented): the final
  validation-stat → `O_NOFOLLOW` open adjacency (microseconds, one
  synchronous block) — down from the full validation → rig-exec span.
  File:line evidence: `scripts/seat-sandbox.sh:127, 91-92, 137-169`
  post-fix; test `tests/test_seat_sandbox.py:549-646`.
- **F3 — VALID (line number drifted: cited `:433`, actual `:428`), fixed.**
  The `TestRigRelayEnforcement` fake-rig shebang was
  `#!/usr/bin/env python3` while the test deliberately restricts
  `PATH` to `{fakebin}:/usr/bin:/bin` (`:434`) — passes today only by PATH
  luck. Fix (one line + the `import sys` the file lacked):
  `f"#!{sys.executable}\n"`. Verified: shebang is 59 bytes (< 100 limit);
  the written fake rig executes with `PATH=/nonexistent`
  (`FAKE-RIG-RAN hello`). The OTHER fake rig (escape corpus, `:339`) keeps
  `env python3`: it inherits the full runner `PATH` (`"PATH":
  f"{self.bin}{os.pathsep}{os.environ['PATH']}"`), i.e. the finding's own
  PATH-controlled carve-out — deliberately unchanged (minimal scope).
  File:line evidence: `tests/test_seat_sandbox.py:16, 427-428` post-fix.

## Red → Green evidence (behavior changes F2 + F1 probe creation)

- F1: scratch RED (symlink followed, victim clobbered) → fixed lines →
  scratch GREEN (`FileExistsError` on pre-placed symlink, victim intact,
  content + `/tmp` scope preserved). Scratch scripts removed.
- F2: new `TestRigRelayTOCTOU.test_swapped_path_cannot_redirect_granted_read`
  (space + `=` subTests) RED pre-fix (`RIG-READ:dummy-secret-content`,
  both forms) → GREEN post-fix (`/dev/fd/` in argv,
  `RIG-READ:{"slice": 12}`, no secret bytes).
- F3: no behavior change (test-harness robustness); proof is the
  `PATH=/nonexistent` execution above.
- Incidental edit hazard caught by the loop: the first F2 comment draft used
  `exec'd`, whose apostrophe broke the `python3 -c '...'` quoting
  (`bash -n` failed) — fixed to `executed`, `bash -n` green before tests ran.

## Acceptance

- `make verify` → rc=0: `SUMMARY: 35 checks passed, 0 failed`; V25 (7/7
  enforcement tests — `TestRigRelayEnforcement` kept at exactly 7 methods,
  the new TOCTOU test lives in its own class the gate does not count),
  V26, V27 all print green.
- Touched suite: `tests.test_seat_sandbox` → `Ran 34 tests … OK`
  (bwrap present, so bwrap-gated tests ran too).
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED` (rc=0).
- Full `make test` → `Ran 375 tests`, 1 failure:
  `test_build_canary.CanaryCatalogPins.test_canary_scope_only` — the single
  PRE-EXISTING canary failure (proven on base `07114e3` in the M1–M3
  report), out of scope; canary, Makefile, and V19 untouched.
- `git status --porcelain` (dirty for coordinator commit):
  `M scripts/seat-sandbox.sh`, `M tests/test_seat_sandbox.py`.

## Self-audit

- No stubs/`TODO`/empty-`catch`/skipped tests; fail-closed throughout
  (new deny messages on every pin mismatch; `os.close` before deny exits).
- V25 sensitivity honored: no new methods in `TestRigRelayEnforcement`
  (still 7), all six relay markers + the `os.execvp("rig", argv)` literal
  intact in `seat-sandbox.sh`.
- Minimal scope: `isfile`/`getsize` folded into one `os.stat` (same deny
  outcomes; no test referenced the retired "unreadable" message);
  `--source`/`-s`/`--note` parsing untouched; no spec/regen files touched.
- Unfinished / out of scope: none for this cycle — all three findings were
  valid and are addressed; the canary failure stays out of scope per
  instructions.
