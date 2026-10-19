---
name: openapi-contract-verification
description: Validates OpenAPI specifications against Spectral style guides and executes Newman automated API contract tests.
---

# OpenAPI Contract Verification Procedure

1. Inspect modified OpenAPI spec using `mcp-openapi-schema-explorer`.
2. Run Spectral linting: `npx spectral lint openapi.yaml`.
3. Check backward compatibility against main branch baseline:
   - Verify no deleted endpoints or changed parameter requirements.
   - Verify no changed status response schemas.
4. Execute automated Newman API collection runner:
   `npx newman run tests/api/collection.json -e tests/api/env.json --reporters cli,json`.
5. Run property-based testing: `schemathesis run openapi.yaml --base-url=http://localhost:8000`.
6. Assert zero unhandled 500 internal server errors.
