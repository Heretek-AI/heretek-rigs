# OpenRig Bundle: `defensive-sec-and-red-team`

Zero-trust defensive security and red-team rig: STRIDE threat modeling, SAST reachability, cloud IAM auditing, SPDX/SBOM compliance, LLM red-teaming, and Ghidra/Radare2 reverse engineering.

## Purpose & Seats (7 Default Boot Seats)
- `blue.threat-modeler` (Threat Modeling & Hardening Engineer) — Policy: `builtin:locked`, Thinking: `xhigh`
- `blue.appsec-engineer` (Application Security (AppSec) Engineer) — Policy: `builtin:locked`, Thinking: `high`
- `blue.cloud-sec-auditor` (Cloud Security & IAM Auditor) — Policy: `builtin:locked`, Thinking: `high`
- `blue.compliance-auditor` (Compliance & License Auditor) — Policy: `builtin:locked`, Thinking: `high`
- `red.ai-red-teamer` (Adversarial AI Red-Teamer) — Policy: `builtin:locked`, Thinking: `xhigh`
- `red.binary-reverse-eng` (Binary & Protocol Reverse Engineer) — Policy: `builtin:locked`, Thinking: `xhigh`
- `red.firmware-sec-analyst` (Firmware & Embedded Security Analyst) — Policy: `builtin:locked`, Thinking: `high`

## Prerequisites & Setup
See `SETUP.md`. Seed seats with `python3 scripts/seed-rig.py rigs/defensive-sec-and-red-team/rig.yaml` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/defensive-sec-and-red-team --json`
- **Validate & preflight**: `(cd rigs/defensive-sec-and-red-team && rig spec validate rig.yaml --json && rig spec preflight rig.yaml --json)`
- **Launch**: `(cd rigs/defensive-sec-and-red-team && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)`
- **Stop**: `rig down defensive-sec-and-red-team`
