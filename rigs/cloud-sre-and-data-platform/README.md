# OpenRig Bundle: `cloud-sre-and-data-platform`

Cloud IaC (OpenTofu), Kubernetes orchestration, SRE incident response, observability, DBA migrations, streaming, ETL, analytics, MLOps, RAG, and CVE patching.

## Purpose & Seats (11 Default Boot Seats)
- `platform.cloud-platform-eng` (Cloud Platform Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `platform.k8s-orchestrator` (Kubernetes & Container Orchestrator) — Policy: `builtin:standard`, Thinking: `high`
- `platform.dependency-patcher` (Dependency & CVE Patching Steward) — Policy: `builtin:standard`, Thinking: `high`
- `sre.sre-incident-eng` (Site Reliability Engineer (SRE)) — Policy: `builtin:locked`, Thinking: `high`
- `sre.observability-eng` (Observability & Telemetry Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `data.dba-specialist` (Database Administrator (DBA)) — Policy: `builtin:standard`, Thinking: `high`
- `data.cache-streaming-eng` (Cache & Streaming Systems Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `data.data-pipeline-eng` (Data Pipeline & ETL Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `data.analytics-metrics-eng` (Analytics & Metrics Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `ml.mlops-serving-eng` (MLOps & Model Serving Engineer) — Policy: `builtin:standard`, Thinking: `high`
- `ml.vector-rag-spec` (Vector Search & RAG Specialist) — Policy: `builtin:standard`, Thinking: `high`

## Prerequisites & Setup
See `SETUP.md`. Seed seats with `python3 scripts/seed-rig.py rigs/cloud-sre-and-data-platform/rig.yaml` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/cloud-sre-and-data-platform --json`
- **Validate & preflight**: `(cd rigs/cloud-sre-and-data-platform && rig spec validate rig.yaml --json && rig spec preflight rig.yaml --json)`
- **Launch**: `(cd rigs/cloud-sre-and-data-platform && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)`
- **Stop**: `rig down cloud-sre-and-data-platform`
