# Tooling Batch B2 — Rig 6 (qa-and-verification-gauntlet)

**Slice:** Workstream B, batch B2 · **Branch:** `feat/self-rig6-tooling` (worktree `heretek-rigs-self-b2`)
**Date:** 2026-10-20 · **Source:** Issue #14 rows 39–43 vs `fleet/mcp-servers.yaml` (20 servers) + `fleet/skills-lock.json` (64 skills) + Rig 6 seat attachments in `fleet/fleet.yaml`
**Status:** Implemented, regen + `verify-rigs.sh --check-only` **22/0**. UNCOMMITTED, no push. Live-seat proof deferred (fleet down).
**Net catalog/fleet change: ZERO.** Every row 39–43 item is already present, excluded on license/pin grounds, or deferred with a named blocker. This ledger is the batch deliverable (precedent: B1 ledger `TOOLING-B1-RIG5.md`).

## Row-by-row diff (#14 rows 39–43 vs in-tree state)

| #14 item | In-tree state | Decision |
|---|---|---|
| Row 39 `release-qa-officer`: GitLab 19.5 + Linear (MCP col) | No `gitlab`/`linear` server in catalog. #14 states service/product names, **no MCP pin** | EXCLUDED — no-pin-no-add (see §Drop list) |
| Row 39: `superpowers:test-driven` | Vendored `test-driven-development` (obra/superpowers, MIT). Seat already binds heretek-crew `tdd` + superpowers `verification-before-completion` | NO ACTION — binding a second TDD skill is redundant token noise, not leverage |
| Row 39: Spectral + Playwright (OSS col) | No fleet mechanism pins OSS versions; seat's remit is sign-off, not execution | NO ACTION — recorded informational (§OSS pins) |
| Row 40 `e2e-browser-qa`: Playwright MCP | Catalog `playwright` @ `npm:@playwright/mcp@0.0.83`, Apache-2.0, run-verified; **bound to this seat** (+ `chrome-devtools`) | ALREADY PRESENT — no action. Freshness: 0.0.83 == npm `latest` as of 2026-10-20 |
| Row 40: `vercel-labs` skill | Vendored `vercel-labs/agent-skills` (MIT) exposes only `react-best-practices` + `web-design-guidelines`; seat already binds anthropic `webapp-testing` | NO ACTION — no vendored vercel-labs skill fits browser-automation; binding one would be ill-fitting (B1 §"no ill-fitting skill" precedent) |
| Row 40: Playwright (OSS col, MIT) | Seat `bash_allow` already has `npx playwright test*` / `show-trace*`; `tests/e2e/*` + `playwright.config.*` write paths present | ALREADY PRESENT — no action |
| Row 41 `api-contract-tester`: Neon fixtures | #14 states "Neon remote", **no pin** | EXCLUDED — no-pin-no-add (B1 same verdict) |
| Row 41: `trailofbits:api` | No `api`-named skill in the vendored `trailofbits/skills` set (closest: `document-api-endpoint`, sentry — **already bound** to this seat) | NO ACTION — no such vendored skill exists; seat already carries `openapi-contract-verification` (heretek-crew) + `document-api-endpoint` |
| Row 41: Spectral (OSS col, Apache-2.0) | Seat `bash_allow` already has `npx spectral lint*` (+ `newman`, `schemathesis`); `openapi` MCP bound | ALREADY PRESENT as CLI — no action. No Spectral MCP adopted (see §Drop list) |
| Row 42 `load-stress-tester`: Grafana (MCP col) | Grafana MCP exists only on the unmerged B1 branch, bound to Rig 5 seats | DEFERRED — binding post-B1-merge is a one-line follow-up; duplicating B1's catalog entry here would guarantee a merge conflict |
| Row 42: `superpowers` skill | Seat `shared: []`; candidate `test-driven-development` (superpowers) is a dev-workflow skill, not a load-testing skill | NO ACTION — ill-fitting by B1's own bar |
| Row 42: k6 v2.3.0 AGPL-3.0 | **EXCLUDED from defaults** — AGPL-3.0 per #14's own notes. Seat's pre-existing `k6` MCP + `k6 run*` bash binding left untouched (removal is a behavior change beyond batch scope) | EXCLUDED — recorded §k6. No license-clean load MCP exists in the current catalog; closest license-clean perf signal is `chrome-devtools` Lighthouse-style audits (Apache-2.0, already bound to `e2e-browser-qa`) |
| Row 43 `sabotage-qa-tester`: Sentry (MCP col) | Sentry MCP is FSL-1.1 per #14's correction | EXCLUDED — fails the MIT/Apache-2.0 bar (B1 same verdict). Covered by vendored `find-bugs`/`security-review` sentry skills where fitted |
| Row 43: `fuzzing` skill | Vendored tob fuzz skills are language-specific (`cargo-fuzz`, `libfuzzer` — Rust); seat is language-general adversarial with `mutation-testing` + `property-based-testing` (tob) already bound | NO ACTION — ill-fitting; seat already carries the fitting tob testing skills |
| Row 43: Stryker 9.x (OSS col, Apache-2.0) | Seat `bash_allow` already has `npx stryker run*` (+ `cargo mutants*`, `mutmut run*`); no fleet mechanism pins OSS versions | ALREADY PRESENT as CLI allowance — no action. Pin verified: 9.x exists (`9.6.1` latest in range); freshness note: `10.0.0` published 2026-08-14 supersedes #14's 9.x |
| Rows 39/43: `pi-subagents@0.79.2` | Banned second delegation path | EXCLUDED — verify gate HR-6.2 rejects `pi-subagents` (B1 same verdict) |
| Rows 40/41: `pi-web-access@0.42.0` | Not adopted anywhere in fleet | DEFERRED — pi extensions need individual pin/license verification per seat; follow-up batch. Freshness: npm `latest` is now `0.43.0` (2026-10-20), superseding #14's `0.42.0` |
| Row 43 seat stale `pi_packages` (`pi-lsp-extension@1.4.0`, `pi-ast-grep@0.1.0`) | Same staleness B1 fixed for `dependency-patcher` — but the companion fix (scoped-name allowlist in `scripts/render-seat.py`) lives on the unmerged B1 branch | DEFERRED with evidence: dry-run render of `sabotage-qa-tester` today carries the 9 AST/LSP allows via the legacy-name gate; bumping names without B1's fix would silently drop them. Follow-up after B1 merges |

## What was added

**Nothing.** No catalog server, binding, pin bump, or skill attachment met the bar of *missing + verifiable at a stated pin + license-clean + fitting*. A zero-change batch is the correct minimal-batch outcome here, not a failure to find work: five of the twelve recommendable items are already in-tree, and the rest fail a stated rule.

## Dropped/excluded, with verification evidence (all checks 2026-10-20 via npm registry)

- **Spectral MCP:** no stated pin in #14, and no verifiable distribution exists (`@stoplight/spectral-mcp` → 404 on npm). CLI path already allowed on `api-contract-tester`. DROP.
- **GitLab MCP / Linear MCP:** no stated pins in #14 (`@gitlab/mcp-server`, `@linear/mcp-server` → 404 on npm under those names). Remote OAuth surfaces in any case — out for a minimal batch. DROP.
- **Neon MCP:** no pin in #14 (B1 same verdict). DROP.
- **Sentry MCP:** FSL-1.1 license bar failure. DROP.
- **k6 as default tooling:** AGPL-3.0 license bar failure for defaults. Existing seat binding grandfathered, untouched. See §k6 record below.
- **OSS service/version pins** (GitLab 19.5, Stryker 9.x, Spectral, Playwright): NOT ACTIONABLE — no fleet mechanism pins OSS versions (`sidecar_profiles` are labels; no versioned service pins exist in `fleet/`). Recorded informational only.

## k6 exclusion record (row 42)

Per program plan license watch + #14's own "Grafana/k6 AGPL-3.0" note: k6 is **excluded from fleet defaults**. Concretely for this batch: (a) no k6 pin bump adopted (#14's `v2.3.0` would touch a grandfathered binding — out of scope); (b) no k6-equivalent added (nothing license-clean and load-shaped exists in the 20-server catalog); (c) the pre-existing `load-stress-tester → k6` MCP + `k6 run*` binding is left exactly as-is — removing working seat capability without a replacement would be a behavior regression, not a license fix. Closest license-clean perf signal in-catalog: `chrome-devtools` (Apache-2.0, Lighthouse-style audits), already bound to `e2e-browser-qa`. A license-clean load-generation follow-up (e.g. evaluating whether any MIT/Apache-2.0 load MCP exists at a verifiable pin) is noted, not started.

## Regen + verify evidence

- Tree was clean at start (`git status` empty on `feat/self-rig6-tooling` @ branch base); regen ran **without** `ALLOW_DIRTY` (no reason to state).
- Generator: `python3 ./scripts/generate-rigs.py --vendor-dir <main-checkout>/.scratch/vendor --crew-source <heretek-crew-checkout>` → "wrote 51 specialist AgentSpecs, 64 shared skills, 8 RigBundles…". Vendor SHAs unchanged; no new vendor sources introduced.
- Regen diff: **16 registry files only, pure provenance relag** (`resolvedCommit` e8577db→88c13d7 + matching `canonicalUrl`s) — the known per-merge convention, same shape as B1. Zero changes under `specs/`, `rigs/`, `rosters/`, or seat `mcp.json`/`behaviour` content.
- `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 22 checks passed, 0 failed**, incl. "All 20 MCP servers … verified (pinned, command-backed secrets)".
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- Render proof (dry-run, dummy secrets dir, no values read): `sabotage-qa-tester` permissions carry the 9 `READONLY_AST_LSP_TOOLS` allows — the evidence behind the pin-bump deferral above.
- `git status`: 16 relag files (regen output) + this ledger. No hand-edits to generated leaves; no A-slice or B1 files touched; no secrets/values; no machine-local paths in this ledger (placeholders only).

## Deferred live proof (fleet down)

Not run: `seed-rig.py` for `qa-and-verification-gauntlet`, `pi mcp list --json` connectivity, any e2e/spectral/stryker smoke run. Required before merge: freshness re-check of the verification claims above (pins rot; today's `latest` values are dated in this ledger for that purpose).
