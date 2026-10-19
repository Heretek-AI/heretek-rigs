---
name: collision-broadphase-optimization
description: Optimizes spatial partitioning structures (BVH, dynamic AABB trees) to minimize narrow-phase collision pairs.
---

# Collision Broadphase Optimization Procedure

1. Profile current collision pair generation under high entity density.
2. Update spatial tree structure (BVH / Dynamic Tree) with fast rebalancing heuristics.
3. Implement Raycast / AABB query acceleration structures.
4. Verify Continuous Collision Detection (CCD) prevents fast-moving entity tunneling.
5. Execute physics stability test suite (stacking tests, restitution tests).
6. Verify deterministic outcomes across repeated simulation runs.
