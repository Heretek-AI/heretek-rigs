# Design: remediate-44-json-trailer

## Why two tracks (local docs now, upstream fix requested)
The trailer lives in upstream `dist/commands/queue.js` — this repo cannot
move it. But every in-fleet failure came from seats/scripts using the bare
form when `--json` already parses clean. Local `--json` discipline stops
the bleeding today with zero dependency on upstream release cadence; the
upstream issue fixes the root cause for all consumers.

## Why BOTH notices in ONE upstream issue
The trailer (`1115-1117`) and the adjacent compact notice (`1118-1123`)
both pollute stdout; moving only one leaves stdout impure under some
config. Filing them together (plus #42's receipt, same stdout-purity
principle) gives upstream a single coherent "stdout MUST be pure JSON"
request instead of three drips. Explicit coordination rule: the #42 spec
references the issue URL filed from THIS change's tasks — file once.

## Why stderr is the right ask (not "valid JSON by default")
Upstream already sends the transitions notice to stderr — the codebase
concedes notices belong off stdout. Asking for default-valid-JSON would be
a bigger behavioral change (breaks humans piping to `head`); stderr keeps
human UX identical while making stdout parseable. Smaller ask, precedent-
backed, harder to refuse.

## Failure modes
- Upstream declines/defers: local discipline already covers the fleet; the
  recorded URL lets future phases re-check. Fail closed — no local monkey-
  patch of `node_modules`/dist.
- New bare examples creep back in: QA greps for bare queue examples as a
  regression gate; charter regen is deterministic.
