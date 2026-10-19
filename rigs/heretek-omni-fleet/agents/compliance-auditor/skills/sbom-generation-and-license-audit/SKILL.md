---
name: sbom-generation-and-license-audit
description: Scans all repository lockfiles, generates CycloneDX SBOMs, and audits licenses against enterprise policy.
---

# SBOM Generation and License Audit Procedure

1. Scan repository lockfiles using `syft`: `syft dir:. -o cyclonedx-json=sbom/cyclonedx.json`.
2. Parse all detected software licenses.
3. Enforce license compliance rules:
   - **APPROVED**: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC.
   - **RESTRICTED**: LGPL-2.1/3.0 (allowed only if dynamically linked without code modifications).
   - **BANNED IN PROPRIETARY LIBS**: AGPL-3.0, GPL-2.0, GPL-3.0, SSPL.
4. If a banned license is detected: Immediately file a blocking issue to remove or replace the package.
5. Generate License Inventory report in `docs/compliance/LICENSES.md`.
6. Commit SBOM and report to repository.
