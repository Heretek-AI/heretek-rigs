# 107-identity M2 — revoke + re-add rotation runbook (REQ-I2)

Date: 2026-10-27. Host: this machine. Worktree: `.lane/trees/107-identity`
(branch `feat/107-identity`).

`rig` 0.7.2 (`8b180689`) offers no expiry/audience/rotation flags
(`rig mcp token add --help` lists only `--seat/--rig/--root/--workspace/--owner`;
M0 §5). Rotation is therefore **revoke + re-add**: the old bearer 401s on
its very next request, the new bearer allows. This document is the operator
runbook (§1) plus its executed-live proof in scratch (§2, REQ-I2 scenario:
revoked-then-represented token refused with 401).

No repo file other than this one was touched for M2. No commit was made.

## §1 Runbook (real environment)

All commands run with the operator's real `OPENRIG_HOME` (default
`~/.openrig/`). The daemon keeps serving throughout: revocation is effective
on the next request, no restart involved (proven §2).

1. Identify the grant (hashes only — tokens are never listed):
   `rig mcp token list --json`
2. Revoke the compromised/rotated grant:
   `rig mcp token revoke <name>`
   Expected: `Revoked <name>: its next request is refused. Its rows and
   records stay.` (`rc=0`). Already-handed-over work stays with its owners.
3. Mint the replacement (same name, same seat + rig scope):
   `rig mcp token add <name> --seat <session> --rig <managed-rig>`
   (`<managed-rig>` is the seat's own rig — the same scope the seeder
   mints with `issue_seat_grant(..., rig=<rig>)` and the same scope the
   F3 reuse check (`_grant_scope_matches`) expects. Omitting `--rig`
   mints a rig-unscoped grant that the next seed will treat as a scope
   mismatch and revoke-and-replace, undoing this rotation.)
   The token prints ONCE — capture it to the secrets file immediately, e.g.
   per the M1 seed path `$HERETEK_SECRETS/mcp-http-<session>.key` (mode 600):
   never paste it on a command line, in chat, or in a file that is committed.
4. Redistribute: seat config picks the new file up through the existing
   `!echo Bearer $(cat ...)` header on the seat's next MCP reconnect
   (no config edit — the header references the file, not the token).
5. Verify, in order (the bearer MUST NEVER appear in a curl argument —
   neither literally nor through shell expansion such as `$(cat file)`
   or `$TOK`, which place the secret in the process argument vector
   visible to `ps`: keep the token in a mode-600 header file holding
   the single line `Authorization: Bearer <token>` and pass it with
   curl's `@file` form (`curl -H @/path/to/auth.header ...`), or pipe
   a header securely with `-H @-`
   (`cat /path/to/auth.header | curl -H @- ...`). Never put
   `Authorization:` on a command line that lands in shell history):
   old token → expect `401` `{"error":"unauthenticated",...}`;
   new token → expect `200`.
6. If step 3's output is unparseable (token unrecoverable): `revoke <name>`
   at once so no live grant with an unknown token lingers, then repeat from
   step 3. The M1 seeder (`scripts/seed-rig.py`) does exactly this
   automatically (revoke-best-effort + fatal exit).

Failure modes (all fail closed): `add` for an existing name refuses
(`'...' already has a grant; revoke it first...`, non-zero exit) — revoke
first; `revoke` for an unknown name refuses (`No grant named ...`) — nothing
changes; token file missing/unreadable while a grant exists refuses EVERY
request until the file is restored or the server restarts grant-free.

## §2 Executed-live evidence (scratch isolation, verbatim)

Isolation: `SCRATCH=/tmp/107-rotate-20261027-012812` (mode 700, marker saved
to `/tmp/107-rotate-latest`). Every `rig` invocation below ran with
`OPENRIG_HOME=$SCRATCH`; the real daemon/state at `~/.openrig/` was never
contacted (verified byte-identical afterwards, §3). Scratch ports: daemon
`127.0.0.1:18433`, grant MCP server `127.0.0.1:18437`. Tokens lived at
`$SCRATCH/tok1` / `$SCRATCH/tok2` (mode 600, scratch-only, never copied
anywhere); below they appear redacted to first/last 2 chars (`or...Tk`,
`or...VE`), exactly as recorded live (`len=47` both).

Daemon start:

```
$ OPENRIG_HOME=$SCRATCH rig daemon start --port 18433 --host 127.0.0.1 --no-kernel
Daemon started on port 18433 (pid 648666)
rc=0
```

Serve (background; banner verbatim from `serve.log`):

```
OpenRig MCP over HTTP at http://127.0.0.1:18437/mcp: no grants, so loopback only, acting as no seat, declared and not authenticated. Add a grant (rig mcp token add) before reaching it through a tunnel or proxy.
```

`ss -ltn` confirmed `127.0.0.1:18433` and `127.0.0.1:18437` listening.

Step A — add `rot-seat` (M1 shape: seat-only, no scope flags):

```
$ OPENRIG_HOME=$SCRATCH rig mcp token add rot-seat --seat rot-session
Token for rot-seat, shown once (only its hash is kept in /tmp/107-rotate-20261027-012812/mcp-http-tokens.json):
or...Tk
The client sends it as: Authorization: Bearer <token>. Revoke it with: rig mcp token revoke rot-seat
rc=0
```

```
$ ls -l $SCRATCH/mcp-http-tokens.json
-rw-------. 1 john john 313 Oct 27 01:28 /tmp/107-rotate-20261027-012812/mcp-http-tokens.json

$ python3 -c "import json; ..."  # token file content
{
  "name": "rot-seat",
  "seat": "rot-session",
  "rigs": [],
  "roots": [],
  "workspace": false,
  "owner": false,
  "tokenSha256": "f1c962805722a53dff7b2ec15a1ea215f9f972ed657035b1c0174c1faf373e4b",
  "createdAt": "2026-10-27T05:28:31.968Z"
}
```

Hash-only storage, mode 600 — matches M0 §1.

Step B — pre-rotation Bearer → 200 (token via file into the header; `curl rc=0`):

```
HTTP/1.1 200 OK
cache-control: no-cache, no-transform
connection: keep-alive
content-type: text/event-stream
x-accel-buffering: no
content-length: 1304
Date: Tue, 27 Oct 2026 05:28:38 GMT

event: message
data: {"result":{... "serverInfo":{"name":"openrig","version":"0.7.2 (8b180689)"} ...},"jsonrpc":"2.0","id":1}
```

(`...` elides the instructions string, byte-identical to the M0 §3 body;
no token material appears in any response body.)

Step C — revoke, then re-present the same token → 401 (REQ-I2 red-proof):

```
$ OPENRIG_HOME=$SCRATCH rig mcp token revoke rot-seat
Revoked rot-seat: its next request is refused. Its rows and records stay.
rc=0
```

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer realm="openrig"
Date: Tue, 27 Oct 2026 05:28:41 GMT
Connection: keep-alive
Keep-Alive: timeout=5
Transfer-Encoding: chunked

{"error":"unauthenticated","message":"This credential isn't valid here: it's unknown or was revoked."}
```

`curl rc=0` (the 401 rides a successful transport, as in M0 §4–§5).

Step D — re-add under the same name (rotation completes):

```
$ OPENRIG_HOME=$SCRATCH rig mcp token add rot-seat --seat rot-session
rc=0
len2=47 same_as_old=False first2=or last2=VE
DIFFERENT
```

A fresh 47-char bearer, different from the revoked one.

Step E — post-rotation matrix (each `curl rc=0`):

```
new-token:200
old-token:401
no-token:401
```

New bearer allows; revoked bearer refuses; missing credential refuses.
Grant state afterwards (`token list --json`, `rc=0`):

```
{
  "configured": true,
  "file": "/tmp/107-rotate-20261027-012812/mcp-http-tokens.json",
  "grants": [
    {
      "name": "rot-seat",
      "seat": "rot-session",
      "rigs": [],
      "roots": [],
      "workspace": false,
      "owner": false,
      "createdAt": "2026-10-27T05:28:44.403Z"
    }
  ]
}
```

## §3 Cleanup (verbatim)

```
$ pkill -f "rig mcp serve.*18437"; OPENRIG_HOME=$SCRATCH rig daemon stop
Daemon stopped
rc=0
$ ss -ltn | grep -E '1843' || echo "(scratch listeners gone)"
(scratch listeners gone)
```

No `rig mcp/daemon` processes remain. Real-state intact check:

```
$ python3 -c "import json; d=json.load(open('/home/john/.openrig/daemon.json')); print(d)"
{'pid': 57353, 'port': 7433, 'host': '127.0.0.1', 'db': '/home/john/.openrig/openrig.sqlite', 'startedAt': '2026-10-23T18:31:27.164Z'}
```

Identical to the M0 pre-spike read. Nothing under `~/.openrig/` was
created, modified, or deleted. Scratch dir `/tmp/107-rotate-20261027-012812`
(mode 700, token files 600) retains the scratch tokens outside the repo.

## §4 Verdict

PASS — rotation = revoke + re-add, executed end-to-end live: pre-rotation
200 → revoke → 401 → re-add → new-token 200 with old-token 401 and
no-token 401. No expiry flags involved (0.7.2 offers none). The §1 runbook
above is exactly what was executed in §2, with `<name>`/`<session>` and the
real `OPENRIG_HOME` substituted.
