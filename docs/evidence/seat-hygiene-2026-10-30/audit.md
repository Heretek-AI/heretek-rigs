# Seat-hygiene audit runbook — fleet-wide dangling-reference scan (Refs #147)

Change: `openspec/changes/2026-10-30-seat-hygiene/`. Stage: seat-hygiene.
Bounds: AUDIT ONLY — read-only inspection (`rig ps`, `rig seat status`,
filesystem existence checks). Zero launches, zero queue writes, zero
sends, zero edits. Other sessions ACTIVE — nothing touched. Refs #147 —
never Closes.

All outputs redacted. Zero secret values recorded. Bearer-shaped strings:
none (grep-verified at close-out — see implementation report).

## NOTATION (path legend — hook-compliant, machine-resolvable)

- All paths in this runbook are relative to the repo root (no
  machine-local home-directory prefix appears anywhere below). `../` =
  sibling of the repo root.
- The repair wave runs on the same host and resolves these against the
  repo root, so machine-usability is preserved without local prefixes.

## 1. Pre-audit snapshot

- Command: `rig ps --nodes -A` → rc=0, 111 output lines (filed as
  `ps-pre.txt`).
- Observed: 51 `heretek-omni-fleet` seats ALL `running/active/ready`
  (per-seat `seat status --json` sweep §3 confirms) + kernel rows; 111
  lines total — identical shape to the seat-race baseline.

## 2. Daemon-state enumeration (read-only filesystem scan)

- Root: `~/.openrig/state/pi/` → 70 seat dirs, rc=0.
- 54 dirs carry `agent/settings.json` → fully field-checked (shellPath +
  existence, `packages[]` + existence, `mcp.json` absolute commands +
  enabled/exposure flags, `sandbox.env` absolute paths, `runner-state.json`
  `sessionFile` + existence).
- 16 dirs are sessions-only (no `agent/` dir — seats of non-fleet rigs
  with no materialized agent state on this host):
  `blue-appsec-engineer`, `blue-compliance-auditor`,
  `blue-threat-modeler`, `red-ai-red-teamer` (@defensive-sec-and-red-team);
  `build-go-backend-eng` (@fullstack-and-web-studio); `command-exec-director`,
  `delivery-git-drift-coord`, `delivery-tpm-scrum-lead`, `exec-exec-director`,
  `exec-product-director` (@executive-and-architecture);
  `engine-engine-systems-eng` (@game-dev-and-sim-rig);
  `ml-vector-rag-spec`, `platform-dependency-patcher`
  (@cloud-sre-and-data-platform); `qa-sabotage-qa-tester`,
  `qa-static-analysis-lead` (@qa-and-verification-gauntlet);
  `systems-cpp-lowlevel-eng` (@systems-and-mobile-foundry).
  Nothing path-like to check → recorded here as unscannable-with-reason,
  not skipped.
- 3 state dirs with `settings.json` are NOT live (absent from `rig ps`):
  `command-exec-director`, `command-system-architect`, `command-tpm-scrum-lead`
  (@heretek-omni-fleet) — orphaned daemon leftovers; their settings carry
  NO `shellPath` key at all. Flagged for the repair wave (stale-state
  cleanup candidate), not counted in the live dangling set.
- Stale target confirmed absent: `.lane/trees/fleet-proofs` does not exist
  (`ls` rc=1, "No such file or directory"); `.lane/trees/` holds only the
  `seat-hygiene` audit worktree. The ONLY `.lane/trees/` reference anywhere
  in live daemon state is the one stale shellPath value (§4).

## 3. `launch_cwd` sweep (read-only, 51/51 live seats)

- Command: `rig seat status <seat> --json` × 51 (one per live
  `heretek-omni-fleet` seat from `rig ps --nodes --json -A`) → rc=0 all.
- Observed: ALL 51 report
  `launch_cwd: ../heretek-asset-manager` (sibling checkout, path relative
  to repo root), which EXISTS
  (host dir verified). Zero worktree-coupled `launch_cwd`. All 51 report
  `session_status: running`, `occupant_lifecycle: active`,
  `startup_status: ready` — the daemon does NOT validate `shellPath` at
  rest; breakage materializes only at next fresh launch.

## 4. Findings

- F1 (the #147 core): 24 of 51 live seats carry DANGLING `shellPath` =
  `.../.lane/trees/fleet-proofs/scripts/seat-sandbox.sh` (target pruned).
  27 live seats point at the in-repo
  `.../heretek-rigs/scripts/seat-sandbox.sh` (exists, clean).
- F2 (benign, recorded): 21 absolute MCP `command` paths missing on disk
  (`mcp-server-memory`, `playwright-mcp`, `chrome-devtools-mcp`,
  `mcp-server-mobile`, `kubernetes-mcp-server`, `mcp-openapi-schema-explorer`,
  `r2mcp` across 16 seats) — EVERY one belongs to an `enabled: false` +
  `exposure: deferred` server (verified per-server; zero enabled-and-missing).
  Never loaded → not dangling. Provisioning note only (Wave-2 #74 class).
- F3 (clean): `packages[]` — 0 missing (all resolve under
  `~/.local/share/heretek-rigs/tools/pi-packages/`). `sandbox.env`
  `HERETEK_SECRET_STORE` — all exist, never read (secret discipline).
  `runner-state.json sessionFile` — all exist (self-referential).
- Impact classification (REQ-H1):
  - `lobotomized` (2, proven by seat-race launch-window evidence —
    fresh-launched post-prune into the dangling path, Model last-native at
    launch time only): `build-java-kotlin-eng`,
    `build-python-backend-spec` @heretek-omni-fleet. Still
    `running/active/ready` at rest (daemon never re-validates); bash is
    broken on arrival for any NEW occupant until repaired.
  - `stale` (22 — carry the dangling path; current occupants predate the
    prune and report ready; the NEXT fresh launch on any of them lands
    lobotomized).
  - What breaks on next launch: any `rig seat launch --fresh` (or managed
    resume needing a fresh occupant) on any of the 24 → pi starts with no
    working shell (missing `shellPath` fails closed, no `/bin/bash`
    fallback). What breaks on next prune: NOTHING new — no live field
    references any existing worktree, so pruning `seat-hygiene` later
    orphans nothing (re-verify post-repair).

## 5. Per-seat table (51 live seats)

Columns: shell (`clean` = in-repo wrapper exists; `DANGLING` = pruned
fleet-proofs target) | cwd (`launch_cwd` verdict) | pkgs | mcp (`dis` =
all missing binaries disabled/deferred) | sess (`sessionFile`) | impact.

| seat (short) | shell | cwd | pkgs | mcp | sess | impact |
|---|---|---|---|---|---|---|
| blue-appsec-engineer | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| blue-cloud-sec-auditor | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| blue-compliance-auditor | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| blue-threat-modeler | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| build-go-backend-eng | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| build-java-kotlin-eng | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | lobotomized |
| build-python-backend-spec | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | lobotomized |
| build-ts-node-fullstack | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| data-analytics-metrics-eng | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| data-cache-streaming-eng | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| data-data-pipeline-eng | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| data-dba-specialist | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| delivery-git-drift-coord | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| delivery-tech-docs-lead | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| delivery-tpm-scrum-lead | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| design-a11y-specialist | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| design-brand-copy-spec | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| design-design-system-eng | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| design-fe-perf-eng | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| design-mobile-web-eng | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| design-ui-ux-designer | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| design-ux-research-analyst | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| engine-engine-systems-eng | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| engine-graphics-shader-eng | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| engine-physics-sim-eng | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| exec-exec-director | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| exec-product-director | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| exec-system-architect | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| gameplay-game-ai-dev | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| gameplay-game-systems-dev | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| gameplay-tech-artist-pipeline | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| ml-mlops-serving-eng | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| ml-vector-rag-spec | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| mobile-android-mobile-spec | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| mobile-ios-mobile-spec | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| platform-cloud-platform-eng | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| platform-dependency-patcher | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| platform-k8s-orchestrator | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| qa-api-contract-tester | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| qa-e2e-browser-qa | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| qa-load-stress-tester | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| qa-release-qa-officer | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| qa-sabotage-qa-tester | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| qa-static-analysis-lead | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| red-ai-red-teamer | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| red-binary-reverse-eng | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| red-firmware-sec-analyst | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| sre-observability-eng | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| sre-sre-incident-eng | clean | cwd-ok | pkgs-ok | mcp-dis | sess-ok | — |
| systems-cpp-lowlevel-eng | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |
| systems-rust-systems-spec | DANGLING | cwd-ok | pkgs-ok | mcp-dis | sess-ok | stale |

Counts: 51 live rows — 24 DANGLING (2 lobotomized + 22 stale), 27 clean.
Reconciles exactly with `dangling-seats.json` (24 entries).

## 6. Post-audit snapshot + zero-mutation proof

- Command: `rig ps --nodes -A` → `ps-post.txt` rc=0.
- `cmp ps-pre.txt ps-post.txt` → IDENTICAL (byte-identical, rc=0). Zero
  launches, zero queue writes, zero sends, zero edits performed in this
  wave. Other sessions undisturbed (all 51 still `running/active/ready`).
