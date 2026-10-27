# 107-identity rework cycle 1 report (post-PASS review findings)

Stage/wave: 107-identity rework 1 (prior VERDICT: PASS — bounded rework, max 3 cycles).
Worktree: `.lane/trees/107-identity` (branch `feat/107-identity`). No commit;
worktree left dirty for coordinator commit.

## Verdict on the five findings

All five findings verified against current code and all five were still
valid. Each was fixed minimally. No finding was skipped.

### F1 — rotation runbook step 5 blessed `$(cat file)` expansion — VALID, fixed

Evidence: `docs/evidence/107-identity-rotation.md` lines 35-37 (pre-fix)
read "never `Authorization:` on a command line that lands in shell history
— use the `$(cat file)` form or a header file". `$(cat file)` (and `$TOK`)
expansion places the bearer in the curl argument vector, visible to `ps`
and captured by process accounting — the exact placement the finding
prohibits.

Change: rewrote step 5 to prohibit the bearer in curl arguments literally
and through shell expansion, and to prescribe the safe forms — a mode-600
header file holding the single line `Authorization: Bearer <token>` passed
with curl's `@file` form (`curl -H @/path/to/auth.header ...`), or a
securely piped header with `-H @-`. The seat-configuration convention
(`!echo Bearer $(cat ...)` in render-seat.py, evaluated inside the seat by
Pi — not a shell argument) is untouched, per the finding. No evidence
section needed changes: §2 records only response bodies, no token-bearing
curl commands.

Test updates: none (prose-only doc fix). Live corroboration: the F5 probe
below authenticated with exactly the `-H @auth.header` form (200).

### F2 — grants issued for every seat, bound or not — VALID, fixed

Evidence: `scripts/seed-rig.py` lines 390-396 (pre-fix) called
`issue_seat_grant` unconditionally for every seeded seat. Zero fleet roles
bind `rig-mcp-http` (corpus catalog test asserts the bound list is `[]`),
so every seed run minted grants no seat could ever render — the opposite
of opt-in.

Change: added `seat_needs_grant(role, mcp_catalog, opt_in)` (generic over
the `seat_grant` catalog flag, not hardcoded to `rig-mcp-http`) plus
`GRANT_OPT_IN_ENV = "HERETEK_SEAT_GRANT_OPT_IN"` for the explicit opt-in;
`main()` now issues only when the seat's role binds a seat-grant server or
`HERETEK_SEAT_GRANT_OPT_IN=1`, otherwise prints
`ok <session>: no seat-grant binding, ordinary seed path (no grant
issued)` and continues to render. Unknown roles (`_role74 is None`) never
mint — safe because render dies on unknown roles anyway
(`render-seat.py:733,1379`).

Test updates: new `SeatNeedsGrantTests` (3 tests: bound needs, unbound/
empty/None needs-not, opt-in override). `main()` wiring itself is covered
by helper tests, not a live seed run (same boundary as M1, which never ran
the seeder against the real fleet).

Consequence (intended): with no fleet role currently bound, seeding now
issues zero grants until a role opts in — exactly the finding's demand.

### F3 — reuse path trusted names only, ignored grant metadata — VALID, fixed

Evidence: `scripts/seed-rig.py` lines 220-239 (pre-fix) reused the token
file whenever `session in _list_grant_names(...)` — a name-only check. A
grant name taken by a foreign seat/scope would have its bearer re-rendered
into our seat's config.

Design basis confirmed first, per the finding's note: `token list --json`
exposes `name/seat/rigs/roots/workspace/owner/createdAt` and never
tokens/hashes (M0 §1, re-confirmed live in the F5 probe: `rigs:
["testrig"]`, no secret fields). The match is built on those exposed
fields only.

Change: `_list_grant_names` replaced by `_list_grants` (name →
metadata-dict; sole caller was `issue_seat_grant`, no stale refs remain)
plus `_grant_scope_matches(grant, session, rig)` (seat equal, rigs equal to
`[rig]`/`[]`, roots empty, workspace/owner falsy; fail-closed on any
deviation or non-dict). A mismatched grant warns to stderr, is revoked,
and the loop re-issues — a foreign grant's bearer is never rendered.

Test updates: fake `rig` now records/emits full grant metadata (state
shape `{name: {seat, rigs, roots, workspace, owner}}`; legacy
string-valued state auto-normalized); new
`test_reuse_requires_matching_grant_metadata` (foreign seat →
revoke + re-add, file replaced) and
`test_reuse_rejects_scope_widened_grant` (`rigs: ["other-rig"]` →
re-scoped to `["rig-y"]`). The existing idempotence test now also proves
matching metadata reuses with exactly one `token add`.

### F4 — store flow could write a bearer into a permissive file — VALID, fixed

Evidence: `scripts/seed-rig.py` lines 272-275 (pre-fix) used
`os.open(... O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW, 0o600)` — confirmed the
mode/flags before changing, per the note. The `0o600` applies only at
creation; truncating a pre-existing `0644` file keeps it permissive, so
reseeding wrote a fresh bearer into a world-readable path.

Change (both halves of the finding's either/or, belt and braces):
(1) the target path is validated with `os.lstat` BEFORE `token add` —
an existing symlink, non-regular file, or non-`0600` mode fails closed
(strict: rc=2; `--allow-missing-secrets`: loud warn, no grant minted,
nothing stored); (2) the store itself mints a fresh `0600` temp file
(`tempfile.mkstemp` + explicit `fchmod`) and atomically `os.replace`s it
onto the path — the bearer never passes through a pre-existing file, and
replacing onto a symlink swaps the link, never its target. Temp files are
unlinked on any failure; every store failure still revokes the minted
grant (never a dead grant).

Test updates: new `test_permissive_existing_file_is_rejected_before_add`
(strict: rc≠0, no `token add` in the fake log, file byte-identical) and
`test_permissive_existing_file_degrades_loudly_with_opt_out`
(allow-missing: rc=0, warn, no grant minted).

Considered non-expansion (recorded deliberately): the *reuse* path does
not re-check the file's mode — the finding pins the file-opening (store)
flow, and reuse performs no write. A drifted-mode file predates reseeding
and is outside this finding's scope.

### F5 — seat-only scope → rig-scoped issuance — VALID, implemented with live proof

Evidence: `scripts/seed-rig.py` line 251 (pre-fix)
`token add <session> --seat <session>`. `rig mcp token add --help`
documents `--rig <name...>` as "Rigs whose seats and work this caller may
reach" — valid for single-rig seats (the seed context always knows the
seat's own rig: rig name, pod-fragment `--rig`, or member-fragment
`--rig`). Least-privilege-correct: it narrows the grant from the
ambiguous empty-`rigs` default to exactly the seat's own rig.

Live proof (scratch `OPENRIG_HOME=/tmp/107-rework1-20261027-030933`,
daemon `:18443`, serve `:18447`, real state byte-identical before/after —
`~/.openrig/daemon.json` still `pid 57353, port 7433`):
`token add blue-probe@testrig --seat blue-probe@testrig --rig testrig`
→ rc=0, 47-char bearer; `token list --json` shows
`rigs: ["testrig"]` with no secret fields; bearer presented via the F1
`-H @auth.header` (mode-600) form → `initialize` 200. M0-proven allow
behavior is preserved under rig scoping — the finding's go-condition is
met, so the change was implemented rather than skipped.

Change: `issue_seat_grant(..., rig=None)` appends `--rig <rig>` when set;
`main()` passes `rig=s["rig"]`. Aligned strings: REQ-I1 parenthetical in
`openspec/changes/107-identity/specs/identity/spec.md` now reads
"(scoped to the seat's own managed rig via `--rig`; no
`--root/--workspace/--owner` per M0 outcome)"; catalog `rig-mcp-http`
description and seeder comments updated to the rig-scoped command shape.
Prior-stage evidence/reports (`107-identity-m0.md`, `-rotation.md` §2,
`red-proofs.log`, implementation/verification reports) are history and
were NOT rewritten. The M2 runbook's step 3 (`token add <name>
--seat <session>`) is unchanged: it is the manual operator form, and
adding `--rig` there is a future runbook refinement, not this finding.

Deviation rationale (for the record): M0's "seat-only proven sufficient"
conclusion is preserved, not contradicted — the probe above shows
`--rig` allow-equivalent on `initialize`, and strictly tighter on scope.
`_grant_scope_matches` (F3) expects `rigs == [rig]`, closing the loop.

Test updates: `issue()` helper takes `rig="rig-y"` and passes it through;
new `test_add_scopes_grant_to_managed_rig` asserts the fake CLI received
`token add blue-x@rig-y --seat blue-x@rig-y --rig rig-y` and stored
`rigs == ["rig-y"]` with `roots []`, no workspace/owner. All pre-existing
issue calls now exercise the rig-scoped path.

## Files changed

- `scripts/seed-rig.py` (+~130/-~35): F2 gate + helper, F3 metadata
  match, F4 pre-check + atomic store, F5 `--rig` + `rig` param, `stat`/
  `tempfile` imports, comment alignment.
- `tests/test_identity_m1.py` (15 → 23 tests): metadata-aware fake rig,
  rig-plumbed helper, 2 scope tests (F5), 2 metadata tests (F3), 2
  permissive-file tests (F4), 3 gating tests (F2).
- `docs/evidence/107-identity-rotation.md`: F1 step-5 rewrite (only §1
  runbook step 5 touched).
- `openspec/changes/107-identity/specs/identity/spec.md`: REQ-I1
  parenthetical aligned to rig-scoped issuance (the one spec line the
  stage orders authorize).
- `fleet/mcp-servers.yaml`: `rig-mcp-http` description aligned (one line).

Untouched per standing rules: `specs/`, `rigs/`, `rosters/`, `registry/`
(no regen needed — no `.key`/role/binding change while unbound);
`SUMMARY` frozen at 35; V23 block unrenumbered (floor `>= 15` still holds
at 23); `yaml.safe_load` only; dummy tokens in `/tmp` 0600 scratch only.

## Exact commands + exit codes

| Command | Result |
|---|---|
| `rig mcp token add --help` | rc=0; confirms `--seat`, `--rig <name...>`, `--root`, `--workspace`, `--owner` |
| Live F5 probe (scratch daemon `:18443`, serve `:18447`): `token add blue-probe@testrig --seat ... --rig testrig` → `list --json` → `curl -H @auth.header initialize` | add rc=0 (47-char bearer); list shows `rigs: ["testrig"]`, no secrets; `curl` 200 (header-file form also validates F1) |
| `rig daemon stop` (scratch) + listener/proc sweep + `~/.openrig/daemon.json` compare | `Daemon stopped` rc=0; listeners gone; real daemon.json byte-identical to M0 pre-spike read |
| `python3 -m unittest tests/test_identity_m1.py` (RED, pre-implementation) | 23 ran, 14 errors (missing `rig` param, `seat_needs_grant`, metadata/perms paths) — expected |
| `python3 -m unittest tests/test_identity_m1.py` (GREEN) | `Ran 23 tests ... OK` (exit 0) |
| `python3 -m unittest tests/test_render_seat.py tests/test_seed_rig.py` | `Ran 27 tests ... OK` (exit 0) |
| `make verify` | exit 0 — `SUMMARY: 35 checks passed, 0 failed`; `V23/107-identity M1 green ... 23 corpus tests pass (FAIL-ONLY, SUMMARY frozen)`; live-health `[SKIP]`s are the normal no-daemon data-source skips |
| Stub/secret scan over all touched files; stale-ref grep for `_list_grant_names` | clean (no `TODO`/`|| true`/empty-catch/skips; no bearer material in edited docs) |

Note: one self-inflicted shell incident during cleanup — `pkill -f
"rig mcp serve.*18447"` matched the invoking shell's own command line
(the `pgrep -f` footgun AGENTS.md warns about) and SIGTERM'd it before
completing. Recovery: confirmed the serve proc was gone, stopped the
scratch daemon normally, verified listeners/processes/real-state. No
repo impact; recorded so the coordinator does not misread a truncated
terminal log.

## Self-audit notes (stated plainly)

- All five findings were valid against current code; nothing was skipped,
  so no skip reasons are owed. The one deliberate boundary (reuse path
  does not re-check file mode) is documented under F4 above.
- F2 changes live behavior for the current fleet: zero grants are minted
  until a role binds `rig-mcp-http` (or env opt-in) — intended, and the
  M1 strict-render path is unaffected because render only requires the
  token file for bound roles.
- F5's `--rig` addition is the sole behavior change to the M0-winning
  shape, and it carries its own live 200 proof above plus corpus
  coverage; revocation semantics are untouched (revoke is name-keyed).
- Not done (out of scope): binding any fleet role to `rig-mcp-http`,
  upstream queue filing, T2 sabotage (later stage), and any regen
  (no generated-leaf inputs changed).
