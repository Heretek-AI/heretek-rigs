---
name: cache-conscious-ecs-design
description: Audits and optimizes Entity-Component-System data structures for CPU L1/L2 cache locality and SIMD vectorization.
---

# Cache-Conscious ECS Design Procedure

1. Inspect target component layout in `src/engine/ecs/`.
2. Evaluate Struct-of-Arrays (SoA) vs. Array-of-Structs (AoS) representation for high-frequency components.
3. Ensure component structs are packed and properly aligned to CPU cache line boundaries (64 bytes).
4. Profile iteration performance using micro-benchmarks.
5. Eliminate pointer chasing across hot iteration loops.
6. Run engine stress tests to verify zero memory fragmentation or memory leaks.
