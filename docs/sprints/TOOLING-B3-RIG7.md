# Tooling Batch B3 — Rig 7 (defensive-sec-and-red-team)

**Slice:** Workstream B, batch B3 · **Branch:** `feat/self-rig7-tooling` (worktree `heretek-rigs-self-b3`)
**Date:** 2026-10-20 · **Source:** Issue #14 rows 44–51 vs `fleet/mcp-servers.yaml` (20 servers) + `fleet/skills-lock.json` (64 skills) + Rig 7 seat attachments in `fleet/fleet.yaml`
**Status:** Implemented, regen + `verify-rigs.sh --check-only` **22/0**. UNCOMMITTED, no push. Live-seat proof deferred (fleet down).
**Net catalog/fleet change: ZERO.** Every rows 44–51 item is already present, excluded on license/pin/auth-model grounds, deferred with a named blocker, or informational (no fleet mechanism). This ledger is the batch deliverable (precedent: B1 ledger `TOOLING-B1-RIG5.md`, B2 ledger `TOOLING-B2-RIG6.md`).

## Scope note (row 44)

Row 44 (`static-analysis-lead`) is a **Rig 6** seat (`qa-and-verification-gauntlet`), not Rig 7 — B2 covered Rig 6 rows 39–43, so row 44 fell between batches. It is accounted here (§Row 44) with **no change**; a Rig-6 follow-up may claim it.

## Row-by-row diff (#14 rows 44–51 vs in-tree state)

| #14 item | In-tree state | Decision |
|---|---|---|
| Row 44 `static-analysis-lead`: SonarQube 1.29.0, Snyk (MCP col) | SonarQube MCP: 404 under `@sonarqube/mcp-server`, `@sonarsource/sonarqube-mcp`, `sonarqube-mcp` (re-verified 2026-10-20); Snyk: `snyk-mcp` → 404, CLI numbering is not an MCP pin, proprietary | DROPPED / EXCLUDED — DNP + no-distribution (B1 same verdicts, re-verified not assumed) |
| Row 44: `static-analysis` skill | Seat binds tob `semgrep`, `semgrep-rule-creator`, `semgrep-rule-variant-creator`, `codeql`, `sarif-parsing` + heretek-crew `custom-semgrep-rule-authoring`; upstream tob plugin list contains `static-analysis` but it is **not vendored** — new vendor source = generator surgery | NO ACTION — covered; vendoring a duplicate static-analysis skill is token noise (B1 ill-fitting precedent) |
| Row 44: Semgrep 1.x + CodeQL 2.2x (OSS col) | Catalog `semgrep` pin `pypi:semgrep==1.181.0` satisfies "1.x"; CodeQL via vendored tob `codeql` skill; no fleet mechanism pins OSS versions | ALREADY PRESENT / INFORMATIONAL — no action |
| Row 45 `threat-modeler`: Rovo (MCP col) | No npm distribution (`@atlassian/rovo-mcp` → 404, 2026-10-20); Atlassian remote MCP is an OAuth cloud surface; #14 states **no pin** | EXCLUDED — no-pin-no-add + remote-OAuth surface out for a minimal batch |
| Row 45: `pi-btw@0.8.0` | Exists on npm (`0.8.0`, MIT — verified 2026-10-20) | DEFERRED — pi extensions need individual per-seat verification; follow-up batch (B1 precedent). Seat carries only `@gotgenes/pi-permission-system@41.0.0` today |
| Row 45: `threat-model` (skill col) | No such skill in the 64-skill lock; upstream tob plugin listing has **no** `threat-model` plugin; seat already binds heretek-crew `stride-threat-modeling` | NO ACTION — category label, not a vendored skill ID; seat already carries the fitting skill |
| Row 45: OWASP Threat Dragon (OSS col, Apache-2.0) | Desktop/web review app (latest `v2.6.2`, 2026-05-10); no MCP distribution, no CLI scanner role | INFORMATIONAL — no fleet mechanism (not an MCP server, skill, or seat-executed scanner) |
| Row 46 `appsec-engineer`: Snyk Evo GA, SonarQube (MCP col) | As row 44: no Snyk MCP distribution; SonarQube DNP re-verified | EXCLUDED / DROPPED — proprietary + DNP (B1 same verdicts) |
| Row 46: `sentry-for-ai` | Vendored `getsentry/skills`; seat already binds `security-review` (plus tob `semgrep`/`variant-analysis`/`fp-check`, heretek-crew `code-review`/`security-audit`/`owasp-reachability-triage`) | ALREADY PRESENT — no action |
| Row 46: Gitleaks 8.2x (OSS col, MIT) | 8.x line confirmed (latest `v8.30.1`; #14's "8.2x" prefix stale); no fleet version-pin mechanism for CLI tools; blue-pod sibling `cloud-sec-auditor` already carries `gitleaks detect*` | NO ACTION — duplicating the sibling's scanner onto this seat is scope expansion, not minimal |
| Row 46: Trivy v0.76.0 (OSS col) | Exact pin confirmed (`v0.76.0`, 2026-10-14); seat already has `trivy fs*` | ALREADY PRESENT — no action |
| Row 46: Checkov 3.x (OSS col) | PyPI `3.3.30`, Apache-2.0 (3.x confirmed); carried by `cloud-sec-auditor` (`checkov -d*`) | NO ACTION — same anti-duplication reason as Gitleaks |
| Row 46: stale `pi-lsp-extension@1.4.0` / `pi-ast-grep@0.1.0` | Same staleness B1 fixed for `dependency-patcher`, but the companion fix (scoped-name allowlist in `scripts/render-seat.py`) lives on the **unmerged B1 branch** — this tree's `has_ast_lsp` gate (render-seat.py:311-313) keys on legacy names only | DEFERRED with evidence: dry-run render of `appsec-engineer` today carries 10 AST/LSP read-only allows (`ast_grep`, `ast_search`, 8× `lsp_*`); bumping names without B1's fix would silently drop them. Follow-up after B1 merges (B2 same verdict for `sabotage-qa-tester`) |
| Row 47 `cloud-sec-auditor`: Azure 3.0.0 (MCP col) | Pin **exists** (`@azure/mcp@3.0.0`, MIT — B1's beta-only objection to `4.0.0-beta.1` is resolved for the 3.0.0 line) BUT: auth requires an `az login` interactive session, incompatible with the fleet's `!cat <secret-file>` static-secret pattern; broad Azure control-plane credential surface; fleet down so connectivity unverifiable | DEFERRED with named blockers — not adopted in a minimal batch. Blockers: (a) secret-pattern-incompatible auth model, (b) new cloud credential surface, (c) no live verification possible |
| Row 47: GCP (MCP col) | Console-managed, no MCP/pin in #14 | NOTHING TO ADD (B1 same verdict) |
| Row 47: `cloud` (skill col) | No `cloud` plugin upstream or vendored; seat carries `security-audit` + `gha-security-review` + `agentic-actions-auditor` | NO ACTION — label, not a skill ID |
| Row 47: Checkov + Trivy (OSS col) | `checkov -d*` (+ `tfsec*`, `gitleaks detect*`) already allowed; Trivy covered on `appsec-engineer`; pins confirmed informational (§OSS pins) | ALREADY PRESENT — no action |
| Row 47: `pi-mcp-adapter@5.4.0` | Exists on npm (`5.4.0`, MIT — verified) | DEFERRED — pi-extensions follow-up batch (B1 precedent) |
| Row 48 `compliance-auditor`: Rovo + Notion (MCP col) | Neither has a pin in #14 → no-pin-no-add. Noted: `@notionhq/notion-mcp-server` exists (npm `2.5.2`, MIT, verified to exist 2026-10-20) but NOT adopted here — same rule as B1's Neon note | EXCLUDED — Rovo: no distribution + OAuth; Notion: exists but unpinned by #14. Follow-up batch with pin + secret wiring |
| Row 48: `compliance` (skill col) | No `compliance` plugin upstream or vendored; seat carries `supply-chain-risk-auditor` + `spec-to-code-compliance` (tob) + `sbom-generation-and-license-audit` (heretek-crew) | NO ACTION — covered by fitting skills |
| Row 48: Checkov + Docusaurus (OSS col) | Checkov belongs to the cloud seat (already there); Docusaurus 3.9.x is a doc-site framework with no fleet build/serve mechanism (seat writes `docs/compliance/*` + `sbom/*`) | NO ACTION / INFORMATIONAL |
| Row 48: `pi-btw@0.8.0` | As row 45 | DEFERRED — extensions batch |
| Row 49 `ai-red-teamer` 🔴: Vertex (MCP col) | GCP console-managed, no MCP/pin in #14 | NOTHING TO ADD (B1 precedent) |
| Row 49 🔴: `ai-safety` (skill col) | No such vendored skill; no upstream tob plugin; seat already carries `skill-scanner` + `agentic-actions-auditor` (tob/sentry) + 5 heretek-crew prompt-injection skills (`detecting-ai-model-prompt-injection-attacks`, `detecting-indirect-prompt-injection`, `testing-for-system-prompt-leakage`, `testing-prompt-injection-in-rag-pipelines`, `auditing-mcp-servers-for-tool-poisoning`) | NO ACTION — heavily covered already |
| Row 49 🔴: Garak + PyRIT (OSS col) | CLI allows **already present** (`garak*`, `pyrit*`, `promptfoo*` in `bash_allow`); PyPI existence confirmed (garak `0.17.1`, pyrit `1.1.0`); no version-pin mechanism for seat-executed tools | ALREADY PRESENT + INFORMATIONAL — no action |
| Row 49 🔴: `pi-subagents@0.79.2` | Rejected second delegation path | EXCLUDED — verify gate HR-6.2 rejects `pi-subagents` (B1/B2 same verdict) |
| Row 50 `binary-reverse-eng` 🔴: Docker (MCP col) | Catalog explicitly dropped `docker-mcp` (`dropped.docker`: daemon-level access, last release 2024-12); seats use explicit bash allows instead | REFUSED — granting docker execution to a red seat widens execution capability (task bar). No docker allow added |
| Row 50 🔴: `reverse-eng` (skill col) | Seat binds `dwarf-expert` + `yara-rule-authoring` (tob) + `radare2-defensive-disassembly` + `rea-evidence-based-decompilation` (heretek-crew); `radare2` MCP bound read-only (`-R`) | ALREADY PRESENT — no action |
| Row 50 🔴: Ghidra 11.4.x (OSS col, Apache-2.0) | Tags `Ghidra_11.4`–`Ghidra_11.4.3` confirmed to exist; superseded upstream (latest `Ghidra_12.1.4`, 2026-09-21); no ghidra binary allow on the seat | INFORMATIONAL — adding Ghidra execution to a red seat would widen capability; no grant (task bar) |
| Row 50 🔴: YARA 4.5.x (OSS col) | `v4.5.8` confirmed (2026-07-28); authoring skill bound, but **no** yara binary allow on the seat | INFORMATIONAL — same no-new-red-execution bar; no grant |
| Row 50 🔴: base + `pi-web-access` | `pi-web-access` npm latest is now `0.43.0` (2026-10-20), superseding #14's `0.42.0` | DEFERRED — extensions batch (B2 same verdict) |
| Row 51 `firmware-sec-analyst` 🔴: Docker (MCP col) | As row 50 | REFUSED — no docker grant to a red seat |
| Row 51 🔴: `firmware` (skill col) | Seat binds `firmware-extraction-and-hardening-audit` (heretek-crew) + `yara-rule-authoring` + `dwarf-expert` (tob); `radare2` MCP bound | ALREADY PRESENT — no action |
| Row 51 🔴: Binwalk v3.x (OSS col, MIT) | `v3.1.0` confirmed; `binwalk*` (+ `readelf*`, `objdump*`, `checksec*`) **already** in `bash_allow` | ALREADY PRESENT — no action |
| Row 51 🔴: base + `pi-web-access` | As row 50 | DEFERRED — extensions batch |

🔴 = red-team seat (red pod). **Zero new tool grants to any red seat in this batch**: no new `bash_allow` entries, no new MCP bindings, no permission widening. All red-relevant executables in #14 (garak, pyrit, binwalk) were pre-existing scoped allows.

## What was added

**Nothing.** No catalog server, binding, pin bump, or skill attachment met the bar of *missing + verifiable at a stated pin + license-clean + fitting + within red-team restraint*. A zero-change batch is the correct minimal-batch outcome (B2 precedent), not a failure to find work: nine recommendable items are already in-tree, and the rest fail a stated rule.

## Dropped/excluded, with verification evidence (all checks 2026-10-20 via npm registry / PyPI / GitHub API)

- **Snyk MCP:** `snyk-mcp` → 404 on npm. No verifiable MCP distribution at any pin; CLI numbering is not an MCP pin; proprietary-vendor auth surface. DROP.
- **SonarQube MCP:** 404 under three plausible npm names (`@sonarqube/mcp-server`, `@sonarqube`-scoped alternate, `sonarqube-mcp`); B1's DNP re-verified, not assumed. DROP.
- **Rovo MCP:** `@atlassian/rovo-mcp` → 404; remote-only OAuth cloud surface; #14 states no pin. DROP.
- **Notion MCP:** exists (`@notionhq/notion-mcp-server@2.5.2`, MIT) but #14 states no pin → no-pin-no-add (B1 Neon precedent). Follow-up: pin + `NOTION_API_KEY`-style secret wiring.
- **Azure MCP:** `@azure/mcp@3.0.0` stable exists (MIT) — beta objection resolved — but `az login` auth is incompatible with the `!cat` secret pattern; broad control-plane surface; unverifiable with fleet down. DEFERRED with blockers (§Row 47).
- **GCP / Vertex managed:** console-managed, no MCP/pin in #14. NOTHING TO ADD.
- **Docker MCP / docker execution for red seats:** catalog-dropped (`dropped.docker`); new red execution grants refused per slice bar. REFUSED.
- **`pi-subagents`:** banned second delegation path, gate HR-6.2. EXCLUDED.
- **`pi-btw@0.8.0`, `pi-mcp-adapter@5.4.0`, `pi-web-access@0.42.0`:** all verified to exist (MIT; `pi-web-access` latest now `0.43.0`, superseding #14). DEFERRED to a pi-extensions follow-up batch (B1 precedent).
- **Stale `pi-lsp-extension` / `pi-ast-grep` on `appsec-engineer`:** DEFERRED pending B1 merge (companion render fix unmerged; §Row 46 evidence).
- **#14 skill-column labels** (`threat-model`, `cloud`, `compliance`, `ai-safety`, `reverse-eng`, `firmware`): verified against the 64-skill lock **and** the upstream tob plugin listing — none exists as a vendored or vendorable skill ID. New vendor sources require generator `pins`-dict surgery (B1 `prisma`/`supabase` deferral precedent). DEFERRED at most; seats already carry fitting skills.

## OSS pins (informational — no fleet mechanism pins service/binary versions)

`sidecar_profiles` are labels; `bash_allow` entries carry no versions. Confirmed to exist 2026-10-20, recorded for merge-time freshness only: Gitleaks 8.x (`v8.30.1` latest; #14's "8.2x" prefix stale), Trivy `v0.76.0` exact (2026-10-14), Checkov `3.3.30` (Apache-2.0), YARA `v4.5.8` (2026-07-28), Ghidra 11.4.x tags exist / superseded by `12.1.4` (2026-09-21), Binwalk `v3.1.0`, Threat Dragon `v2.6.2`, garak `0.17.1` / pyrit `1.1.0` (PyPI). Docusaurus 3.9.x not re-verified here — no fleet doc-site mechanism exists regardless. Re-check at PR merge time per program plan §4.

## Regen + verify evidence

- Tree was clean at start (`git status` empty on `feat/self-rig7-tooling` @ `88c13d7`); regen ran **without** `ALLOW_DIRTY` (no reason to state).
- Generator: `python3 ./scripts/generate-rigs.py --vendor-dir <main-checkout>/.scratch/vendor --crew-source <heretek-crew-checkout>` → "wrote 51 specialist AgentSpecs, 64 shared skills, 8 RigBundles…". Vendor SHAs unchanged; no new vendor sources introduced.
- Regen diff: **16 registry files only, pure provenance relag** (`resolvedCommit` e8577db→88c13d7 + matching `canonicalUrl`s, 24+/24- symmetric) — the known per-merge convention, same shape as B2. Zero changes under `specs/`, `rigs/`, `rosters/`, or seat content.
- `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 22 checks passed, 0 failed**, incl. "All 20 MCP servers … verified (pinned, command-backed secrets)".
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- Render proof (dry-run with dummy 0600 secrets dir + `--allow-missing-secrets`, no values read): `appsec-engineer` permissions carry the 10 AST/LSP read-only allows (`ast_grep`, `ast_search`, 8× `lsp_*`) — the evidence behind the pin-bump deferral above.
- `git status`: 16 relag files (regen output) + this ledger. No hand-edits to generated leaves; no A-slice, B1, or B2 files touched; no secrets/values; no machine-local paths in this ledger (placeholders only).

## Deferred live proof (fleet down)

Not run: `seed-rig.py` for `defensive-sec-and-red-team`, `pi mcp list --json` connectivity, any garak/pyrit/binwalk/yara smoke run. Required before merge: freshness re-check of the verification claims above (pins rot; today's `latest` values are dated in this ledger for that purpose).
