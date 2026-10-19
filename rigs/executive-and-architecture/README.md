# OpenRig Bundle: `executive-and-architecture`

Executive governance, product strategy, sprint decomposition, system architecture, git drift coordination, and technical documentation squad.

## Purpose & Seats (6 Default Boot Seats)
- `exec.exec-director` (Director / CEO-Delegate) — Policy: `builtin:locked`, Thinking: `xhigh`
- `exec.product-director` (Product Director / Head of Product) — Policy: `builtin:locked`, Thinking: `high`
- `exec.system-architect` (System Architect) — Policy: `builtin:locked`, Thinking: `xhigh`
- `delivery.tpm-scrum-lead` (Technical Product Manager / Scrum Lead) — Policy: `builtin:locked`, Thinking: `high`
- `delivery.git-drift-coord` (Git & Worktree Drift Coordinator) — Policy: `builtin:locked`, Thinking: `high`
- `delivery.tech-docs-lead` (Technical Documentation Lead) — Policy: `builtin:locked`, Thinking: `high`

## Prerequisites & Setup
See `SETUP.md`. Seed seats with `python3 scripts/seed-rig.py rigs/executive-and-architecture/rig.yaml` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/executive-and-architecture --json`
- **Validate & preflight**: `(cd rigs/executive-and-architecture && rig spec validate rig.yaml --json && rig spec preflight rig.yaml --json)`
- **Launch**: `(cd rigs/executive-and-architecture && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)`
- **Stop**: `rig down executive-and-architecture`
