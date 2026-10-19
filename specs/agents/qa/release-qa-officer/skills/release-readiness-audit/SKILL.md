---
name: release-readiness-audit
description: Audits all verification test reports, security scans, and changelog diffs to issue a binding GO/NO-GO release decision.
---

# Release Readiness Audit Procedure

1. Verify all CI pipelines on the candidate commit passed with zero failures.
2. Confirm sign-offs from specialized QA:
   - Playwright E2E: 100% pass rate.
   - API Contract tests: Zero backward-incompatible changes.
   - k6 Load Test: SLA thresholds satisfied.
   - AppSec: Zero critical or high vulnerabilities.
   - Accessibility: Zero WCAG AA violations.
3. Review git release tag diff: `git log <last_tag>..HEAD --oneline`.
4. If all gates pass: Author `docs/releases/RELEASE-<version>-SIGNOFF.md` marking **DECISION: GO**.
5. If any gate fails: Mark **DECISION: NO-GO**, log blocking GitHub issue, and alert `product-director`.
