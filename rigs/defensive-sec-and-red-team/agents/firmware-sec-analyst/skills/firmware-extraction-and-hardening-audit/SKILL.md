---
name: firmware-extraction-and-hardening-audit
description: Extracts embedded firmware images, verifies filesystem integrity, and audits binary compiler hardening protections.
---

# Firmware Extraction and Hardening Audit Procedure

1. Ingest raw firmware image.
2. Scan and extract components: `binwalk -e -M <firmware.bin>`.
3. Inspect kernel and executable binaries:
   - Verify ELF headers: `readelf -h -l <binary>`.
   - Run hardening check: `checksec --file=<binary>`.
   - Check for: Stack Canaries, NX (No-Execute stack), ASLR (PIE), and RELRO.
4. Search for hardcoded private keys, default credentials, or debug UART backdoors.
5. Document vulnerabilities and author Firmware Security Audit Report in `docs/security/firmware/`.
6. File hardening requirements for embedded build pipelines.
