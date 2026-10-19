---
name: shader-compilation-and-validation
description: Validates and cross-compiles GLSL/HLSL/WGSL shaders to SPIR-V, checking syntax, register pressure, and portable GPU compatibility.
---

# Shader Compilation and Validation Procedure

1. Read shader source file from `src/shaders/`.
2. Inspect pipeline uniform and storage buffer bindings.
3. Validate shader syntax using the official toolchain:
   - For WGSL: Execute `naga <file.wgsl>` to verify WebGPU validity.
   - For GLSL: Execute `glslangValidator -V <file.glsl> -o <file.spv>`.
4. Inspect reflection data to verify binding indices match host CPU structs.
5. Check memory alignment: Verify std140/std430 padding invariants.
6. Run automated rendering integration test or headless mock test.
