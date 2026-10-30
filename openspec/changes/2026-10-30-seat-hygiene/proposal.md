# Proposal: 2026-10-30-seat-hygiene — fleet-wide dangling-reference audit (Refs #147)

## Goal

Audit-only wave for #147: enumerate EVERY live seat config vs on-disk
reality and list every dangling reference — `shellPath` and ALL other
path-like fields (`launch_cwd`, `packages[]`, MCP `command` paths,
`sandbox.env` roots, runner `sessionFile`) — checked against the
filesystem. Deliverables: a human report (per-seat findings, counts,
impact assessment — which seats are lobotomized vs merely stale, what
breaks on next launch/prune) plus a machine-readable JSON list of
dangling seats as the repair wave's input. Refs #147 — never Closes
(#147 stays open until a repair wave lands and a triad records
`VERDICT: PASS`).

## Non-goals (explicit boundary — repair and prevention are follow-up waves)

- No repairs: no seat relaunch, no `--refresh-policy-only`, no daemon-state
  surgery, no re-resolution of any dangling path. The 2 known lobotomized
  seats (`build-java-kotlin-eng`, `build-python-backend-spec` @
  `heretek-omni-fleet`) stay exactly as found.
- No launches: zero `rig seat launch`, zero queue creates, zero `rig send`.
  Read-only commands only (`rig ps`, `rig seat status`, filesystem
  existence checks against referenced paths).
- No `make live-health` change, no new V-gate. A V-gate appends ONLY if a
  follow-up wave proves a pinnable-green live behavior gap (then with
  V19-freeze note + live-count docs); otherwise 39/0 stands.
- Never `Closes #147` (not in this package, not in any close-out text).

## Method (read-only)

1. Pre-audit snapshot: `rig ps --nodes -A` → `ps-pre.txt`.
2. Enumerate every seat dir in `~/.openrig/state/pi/`; for each, read
   `agent/settings.json` (`shellPath`, `packages[]`), `agent/mcp.json`
   (absolute `command` paths + enabled/exposure flags), `agent/sandbox.env`
   paths, `runner-state.json` (`sessionFile`); run `rig seat status --json`
   per live seat (`launch_cwd`, session/occupant/startup state,
   `handover_at`); existence-check every referenced absolute path.
3. Post-audit snapshot: `rig ps --nodes -A` → `ps-post.txt`; byte-compare
   with pre (REQ-H3 zero-mutation proof).
4. If any inspection command would mutate (check `--help` first), use the
   read-only equivalent or record the field as unobservable-with-reason.

## Acceptance

- Compound green in the worktree (39/0; `openspec validate
  2026-10-30-seat-hygiene` rc=0; self-test PASSED; generate
  `--check-idempotent`; `make test` skipped with reason iff `git diff
  --name-only` shows zero code/test/script diffs).
- Evidence under `docs/evidence/seat-hygiene-2026-10-30/`: `audit.md`
  (every command rc=0, per-seat table, counts, impact), `dangling-seats.json`
  (machine-readable repair input), `ps-pre.txt` + `ps-post.txt`
  (byte-identical). Redacted; Bearer-shaped strings: none (grep-verified).
- Triad box in `tasks.md` stays UNCHECKED (coordinator runs the triad;
  this stage does not commit).
