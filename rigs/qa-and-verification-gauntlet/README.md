# OpenRig Bundle: `qa-and-verification-gauntlet`

Adversarial quality assurance gauntlet: Playwright E2E browser automation, OpenAPI contract testing, k6 load testing, mutation sabotage, static analysis, and release QA veto.

## Purpose & Seats (6 Default Boot Seats)
- `qa.release-qa-officer` (Release QA & Acceptance Sign-off Officer) — Policy: `builtin:locked`, Thinking: `high`
- `qa.e2e-browser-qa` (End-to-End Browser Automation Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `qa.api-contract-tester` (API & Contract Testing Specialist) — Policy: `builtin:standard`, Thinking: `high`
- `qa.load-stress-tester` (Load & Performance Stress Tester) — Policy: `builtin:standard`, Thinking: `high`
- `qa.sabotage-qa-tester` (Adversarial Red-Proof Sabotage Tester) — Policy: `builtin:locked`, Thinking: `high`
- `qa.static-analysis-lead` (Code Style & Static Analysis Lead) — Policy: `builtin:locked`, Thinking: `high`

## Prerequisites & Setup
See `SETUP.md`. Seed seats with `python3 scripts/seed-rig.py rigs/qa-and-verification-gauntlet/rig.yaml` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/qa-and-verification-gauntlet --json`
- **Validate & preflight**: `(cd rigs/qa-and-verification-gauntlet && rig spec validate rig.yaml --json && rig spec preflight rig.yaml --json)`
- **Launch**: `(cd rigs/qa-and-verification-gauntlet && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)`
- **Stop**: `rig down qa-and-verification-gauntlet`
