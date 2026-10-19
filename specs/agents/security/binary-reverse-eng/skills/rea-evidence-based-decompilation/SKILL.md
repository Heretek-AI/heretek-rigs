---
name: rea-evidence-based-decompilation
description: Performs deep evidence-based decompilation, symbol reconstruction, and control-flow graph extraction using REA and Ghidra.
---

# REA Evidence-Based Decompilation Procedure

1. Ingest compiled binary or shared library into REA via `rea_load_binary`.
2. Generate control flow graph (CFG) for target routines via `rea_get_cfg`.
3. Execute headless Ghidra decompilation pass via `rea_decompile_function`.
4. Trace cross-references (xrefs) to data buffers and network socket read/write calls:
   `rea_get_xrefs --symbol recv --direction inbound`.
5. Perform semantic symbol renaming on opaque identifiers:
   `rea_rename_symbol --old "FUN_00401230" --new "parse_packet_header"`.
6. Extract serialized message structs, endianness byte orders, and magic headers.
7. Author clean-room protocol specification in `docs/protocols/SPEC-<name>.md`.
