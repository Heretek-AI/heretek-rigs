# Design: remediate-37-id-discipline

## Why local discipline, not an upstream fix
`rig` is upstream `@openrig/cli@0.6.13` and this repo owns zero queue
rendering code. Live verification refuted the truncation claim: `list`
already emits full 37-char IDs. The failure mode was a confabulated suffix
after viewing a shortened form — a seat-side habit, fixed by a seat-side
rule. Filing an upstream issue for non-buggy output would burn upstream
goodwill for zero gain.

## Why --json as the source of truth (not "eyeball the table")
Table layouts may wrap, truncate, or ellipsize at any terminal width or
future CLI version; `--json` output is field-exact and machine-copyable.
Mandating the JSON form future-proofs the rule against any rendering change.

## Alternatives rejected
- `--full-ids` flag request: nothing to flag — IDs are already full.
- Short stable refs: new addressing scheme for a non-problem; adds
  alias-resolution failure modes.
- Local CLI wrapper: out-of-scope machinery; docs + charter text suffices.

## Failure modes
- Seats ignore prose and retype anyway: mitigated by making `--json` the
  only form shown in examples (no bare form to copy from) and by QA
  red-proof (deliberately truncated ID MUST fail closed with not-found,
  proving the rule load-bearing).
- Regen drift: generator patch replays deterministically; `make verify`
  22/0 gates it. Dirty-tree refusal is issue #43's domain, not this change.
