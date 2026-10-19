---
name: stride-threat-modeling
description: Decomposes a target system architecture into data flows and generates a comprehensive STRIDE threat model with mitigations.
---

# STRIDE Threat Modeling Procedure

1. Read target architectural ADR and inspect codebase memory for component connections.
2. Map Trust Boundaries (e.g., Public Internet -> API Gateway -> Internal Service -> Database).
3. Evaluate threats across all 6 STRIDE categories:
   - **S**poofing: Identity verification and token impersonation.
   - **T**ampering: In-transit payload tampering and DB record mutation.
   - **R**epudiation: Audit log integrity and non-repudiation proof.
   - **I**nformation Disclosure: Data leaks, unencrypted caches, verbose error messages.
   - **D**enial of Service: Resource exhaustion, algorithmic complexity attacks.
   - **E**levation of Privilege: Missing RBAC guards and IDOR.
4. Formulate concrete mitigation controls for every identified threat.
5. Publish Threat Model in `docs/security/threat-models/`.
6. Dispatch mitigation backlog tickets to `tpm-scrum-lead`.
