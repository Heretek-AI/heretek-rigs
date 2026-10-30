# Provisioning Matrix — issue #74 existence gate (provisioning-gate-74)

Status: gate landed, issue #74 stays OPEN until every row below is
provisioned-or-documented on every host that renders seats.

Scope: all 20 command-bearing catalog servers (`fleet/mcp-servers.yaml`)
plus bash-grant binaries B1–B3 (`fleet/fleet.yaml` binary-reverse-eng
grants). `github` (remote-http, no command) is the documented exclusion
accounting 20-vs-21 (REQ-P4).

Gate behavior (REQ-P1/P2): `scripts/render-seat.py` + `scripts/seed-rig.py`
resolve each artifact read-only (`shutil.which` + path-exists — no installs,
no pulls, no network). Unresolvable entries render `enabled:false` (MCP) or
keep the allow with a loud warn (bash) AND always emit a stderr warn naming
seat, server/grant, and artifact. Silent degradation is forbidden.
`scripts/live-health.py` carries the WARN-first `tool-provisioning`
sub-check (`0 missing tools` when clean). The verify block V16 asserts the
gate strings and red-proofs both directions.

How to re-check on any host:

- `python3 scripts/live-health.py --fixture-dir <dir>` (WARN-first) or live
  against the daemon.
- Render any seat: missing artifacts appear as
  `warn: <seat>: <server> disabled, missing tool artifact: <artifact>`.
- `HERETEK_TOOLS=<dir> PATH=<bin> ./scripts/verify-rigs.sh --check-only`
  (V16 red-proofs both directions with stub binaries).

Host snapshot below was taken 2026-10-25 on the implementor host
(`$HERETEK_TOOLS` default `~/.local/share/heretek-rigs/tools`). State varies
per host by design — the gate resolves with the PATH/`$TOOLS` the seat will
see, and this table must be re-taken per host (never treated as global truth).

Known shallow-presence caveat (recorded follow-up, NOT this change):
`uvx`/`docker` PRESENT below means the launcher binary resolves, not that
the pinned package (`uvx --from …`) or image (`docker image inspect …`) is
available. Deep probes need network/pulls and are explicitly out of scope.

## MCP servers (20 command-bearing; github excluded)

| # | server | pin | required artifact | bound roles (count) | host state 2026-10-25 |
|---|--------|-----|-------------------|---------------------|-----------------------|
| 1 | codebase-memory | npm:codebase-memory-mcp@0.12.1 | `@TOOLS@/mcp/node_modules/.bin/codebase-memory-mcp` | 31 roles (ai-red-teamer, analytics-metrics-eng, android-mobile-spec, appsec-engineer, cloud-platform-eng, cloud-sec-auditor, cpp-lowlevel-eng, data-pipeline-eng, dba-specialist, dependency-patcher, design-system-eng, engine-systems-eng, game-ai-dev, game-systems-dev, git-drift-coord, go-backend-eng, graphics-shader-eng, ios-mobile-spec, java-kotlin-eng, load-stress-tester, observability-eng, physics-sim-eng, python-backend-spec, rust-systems-spec, sabotage-qa-tester, static-analysis-lead, system-architect, tech-docs-lead, threat-modeler, ts-node-fullstack, vector-rag-spec) | PRESENT |
| 2 | context7 | npm:@upstash/context7-mcp@4.4.4 | `@TOOLS@/mcp/node_modules/.bin/context7-mcp` | 6 roles (ai-red-teamer, go-backend-eng, python-backend-spec, rust-systems-spec, system-architect, ts-node-fullstack) | PRESENT |
| 3 | memory | npm:@modelcontextprotocol/server-memory@2.0.0 | `@TOOLS@/mcp/node_modules/.bin/mcp-server-memory` | 3 roles (exec-director, product-director, tpm-scrum-lead) | MISSING |
| 4 | playwright | npm:@playwright/mcp@0.0.83 | `@TOOLS@/mcp/node_modules/.bin/playwright-mcp` | 5 roles (a11y-specialist, e2e-browser-qa, fe-perf-eng, mobile-web-eng, ui-ux-designer) | MISSING |
| 5 | chrome-devtools | npm:chrome-devtools-mcp@1.11.0 | `@TOOLS@/mcp/node_modules/.bin/chrome-devtools-mcp` | 6 roles (a11y-specialist, design-system-eng, e2e-browser-qa, fe-perf-eng, mobile-web-eng, ui-ux-designer) | MISSING |
| 6 | mobile | npm:@mobilenext/mobile-mcp@1.0.12 | `@TOOLS@/mcp/node_modules/.bin/mcp-server-mobile` | 1 role (android-mobile-spec) | MISSING |
| 7 | openapi | npm:mcp-openapi-schema-explorer@1.3.5 | `@TOOLS@/mcp/node_modules/.bin/mcp-openapi-schema-explorer` | 1 role (api-contract-tester) | MISSING |
| 8 | semgrep | pypi:semgrep==1.181.0 (`semgrep mcp`) | `uvx` on PATH | 2 roles (appsec-engineer, static-analysis-lead) | PRESENT (launcher only; package probe is follow-up) |
| 9 | radare2 | git:https://github.com/radareorg/radare2-mcp@1.9.0 | `@TOOLS@/bin/r2mcp` | 2 roles (binary-reverse-eng, firmware-sec-analyst) | MISSING |
| 10 | aws | pypi:awslabs.aws-api-mcp-server==1.5.6 | `uvx` on PATH | 2 roles (cloud-platform-eng, cloud-sec-auditor) | PRESENT (launcher only) |
| 11 | duckdb | pypi:mcp-server-motherduck==1.1.0 | `uvx` on PATH | 2 roles (data-pipeline-eng, ux-research-analyst) | PRESENT (launcher only) |
| 12 | postgres | pypi:postgres-mcp==0.3.0 | `uvx` on PATH | 1 role (dba-specialist) | PRESENT (launcher only) |
| 13 | kubernetes | npm:kubernetes-mcp-server@0.0.67 | `@TOOLS@/mcp/node_modules/.bin/kubernetes-mcp-server` | 1 role (k8s-orchestrator) | MISSING |
| 14 | k6 | pypi:k6-mcp-server==2.2.0 | `uvx` on PATH | 1 role (load-stress-tester) | PRESENT (launcher only) |
| 15 | qdrant | pypi:mcp-server-qdrant==0.8.1 | `uvx` on PATH | 1 role (vector-rag-spec) | PRESENT (launcher only) |
| 16 | prometheus | pypi:prometheus-mcp-server==1.6.2 | `uvx` on PATH | 2 roles (observability-eng, sre-incident-eng) | PRESENT (launcher only) |
| 17 | grafana | oci:docker.io/grafana/mcp-grafana:2.0.2 | `docker` on PATH | 4 roles (analytics-metrics-eng, load-stress-tester, observability-eng, sre-incident-eng) | PRESENT (launcher only; image probe is follow-up) |
| 18 | clickhouse | pypi:mcp-clickhouse==0.7.0 | `uvx` on PATH | 1 role (analytics-metrics-eng) | PRESENT (launcher only) |
| 19 | redis | pypi:redis-mcp-server==0.5.1 | `uvx` on PATH | 1 role (cache-streaming-eng) | PRESENT (launcher only) |
| 20 | terraform | oci:docker.io/hashicorp/terraform-mcp-server:1.0.0 | `docker` on PATH | 1 role (cloud-platform-eng) | PRESENT (launcher only; image probe is follow-up) |

Excluded: `github` — remote-http transport, no command to resolve
(7 bound roles: compliance-auditor, exec-director, product-director,
release-qa-officer, threat-modeler, tpm-scrum-lead, ux-research-analyst).
Its gate remains the secrets path (`required_secrets: [github.pat]`).

## Bash-grant binaries B1–B3

| id | grant pattern | leading binary | bound role | host state 2026-10-25 |
|----|---------------|----------------|------------|-----------------------|
| B1 | `r2 -e cfg.sandbox=true -q*` | `r2` | binary-reverse-eng | MISSING |
| B2 | `rabin2*` | `rabin2` | binary-reverse-eng | MISSING |
| B3 | `tshark -r *` | `tshark` | binary-reverse-eng | MISSING |

## Follow-ups (explicitly NOT this change)

- `uvx --from` per-package and `docker image inspect` deep probes (need
  network/pulls; forbidden in verify).
- Provisioning the 7 missing npm artifacts + `r2mcp` + `r2`/`rabin2`/`tshark`
  on every host (host-mutating rollout, own change).
- Browser sufficiency probes (binary presence is necessary, not sufficient
  for playwright/chrome-devtools).

## Re-take 2026-10-30 — fleet-proofs Phase A (this host)

Measured on the fleet host (dev machine). Deltas vs the 2026-10-25 snapshot:

- B1 `r2` / B2 `rabin2` / B3 `tshark`: still MISSING (`command -v` rc=1).
  Installs NOT attempted: `sudo -n` requires a password (unattended apt
  impossible); `r2` needs universe-or-source build, `tshark` needs the
  interactive wireshark-common prompt. Named follow-ups: run with a tty
  (`sudo apt-get install -y --no-install-recommends tshark`,
  radare2 from source or universe) and re-take.
- Extra observation: `render-seat.py --dry-run` for
  `blue-appsec-engineer@defensive-sec-and-red-team` warns
  `bash grant 'trivy fs*' missing tool artifact: trivy` — `trivy` also
  MISSING on this host (needs the aquasecurity repo; follow-up, same
  sudo constraint).
- Build tools PRESENT: `go 1.27.3`, `pytest 9.1.1`, `cmake 4.3.0`,
  `bwrap 0.13.1`, `rig 0.7.5 (b57c4da3)`.
- Secrets finding (fixed same session): `github.pat` was `644`; hardened
  to `600` (`chmod`), re-statted `600`; dir `700`. Strict-mode compliant.
