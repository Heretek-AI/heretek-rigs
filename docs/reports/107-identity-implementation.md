# 107-identity M1–M3 implementation report

Stage: 107-identity M1-M3 (M0 spike done, winner recorded in
`docs/evidence/107-identity-m0.md`: MCP-bearer path via seed-time `!cat`
issuance, stdio unchanged; queue half daemon-blocked).
Worktree: `.lane/trees/107-identity` (branch `feat/107-identity`).
Implementer orders: test-first, zero stubs, `make verify` green, no commit,
leave worktree dirty for coordinator commit.

## Deliverables

- M1 (REQ-I1): seed-time per-seat grant issuance + render + appended
  FAIL-ONLY V23 gate. All acceptance elements proven without a live daemon.
- M2 (REQ-I2): revoke + re-add rotation runbook executed live end-to-end in
  scratch (pre-rotation 200 → revoke → 401 → re-add → 200, old token 401).
- M3 (REQ-I3): queue-half disposition NOTE ONLY. No queue-identity code,
  no upstream filing.

## Files changed

Tracked (modified):

- `fleet/mcp-servers.yaml` (+9): new `rig-mcp-http` catalog server —
  `transport: http`, `url_template: http://127.0.0.1:7437/mcp`,
  `seat_grant: true`, no static env/headers, `exposure: deferred`. Zero
  fleet roles bind it (opt-in default; stdio unchanged).
- `scripts/render-seat.py` (+33/-1): `SEAT_GRANT_FLAG`, module-level
  `seat_grant_token_filename(session)` → `mcp-http-<session>.key` (`.key`
  suffix reuses the frozen `*.key` path deny); `build_seat_files` appends
  the dynamic token file to the existing required/missing/degraded
  machinery and, when present, wires
  `Authorization: !echo Bearer $(cat <secrets>/<file>)` — the existing
  header form (same shape as github), never a third substitution form.
- `scripts/seed-rig.py` (+189): `parse_issued_token` (exact
  `Token for <name>,` + token-shaped line, else None),
  `_list_grant_names`, `_revoke_grant`, `issue_seat_grant`
  (fresh add → 0600 store; reuse when grant+file agree; revoke+re-add heal
  when the file is missing/symlinked; add-parse/write failure revokes the
  minted grant and dies — never a dead grant; `--allow-missing-secrets`
  degrades loudly), wired into `main()` before each seat's render and
  skipped for `--dry-run` / `--refresh-policy-only`.
- `scripts/verify-rigs.sh` (+50): appended V23 FAIL-ONLY block (no ok(),
  SUMMARY frozen at 35) — catalog shape asserts + `seat_grant_token_filename`
  sanity + `tests/test_identity_m1.py` must exit 0 with `Ran >= 15`.

Untracked (new, draft order — coordinator commits):

- `tests/test_identity_m1.py` (15 tests, all green).
- `docs/evidence/107-identity-rotation.md` (M2 runbook + live evidence).
- `docs/evidence/107-identity-queue.md` (M3 upstream-blocked note).

Generated leaves (`specs/`, `rigs/`, `rosters/`, `registry/`) were NOT
hand-edited. A dev regen (`HERETEK_RIGS_ALLOW_DIRTY=1`) produced byte-only
`DIRTY-<sha>` provenance stamps on `registry/entries+views` and zero content
drift anywhere else (proof the new server changes no committed leaf while
unbound); `registry/` was then reverted (`git checkout -- registry/`) so the
tree keeps committed provenance until the coordinator commits sources and
regens clean.

## Exact commands + exit codes

| Command | Result |
|---|---|
| `python3 -m unittest tests/test_identity_m1.py` (RED, pre-implementation) | 15 ran, 11 errors + 3 failures (missing `seat_grant_token_filename`, `parse_issued_token`, `issue_seat_grant`, unknown `rig-mcp-http`) — expected |
| `python3 -m unittest tests/test_identity_m1.py` (GREEN) | `Ran 15 tests ... OK` (exit 0) |
| `python3 -m unittest tests/test_render_seat.py tests/test_seed_rig.py` | `Ran 27 tests ... OK` (exit 0) |
| `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py` (after `.scratch/vendor` symlink via `python3 os.symlink`, gitignored) | exit 0; `git diff` showed only `DIRTY-` provenance stamps on 16 registry files, then reverted |
| `make verify` | exit 0 — `SUMMARY: 35 checks passed, 0 failed`, incl. `V23/107-identity M1 green: seat-grant catalog shape + filename helper + 15 corpus tests pass (FAIL-ONLY, SUMMARY frozen)` (live-health `[SKIP]`s are the normal no-daemon data-source skips) |
| M2 live rotation (scratch `OPENRIG_HOME=/tmp/107-rotate-20261027-012812`, daemon `:18433`, serve `:18437`) | add rc=0 → 200 → revoke rc=0 → 401 → re-add rc=0 (new token differs) → new 200 / old 401 / none 401; `daemon stop` rc=0, listeners gone, `~/.openrig/daemon.json` byte-identical |
| Stub/secret scan over all touched files | no `TODO/FIXME/stub/\|\| true` in new code; no token-shaped material in evidence docs (only redacted `or...Tk`/`or...VE` + `tokenSha256`) |

## Self-audit notes (stated plainly)

- M1 acceptance (`make verify` green, appended blocks, no V1–V22 renumber,
  SUMMARY frozen, `yaml.safe_load` only, dummy keys in `/tmp` 0600) is met.
  Cross-seat/revoked-deny is proven by M0 live (§4–§5) + M2 live (§2 step E)
  plus corpus parser/heal tests — no live daemon is needed for the gate.
- The dev-regen `DIRTY-` stamps were reverted, not committed: after the
  coordinator commits the four tracked source files + three new files, a
  clean-tree regen must re-stamp provenance (V13/#99 refuses `DIRTY-`).
- The `rig` CLI is faked in-process-statefully in tests (add/list/revoke
  semantics incl. dup-add and revoke-missing failures) — a genuine external-CLI
  double, not a pass-through mock.
- M2's evidence IS the revoked-token 401 red-proof (verbatim 401 body with
  `WWW-Authenticate: Bearer realm="openrig"`); T2 agency-qa sabotage remains
  a later stage and is untouched.
- M3 adds no code and files nothing upstream, per REQ-I3 and stage orders.
- Real tokens from the M1 probe (`blue-x@rig-y`) and M2 rotation existed
  only in `/tmp` scratch (700 dirs, 600 files) and tool output; nothing
  secret-shaped was written under the repo.
- Not done (out of scope for this stage): binding any fleet role to
  `rig-mcp-http` (opt-in is a future change with its own gate update),
  upstream filing for the queue half (needs principal authorization).
