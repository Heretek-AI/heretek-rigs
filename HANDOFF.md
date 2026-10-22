# Handoff — heretek-rigs fleet operator session (2026-10-20)

You are taking over an active heretek-rigs session. Repo: `Heretek-AI/heretek-rigs`.
Read `AGENTS.md` at the repo root first — it holds every workflow and hard rule.
Then verify state (branch HEAD, `make verify`, `gh pr list`, daemon/rig status);
trust nothing below without re-checking.

## Live state (last verified this message)

- Fleet is **DOWN**: all-51 omni rig stopped (snapshot `01M5BW93…`, restorable),
  daemon stopped, zero seat processes. Kernel operator tmux sessions untouched.
- Fleet queue (last-known): exactly 1 item (`S01b-…` at
  `delivery-tpm-scrum-lead`, `blocked` on `external:toolchain-exec-and-root-build-contract`).
  Everything else terminal.
- Workspace `/tmp/heretek-omni-51/project` kept on disk (seats' output files).
  Seeded seat dirs + snapshots kept under `~/.openrig` — relaunch needs no re-seed
  unless charters change (see below).
- Secrets: real `opencode-go.key` at `~/.config/heretek-rigs/secrets/` (0600,
  verified working). Never print or copy it.

## What happened today

1. Triad audit + live verification: 8/8 validates, 162 agents, 25/25 schemas,
   digest recomputes match, 64/64 skills both legs, 12/12 sabotage caught,
   live seat refusals proven. Zero repo defects.
2. exec-director incident: seat claimed "no queue surface" (bash denied by rule
   `*`). Root cause, proven from session JSONL + review log: its one attempt was
   `rig whoami --json; echo ...` — killed by the `;` terminal deny, correctly.
   Talked down via `rig send`; it self-corrected, then dispatched both engine
   delegations itself.
3. Prevention landed on `main`: denial-discipline charter text (all 51),
   rig-surface floor gate, `scripts/audit_sessions.py` (+ `make audit-sessions`).
4. Upstream issue filed: `gotgenes/pi-packages#1081` (denial omits command+rule).
5. S01b engine fix merged: `cmake/clang --version*` (engine),
   `cargo/ctest --version*` (physics). A review-bot objection was rebutted with
   matcher evidence (no code change).
6. Prompt rollout merged: Web 3-way taxonomy + Argon pilot merged across all 51
   charters (memory scoped 3/31, steelman leashed off security seats).
7. Docker delivery: `docker/fleet-images` branch (slim 3.5GB + full 4.7GB proven);
   open as PR #4. arm64 QEMU build NOT run locally.

## Open PRs (verify with `gh pr list`)

- #4 `docker/fleet-images` → `main` (open)
- #5 `feature/fleet-topology` → `main` (open, check status)
- #7 `feat/prompt-rollout` → `main` (open at handoff time)
- #8 engine probes: MERGED (`1b65c3b`)

## Pending decisions (need the human)

1. **Reference machine for S01b**: ADR 0001 pins Clang 19.1.0 + CMake 3.30.2;
   this host has 23.1.3 + 4.3.0. Ratify host versions or provision pinned
   toolchain. Nothing downstream moves honestly until answered.
2. **Re-seed after merges**: running seats were stopped; on next launch, re-seed
   so seats pick up post-merge charters (`PROMPT rollout` text + engine probes).
   Then TPM unparks S01b.
3. Stray untracked files (leave alone unless told): `docs/evidence/`,
   `docs/reports/`, `.agents/`, `.claude/`, root `skills-lock.json`,
   `docs/FLEET_EDGE_MAP.md` (superseded by generated `matrix.md` — recommend
   delete), root `PROMPT_REVIEW.md` (superseded by `docs/PROMPT_REVIEW_*.md` —
   recommend delete).

## First three things to do

1. `git status/pull`, `make verify` (expect 22/0), `gh pr list` for current PR states.
2. If relaunching: re-seed (`bootstrap-pi-seats.sh --profile all-51`), `rig up
   rig.all-51.yaml --cwd <fresh-workspace> --yes`, confirm 51 `run`.
3. Ask the human for the reference-machine decision — it gates everything.

## Decisions (2026-10-23, principal-confirmed)

- SCOPE: the 9 issues #37-#45 only; pre-existing backlog (#9,#11,#12,#14-#18) out of scope.
- ORDER: severity order #45,#38,#43,#40,#41,#37,#44,#42,#39.
- #12 deferred with written rationale (architecture program, needs own design tree).
- Per-issue approaches: #37 local guardrail (CLI truncation REFUTED in 0.6.13 — copy IDs only from --json, never retype); #38 event-driven re-eval on note-landed + explicit satisfy transition; #39 reconcile-diff command now, full generation later; #40 stage-time manifest-closure lint; #41 combined minimal verifier (lint-table + run:-vs-scripts); #42/#44 local --json/--full/--verify mandate + ONE upstream issue against mvschwarz/openrig filed alongside local fix; #43 sanctioned-untracked allowlist in generate-rigs.py; #45 warn-first live-health gate (overdue/undelivered + stuck-row age, heartbeat enablement prerequisite).
- EXECUTION: specs-first for all 9 (9 change packages across spec/remediate-45-38-43, spec/remediate-40-41-39, spec/remediate-37-44-42), then implement in severity order with full triad per remediation; PR per change, human merges.
- Live-state correction: tree dirt is now 2 modified (AGENTS.md one-line #44 workaround + HANDOFF.md) plus untracked session-evidence paths, verified 2026-10-23.
