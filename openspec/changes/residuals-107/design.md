# Design: residuals-107 (minimal touch, defer with reasons)

## Why 1-line V13, not authenticated pulls
Authenticated pulls need registry credentials on every host (secret-sprawl); the skip arm treats quota as what it is (transient transport noise) while staying fail-closed on real digest mismatches. Upstream alternative recorded, not built.

## Why counts in 3 docs only
AGENTS.md (operator gate), USER_GUIDE.md (manual), README.md (quickstart) are the live surfaces seats read. Ladder history in NOTES/REMEDIATION_PROMPT stays (audit trail). Canonical automated stale-count guard belongs to #102 (Wave D checker batch), not here.

## Why nx9 without rewriting YZ9W
Reports are evidence (`AUDIT_REPORT_FINDINGS.md`/`REMEDIATION_LOG.md` append-only rule). Rewriting a footer token falsifies provenance. Decision: future footers use `nx9`; history stands.

## Deferred with reasons (stay fail-closed)
- Bare-`TPM`: retirement path already commented (`check-envelope.py:545-548`); removal needs governed-predicate rollout (Wave D or upstream).
- `xyz123` human: needs human-registry source (upstream-watch).
- "QA PASS, no issues": anchored-regex + negator already correct; non-terminal reading is operator error, not code bug.
- F9 bare-leading-env: `send-authenticated.sh:16-21` refusal + env-form deny hold; per-seat tokens are upstream (M10; #72 mitigated).
- Firecrawl boot: needs networked host with `--profile web-research up` vs full rabbitmq/nuq-postgres/playwright stack (upstream-watch).
