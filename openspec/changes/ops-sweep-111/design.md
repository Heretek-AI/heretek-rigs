# Design: why guarded sweep, why no code change

## Why sweep is safe today
21/21 legacy, single owner (invoking user), no secret shapes, no live holders, regenerable content (V8 code-cache + 2-byte stubs). Guards (`-d && ! -L && -O`, legacy glob, liveness re-check) mirror `seat-sandbox.sh:60`'s own predicate, so the sweep cannot exceed what the sandbox already deletes for its own dirs.

## Why not broaden the sweeper in code
`seat-sandbox.sh:54` "left alone" is deliberate per #110 (avoid deleting another seat's or another tool's scratch on shared hosts). Broadening needs a #111 decision with cross-host analysis — out of scope. This change deletes today's known-orphans only.

## Failure modes
- A dir becomes held/owned-different between recon and sweep → guard skips it, sweep reports SKIP (fail-closed, never force). Leftover dirs are re-listed, never forced.
- Fresh pid-namespaced dirs appear mid-sweep → glob excludes them by construction.
- 408-vs-21 delta → recorded as unexplained, not resolved; evidence bounds claims to today's 21.
