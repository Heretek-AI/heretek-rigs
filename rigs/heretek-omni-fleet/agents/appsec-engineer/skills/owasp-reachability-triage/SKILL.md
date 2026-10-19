---
name: owasp-reachability-triage
description: Runs SAST analysis and traces call paths via codebase memory to verify whether a reported vulnerability is genuinely reachable.
---

# OWASP Reachability Triage Procedure

1. Ingest security finding from Semgrep or Trivy scanner.
2. Query `codebase-memory-mcp` using `trace_path` to find all call paths from public HTTP/gRPC ingress routes to the flagged sink function.
3. Determine reachability:
   - If user input passes through unvalidated / unescaped: Classify as **CONFIRMED VULNERABILITY**.
   - If input is strictly validated by schema (e.g., Zod, Pydantic) or route is private: Classify as **LOW RISK / MITIGATED**.
4. Calculate CVSS 3.1 score based on exploitability and impact.
5. Author Security Advisory in `docs/security/advisories/SEC-<id>.md`.
6. File blocking issue with remediation patch recommendations to `tpm-scrum-lead`.
