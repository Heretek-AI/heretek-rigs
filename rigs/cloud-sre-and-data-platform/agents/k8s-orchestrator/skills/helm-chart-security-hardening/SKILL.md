---
name: helm-chart-security-hardening
description: Audits and packages Kubernetes Helm charts to enforce non-root security contexts, resource requests/limits, and network policies.
---

# Helm Chart Security Hardening Procedure

1. Read deployment requirements and container image specifications.
2. Configure Helm chart templates in `deploy/charts/<service>/`:
   - Set `securityContext.runAsNonRoot: true`, `readOnlyRootFilesystem: true`, and drop all capabilities (`drop: ["ALL"]`).
   - Define explicit `resources.requests` and `resources.limits` for CPU and Memory.
   - Configure liveness, readiness, and startup probes.
   - Add default-deny `NetworkPolicy` permitting only necessary ingress/egress.
3. Lint chart: `helm lint deploy/charts/<service>/`.
4. Validate with dry-run: `helm template test deploy/charts/<service>/ | kubeconform -strict`.
5. Commit chart updates and publish to git repository.
