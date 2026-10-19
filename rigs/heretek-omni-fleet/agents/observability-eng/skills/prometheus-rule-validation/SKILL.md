---
name: prometheus-rule-validation
description: Validates Prometheus PromQL alerting and recording rules using promtool unit test specifications.
---

# Prometheus Rule Validation Procedure

1. Read SLI/SLO requirements for the target service.
2. Author PromQL alerting rule with appropriate `for:` duration to prevent alert flapping.
3. Include critical annotations (`summary`, `description`, `runbook_url`).
4. Write Promtool unit tests defining synthetic input series and expected firing alerts.
5. Validate syntax with `promtool check rules <rules.yml>`.
6. Run unit tests with `promtool test rules <test.yml>`.
7. Commit validated alerting configuration to `deploy/prometheus/`.
