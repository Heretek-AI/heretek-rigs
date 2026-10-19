---
name: idiomatic-go-service-development
description: Implements Go microservices using standard project layout, table-driven tests, and structured context propagation.
---

# Idiomatic Go Service Development Procedure

1. Inspect project layout (`cmd/`, `internal/`, `pkg/`) using `codebase-memory-mcp`.
2. Ensure every I/O operation accepts `ctx context.Context` as its first parameter.
3. Implement business logic with clear interface abstractions and explicit error checks (`if err != nil`).
4. Write table-driven unit tests covering happy paths and edge cases.
5. Verify race condition safety: `go test -race ./...`.
6. Run static analysis: `golangci-lint run ./...`.
