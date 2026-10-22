# Proposal: remediate-37-id-discipline — seat-side qitem ID discipline (no upstream change)

## Status
Spec proposal for heretek-rigs issue #37. Specs only — no implementation in this package.

## Verified facts (encoded, not re-litigated)
- `rig` is upstream `@openrig/cli@0.6.13`; this repo contains zero local queue
  rendering code, so there is nothing to fix upstream for #37.
- #37 truncation claim was REFUTED live: bare `rig queue list` already emits
  full 37-character qitem IDs. The night's 4 `qitem_not_found` failures came
  from a confabulated ID suffix reconstructed after viewing a shortened form —
  operator error, not CLI truncation.
- Local seat-side discipline is therefore the complete fix: never retype an ID,
  always copy it from `--json` output.

## Change (local only)
1. Patch the generated seat-charter queue primer in
   `scripts/generate-rigs.py` (~line 701, bare ``rig queue list``) so seats
   are told to list with `--json` and to copy IDs verbatim from that output.
2. Patch every bare queue example in operator docs:
   `docs/USER_GUIDE.md` (~line 215, plus the `queue create` example ~line 226),
   `README.md` (~line 61), and the `AGENTS.md` queue-workflow row (~line 29)
   to append `--json` and state the copy-never-retype rule.
3. Add the rule to the root `AGENTS.md` daily-workflows queue row:
   copy qitem IDs only from `--json` output, never retype or reconstruct them.

## Non-goals
- NO upstream change (nothing to fix upstream — list output is already full-ID).
- No `--full-ids` flag request, no short-stable-ref scheme, no CLI wrapper.
- No behavior change to `rig` invocation beyond adding `--json` to examples.

## Acceptance
- `openspec validate remediate-37-id-discipline` passes clean.
- Implementer checklist in `tasks.md` is fully testable (grep + live
  copy-paste proof: an ID copied from plain `rig queue list` feeds
  `rig queue show <id>` with zero failures).
