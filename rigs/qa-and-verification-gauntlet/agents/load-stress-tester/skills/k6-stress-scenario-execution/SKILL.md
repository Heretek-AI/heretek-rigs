---
name: k6-stress-scenario-execution
description: Authors and runs k6 load test scripts asserting throughput, latency thresholds, and error rates under stress.
---

# k6 Stress Scenario Execution Procedure

1. Read performance SLA requirements (Target RPS, p95/p99 latency bounds).
2. Author modular k6 script in `tests/load/`:
   - Define stages: Ramp-up (e.g. 100 -> 1000 VUs), Steady-state (10m), Ramp-down.
   - Configure thresholds: `http_req_failed: ['rate<0.01']`, `http_req_duration: ['p(95)<250']`.
   - Implement realistic payload generation with checks and metrics.
3. Validate script syntax locally: `k6 check tests/load/script.js`.
4. Execute load run against isolated staging target: `k6 run tests/load/script.js`.
5. Analyze summary metrics and identify breaking point.
6. Commit test script and log results in `docs/perf/LOAD_REPORT.md`.
