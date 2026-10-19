---
name: rust-async-service-hardening
description: Builds or refactors asynchronous Rust services ensuring cancellation safety, structured concurrency, and zero clippy warnings.
---

# Rust Async Service Hardening Procedure

1. Read ticket spec and trace existing crate dependencies via `codebase-memory-mcp`.
2. Implement requested feature adhering to idiomatic Rust:
   - Handle errors with `thiserror` for library crates and `anyhow` for binaries.
   - Ensure async futures are cancellation-safe (no data loss if dropped).
   - Document any `unsafe` block with a `// SAFETY:` invariant explanation.
3. Run compiler verification: `cargo check --all-targets`.
4. Run Clippy with pedantic rules: `cargo clippy -- -D warnings`.
5. Run test suite: `cargo test --all`.
6. Run security audit: `cargo audit`.
