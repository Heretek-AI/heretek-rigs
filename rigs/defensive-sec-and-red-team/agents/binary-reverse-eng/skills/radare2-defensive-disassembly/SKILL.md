---
name: radare2-defensive-disassembly
description: Disassembles and analyzes binary functions using radare2/r2mcp to map out memory layouts, string tables, and control flows.
---

# Radare2 Defensive Disassembly Procedure

1. Ingest target binary into Radare2 workspace.
2. Analyze all symbols and control flow graphs: `r2 -q -c "aaa; afl" <binary>`.
3. Extract string references and imports: `r2 -q -c "iz; ii" <binary>`.
4. Inspect candidate entry points and message handlers:
   - Decompile function to pseudo-C.
   - Trace buffer offsets, length headers, and checksum validations.
5. Author reverse-engineered protocol schema in `docs/protocols/`.
6. Provide safe Rust/C struct definition with verified field byte offsets.
