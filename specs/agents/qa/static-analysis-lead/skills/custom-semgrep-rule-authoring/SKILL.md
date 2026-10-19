---
name: custom-semgrep-rule-authoring
description: Authors and tests custom Semgrep rules to detect proprietary anti-patterns and code style deviations across repositories.
---

# Custom Semgrep Rule Authoring Procedure

1. Identify anti-pattern (e.g., direct usage of unvalidated user input or un-sandboxed process execution).
2. Author a YAML rule in `rules/semgrep/<rule-id>.yml` defining:
   - Pattern / Pattern-Inside / Pattern-Not.
   - Informative error message with remediation guidance.
   - Severity: ERROR or WARNING.
3. Test rule against positive and negative code test cases: `semgrep --config=rules/semgrep/<rule-id>.yml --test`.
4. Run full repository scan via Semgrep MCP.
5. Commit custom rule to repository configuration.
