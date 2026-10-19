# OpenRig Bundle: `game-dev-and-sim-rig`

Real-time game engine architecture, ECS systems, deterministic physics simulation, GPU shader pipelines, game AI, and glTF/KTX2 asset tooling.

## Purpose & Seats (6 Default Boot Seats)
- `engine.engine-systems-eng` (Engine & Systems Programmer) — Policy: `builtin:standard`, Thinking: `high`
- `engine.physics-sim-eng` (Physics & Simulation Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `engine.graphics-shader-eng` (Graphics & Shader Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `gameplay.game-systems-dev` (Game Systems & Gameplay Programmer) — Policy: `builtin:standard`, Thinking: `high`
- `gameplay.game-ai-dev` (Game AI Programmer) — Policy: `builtin:standard`, Thinking: `high`
- `gameplay.tech-artist-pipeline` (Technical Artist & Asset Pipeline Lead) — Policy: `builtin:standard`, Thinking: `high`

## Prerequisites & Setup
See `SETUP.md`. Seed seats with `python3 scripts/seed-rig.py rigs/game-dev-and-sim-rig/rig.yaml` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/game-dev-and-sim-rig --json`
- **Validate & preflight**: `(cd rigs/game-dev-and-sim-rig && rig spec validate rig.yaml --json && rig spec preflight rig.yaml --json)`
- **Launch**: `(cd rigs/game-dev-and-sim-rig && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)`
- **Stop**: `rig down game-dev-and-sim-rig`
