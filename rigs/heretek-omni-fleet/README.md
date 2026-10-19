# OpenRig Bundle: `heretek-omni-fleet`

Master composable 51-agent omni-fleet topology booting a 3-seat command center with 15 pod fragments and 51 member fragments for dynamic scaling.

## Purpose & Seats (3 Default Boot Seats)
- `command.exec-director` (Director / CEO-Delegate) — Policy: `builtin:locked`, Thinking: `xhigh`
- `command.tpm-scrum-lead` (Technical Product Manager / Scrum Lead) — Policy: `builtin:locked`, Thinking: `high`
- `command.system-architect` (System Architect) — Policy: `builtin:locked`, Thinking: `xhigh`

## Dynamic Scaling (`rig expand` & `rig add`)
- **Pod fragments (`pods/*.yaml`)**: 15 departmental/rig pods ready for `rig expand <RIG-ID> pods/<pod>.yaml --rig-root "$PWD"`.
- **Member fragments (`members/*.yaml`)**: All 51 specialist seats ready for `rig add heretek-omni-fleet <pod> members/<role>.yaml --rig-root "$PWD"`.
- **Static All-51 Profile**: `rig.all-51.yaml` declares all 51 seats across all 15 pods.

## Prerequisites & Setup
See `SETUP.md`. Seed seats with `python3 scripts/seed-rig.py rigs/heretek-omni-fleet/rig.yaml` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/heretek-omni-fleet --json`
- **Validate & preflight**: `(cd rigs/heretek-omni-fleet && rig spec validate rig.yaml --json && rig spec preflight rig.yaml --json)`
- **Launch**: `(cd rigs/heretek-omni-fleet && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)`
- **Stop**: `rig down heretek-omni-fleet`
