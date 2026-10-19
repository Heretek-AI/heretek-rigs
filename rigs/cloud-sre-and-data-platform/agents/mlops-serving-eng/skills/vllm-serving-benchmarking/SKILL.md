---
name: vllm-serving-benchmarking
description: Configures, launches, and benchmarks vLLM/Ollama model serving engines, measuring TTFT and generation tokens/sec.
---

# vLLM Serving Benchmarking Procedure

1. Read model specification and target GPU memory bounds.
2. Select optimal quantization format (e.g., AWQ 4-bit for Ampere/Hopper GPUs, GGUF for CPU/hybrid).
3. Configure vLLM serving parameters in `deploy/mlops/serving.yaml`:
   - Set `--gpu-memory-utilization 0.90`.
   - Set `--max-model-len` and `--tensor-parallel-size`.
4. Deploy container and healthcheck endpoint.
5. Execute throughput benchmark using `vllm.entrypoints.openai.api_benchmark`:
   - Measure Time-To-First-Token (TTFT < 50ms target).
   - Measure aggregate tokens per second across 50 concurrent requests.
6. Verify output responses meet perplexity and quality thresholds.
7. Commit deployment manifests and log benchmark report.
