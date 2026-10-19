# OpenRig Bundle: `systems-and-mobile-foundry`

Low-level Rust and C++ systems programming paired with native Android (Jetpack Compose) and iOS (Swift 6/SwiftUI) engineering.

## Purpose & Seats (4 Default Boot Seats)
- `systems.rust-systems-spec` (Rust Systems Specialist) — Policy: `builtin:standard`, Thinking: `high`
- `systems.cpp-lowlevel-eng` (C++ Systems & Low-Level Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `mobile.android-mobile-spec` (Mobile Android Specialist) — Policy: `builtin:standard`, Thinking: `high`
- `mobile.ios-mobile-spec` (Mobile iOS Specialist) — Policy: `builtin:standard`, Thinking: `high`

## Prerequisites & Setup
See `SETUP.md`. Seed seats with `python3 scripts/seed-rig.py rigs/systems-and-mobile-foundry/rig.yaml` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/systems-and-mobile-foundry --json`
- **Validate & preflight**: `(cd rigs/systems-and-mobile-foundry && rig spec validate rig.yaml --json && rig spec preflight rig.yaml --json)`
- **Launch**: `(cd rigs/systems-and-mobile-foundry && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)`
- **Stop**: `rig down systems-and-mobile-foundry`
