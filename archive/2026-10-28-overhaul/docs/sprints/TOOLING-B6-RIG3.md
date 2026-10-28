# Tooling Batch B6 — Rig 3 (systems-and-mobile-foundry)

**Slice:** Workstream B, batch B6 · **Branch:** `feat/self-rig3-tooling` (worktree `heretek-rigs-self-b6`)
**Date:** 2026-10-20 · **Source:** Issue #14 rows 18–21 vs `fleet/mcp-servers.yaml` (20 servers) + `fleet/skills-lock.json` (64 skills) + Rig-3 seat records in `fleet/fleet.yaml`
**Status:** Zero-change batch, regen + `verify-rigs.sh --check-only` **22/0**. UNCOMMITTED, no push. Live-seat proof deferred (fleet down).
**Rig 3 membership confirmed:** exactly 4 seats carry `rig: systems-and-mobile-foundry` — `rust-systems-spec`, `cpp-lowlevel-eng`, `android-mobile-spec`, `ios-mobile-spec`. No other seat belongs to this rig.

Every row 18–21 is accounted below. Net catalog/fleet change: **none** — all items resolve to ALREADY PRESENT, license/pin-barred, DEFERRED with a named blocker, or INFORMATIONAL (no fleet mechanism). B2/B3/B5 honest zero-change precedent applies; per the task envelope, no changes are forced. All known bars were re-verified live 2026-10-20, not assumed.

## Row-by-row diff (#14 rows 18–21 vs in-tree state)

| #14 item | In-tree state | Decision |
|---|---|---|
| Row 18 `rust-systems-spec`: `pi-lens` (Pi ext col; seat ships `pi-lsp-extension@1.4.0` + `pi-ast-grep@0.1.0`) | Exists on npm (MIT; B2/B3/B4/B5 same pattern) | DEFERRED — pi-extension follow-up batch (§Deferred) |
| Row 18: `Snyk CLI 1.1298.0+` (MCP col) | No `snyk` server in catalog; #14 states a CLI version, not an MCP distribution | EXCLUDED — re-verified 2026-10-20: `snyk-mcp` → 404, `@snyk/mcp-server` → 404 on npm; Snyk CLI is proprietary vendor tooling with no MIT/Apache-2.0 MCP distribution at a stated pin. Proprietary-vendor auth surface; out for a minimal batch (B1 row-30 same verdict, re-verified) |
| Row 18: `trailofbits:rust` | Seat **already binds** `rust-review` + `cargo-fuzz` (tob). Both vendored (`trailofbits/skills@5c99c03`); both present in the pinned checkout (`plugins/rust-review`, `plugins/testing-handbook-skills`) — verified against the checkout, not assumed (unlike B5's Java gap, the rust skills exist) | ALREADY PRESENT — no action |
| Row 18: Tokio (OSS col, MIT) | No fleet mechanism pins seat-executed crate versions | INFORMATIONAL — no action |
| Row 18: `context7` bound to this seat | Catalog pins `npm:@upstash/context7-mcp@4.4.2`; npm `latest` is `4.4.4` (B4/B5 re-verified) | NO ACTION — the 4.4.2→4.4.4 bump belongs to the dedicated catalog batch (B5 §Deferred); its consumers span 4 rigs, not a per-rig change |
| Row 19 `cpp-lowlevel-eng`: `pi-subagents` | Second delegation path | EXCLUDED — verify gate HR-6.2 bans `pi-subagents` (`scripts/verify-rigs.sh:1075-1082`, re-confirmed in-tree; B1/B2/B3/B4/B5 same verdict) |
| Row 19: `SonarQube 1.29.0` | No `sonarqube` server in catalog; #14 marks it DNP | DROPPED — re-verified 2026-10-20: `github.com/SonarSource/sonarqube-mcp` → repository-not-found (B1/B3 same verdict, re-verified). Noted: npm `sonarqube-mcp-server@1.10.21` exists but is NOT the #14 pin (1.29.0) and is of unverified provenance — no-pin-no-add |
| Row 19: `trailofbits:cpp` | Seat **already binds** `c-review` + `address-sanitizer` + `libfuzzer` (tob), all vendored in `skills-lock.json` and present in the pinned checkout; plus role-local `modern-cpp-sanitizer-verification` (heretek-crew). The tob `modern-cpp` plugin exists in the checkout but is NOT vendored (absent from the 64-skill lock) and #14 names only `trailofbits:cpp` generically, which the three bound skills satisfy | ALREADY PRESENT — no action; not vendoring an extra skill without a #14-named need |
| Row 19: LLVM sanitizers (OSS col, Apache-2.0) | No version-pin mechanism; seat already binds `address-sanitizer` (tob) + role-local sanitizer-verification skill | INFORMATIONAL — covered at tooling level, no action |
| Row 20 `android-mobile-spec`: `pi-web-access@0.42.0` | Exists on npm (MIT; B4 freshness note: latest is `0.43.0`) | DEFERRED — extensions batch |
| Row 20: `GCP managed` (MCP col) | No `gcp` server in catalog; #14 states console-managed, no MCP/pin | NOTHING TO ADD (B1 rows-28/29/34/35/37 same verdict) |
| Row 20: `supabase` (skill, MIT) | Neither `supabase` nor `prisma` is a vendored source; `pins` dict in `scripts/generate-rigs.py` carries only heretek-crew/superpowers/tob/sentry/anthropic/vercel | DEFERRED — new vendor source needs generator `pins`-dict surgery + new pinned clone (B1 rows-33/35/38 same verdict). Follow-up batch |
| Row 20: NowInAndroid (OSS col, Apache-2.0) | Sample-app repo, no fleet mechanism pins it; seat already binds `mobile` MCP (emulator control) + role-local `artemis-android-ui-exploration` + `jetpack-compose-state-hoisting` | INFORMATIONAL — no action |
| Row 21 `ios-mobile-spec`: `pi-web-access@0.42.0` | As row 20 | DEFERRED — extensions batch |
| Row 21: `Figma MCP` | No `figma` server in catalog; #14 directs to the official remote (OAuth, no pin) | EXCLUDED — re-verified 2026-10-20: `@figma/mcp` → 404 on npm; remote-OAuth surface out for a minimal batch (B4 rows-2/12 same verdict, re-verified) |
| Row 21: `vercel-labs` (MIT) | Vendored `vercel-labs/agent-skills@063bee9` exposes `react-best-practices`, `web-design-guidelines`, `react-native-skills`, `composition-patterns`, deploy/cli helpers — none fits a SwiftUI/Packaging charter (seat's only skill is role-local `swiftui-concurrency-implementation`) | NO ACTION — ill-fitting (B1/B2/B4/B5 same bar); not forcing a near-miss binding |
| Row 21: CS193p Stanford (OSS col) | Course material, no vendoring mechanism or fleet pin for coursework | INFORMATIONAL — no action |

## Considered and rejected (not #14-traceable — recorded so a follow-up does not re-litigate)

- **tob `firebase-apk-scanner`** (exists in the pinned checkout, not vendored): a Firebase-misconfiguration APK scanner. Not named anywhere in #14; wiring it would need a new vendored skill + `apktool`/`curl` bash grants on a feature-dev seat — a scope widening without a #14 mandate. NO ACTION.

## What was added

None. Zero catalog, script, or seat-content change. The regen diff is 16 registry files of pure provenance relag (`resolvedCommit` `e8577db` → `88c13d7`, the known per-merge convention) plus this ledger — the B2/B3/B5 zero-change shape.

## Deferred with named blockers (not started here)

- **Pi-extension batch** (all #14 pins in rows 18–21: `pi-lens`, `pi-web-access@0.42.0` — B4 freshness note: latest `0.43.0`): every pin verified to exist on npm, all MIT. NOT adopted here — B2/B3/B4/B5 deferred a dedicated per-seat extension batch, and B6 must coordinate by not duplicating it.
- **New vendor sources** (`supabase` skills; `prisma` noted in B1): each needs generator `pins`-dict surgery + a new pinned clone. Follow-up batch (B1/B4/B5 precedent).
- **OSS pins** (Tokio, LLVM sanitizers, NowInAndroid, CS193p): no fleet mechanism pins them (`sidecar_profiles` are labels; `bash_allow` is a capability grant, not a version pin, and this batch grants no new execution). Recorded informational. LLVM sanitizers and the Android sample-app space are additionally covered at tooling level (`address-sanitizer` + role-local skills; `mobile` MCP).
- **`context7` catalog bump** (consumer: `rust-systems-spec` among 6 seats across 4 rigs): dedicated catalog batch (B5 §Deferred). Not duplicated here.

## Regen + verify evidence

- Tracked tree was clean at start (`git status` showed only pre-existing untracked strays — `.agents/`, `.claude/`, `docs/evidence/`, `docs/reports/`, `recommendations.*`, `skills-lock.json` — left untouched per AGENTS.md); regen ran **without** `ALLOW_DIRTY` (no stated reason needed).
- Generator: `python3 ./scripts/generate-rigs.py --vendor-dir <main-checkout>/.scratch/vendor --crew-source <heretek-crew-checkout>` → "wrote 51 specialist AgentSpecs, 64 shared skills, 8 RigBundles…". Vendor SHAs matched pins (`bb92a77`, `5c99c03`, `f57ada2`, `dbd4588`, `063bee9`; Heretek-Crew `0b41346` = allowed alternate). No new vendor sources introduced. (Placeholders used for machine-local paths.)
- Regen diff: **16 files, +24/−24** — registry entries + views only; every hunk is the `resolvedCommit` relag (`e8577db` → `88c13d7`) plus `canonicalUrl` commit pins. Zero hand-edits to generated leaves; `fleet/` and `scripts/` untouched.
- `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 22 checks passed, 0 failed**, incl. "All 20 MCP servers … verified (pinned, command-backed secrets)".
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- `git status`: the 16 regen files above + this ledger. No A-slice or B1–B5 files touched; no secrets/values; no machine-local paths in this ledger (placeholders only).

## Deferred live proof (fleet down)

Not run: `seed-rig.py` for `systems-and-mobile-foundry`, any skill/MCP smoke beyond dry verification. Nothing to smoke — zero content change. Required before merge: freshness re-check of the deferred extension pins (pins rot; today's `latest` values are dated in this ledger for that purpose).
