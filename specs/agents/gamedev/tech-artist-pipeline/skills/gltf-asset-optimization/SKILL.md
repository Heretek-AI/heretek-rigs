---
name: gltf-asset-optimization
description: Optimizes 3D glTF/GLB models using meshopt compression, texture resizing, and Basis Universal KTX2 encoding.
---

# glTF Asset Optimization Procedure

1. Inspect incoming 3D model with `gltf-transform inspect <model.glb>`.
2. Check polygon counts, material counts, and texture dimensions against platform budget.
3. Run optimization pipeline:
   - Deduplicate accessors and prune unused nodes.
   - Re-index vertices and optimize cache locality with meshoptimizer.
   - Compress textures to KTX2 with UASTC or ETC1S.
4. Verify vertex bone weights (maximum 4 influences per vertex).
5. Output optimized asset to `assets/processed/`.
6. Emit validation report verifying zero visual degradation.
