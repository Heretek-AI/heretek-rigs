# Proposal: provisioning-gate-74 — full-matrix existence gate, no provisioning claims

Status: scope approved (HANDOFF Wave C + operator "Proceed", 2026-10-24).
Issue: #74 stays OPEN (this change does not close it). #89 context (closed as dup) supplies the gate shape.

## Root cause (verified read-only 2026-10-24, Wave C recon)

- 7/20 command-bearing MCP servers missing on host (`$TOOLS/bin/` + `src/` empty; only `codebase-memory-mcp` + `context7-mcp` present in `.bin/`); `r2`/`rabin2`/`tshark`/`r2mcp` unresolvable; `uvx`/`docker` present but per-package resolution unchecked. Matches #74 body exactly.
- PR #104 (single-slice playwright→browserbridge swap, author's own fork, no gate, claimed `Closes #74`) declined 2026-10-24T18:04Z with record: relieves one slice only, misleading browser claim, no gate. Must not repeat.
- V12 (`verify-rigs.sh:1623-1722`) resolves per-seat MCP commands as `[NOTE]` only ("installing host tooling is M9 scope") and ignores bash-grant leading binaries entirely. `render-seat.py:512-560` substitutes `command` blindly; only secrets drive `enabled:false`. `live-health.py` has no tool-resolution sub-check. That three-layer blind spot is the missing gate.

## Change (gate only, honestly scoped)

Full-matrix existence gate covering all 20 command-bearing servers + bash-grant leading binaries (matrix skeleton in recon §5, bound roles in `fleet/fleet.yaml`):

- `render-seat.py` mcp.json section (beside `secret_ok`/`entry["enabled"]=False :549`): resolve each bound `command` + each `bash_allow` leading token at render time → missing yields `enabled:false` + stderr warn (mirrors degraded-secrets path #74 checkbox 2 blesses). Never silent.
- `seed-rig.py` per-seat staging loop: same check at seed/stage time (the literal "stage-time").
- New appended verify block (no renumber) asserting renderer/seed gate strings exist + corpus red-proofs both directions (missing → named FAIL/NOTE; present → green).
- `live-health.py` WARN-first "0 missing tools" sub-check (fits REQ-LH7 warn-first policy; #89's live-health half).

Explicitly NOT in scope: installing any tool on any host; `uvx --from`/`docker image inspect` deep probes (recorded as follow-up); closing #74 (stays OPEN until all rows provisioned-or-documented AND this gate lands).

## Acceptance

1. Matrix doc `docs/74-PROVISIONING-MATRIX.md` (or evidence-annexed table) lists all 20 servers + B1–B3 bash binaries with required artifact, bound roles, current state.
2. Render + seed gates resolve and degrade loudly (red-proofed: missing binary → `enabled:false` + warn; present → enabled).
3. `make verify` green (new block appended, no renumber); red-proofs both directions on disk.
4. Drift-guard `VERDICT: PASS` → PR with `Refs #74` (never `Closes #74`).
