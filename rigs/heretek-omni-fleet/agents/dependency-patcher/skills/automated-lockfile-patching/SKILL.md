---
name: automated-lockfile-patching
description: Upgrades dependencies in lockfiles, executes test suites, and verifies zero regressions or broken peer dependencies.
---

# Automated Lockfile Patching Procedure

1. Read CVE advisory or scheduled dependency upgrade target.
2. Create an isolated patch branch: `git checkout -b patch/<package>-<version>`.
3. Apply version update in package manifest and lockfile:
   - For Node: `npm update <package>` or `npm install <package>@<version>`.
   - For Rust: `cargo update -p <package>`.
   - For Python: `uv lock --upgrade-package <package>`.
   - For Go: `go get <package>@<version> && go mod tidy`.
4. Run static analysis and lint checks: confirm zero compile errors or peer dependency conflicts.
5. Execute full test suite: confirm 100% test pass rate.
6. Commit lockfile with detailed message referencing CVE ID or release notes.
7. Open PR and assign to `release-qa-officer`.
