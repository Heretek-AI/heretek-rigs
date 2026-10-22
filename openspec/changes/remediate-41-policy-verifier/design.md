# Design: remediate-41-policy-verifier

## Why one verifier, minimal (option (c))
Lint-table names and workflow `run:` lines are the same defect class
("text nothing executes is text nothing checks", #41) and share the same
trigger point (stage time, before QA handoff) and the same I/O shape
(parse staged text files, resolve names against an authority, fail closed).
Two separate tools would duplicate the staging-scan, the `make`/gate
wiring, and the diagnostics format. One script, two sub-checks, one exit
code. Anything beyond these two classes (levels, priorities, shell
semantics, schema language) is explicitly out — scope creep here rebuilds
clippy.

## Authority sources
- Lint names: local toolchain preferred (always current), checked-in
  snapshot fallback (offline/deterministic). Snapshot staleness risk:
  snapshot file carries the toolchain version it was taken from; on
  toolchain-pin bump, a mismatch between snapshot pin and repo toolchain
  pin MUST fail with "snapshot stale, refresh" rather than silently
  passing. Refresh is a deterministic command (`rustc -W help` capture),
  reviewable as a diff.
- Script names: staged `package.json` files only (same offline
  manifest-text principle as the #40 manifest-closure lint; the two tools
  SHOULD share the package-script parser at implementation time but MUST
  remain separately invokable so either gate fires independently).

## Fail-closed modes
- Unknown lint name → `unknown lint: <tool>::<name>` at file:line,
  non-zero exit (mirrors the clippy error that caught `cast_lossy` late).
- Unresolvable `run:` reference → file:line + command, non-zero exit.
- Unparseable TOML/YAML, missing toolchain + missing snapshot, stale
  snapshot pin → non-zero exit, never skip-silent.

## Risks
- Toolchain lint-list output formats differ across versions; parser pins
  to the repo's toolchain and its snapshot, and version drift fails
  loudly (stale-snapshot rule) instead of drifting silently — the exact
  failure mode this verifier exists to kill.
- Overlap with the #40 manifest-closure lint on `pnpm <name>` resolution:
  intentional defense in depth (closure asks "is the binary declared",
  this asks "does the workflow command name a real script"); shared
  parser, separate verdicts.
