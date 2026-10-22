# Design: remediate-42-create-receipt

## Why mandate --json --verify (not just --json)
Bare `create` under `output.compact` returns an advisory sentence that is
explicitly "not proof of persistence". `--json` fixes the shape; `--verify`
fixes the semantics (row actually persisted, state known). Mandating the
pair closes both gaps in one form, matching the issue's returnable: a
single call yields qitemId + state with no follow-up.

## Why the wrapper parses (not just documents)
`scripts/send-authenticated.sh` is the sole local create wrapper and the
fleet's authenticated-delivery path. Prose alone leaves every caller to
hand-roll receipt parsing (the exact failure family as #44). Parsing in
the wrapper, fail-closed, turns the discipline into a guarantee for all
callers at once.

## Why one shared upstream issue with #44
#42's receipt and #44's notices are one principle: stdout MUST be pure
JSON, human hints go to stderr. Two issues would split upstream attention
and risk inconsistent resolution (notices moved, receipt forgotten). The
#44 package files the issue; this package links it. Filing order matters:
if the #44 package has not filed yet, THIS change's implementer waits for
(or coordinates with) that URL rather than filing a duplicate.

## Failure modes
- `--verify` flag drift across CLI versions: wrapper pins behavior against
  `@openrig/cli@0.6.13`; version bumps re-run the parse proof (tasks T3).
- Upstream ships JSON receipt natively: wrapper parsing becomes a harmless
  pass-through; docs updated to the native form in a follow-up (no rework
  needed here — fail-closed parsing accepts valid JSON either way).
- Wrapper change breaks authenticated delivery: `make verify` + dry-run
  (`--dry-run` prints the exact invocation, executes nothing) gate it
  before any live send.
