# Tooling Batch B4 — Rig 1 (executive-and-architecture)

**Slice:** Workstream B, batch B4 · **Branch:** `feat/self-rig1-tooling` (worktree `heretek-rigs-self-b4`)
**Date:** 2026-10-20 · **Source:** Issue #14 rows 1–6 vs `fleet/mcp-servers.yaml` (20 servers) + `fleet/skills-lock.json` (64 skills) + Rig-1 seat attachments in `fleet/fleet.yaml`
**Status:** Implemented, regen + `verify-rigs.sh --check-only` **22/0**. UNCOMMITTED, no push. Live-seat proof deferred (fleet down).
**Net catalog/fleet change: 3 lines** (1 MCP pin bump + 2 shared-skill bindings). Everything else in rows 1–6 is already present, excluded on license/pin/auth-model grounds, deferred with a named blocker, or informational (no fleet mechanism).

## Row-by-row diff (#14 rows 1–6 vs in-tree state)

| #14 item | In-tree state | Decision |
|---|---|---|
| Row 1 `exec-director`: `@narumitw/pi-plan-mode@0.59.4`, `@narumitw/pi-usage@0.67.0` | Both exist on npm (verified 2026-10-20, MIT) | DEFERRED — pi-extensions follow-up batch (B2/B3 precedent; §Extensions) |
| Row 1: `memory 2.0.0 MIT ADOPT-ready (server-memory 1.0.0→2.0.0 queued)` | Catalog pins `npm:@modelcontextprotocol/server-memory@1.0.0` | **ADOPTED — bumped to `2.0.0`** (§Added). All 3 consumers are Rig-1 seats, so blast radius is contained to this batch |
| Row 1: `github remote` | Catalog `github` (MIT, remote issues toolset) **bound to this seat** | ALREADY PRESENT — no action |
| Row 1: `Slack GA` (MCP col) | No `slack` server in catalog; #14 states no pin (remote OAuth surface, docs-moved) | EXCLUDED — no-pin-no-add + remote-OAuth surface out for a minimal batch |
| Row 1: `superpowers (brainstorming)` | Vendored `obra/superpowers@bb92a77` (MIT); seat binds only `dispatching-parallel-agents` | **ADDED — `brainstorming` bound** (fitting: executive discovery/options; §Added) |
| Row 1: Docusaurus v3.10.2 (OSS col, MIT) | No fleet mechanism pins doc-site versions; seat writes `docs/executive/*`, serves nothing | INFORMATIONAL — pin confirmed (`@docusaurus/core` latest = 3.10.2, 2026-10-20); no action |
| Row 2 `product-director`: `pi-lens@4.4.4` | Exists on npm (verified 2026-10-20, MIT) | DEFERRED — extensions batch |
| Row 2: `pi-subagents@0.79.2` | Second delegation path | EXCLUDED — verify gate HR-6.2 bans `pi-subagents` (B1/B2/B3 same verdict) |
| Row 2: `@narumitw/pi-plan-mode@0.59.4` | Exists on npm (MIT) | DEFERRED — extensions batch |
| Row 2: `Linear official` (MCP col) | No `linear` server in catalog; #14 states no pin; `@linear/mcp-server` → 404 (re-verified 2026-10-20) | DROPPED — no-pin-no-add (B2 same verdict, re-verified not assumed) |
| Row 2: `Figma official remote` | No `figma` server in catalog; #14 directs to the official remote (OAuth, no pin); `@figma/mcp` → 404; npm `figma-mcp@0.1.4` is not the official remote (unknown provenance) | EXCLUDED — remote-OAuth surface, no stated pin |
| Row 2: `Notion remote` | No `notion` server in catalog; #14 states no pin. Noted: `@notionhq/notion-mcp-server` exists (npm `2.5.2`, verified 2026-10-20) but NOT adopted here — same rule as B1's Neon note | EXCLUDED — no-pin-no-add (B3 same verdict) |
| Row 2: `vercel-labs` skill | Vendored `vercel-labs/agent-skills@063bee9` (MIT) exposes only `react-best-practices` + `web-design-guidelines`; neither fits a product-strategy charter | NO ACTION — ill-fitting (B1/B2 same bar) |
| Row 2: `superpowers` | Seat already binds `brainstorming` + `writing-plans` + `subagent-driven-development` | ALREADY PRESENT — no action |
| Row 2: PostHog (OSS col) | #14 states no pin; B1's verdict stands (upstream `PostHog/mcp` archived). Noted: npm `posthog-mcp@1.1.1` exists but is adoption without a #14 pin | EXCLUDED — no-pin-no-add + archived upstream (B1 same verdict) |
| Row 3 `system-architect`: `pi-lens@4.4.4` | Exists on npm (MIT) | DEFERRED — extensions batch |
| Row 3: `@ff-labs/pi-fff@0.11.0` | Exists on npm (verified 2026-10-20, MIT) | DEFERRED — extensions batch |
| Row 3: `pi-memory@0.4.2` | Exists on npm (verified 2026-10-20, MIT) | DEFERRED — extensions batch |
| Row 3: `Rovo` (MCP col) | No `rovo` server in catalog; #14 states no pin; `@atlassian/rovo-mcp` → 404 (re-verified 2026-10-20); Atlassian remote is an OAuth cloud surface | EXCLUDED — no-pin-no-add + remote-OAuth surface (B3 same verdict, re-verified) |
| Row 3: `@azure/mcp@4.0.0-beta.1` | Not in catalog | EXCLUDED — beta-only tag on an archived-predecessor lineage; broad Azure credential surface unverifiable in a minimal batch (B1 same verdict) |
| Row 3: `anthropics/skills` | Vendored `anthropics/skills@dbd4588` exposes `doc-coauthoring`, `frontend-design`, `webapp-testing` — none fits a system-architecture charter | NO ACTION — ill-fitting (B1/B2 same bar) |
| Row 3: OpenTofu 1.13.1 (OSS col, MPL-2.0) | No fleet mechanism pins IaC versions (`sidecar_profiles` are labels; no versioned service pins in `fleet/`). `terraform` MCP (MPL-2.0, registry lookups) already in catalog for registry/doc queries | INFORMATIONAL — no action |
| Row 4 `tpm-scrum-lead`: `pi-subagents@0.79.2` | Second delegation path | EXCLUDED — HR-6.2 ban (B1/B2/B3 same verdict) |
| Row 4: `pi-btw@0.8.0` | Exists on npm (verified 2026-10-20, MIT) | DEFERRED — extensions batch |
| Row 4: `@narumitw/pi-plan-mode@0.59.4` | Exists on npm (MIT) | DEFERRED — extensions batch |
| Row 4: `Linear official` | As row 2 | DROPPED — 404 + no pin |
| Row 4: `Slack GA` | As row 1 | EXCLUDED — no pin + remote-OAuth surface |
| Row 4: `GitLab 19.6` (MCP col) | No `gitlab` server in catalog; #14 states service version, **no MCP pin**; `@gitlab/mcp-server` → 404 (re-verified 2026-10-20) | EXCLUDED — no-pin-no-add (B2 same verdict, re-verified) |
| Row 4: `superpowers (systematic-debugging)` | Vendored `obra/superpowers@bb92a77` (MIT); seat binds `dispatching-parallel-agents` + heretek-crew `git-flow`, no debugging skill | **ADDED — `systematic-debugging` bound** (fitting: delivery-blocker triage; §Added) |
| Row 4: GitLab 19.6 (OSS col, MIT) | Service version, not seat tooling; no fleet version-pin mechanism | INFORMATIONAL — no action |
| Row 5 `git-drift-coord`: `pi-web-access@0.43.0` | Exists on npm (verified 2026-10-20, MIT; supersedes #14-era 0.42.0) | DEFERRED — extensions batch |
| Row 5: `pi-mcp-adapter@5.4.0` | Exists on npm (verified 2026-10-20, MIT) | DEFERRED — extensions batch |
| Row 5: `pi-web-search@1.7.0` | Exists on npm (verified 2026-10-20, MIT) | DEFERRED — extensions batch |
| Row 5: `GitLab 19.6` (MCP col) | As row 4 | EXCLUDED — no-pin-no-add |
| Row 5: `github remote` | Catalog `github` (MIT) exists but is **not bound to this seat** (seat binds only `codebase-memory`) | NO ACTION — seat's drift remit (worktree/rebase orchestration) is served by local `git` bash allows + `codebase-memory`; `github`-issues read is the governance-leads pattern (exec/product/tpm), not a drift need. Adding tool surface without a charter need fails the minimal-batch bar |
| Row 5: `tob (git)` | No git-named skill in the 64-skill lock; seat already carries heretek-crew `git-flow` + superpowers `using-git-worktrees` + `finishing-a-development-branch`. New tob vendor source would need generator `pins`-dict surgery | NO ACTION — covered (B2 redundancy precedent); vendoring a duplicate git skill is token noise (B1 ill-fitting precedent) |
| Row 5: Syft v1.55.0 (OSS col, Apache-2.0) | No fleet version-pin mechanism for seat-executed CLI tools; seat has no `syft` bash allow today | INFORMATIONAL — no new execution grant in a minimal batch (B3 Gitleaks/Trivy same bar) |
| Row 6 `tech-docs-lead`: `pi-btw@0.8.0`, `pi-lens@4.4.4` | Both exist on npm (MIT) | DEFERRED — extensions batch |
| Row 6: `Notion remote` | As row 2 | EXCLUDED — no-pin-no-add |
| Row 6: `Rovo` | As row 3 | EXCLUDED — 404 + OAuth surface |
| Row 6: `vercel-labs` | As row 2 (no fitting vendored skill for a docs charter) | NO ACTION — ill-fitting |
| Row 6: `mattpocock/skills` | **Not vendored** — new vendor source would need generator `pins`-dict surgery + a new pinned clone | DEFERRED — out of minimal-batch scope (B1 prisma/supabase precedent). Follow-up batch |
| Row 6: Vale v3.24.0 + Docusaurus v3.10.2 (OSS col, MIT) | No version-pin mechanism; seat carries `markdownlint*` today | INFORMATIONAL — no new execution grant (same bar as Syft); Vale move to `vale-cli/vale` noted |

## What was added (1 pin bump + 2 skill bindings, all #14-traceable)

1. **`memory` MCP server pin bump `1.0.0` → `2.0.0`** (`fleet/mcp-servers.yaml`, 1 line). Row 1 queues it explicitly ("memory 2.0.0 MIT ADOPT-ready", "server-memory 1.0.0→2.0.0 queued").
   - Verified live 2026-10-20: `@modelcontextprotocol/server-memory@2.0.0` is npm `latest` (published 2026-10-19); `bin` unchanged (`mcp-server-memory` → `dist/index.js`), so the catalog `command` path is untouched; `license` field unchanged (`SEE LICENSE IN LICENSE`, MIT upstream — same declaration as 1.0.0, so license posture is unchanged); README confirms the same `MEMORY_FILE_PATH` env contract the catalog already wires per-seat.
   - Blast-radius note: exactly 3 seats bind `memory` — `exec-director`, `product-director`, `tpm-scrum-lead` — **all Rig 1**. This is why the bump belongs to B4: B1 correctly scoped it out as "other rigs' batches," and Rig 1 is that batch. No other rig is affected.
2. **`exec-director` shared skills += `brainstorming`** (superpowers, 1 line in `fleet/fleet.yaml`). Missing (seat had no discovery-shaped skill) + verifiable (vendored `obra/superpowers@bb92a77`, MIT) + license-clean + fitting (CEO-delegate discovery/options framing; #14 row 1 names it). Render proof: seat dry-render carries `brainstorming`.
3. **`tpm-scrum-lead` shared skills += `systematic-debugging`** (superpowers, 1 line in `fleet/fleet.yaml`). Missing (no debugging skill on the seat) + verifiable (same vendored MIT source) + fitting (delivery-blocker triage alongside `e2e-browser-qa`/`rust-systems-spec` collaborators; #14 row 4 names it). Render proof: seat dry-render carries `systematic-debugging`.

## Dropped/excluded, with verification evidence (all checks 2026-10-20 via npm registry)

- **Linear MCP:** no stated pin in #14; `@linear/mcp-server` → 404. DROP.
- **GitLab MCP:** no stated pin in #14 (19.6 is a service version, not an MCP distribution); `@gitlab/mcp-server` → 404. DROP.
- **Rovo MCP:** no stated pin; `@atlassian/rovo-mcp` → 404; Atlassian remote is an OAuth cloud surface in any case. DROP.
- **Figma:** #14 directs to the official remote (OAuth, no pin); `@figma/mcp` → 404; npm `figma-mcp@0.1.4` is not the official remote. EXCLUDED.
- **Notion MCP:** no pin in #14; `@notionhq/notion-mcp-server` exists (`2.5.2`) but is NOT adopted here — no-pin-no-add (B3 same verdict).
- **Slack MCP:** remote OAuth surface, docs-moved, no pin in #14. EXCLUDED.
- **Azure `@azure/mcp@4.0.0-beta.1`:** beta-only tag on archived-predecessor lineage; broad credential surface. EXCLUDED (B1 same verdict).
- **PostHog:** no pin in #14; upstream MCP archived per B1. EXCLUDED (B1 same verdict).
- **`pi-subagents` (rows 2, 4):** EXCLUDED — verify gate HR-6.2 rejects the second delegation path (B1/B2/B3 same verdict).
- **OSS service/version pins** (Docusaurus 3.10.2, OpenTofu 1.13.1, GitLab 19.6, Syft 1.55.0, Vale 3.24.0): NOT ACTIONABLE — no fleet mechanism pins service/CLI versions (`sidecar_profiles` are labels; `bash_allow` is a capability grant, not a version pin, and this batch grants no new execution). Recorded informational; Docusaurus 3.10.2 re-confirmed (`@docusaurus/core` latest, 2026-10-20).

## Deferred with named blockers (not started here)

- **Pi-extension batch (all 9 pins, rows 1–6):** `pi-lens@4.4.4`, `pi-btw@0.8.0`, `pi-web-access@0.43.0`, `pi-mcp-adapter@5.4.0`, `@ff-labs/pi-fff@0.11.0`, `pi-web-search@1.7.0`, `pi-memory@0.4.2`, `@narumitw/pi-plan-mode@0.59.4`, `@narumitw/pi-usage@0.67.0` — every pin verified to exist on npm 2026-10-20, all MIT. NOT adopted here: B2/B3 deferred a dedicated pi-extension follow-up batch (per-seat license/compat verification), and per the B4 task envelope B4 must coordinate by **not duplicating it**. If extension bumps end up the only remaining delta elsewhere, they belong to that batch, not this one. Freshness note for that batch: `pi-web-access` latest is `0.43.0` (supersedes #14's `0.42.0`).
- **`context7` 4.4.2 → 4.4.4:** verified (`@upstash/context7-mcp` latest = 4.4.4, 2026-10-20) but OUT OF SCOPE — #14 queues it at row 14 (Rig 2, no batch yet) and its 6 consumers span 4 rigs (`ai-red-teamer`, `go-backend-eng`, `python-backend-spec`, `rust-systems-spec`, `system-architect`, `ts-node-fullstack`). A cross-rig catalog bump belongs to a future Rig-2 batch or a dedicated catalog batch, not to B4. (`memory` is B4's precisely because all its consumers are Rig 1.)
- **`mattpocock/skills` (row 6):** not vendored; needs generator surgery + pinned clone. Follow-up batch (B1 prisma/supabase precedent).

## Regen + verify evidence

- Tree was clean at start (`git status` empty on `feat/self-rig1-tooling` @ 88c13d7); regen ran **with** `HERETEK_RIGS_ALLOW_DIRTY=1` — stated reason: the 3 catalog lines above ARE the change, and the generator refuses dirty trees by design (AGENTS.md-sanctioned dev regen; B1 precedent).
- Generator: `python3 ./scripts/generate-rigs.py --vendor-dir <main-checkout>/.scratch/vendor --crew-source <heretek-crew-checkout>` → "wrote 51 specialist AgentSpecs, 64 shared skills, 8 RigBundles…". Vendor SHAs unchanged; no new vendor sources introduced.
- Regen diff: **34 files, +64/−46** — 2 catalog files (the 3-line change) + 8 registry entries + `status.json` + 8 registry views + 2 seats × (rig + omni `agent.yaml`/`role.md`, carrying `heretek-shared:brainstorming` / `heretek-shared:systematic-debugging`) + 2 `bundle.yaml` digest updates + 1 roster + 4 specs files. Registry churn is pure provenance relag (`resolvedCommit`/hashes), the known per-merge convention. Zero hand-edits to generated leaves.
- `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 22 checks passed, 0 failed**, incl. "All 20 MCP servers … verified (pinned, command-backed secrets)".
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- Render proof (dry-run, dummy secrets dir, no values read): `tpm-scrum-lead` render carries `systematic-debugging`; `exec-director` render carries `brainstorming`.
- `git status`: the 34 regen files above + this ledger. No hand-edits to generated leaves; no A-slice or B1–B3 files touched; no secrets/values; no machine-local paths in this ledger (placeholders only).

## Deferred live proof (fleet down)

Not run: `seed-rig.py` for `executive-and-architecture`, `pi mcp list --json` memory 2.0.0 connectivity, any skill-render smoke beyond dry-run. Required before merge: freshness re-check of the `2.0.0` pin + the 9 deferred extension pins (pins rot; today's `latest` values are dated in this ledger for that purpose).
