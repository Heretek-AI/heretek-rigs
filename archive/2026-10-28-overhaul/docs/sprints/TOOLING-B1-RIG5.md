# Tooling Batch B1 — Rig 5 (cloud-sre-and-data-platform)

**Slice:** Workstream B, batch B1 · **Branch:** `feat/self-rig5-tooling` (worktree `heretek-rigs-self-b1`)
**Date:** 2026-10-20 · **Source:** Issue #14 rows 28–38 vs `fleet/mcp-servers.yaml` (20 servers) + `fleet/skills-lock.json` (64 skills)
**Status:** Implemented, regen + `verify-rigs.sh --check-only` **22/0**. UNCOMMITTED, no push. Live-seat proof deferred (fleet down).

## What was already present (no action)

| #14 item | In-tree state |
|---|---|
| Row 29 `kubernetes-mcp 0.0.67` (Apache-2.0) | Present in catalog, bound to `k8s-orchestrator` |
| Row 30 `tob` skills (supply-chain) | Vendored `trailofbits/skills@5c99c03`; `supply-chain-risk-auditor` already bound to `dependency-patcher` |
| Row 28 `superpowers` (MIT) | Vendored `obra/superpowers@bb92a77` (12 skills in lock) |
| Rows 31/32 `sentry-for-ai` skills (MIT) | Vendored `getsentry/skills@f57ada2` (5 skills in lock: `find-bugs`, `security-review`, `document-api-endpoint`, `gha-security-review`, `skill-scanner`). No new seat binding: no vendored skill is a fit for incident-response charters; binding an ill-fitting skill would be token noise, not leverage. |
| Row 34 `vercel-labs` (MIT) | Vendored `vercel-labs/agent-skills@063bee9` |
| Row 37 `anthropics/skills` (Apache-2.0) | Vendored `anthropics/skills@dbd4588` |
| Rows 33/38 `postgres`, `qdrant`; row 35 `duckdb`; row 36 `clickhouse`; rows 31/32 `prometheus`; row 28 `aws`+`terraform`; row 34 `redis`; all rows `codebase-memory` | All present in catalog and already bound to the recommending seats |

## What was added (2 catalog/binding changes, both #14-traceable)

1. **`grafana` MCP server → catalog + bound to `sre-incident-eng`, `observability-eng`, `analytics-metrics-eng`** (rows 31, 32, 36).
   - Pin `oci:docker.io/grafana/mcp-grafana:2.0.2`, Apache-2.0, `status: registry-verified`. Verified live 2026-10-20: tag `v2.0.2` exists on GitHub releases, Docker Hub tag `2.0.2` published 2026-10-10, repo license Apache-2.0, not archived.
   - License honesty: only the **client** (`mcp-grafana`, Apache-2.0) ships; the Grafana **server** stays AGPL-3.0 and is neither shipped nor redistributed — noted in the catalog entry.
   - Secrets follow the existing `!cat` pattern (`GRAFANA_URL`←`grafana.url`, `GRAFANA_SERVICE_ACCOUNT_TOKEN`←`grafana.token`, `required_secrets`, fail-closed). No values in repo. Operator must create the two secret files before seeding, else strict seed refuses / `--allow-missing-secrets` renders the server `enabled: false`.
   - Docker transport passes `-e GRAFANA_URL -e GRAFANA_SERVICE_ACCOUNT_TOKEN` (container would not otherwise inherit Pi-spawned env); matches the existing `terraform` docker precedent.
2. **`dependency-patcher` pi_packages bump** (row 30): `pi-lsp-extension@1.4.0` → `@narumitw/pi-lsp@0.49.10`, `pi-ast-grep@0.1.0` → `@nicknisi/pi-ast-grep@0.3.1`. Both pins verified live on npm 2026-10-20 (both are also `latest`), both MIT. All other 20 stale seats left untouched — per-rig batch scope.
   - Required companion fix in `scripts/render-seat.py`: the `has_ast_lsp` allowlist was keyed on the legacy bare names (`pi-lsp-extension`, `pi-ast-grep`), so the renamed scoped packages silently dropped the seat's 9 read-only AST/LSP tool allows from rendered permissions. Extended the prefix tuple with `@narumitw/pi-lsp` + `@nicknisi/pi-ast-grep`; regen diff now shows only the pin change with allows intact. Caught by diffing rendered output, not by verify (no gate covers per-tool completeness) — recorded here as the audit trail.

## What was dropped/excluded, with reason

- **Sentry MCP 0.42.0 (rows 31/32):** EXCLUDED — FSL-1.1 per #14's own correction; fails the MIT/Apache-2.0 license-clean bar. Covered instead by vendored Sentry skills + prometheus/grafana.
- **SonarQube (row 30):** DROPPED — #14 marks it DNP (404). Agree.
- **Snyk 1.1308.1 (row 30):** EXCLUDED — the pin is not an MCP-server pin (IDE-extension/CLI numbering) and no verifiable MIT/Apache-2.0 MCP distribution exists at a stated pin. Proprietary-vendor auth surface; out for a minimal batch.
- **Azure `@azure/mcp@4.0.0-beta.1` (rows 28/29/37):** EXCLUDED — beta-only tag on an archived-predecessor lineage; broad Azure credential surface unverifiable in a minimal batch.
- **GCP managed (rows 28/29/34/35/37):** NOTHING TO ADD — console-managed, no MCP/pin in #14.
- **Neon remote (rows 33/34/35/38):** EXCLUDED — #14 states no pin ("Neon remote" only); rule is no-pin-no-add. Follow-up batch should verify `@neondatabase/mcp-server-neon` (npm latest 0.6.5, MIT, verified to exist 2026-10-20 but NOT adopted here since #14 states no pin) + `NEON_API_KEY` secret wiring.
- **pgai (rows 33/38):** DROPPED — archived upstream per #14; Neon is its stated successor (see above).
- **PostHog (row 36):** EXCLUDED — no stated pin, and upstream `PostHog/mcp` is MIT but **archived**. Double grounds.
- **`prisma/skills`, `supabase` skills (rows 33/35/38):** DEFERRED — new vendor sources would require generator `pins`-dict surgery + new pinned clones; out of minimal-batch scope. Follow-up batch.
- **`skills.sh` catalog (row 36):** NOTED — catalog reference, no vendoring mechanism exists. No action.
- **Pi extensions `pi-mcp-adapter`, `pi-lens@4.4.4`, `@langfuse/pi-observability-plugin@0.1.2`, `@langchain/langsmith-pi-extension@0.2.1`, `@postman/postman-plugin@0.3.0` (rows 28–38):** DEFERRED — `pi_packages` is a valid mechanism but each needs individual pin/license verification; follow-up per-seat batch. **`pi-subagents` explicitly NOT added** — banned by verify gate HR-6.2 (rejected second delegation path).
- **OSS service pins (OpenTofu 1.13.1, K8s 1.34.12, Helm 4.3.1, ArgoCD 3.5.5, Prometheus 3.15.0, Grafana server 12.4.12, OTel 0.163, Trivy 0.76.0, Syft, Postgres 18, Kafka, DuckDB, dbt, ClickHouse 26.9, vLLM, Ollama 0.40.6, Qdrant 1.19.2):** NOT ACTIONABLE — no fleet mechanism pins service versions (`sidecar_profiles` are labels; `compose-sidecars.sh` carries no versions). Recorded as informational. Freshness: #14's own wave-2/3 notes already supersede DuckDB 1.4.5→1.5.6, Kafka 4.3.1→4.4.0, Grafana 12.4.12→13.2.4; re-check at PR merge time per program plan §4.
- **Stale in-tree pins flagged by #14 but outside rows 28–38** (`context7` 4.4.2→4.4.4, `memory` 1.0.0→2.0.0): OUT OF SCOPE for B1 (other rigs' batches).

## Regen + verify evidence

- Generator (dirty-tree dev iteration, AGENTS.md-sanctioned): `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py --vendor-dir <main>/.scratch/vendor --crew-source <path-to-Heretek-Crew-checkout>` → success ("wrote 51 specialist AgentSpecs…").
- Vendor SHAs matched pins (`bb92a77`, `5c99c03`, `f57ada2`, `dbd4588`, `063bee9`; Heretek-Crew `0b41346` = allowed alternate). No new vendor sources introduced, so no generator surgery was needed.
- `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 22 checks passed, 0 failed**, including "All 21 MCP servers … verified (pinned, command-backed secrets)".
- Render proof: `sre-incident-eng` mcp.json → `[grafana, prometheus]`; `observability-eng` → `[codebase-memory, grafana, prometheus]`; `analytics-metrics-eng` → `[clickhouse, codebase-memory, grafana]`; `dependency-patcher` policy-enforcement.json carries `@narumitw/pi-lsp@0.49.10` + `@nicknisi/pi-ast-grep@0.3.1`.
- `git status`: ONLY `fleet/mcp-servers.yaml`, `fleet/fleet.yaml`, `scripts/render-seat.py` (AST/LSP allowlist fix above), regen outputs (4 seats × specs+rigs+omni copies, 2 bundle.yaml, registry entries/views relag incl. known `resolvedCommit` → HEAD convention), plus this ledger. No hand-edits to generated leaves; no A1–A4 files touched; no secrets/values in any file.

## Deferred live proof (fleet down)

Not run: `seed-rig.py` for `cloud-sre-and-data-platform` (needs operator-created `grafana.url`/`grafana.token` secrets + relaunched fleet), `pi mcp list --json` grafana connectivity, dashboard-query smoke test. Required before merge: freshness re-check of the `2.0.2` pin + secret-file creation + seed dry-run.
