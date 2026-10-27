# 107-identity rework cycle 3 report (FINAL cycle, 3 of 3)

Stage/wave: 107-identity rework cycle 3 (prior VERDICT: PASS — bounded rework, FINAL cycle).
Worktree: `.lane/trees/107-identity` (branch `feat/107-identity`). No commit;
worktree left dirty for coordinator commit.

## Rule compliance

All finding text treated as UNTRUSTED: every flagged expression was verified
against current code before any change. No renumber (V1–V23 untouched),
SUMMARY frozen at 35, `yaml.safe_load`-only, dummy tokens in `/tmp` 0600
scratch only (scratch bearers revoked at the source and the scratch dir
removed afterwards). `specs/`, `rigs/`, `rosters/`, `registry/` untouched
(no regen — no generator inputs changed).

## Per-finding verdicts (file:line evidence)

### N1 — sourcery dangerous-subprocess-use at seed-rig.py:363 — BENIGN, no change

Verified all five `subprocess.run` call sites in current `scripts/seed-rig.py`:
:212 (`[rig_bin, "mcp", "token", "list", "--json"]`), :255
(`[rig_bin, "mcp", "token", "revoke", session]`), :358 (`add_cmd`, built as
`[rig_bin, "mcp", "token", "add", session, "--seat", session] + ["--rig", rig]`),
:552 (`cmd`, render-seat argv list), :557 (same `cmd`). Every call is
list-form with NO `shell=True` anywhere in the file (grep `shell` returns
only `shutil`/`shell-quoting`-adjacent identifiers, zero `shell=True`).
Arguments are operator-config-derived (`rig_bin` from `shutil.which`,
session/rig from the fleet spec being seeded). No string-form or
externally-influenced shell invocation exists — benign-with-reason, nothing
to fix.

### N2 — CodeQL clear-text logging (alert 91) at seed-rig.py:297 — COVERED, no change

Line 297 (`print(f"error: {session}: seat grant issuance failed: {msg}", ...)`)
is inside `_fail`, whose FIRST statement (line 290) is
`msg = _redact_for_log(msg)`. Every tainted flow reaching this line
(`detail` from rig-subprocess output :367, `OSError`/`TimeoutExpired`
strings :364, store-path `OSError` :398–401 routed directly) is redacted at
the choke point before interpolation — this is exactly the rework-2 fix,
verified still in place. Recorded benign/covered; no edit (a second
redaction would be dead code).

### N3+N4 — CodeQL overly-permissive chmod (alerts 92, 93) at tests/test_identity_m1.py:270,281 — BENIGN-BY-DESIGN, no change (accepted-risk)

Lines 270 and 281 are `os.chmod(p, 0o644)` inside the F4 fixtures
`test_permissive_existing_file_is_rejected_before_add` and
`test_permissive_existing_file_degrades_loudly_with_opt_out`. The 0644 mode
is the deliberate attack setup: each test plants a world-readable file,
then asserts the seeder refuses to mint/store into it (strict: rc≠0, no
`token add` in the fake log, file byte-identical; degraded: rc=0 with warn,
no grant minted). Changing these modes would destroy the red-proof the
tests exist to provide. Recorded as accepted-risk; file intentionally
untouched.

### Old threads (alerts 85–90, rework-2 scope) — CONFIRMATION ONLY, no change

Verified each flagged-class expression still routes through the rework-2
choke point: `_fail` redacts at :290 covering :292–295 (degraded warn),
:297 (strict error), :303 (list failure), :319 (symlink-unlink error),
:335 (revoke failure), :349–352 (refusing-to-store), :365 (add exception),
:370 (add-failure detail), :407 (did-not-converge); the sole direct print
outside `_fail` (:400–401 store error) carries its own `{_redact_for_log(e)}`.
Pure name/session/filename lines (:309–312, :320–327, :330–333, :374–377,
:405) interpolate no external output. All covered; nothing new found.

### R1 — rotation runbook step 3 missing `--rig` — VALID, fixed

Verified: `docs/evidence/107-identity-rotation.md` §1 step 3 (pre-fix) read
`rig mcp token add <name> --seat <session>`. The seeder's F3 match
(`_grant_scope_matches`, seed-rig.py:231–250) requires
`rigs == [rig]` — a rig-unscoped manual grant (`rigs == []`) is a scope
mismatch, so the next seed would revoke-and-replace the manually rotated
bearer, silently undoing the rotation. Fix: step 3 now reads
`rig mcp token add <name> --seat <session> --rig <managed-rig>` with a
parenthetical naming the seeder scope, the F3 check, and the
revoke-and-replace consequence of omitting `--rig`. Evidence §2 (history of
the executed live rotation) NOT rewritten — it records what was actually
run (seat-only M1 shape, pre-F5). Prose-only doc fix; no test change.

### R2 — spec REQ-I1 overclaims vs the F2 gate — VALID, fixed minimally

Verified: REQ-I1 (`openspec/changes/107-identity/specs/identity/spec.md`
line ~12, pre-fix) required seed-time issuance unconditionally, while the
F2 gate (`seat_needs_grant`, seed-rig.py:170–183 + `main()` wiring :514–522)
issues ONLY for roles binding a `seat_grant: true` catalog entry (or
`HERETEK_SEAT_GRANT_OPT_IN=1`). Fix: one inserted clause limiting issuance
to seats whose role binds a `seat_grant: true` entry (or explicit opt-in),
stating unmarked HTTP entries and stdio servers are unchanged and receive
no grant. No other spec line touched; no test change (behavior already
covered by `SeatNeedsGrantTests`).

### R3 — same-rig cross-seat bearer use — PREMISE REFUTED live, no code change

Live proof (scratch isolation ONLY: `OPENRIG_HOME=/tmp/107-r3-20261027`,
mode 700; daemon `127.0.0.1:18453`, grant MCP `127.0.0.1:18457`; real
`~/.openrig/daemon.json` verified byte-identical afterwards —
`pid 57353, port 7433, startedAt 2026-10-23T18:31:27.164Z`; scratch dir
removed, both scratch grants revoked first):

- `rig mcp token add seat-a-grant --seat blue-a@testrig --rig testrig` → rc=0 (47-char bearer); same for `seat-b-grant`/`blue-b@testrig` → rc=0.
- `rig mcp token add --help` confirms 0.7.2 offers NO seat-level scope flag
  (only `--seat/--rig/--root/--workspace/--owner`) — there is no mechanism
  to build the finding's proposed seat-level boundary, and none was built.
- Presented A's bearer (`curl -H @auth.header`, mode-600 header-file form)
  and called `rig_whoami` → verbatim:
  `{"error":"Session or node 'blue-a@testrig' not found in any managed rig. ...}` —
  the server resolved the caller as **the grant's own seat A**, not B.
  B's bearer likewise resolved to `blue-b@testrig`. (The 404 is the
  expected scratch artifact: no rig is `up` in the scratch HOME, so no
  sessions exist there; the identity RESOLUTION — always the caller's own
  grant seat — is the evidence.)
- Server banner/instructions state the rule verbatim: "each caller acts as
  its grant's seat within its rigs and roots" / "over authenticated HTTP,
  the seat of the caller's grant (rig_whoami shows which...)".

Disposition: cross-seat impersonation is IMPOSSIBLE by construction — a
bearer always resolves to its own grant's seat server-side, so presenting
A's bearer can never yield B's identity and no 401/`out_of_scope` tripwire
is reachable or needed. Both seats sharing one rig's scope is the intended
F5/M0 rig-level design, not a boundary violation. Note-only; no dead
seat-level mechanism invented for 0.7.2. No code change.

Self-correction recorded: one `printf` during header-file setup embedded a
scratch bearer on a command line (the exact placement the F1 runbook
prohibits). Scratch-only, revoked at source, dir removed — no repo or real-
state impact. Header files themselves were mode 600 and all authenticated
probes used the `-H @file` form.

## Files changed

- `docs/evidence/107-identity-rotation.md` (R1): step 3 now mints with
  `--seat <session> --rig <managed-rig>` + scope-mismatch rationale.
- `openspec/changes/107-identity/specs/identity/spec.md` (R2): REQ-I1
  limited to `seat_grant: true` opt-in; unmarked HTTP + stdio unchanged.
- This report (new file).

Untouched per standing rules: `scripts/seed-rig.py`, `tests/`,
`fleet/mcp-servers.yaml`, `specs/`, `rigs/`, `rosters/`, `registry/`,
SUMMARY, V23 block (floor `>= 15` still holds at 25 — block text already
states 25, no update required).

## Exact commands + exit codes

| Command | Result |
|---|---|
| `python3 -m unittest tests/test_identity_m1.py` | `Ran 25 tests ... OK` (exit 0) |
| `python3 -m unittest tests/test_render_seat.py tests/test_seed_rig.py` | `Ran 27 tests ... OK` (exit 0) |
| `make verify` | exit 0 — `SUMMARY: 35 checks passed, 0 failed`; `V23/107-identity M1 green ... 25 corpus tests pass (FAIL-ONLY, SUMMARY frozen)`; live-health `[SKIP]`s are the normal no-daemon data-source skips |
| R3 live (scratch): `token add` ×2 same-rig, `serve --http`, `initialize` 200, `rig_whoami` ×2 (A→A, B→B), `revoke` ×2, `daemon stop`, scratch removed, real daemon.json identical | recorded verbatim above |
| Stub scan (`TODO`/`NotImplementedError`/`test.skip`/`\|\| true`/`set +e`) over both edited files | clean |

## Self-audit notes (stated plainly)

- Five of seven findings required no code: N1/N2/N3+N4 verified
  benign/covered/by-design with file:line evidence; old threads confirmed
  under the rework-2 choke point; R3 refuted live. Two doc/spec fixes
  (R1/R2) are prose-only — no behavior change, so no red-first cycle
  applied (nothing to redden); all 25 + 27 tests green unmodified.
- R3's 404-shaped whoami output is evidence OF resolution (own-seat), not
  a failed probe: in scratch no sessions exist, so any resolved seat 404s —
  the discriminating fact is WHICH seat each bearer resolved to.
- Not done (out of scope): binding any fleet role to `rig-mcp-http`,
  upstream queue filing, any regen, any seat-level scope mechanism.
