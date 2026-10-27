# Handoff — next session (2026-10-26, post-PR #119 merge on main)

> Superseded 2026-10-24 handoff archived in git history (`1e2979c`..`41ccec3`).
> This document reflects the authoritative state of `main` after merging PR #117, PR #118, and PR #119.

---

## 1. Live State & Environment

- **Repository**: `/home/john/Projects/heretek-rig-workspace/heretek-rigs`
- **Branch**: `main` @ `41ccec3` (Merge PR #119). Working directory clean (`git status -s` clean; sanctioned `.lane/` stray only).
- **Core Stack**:
  - `@openrig/cli@0.7.2` (bumped from 0.6.13 in PR #118)
  - Pi `1.4.0` (`@earendil-works/pi-coding-agent`, bumped from 1.3.0 in PR #118)
  - `@gotgenes/pi-permission-system@41.0.0`
  - Model: `opencode-go/muse-spark-1.3-contributor:high` via `https://opencode.ai/inference/go/v1`
- **Verification Baseline**:
  - `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 35 checks passed, 0 failed** (all V1–V21 gates green).
  - `make test` → **359 unit tests passed, 0 failed** across 15 test suites.
  - `python3 scripts/audit_loop.py --self-test` → **`SELF-TEST PASSED`**.
  - `python3 scripts/generate-rigs.py --check-idempotent` → **Byte-identical**.

---

## 2. Merged Landings Since Last Handoff

### PR #119 (`41ccec3`, 2026-10-26)
- **#98 Contract Schemas**: Vendored upstream contract schemas byte-for-byte from `@openrig/cli@0.7.2` (`package/daemon/docs/reference/schemas/`), pinned in `schemas/contract-schemas.sha256`, and cmp'd in V18 against installed CLI copies. Aligned attestation tokens (`not_tested`, `NOT_RUN`). Local `$ref` resolution handles absolute upstream schema IDs.
- **#102 Claim 6.1 (License-less Skills)**: Added declared license provenance (`skills-lock.json`) for 10 shared skills lacking license files; `generate-rigs.py` pre-validates licenses using safe YAML parsing (`yaml.safe_load`) before deleting generated trees; `verify-rigs.sh` checks declared licenses against standard SPDX identifiers and cross-verifies against frontmatter / source pins.
- **#96 Live Policy Refresh**: Implemented `scripts/render-seat.py --policy-only` and `scripts/seed-rig.py --refresh-policy-only` to atomically refresh `extensions/pi-permission-system/` and `sandbox.env` (updating bubblewrap write-roots for `path_write` changes) with `config.json` replaced last via same-directory `.tmp` rename (`0600`). Proved seat subprocess isolation against agentDir self-edits (`test_seat_sandbox.py`).
- **Remediated Review Feedback**: Sourcery #5660213174 (pre-rmtree validation, SPDX checking), CodeRabbit #5660659989 (frontmatter YAML parsing, dry-run seat check, `sandbox.env` in refresh, V18 npm package resolution fallback), and SonarCloud Security/Complexity rules (path containment, complexity < 15).

### PR #118 (`91da43e`, 2026-10-26)
- **Stack Upgrades**: OpenRig 0.7.2 bump ledger (`docs/openrig/`); Pi 1.4.0 bump ledger (`docs/pi/`).
- **V21 Gate**: Vendored agent file-set parity gate (105 rig members match `specs/agents/`).
- **V13 Fix**: Skopeo offline keyword match on full stderr (handles rate-limiting).
- **Runtime Degraded Auth**: Degraded seats emit `{}` in `auth.json` (avoids pi failing on dangling `!cat`).
- **Model Endpoint**: `fleet.yaml` `model.base_url` drives `models.json` with pinned endpoint check.
- **Audit Row Isolation**: `audit_sessions` `FALSE_DELIVERY_CLAIM` evaluated per-row instead of per-file.
- **Canary Alignment**: Updated `test_build_canary.py` pins to match #91 scoped compiler grants.

### PR #117 (`17f119c`, 2026-10-26)
- **#91 Scoped Build/Test Path Args**: Added scoped `pytest`, `go build`, `cmake -S . -B build`, and `gcc -c` grants via native-map `commandEffects`, resolving path-argument policing issues code-side. Added gate V20.

---

## 3. Current Issue Triage (15 Open Issues)

| Issue | Priority | Title / Scope | State & Next Steps |
|---|---|---|---|
| **#102** | P3 | Audit P3 bundle: doc drift, minor gates | **Partially done**. Claim 6.1 (10 skill licenses), 64-vs-68 drift, 0.6.11 prompt pin, V19/V21 gates, and `--out` check are resolved. **Remaining**: HR-F18 (bare `rig queue`/`rig send` policy in seat maps), HR-2.5 (`rig bundle check` on `rig.all-51.yaml`), dangling `superpowers:writing-skills` ref, OpenRig DAG cycle report. |
| **#107** | P2 | Remediation follow-up bundle (post-#105) | **Partially done**. V13 rate-limit regex, session URL, and stale count closed. **Remaining**: firecrawl standalone boot on networked host; governance limitations (bare-TPM shorthand, `xyz123` human check); explore OpenRig 0.7.2 HTTP bearer-token identity grants (upstream #1860) to address F9. |
| **#91** | P2 | Scoped build/test path args | **Code done** in PR #117 + PR #118. **Pending**: Live proof on fleet host (`pytest tests/rag`, `go build ./...`, `cmake -S . -B build`, `gcc -c`). |
| **#12** | P1 | No seat can execute builds | **Blockers #106 and #91 cleared code-side**. **Pending**: Real in-seat runner proof D1–D4 on fleet host, committer path D5–D7 through REQ-BC4 envelope. |
| **#74** | P1 | Granted tools not provisioned | **Gate done** (V16 + render warning in PR #114). **Pending**: Host-side provisioning of 7 npm packages + `r2`/`rabin2`/`tshark`, or updating matrix docs. |
| **#66** | Umbrella | Tracking: Oct 23–24 adversarial audit | Umbrella issue. Updated with #96 and #98 completions. Stays open until remaining P1/P2 items close. |
| **#77** | P2 | Mission parent rows stuck 'standing by for gate' | Live workflow/governance item. Needs gate owner assignment or automated gate reconciler. |
| **#78** | P2 | Seats pinned to one workspace | Architectural: multi-workspace / mission workspace isolation. |
| **#80** | P3 | `rig snapshot list <name>` prints `[object Object]` | Upstream CLI bug. Documented local mitigation in place. |
| **#81** | P2 | Seats park idle right after claiming | OpenRig daemon scheduling behavior. |
| **#9** | P2 | Operator `rig send` carries no sender identity | Needs upstream envelope/identity standard. |
| **#11** | P2 | `rig launch` refuses running nodes | Replaced repo-side by `#96` live policy refresh; full seat restart tracked upstream. |
| **#15** | P2 | Authorization loop lags seat fix cycles | Investigation / auto-unblock rules. |
| **#16** | P2 | Parallel slice execution: throughput vs collision | Investigation / scheduler policy. |
| **#17** | P2 | Fleet utilization and slice queue patterns | Investigation / telemetry. |
| **#18** | P2 | GPU-capable runner for godot/bevy testing | Infrastructure provisioning. |

---

## 4. Priority Roadmap for OpenCode

### Priority 1: #102 Close-out (Code & Policy)
1. **HR-F18 (Bare Queue Discipline)**:
   - Audit seat bash maps in `fleet/fleet.yaml` and `fleet/command-effects/` to check whether bare `rig queue list`, `rig queue create` (without `--json --verify`), and bare `rig send` should be explicitly denied or warned.
   - If principal approves denying bare forms in seat maps: update `fleet/fleet.yaml`, regenerate via `python3 scripts/generate-rigs.py`, verify 35/35 green.
2. **HR-2.5 & Upstream Reports**:
   - Confirm `rig spec validate` covers `rig.all-51.yaml` (already verified by V3/V18).
   - Document or submit upstream report for DAG cycle checks if authorized.
3. **Dangling Skill Reference**:
   - Address `superpowers:writing-skills` ref in `specs/agents/_shared/skills/test-driven-development/writing-good-tests.md` via fleet vendor patch or upstream PR.

### Priority 2: #107 OpenRig 0.7.2 Identity Integration (Upstream #1860)
- In `@openrig/cli@0.7.2`, `rig mcp serve --http` introduces per-seat bearer-token grants.
- Evaluate adopting this primitive for MCP communications to close the F9 / `OPENRIG_SESSION_NAME` provenance gap.

### Priority 3: Fleet Host Proofs (When Operating on Live Host)
- **#96 Live Check**: Run `python3 scripts/seed-rig.py rigs/<rig>/rig.yaml --refresh-policy-only` on a running seat with a tightened rule and verify immediate denial on the next turn.
- **#91 Live Proof**: Verify `pytest tests/rag`, `go build ./...`, `cmake -S . -B build` execute cleanly in-seat.
- **#12 D1–D4 Proof**: Execute end-to-end engine compile and ELAPSED clocking in-seat.
- **#74 Host Provisioning**: Install `playwright-mcp`, `chrome-devtools-mcp`, `r2mcp`, and system packages `r2`/`rabin2`/`tshark`.

---

## 5. Standard Operating Discipline

> [!IMPORTANT]
> **The One Rule**: Never hand-edit `specs/`, `rigs/`, `rosters/`, or `registry/`.
> Edit `fleet/fleet.yaml`, `fleet/mcp-servers.yaml`, `fleet/skill-patches/`, or `scripts/`, then regenerate:
> ```bash
> python3 ./scripts/generate-rigs.py
> ./scripts/verify-rigs.sh --check-only     # Expect: 35 checks passed, 0 failed
> python3 ./scripts/audit_loop.py --self-test
> ```

- **Git Discipline**:
  - Always branch from `main` (`fix/...`, `feat/...`, `chore/...`).
  - Never push directly to `main`.
  - Never `--force` push.
  - One closing keyword per issue (`Closes #X, closes #Y`). Use `Refs #Z` for issues that stay open.
  - When committing generator changes, commit source changes first, then run `python3 scripts/generate-rigs.py` on the clean tree to bake provenance (`resolvedCommit`), and commit the regenerated leaves in a separate chore commit.
- **Secrets Rule**:
  - Keys live strictly in `~/.config/heretek-rigs/secrets/` (0700/0600). Never print, log, or commit secret values. Always use dummy keys in scratch/tests.
