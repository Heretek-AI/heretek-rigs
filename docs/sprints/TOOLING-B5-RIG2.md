# Tooling Batch B5 — Rig 2 (fullstack-and-web-studio)

**Slice:** Workstream B, batch B5 · **Branch:** `feat/self-rig2-tooling` (worktree `heretek-rigs-self-b5`)
**Date:** 2026-10-20 · **Source:** Issue #14 rows 7–17 vs `fleet/mcp-servers.yaml` (20 servers) + `fleet/skills-lock.json` (64 skills) + Rig-2 seat records in `fleet/fleet.yaml`
**Status:** Zero-change batch, regen + `verify-rigs.sh --check-only` **22/0**. UNCOMMITTED, no push. Live-seat proof deferred (fleet down).

Every row 7–17 is accounted below. Net catalog/fleet change: **none** — all items resolve to ALREADY PRESENT, license/pin-barred, ill-fitting, DEFERRED with a named blocker, or INFORMATIONAL (no fleet mechanism). B2/B3 honest zero-change precedent applies; per the task envelope, no changes are forced.

## Row-by-row diff (#14 rows 7–17 vs in-tree state)

| #14 item | In-tree state | Decision |
|---|---|---|
| Row 7 `ts-node-fullstack`: `pi-mcp-adapter@5.4.0` | Exists on npm (MIT, B4-re-verified pattern) | DEFERRED — pi-extension follow-up batch (§Deferred) |
| Row 7: `Neon` (MCP col) | No `neon` server in catalog | EXCLUDED — no-pin-no-add: #14 states "Neon" with no MCP pin (B1 same verdict). Noted: npm `mcp-server-neon@0.0.1` is an unknown-provenance squat, not an adoptable pin |
| Row 7: `pgai` | No `pgai` entry anywhere | DROPPED — archived upstream, Neon is its stated successor (B1 same verdict) |
| Row 7: `Sentry MCP` | No `sentry` MCP in catalog | EXCLUDED — FSL-1.1 (re-verified 2026-10-20: `getsentry/sentry-mcp` resolves to `getsentry/toolkit`, LICENSE.md opens "Functional Source License, Version 1.1, Apache 2.0 Future License"). Fails the MIT/Apache-2.0 bar (B1/B2/B3/B4 same verdict, re-verified not assumed) |
| Row 7: `prisma` + `supabase` skills (MIT) | Neither `prisma` nor `supabase` is a vendored source; `pins` dict in `scripts/generate-rigs.py` carries only heretek-crew/superpowers/tob/sentry/anthropic/vercel | DEFERRED — new vendor source needs generator `pins`-dict surgery + new pinned clone (B1 same verdict). Follow-up batch |
| Row 7: Biome + `tsgo`/TS7 (OSS col) | No fleet mechanism pins seat-executed CLI/toolchain versions | INFORMATIONAL — no action |
| Row 8 `python-backend-spec`: `Neon`, `Sentry MCP Oct 1 2026` | As row 7 | EXCLUDED (both) — same grounds, re-verified above |
| Row 8: `sentry-for-ai` (MIT) | Vendored `getsentry/skills@f57ada2`; seat binds systematic-debugging/tdd/modern-python/property-based-testing, no sentry skill | NO ACTION — ill-fitting: vendored sentry skills are `find-bugs`, `security-review`, `document-api-endpoint`, `gha-security-review`, `skill-scanner` (plus Django-specific `django-access-review`/`django-perf-review`, wrong framework for a FastAPI charter). Binding an ill-fitting skill is token noise, not leverage (B1 incident-response precedent) |
| Row 8: FastAPI `0.150.0` + Ruff + `uv` (OSS col) | No version-pin mechanism | INFORMATIONAL — no new execution grant in a minimal batch |
| Row 9 `go-backend-eng`: `pi-lens` | Exists on npm (MIT) | DEFERRED — extensions batch |
| Row 9: `GCP managed` (MCP col) | No `gcp` server in catalog; #14 states console-managed, no MCP/pin | NOTHING TO ADD (B1 same verdict) |
| Row 9: `Grafana v2.0.2` | No `grafana` server in this branch's catalog — B1 added `oci:docker.io/grafana/mcp-grafana:2.0.2` (Apache-2.0) on `feat/self-rig5-tooling`, unmerged | DEFERRED — binding here without the catalog entry fails verify; duplicating B1's entry guarantees a merge conflict. After B1 merges, a follow-up may bind `grafana` to `go-backend-eng`/`fe-perf-eng` if a charter need is shown (B2 precedent). Prefer deferral per task envelope |
| Row 9: `vercel-labs` (MIT) | Vendored `vercel-labs/agent-skills@063bee9` exposes only frontend skills (`react-best-practices`, `web-design-guidelines`, etc.); none fits a Go-service charter | NO ACTION — ill-fitting |
| Row 9: Gin (OSS col, MIT) | No version-pin mechanism | INFORMATIONAL |
| Row 10 `java-kotlin-eng`: `pi-subagents` | Second delegation path | EXCLUDED — verify gate HR-6.2 bans `pi-subagents` (B1/B2/B3/B4 same verdict; gate re-confirmed in `scripts/verify-rigs.sh`) |
| Row 10: `SonarQube 1.29.0` | No `sonarqube` server in catalog; #14 marks it DNP | DROPPED — re-verified 2026-10-20: `github.com/SonarSource/sonarqube-mcp` → 404 (B1/B3 same verdict, re-verified) |
| Row 10: `trailofbits:java` | Vendored `trailofbits/skills@5c99c03` contains **no Java skill** (checked: plugins list has `modern-cpp`, `modern-python`, `c-review`, `rust-review`, no `java-*`) | NO ACTION — no vendored fit; nothing to bind |
| Row 10: Spring Boot (OSS col, Apache-2.0) | No version-pin mechanism | INFORMATIONAL |
| Row 11 `ui-ux-designer`: `pi-lens@4.4.4`, `pi-btw@0.8.0` | Both exist on npm (MIT) | DEFERRED — extensions batch |
| Row 11: `Figma MCP` | No `figma` server in catalog; #14 directs to the official remote (OAuth, no pin) | EXCLUDED — re-verified 2026-10-20: `@figma/mcp` → 404 on npm; remote-OAuth surface out for a minimal batch (B4 same verdict, re-verified) |
| Row 11: `vercel-labs:design` | Seat **already binds** `web-design-guidelines` (vercel) + `frontend-design` (anthropic) | ALREADY PRESENT — no action |
| Row 11: Tailwind v4 (OSS col, MIT) | No version-pin mechanism; seat already carries heretek-crew `tailwind-ui` | INFORMATIONAL — covered at charter level |
| Row 12 `design-system-eng`: `pi-lens@4.4.4` + `pi-mcp-adapter` | Both exist on npm (MIT) | DEFERRED — extensions batch |
| Row 12: `Figma MCP` | As row 11 | EXCLUDED — same grounds |
| Row 12: `mattpocock/skills` | **Not vendored** — absent from `pins` dict and `skills-lock.json` | DEFERRED — needs generator surgery + new pinned clone; out of minimal-batch scope (B4 row-6 same verdict) |
| Row 12: Storybook `10.4` (OSS col, MIT 2026-05-14) | No version-pin mechanism; seat carries heretek-crew `storybook-component-tokenization` | INFORMATIONAL — #14 itself flags it stale (May 2026) |
| Row 13 `fe-perf-eng`: `pi-lens@4.4.4`, observability | Exists on npm (MIT) | DEFERRED — extensions batch |
| Row 13: `Sentry`, `Grafana v2.0.2` | Sentry FSL-1.1 (re-verified above); Grafana B1-unmerged (row 9) | EXCLUDED + DEFERRED — same grounds |
| Row 13: `sentry-for-ai` (MIT) | Vendored; seat binds `react-best-practices` + role-local `core-web-vitals-profiling`, no sentry skill | NO ACTION — ill-fitting: no vendored sentry skill addresses Web-Vitals/Lighthouse perf profiling (`triage-frontend-issues` is issue-triage, not perf). Same token-noise bar as row 8 |
| Row 13: Lighthouse `13.5.0` (OSS col, Apache-2.0) | No version-pin mechanism; seat already binds `chrome-devtools` MCP (whose description covers "Lighthouse-style audits") | INFORMATIONAL — covered at tooling level |
| Row 14 `a11y-specialist`: `pi-btw@0.8.0` | Exists on npm (MIT) | DEFERRED — extensions batch |
| Row 14: `Playwright MCP` | Catalog `playwright` (Apache-2.0, run-verified) **bound to this seat** | ALREADY PRESENT — no action |
| Row 14: `anthropics/skills:a11y` | Vendored `anthropics/skills@dbd4588` exposes `doc-coauthoring`, `frontend-design`, `webapp-testing`, `brand-guidelines`, etc. — **no accessibility/a11y skill** | NO ACTION — no vendored fit; seat carries role-local `wcag-axe-audit-automation` |
| Row 14: `axe-core` (OSS col, MPL-2.0) | No version-pin mechanism; covered by the role-local skill above | INFORMATIONAL |
| Row 15 `mobile-web-eng`: `pi-web-access@0.42.0` | Exists on npm (MIT; B4 notes latest is now `0.43.0` — extensions batch's freshness item) | DEFERRED — extensions batch |
| Row 15: `Playwright MCP` | Catalog `playwright` + `chrome-devtools` **both bound to this seat** | ALREADY PRESENT — no action |
| Row 15: `vercel-labs` (MIT) | Seat **already binds** `web-design-guidelines` (vercel) | ALREADY PRESENT — no action |
| Row 15: Lighthouse `13.5.0` + Workbox (OSS col) | No version-pin mechanism | INFORMATIONAL |
| Row 16 `brand-copy-spec`: `pi-btw@0.8.0` | Exists on npm (MIT) | DEFERRED — extensions batch |
| Row 16: `Notion`, `Slack GA` (MCP col) | Neither in catalog; #14 states no pins (both remote OAuth surfaces) | EXCLUDED — no-pin-no-add. Re-verified 2026-10-20: `@linear/mcp-server` → 404 (same remote-surface class); `@notionhq/notion-mcp-server` exists (`2.5.2`) but is NOT adopted here — no #14 pin (B4 row-2 precedent) |
| Row 16: `superpowers:writing` | Vendored `obra/superpowers@bb92a77` contains **no bare `writing` skill** (checked: `writing-plans`, `writing-skills` exist; neither is the #14-named item, and neither fits a microcopy charter without forcing) | NO ACTION — no vendored fit for the named item; not forcing a near-miss binding |
| Row 16: Vale + Docusaurus (OSS col) | No version-pin mechanism | INFORMATIONAL |
| Row 17 `ux-research-analyst`: `pi-lens@4.4.4` | Exists on npm (MIT) | DEFERRED — extensions batch |
| Row 17: `Figma`, `PostHog` (MCP col) | Neither in catalog; #14 states no pins; upstream `PostHog/mcp` archived per B1 | EXCLUDED — no-pin-no-add + archived upstream (B1 row-36 same verdict) |
| Row 17: `skills.sh` catalog | Reference catalog, no vendoring mechanism exists | NOTED — no action (B1 row-36 same verdict) |
| Row 17: ClickHouse `v26.9` + PostHog (OSS col) | `mcp-clickhouse==0.7.0` (Apache-2.0) already in catalog but **not bound** to this seat (seat binds `duckdb` + `github-issues`) | NO ACTION — adding a `clickhouse` binding (with `required_secrets`) is a data-access widening without a shown charter need; fails the minimal-batch bar and the prefer-deferral rule. Service version `v26.9` itself has no fleet pin mechanism |
| Cross-row: `context7` 4.4.2 → 4.4.4 | Catalog pins `npm:@upstash/context7-mcp@4.4.2`; npm `latest` re-verified `4.4.4` 2026-10-20; `memory` 1.0.0→2.0.0 likewise confirmed `latest` = 2.0.0 | DEFERRED — B4 explicitly queued `context7` for "a future Rig-2 batch or a dedicated catalog batch," but its 6 consumers span 4 rigs (`ai-red-teamer`, `go-backend-eng`, `python-backend-spec`, `rust-systems-spec`, `system-architect`, `ts-node-fullstack`), so a bump here is a cross-rig catalog change, not a per-rig batch change (Workstream B batch rule). Belongs to a dedicated catalog batch with its own freshness re-check. `memory` 2.0.0 is B4's adopted pin — not duplicated here |

## What was added

None. Zero catalog, script, or seat-content change. The regen diff is 16 registry files of pure provenance relag (`resolvedCommit` `e8577db` → `88c13d7`, the known per-merge convention) plus this ledger — the B2/B3 zero-change shape.

## Deferred with named blockers (not started here)

- **Pi-extension batch** (all #14 pins in rows 7–17: `pi-mcp-adapter@5.4.0`, `pi-lens@4.4.4`, `pi-btw@0.8.0`, `pi-web-access@0.42.0` + B4's freshness note that `pi-web-access` latest is `0.43.0`): every pin verified to exist on npm, all MIT. NOT adopted here — B2/B3/B4 deferred a dedicated per-seat extension batch, and B5 must coordinate by not duplicating it.
- **Grafana binding to Rig-2 seats** (`go-backend-eng`, `fe-perf-eng`): blocked on B1 (`feat/self-rig5-tooling`) merging first — B1 owns the `grafana` catalog entry. A follow-up may bind it with a stated charter need.
- **New vendor sources** (`prisma/skills`, `supabase` skills, `mattpocock/skills`): each needs generator `pins`-dict surgery + a new pinned clone. Follow-up batch (B1/B4 precedent).
- **`context7` 4.4.2→4.4.4 catalog bump**: dedicated catalog batch (cross-rig blast radius, freshness re-check at merge).
- **OSS/service version pins** (Biome, tsgo/TS7, FastAPI 0.150.0, Ruff, uv, Gin, Spring Boot, Tailwind v4, Storybook 10.4, Lighthouse 13.5.0, axe-core, Vale, Docusaurus, ClickHouse v26.9, PostHog, Workbox): no fleet mechanism pins them (`sidecar_profiles` are labels; `bash_allow` is a capability grant, not a version pin, and this batch grants no new execution). Recorded informational.

## Regen + verify evidence

- Tree was clean at start (`git status` empty on `feat/self-rig2-tooling` @ `88c13d7`); regen ran **without** `ALLOW_DIRTY` (clean-tree regen, no stated reason needed).
- Generator: `python3 ./scripts/generate-rigs.py --vendor-dir <main-checkout>/.scratch/vendor --crew-source <heretek-crew-checkout>` → "wrote 51 specialist AgentSpecs, 64 shared skills, 8 RigBundles…". Vendor SHAs matched pins (`bb92a77`, `5c99c03`, `f57ada2`, `dbd4588`, `063bee9`; Heretek-Crew `0b41346` = allowed alternate). No new vendor sources introduced.
- Regen diff: **16 files, +24/−24** — registry entries + views only, every hunk the `resolvedCommit` relag. Zero hand-edits to generated leaves; `fleet/` and `scripts/` untouched.
- `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 22 checks passed, 0 failed**, incl. "All 20 MCP servers … verified (pinned, command-backed secrets)".
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- `git status`: the 16 regen files above + this ledger. No A-slice or B1–B4 files touched; no secrets/values; no machine-local paths in this ledger (placeholders only).

## Deferred live proof (fleet down)

Not run: `seed-rig.py` for `fullstack-and-web-studio`, any skill/MCP smoke beyond dry verification. Nothing to smoke — zero content change. Required before merge: freshness re-check of the deferred pins (pins rot; today's `latest` values are dated in this ledger for that purpose).
