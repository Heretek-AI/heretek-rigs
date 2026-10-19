---
name: docs-as-code-synchronization
description: Inspects recent codebase changes and updates corresponding documentation, API references, and runbooks.
---

# Docs-as-Code Synchronization Procedure

1. Run `git diff` against the last documentation baseline commit.
2. Identify changed public APIs, CLI flags, configuration parameters, and models.
3. Query `codebase-memory-mcp` to identify callers and related documentation references.
4. Update the relevant documentation in `docs/`:
   - Keep code blocks updated with real, runnable syntax.
   - Maintain clear headings and table of contents.
5. Validate markdown formatting and internal links.
6. Commit changes with a descriptive docs commit message (`docs: update API reference for v2.1`).
