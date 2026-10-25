# Proposal: residuals-107 — V13 rate-limit skip + doc-count/pin refresh (no policy loosening)

Status: scope approved (HANDOFF P1 + operator "Execute the remainder", 2026-10-24).
Issue: #107 (residuals bundle). Closes the code+docs boxes below; upstream-watch boxes stay open with reasons.

## Root cause (verified read-only 2026-10-24, Wave B recon)

- V13 skip-regex `scripts/verify-rigs.sh:1779-1785` covers transport errors only (`:1781` pattern); no `toomanyrequests`/`rate limit` arm → quota-burned registry went RED twice, fail-closed (HANDOFF:43, red-proofs.logs, verification reports). Fix shape: extend `:1781` (1 line, not applied).
- Stale counts: `AGENTS.md:15`, `docs/USER_GUIDE.md:127`, `README.md:47` say 26; main reports 31 after V15. Prior refresh attempt `docs/reports/docs-hygiene-verification.md` notes no automated guard.
- Stale pin: `docs/TECHNICAL_DOCUMENTATION.md:408` lists `ghcr.io/mendable/firecrawl:1.6.0`; live pin is `ghcr.io/firecrawl/firecrawl:2.10.19@sha256:5044…6d7ed` (`docker-compose.sidecars.yml:84-105`, `docs/NOTES.md:305`).
- Footer URL `YZ9W` vs `nx9`: cosmetic provenance only (3 nx9 vs 1 YZ9W). Historical reports MUST NOT be rewritten (audit trail); canonical for future footers = `nx9`.

## Change

- CODE (1 line): extend V13 skip pattern with `toomanyrequests|rate limit` (fail-closed otherwise unchanged; adjacent nit: log matched skip token — include if trivial, else note).
- DOCS: 26→31 in AGENTS.md, USER_GUIDE.md, README.md (counts only); firecrawl pin refresh in TECHNICAL_DOCUMENTATION.md:408; session-URL decision recorded in B2 evidence (no report rewrites).
- DEFERRED (no code, reasons in design.md): bare-TPM shorthand, xyz123 human-registry, "QA PASS no issues" non-terminal, F9 bare-leading-env (all intentional fail-closed), firecrawl standalone boot (needs networked host), authenticated registry pulls (V13 alternative).

## Acceptance

1. `verify-rigs.sh --check-only` green; V13 block skips on `toomanyrequests` (red-proofed by sabotage: pattern without arm REDs on fixture, with arm SKIPs).
2. `grep -rn "26 checks" AGENTS.md docs/USER_GUIDE.md README.md` = 0; `grep -rn "31 checks" ...` present.
3. `grep -n mendable/firecrawl:1.6.0 docs/TECHNICAL_DOCUMENTATION.md` = 0; `2.10.19` present.
4. Evidence `docs/evidence/wave-b2-residuals.md` + drift-guard `VERDICT: PASS` → PR.
