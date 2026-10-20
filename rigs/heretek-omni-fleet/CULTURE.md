# Heretek Fleet Culture & Operating Constitution

- Evidence over assertion: every claim of done carries the command that proves it and its output (`verification-before-completion`).
- A denial names one command and one rule: retry the exact command bare (one command per `bash` call, never chained) and quote `command` + `matchedPattern` from the permission review log before claiming a capability is missing.
- Delivery claims carry queue item ids (`qitem-...`); without one the work is `PENDING_DISPATCH`, never `DISPATCHED`.
- Zero stubs, fail closed, least privilege. A permission denial from `@gotgenes/pi-permission-system@41.0.0` is a hand-off, never a puzzle to work around.
- Small slices: one queue item, one verifiable outcome. Hand off with `rig queue` and state what is next.
- Secrets never appear in messages, `rig.yaml` `env:`, files, transcripts, or command lines; they resolve exclusively via `0600` command-backed `!cat` references.
