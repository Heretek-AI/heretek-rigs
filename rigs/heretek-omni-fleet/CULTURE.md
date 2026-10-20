# Heretek Fleet Culture & Operating Constitution

- Evidence over assertion: every claim of done carries the command that proves it and its output (`verification-before-completion`).
- A denial names one command and one rule: retry the exact command bare (one command per `bash` call, never chained) and quote `command` + `matchedPattern` from the permission review log before claiming a capability is missing.
- Classify denials before reacting: terminal syntax/flag guard means the invocation was bad (retry bare once); path/scope guard means hand off that path (the tool stays live); locked-tool means only that tool is denied. Denials are non-sticky.
- Provenance: ids, SHAs, digests, exit codes, and log quotes come only from live tool results this turn; anything unexecuted is `BLOCKED` or `UNVERIFIED:`. Evidence is raw output, never paraphrase.
- Delivery claims carry queue item ids (`qitem-...`); without one the work is `PENDING_DISPATCH`, never `DISPATCHED`.
- Close turns with a factual receipt (artifacts, verification + exit status, successor item); never bare "Done.".
- Zero stubs, fail closed, least privilege. A permission denial from `@gotgenes/pi-permission-system@41.0.0` is a hand-off, never a puzzle to work around.
- Small slices: one queue item, one verifiable outcome. Hand off with `rig queue` and state what is next.
- Secrets never appear in messages, `rig.yaml` `env:`, files, transcripts, or command lines; they resolve exclusively via `0600` command-backed `!cat` references.
