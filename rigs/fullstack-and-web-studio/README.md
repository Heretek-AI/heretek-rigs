# OpenRig Bundle: `fullstack-and-web-studio`

End-to-end web, backend microservice, UI/UX design system, frontend performance, accessibility, and user research studio.

## Purpose & Seats (11 Default Boot Seats)
- `build.ts-node-fullstack` (TypeScript / Node Fullstack Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `build.python-backend-spec` (Python Backend & Systems Specialist) — Policy: `builtin:standard`, Thinking: `high`
- `build.go-backend-eng` (Go Backend Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `build.java-kotlin-eng` (Java / Kotlin Enterprise Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `design.ui-ux-designer` (UI/UX Designer & Prototyper) — Policy: `builtin:standard`, Thinking: `high`
- `design.design-system-eng` (Design System Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `design.fe-perf-eng` (Frontend Performance Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `design.a11y-specialist` (Accessibility (a11y) & Usability Specialist) — Policy: `builtin:standard`, Thinking: `high`
- `design.mobile-web-eng` (Mobile Web & Responsive Layout Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `design.brand-copy-spec` (Brand & Creative Copy Specialist) — Policy: `builtin:standard`, Thinking: `high`
- `design.ux-research-analyst` (User Research & Feedback Analyst) — Policy: `builtin:locked`, Thinking: `high`

## Prerequisites & Setup
See `SETUP.md`. Seed seats with `python3 scripts/seed-rig.py rigs/fullstack-and-web-studio/rig.yaml` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/fullstack-and-web-studio --json`
- **Validate & preflight**: `(cd rigs/fullstack-and-web-studio && rig spec validate rig.yaml --json && rig spec preflight rig.yaml --json)`
- **Launch**: `(cd rigs/fullstack-and-web-studio && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)`
- **Stop**: `rig down fullstack-and-web-studio`
