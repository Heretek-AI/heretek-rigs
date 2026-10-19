---
name: adversarial-mutation-sabotage
description: Deliberately mutates conditions and injects network faults to verify test suites catch failures and services recover gracefully.
---

# Adversarial Mutation Sabotage Procedure

1. Read the target service code and identify critical logic branches.
2. Formulate chaos scenarios:
   - Sudden database connection drop during write transaction.
   - Malformed JSON/Protobuf payload with boundary-exceeding numbers or negative integers.
   - Downstream service returns continuous 503 or 10-second timeout.
3. Author isolated chaos test in `tests/chaos/`.
4. Run mutation testing inside the piston sandbox (Wave 4 P1-5/P2-11:
   mutation runners execute via the piston code-execution API at
   `http://piston:2000/api/v2/execute` — NEVER as raw toolchain commands
   on the agent host):
   - List available runtimes: `curl -s http://piston:2000/api/v2/runtimes`.
   - Submit the chaos/mutation job: `curl -s -X POST
     http://piston:2000/api/v2/execute` with the language, pinned version,
     and test files as JSON (`run_timeout` capped at 3000ms).
   - For Rust mutation runs use the `rust` runtime with `cargo mutants` as
     the packaged command; for TypeScript use the `javascript`/`typescript`
     runtime with the stryker run as the packaged command.
5. Verify test suites catch the mutations (mutation score > 85%).
6. Generate Resilience Audit Report in `docs/qa/RESILIENCE.md`.
