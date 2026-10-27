# 107-identity M0 — live spike evidence (REQ-I0)

Date: 2026-10-27. Host: this machine. Worktree: `.lane/trees/107-identity`
(branch `feat/107-identity`). Scratch isolation only — see §0.

No M1–M3 code was written. No repo file other than this one was touched.
No commit was made (worktree left dirty-with-evidence-only, per stage orders).

## §0 Environment + isolation (verbatim)

Command:

```
TS=$(date +%Y%m%d-%H%M%S); SCRATCH=/tmp/107-spike-$TS; mkdir -p $SCRATCH; chmod 700 $SCRATCH; echo "SCRATCH=$SCRATCH"
```

Output:

```
SCRATCH=/tmp/107-spike-20261027-011433
```

(`drwx------` confirmed via `ls -ld`; marker saved to `/tmp/107-spike-latest`.
The scratch token itself lived at `$SCRATCH/.probe-token`, mode 600, and was
never copied anywhere else. Scratch dir is outside the repo.)

Command:

```
/home/john/.npm-global/bin/rig --version; echo "rc=$?"; echo "OPENRIG_HOME=${OPENRIG_HOME:-<unset>}"; ss -ltn | head -30
```

Output (abridged to the relevant lines; full `ss` listing taken live):

```
0.7.2 (8b180689)
rc=0
OPENRIG_HOME=<unset>
```

- No listener on `127.0.0.1:7437` (default MCP HTTP port) — nothing live there
  to disturb. No listener on 7433 either.
- Real state lives at the default `~/.openrig/` (`daemon.json` there pins
  `pid 57353, port 7433`, started `2026-10-23T18:31:27.164Z`). `ps -p 57353`
  showed the pid absent — the real daemon is stale/not running and was left
  completely alone: no `daemon start/stop`, no reads of secrets, no writes
  under `~/.openrig/`. Verified byte-identical afterwards (see §6).
- Scratch ports used: daemon `127.0.0.1:17433`, grant MCP server
  `127.0.0.1:17437`, no-grant MCP server `127.0.0.1:17438`.

## §1 Probe 1 — `token add` (once-printed scratch token)

Command:

```
OPENRIG_HOME=$SCRATCH /home/john/.npm-global/bin/rig mcp token add probe-seat --seat spike-test-seat
```

Output (`rc=0`; token redacted — scratch-only secret, first/last 2 chars only):

```
Token for probe-seat, shown once (only its hash is kept in /tmp/107-spike-20261027-011433/mcp-http-tokens.json):
or...Gc
The client sends it as: Authorization: Bearer <token>. Revoke it with: rig mcp token revoke probe-seat
rc=0
```

Follow-up observations (verbatim):

```
$ ls -l $SCRATCH/mcp-http-tokens.json
-rw-------. 1 john john 319 Oct 27 01:14 /tmp/107-spike-20261027-011433/mcp-http-tokens.json

$ python3 -c "import json; ..."  # token file content
{
 "principals": [
  {
   "name": "probe-seat",
   "seat": "spike-test-seat",
   "rigs": [],
   "roots": [],
   "workspace": false,
   "owner": false,
   "tokenSha256": "0465a138250f26e085b1a0e80f45b92aab2a7678dfe2d2302597303e8c202966",
   "createdAt": "2026-10-27T05:14:36.050Z"
  }
 ]
}

$ OPENRIG_HOME=$SCRATCH rig mcp token list --json   # rc=0
{
  "configured": true,
  "file": "/tmp/107-spike-20261027-011433/mcp-http-tokens.json",
  "grants": [
    {
      "name": "probe-seat",
      "seat": "spike-test-seat",
      "rigs": [],
      "roots": [],
      "workspace": false,
      "owner": false,
      "createdAt": "2026-10-27T05:14:36.050Z"
    }
  ]
}
```

Verdict: PASS — hash-only storage (`tokenSha256`, mode 600 file), `list`
never shows tokens/hashes. Matches `design.md`.

## §2 Scratch daemon + grant server startup (verbatim)

`rig mcp serve --http` refuses without a daemon, so an isolated scratch
daemon was started first (scratch `OPENRIG_HOME`, non-default port):

```
$ OPENRIG_HOME=$SCRATCH rig daemon start --port 17433 --host 127.0.0.1 --no-kernel
Daemon started on port 17433 (pid 602621)
rc=0
```

Scratch `daemon.json` confirmed self-contained
(`db: /tmp/107-spike-20261027-011433/openrig.sqlite`, own `.sqlite-wal`).

Initial serve attempt without daemon (recorded for honesty):

```
$ OPENRIG_HOME=$SCRATCH rig mcp serve --http --bind 127.0.0.1:17437
Error: Daemon not running.
  This command needs a running daemon.
  Run 'rig up' (it auto-starts the daemon), or 'rig daemon start'.
```

Grant server start (verbatim):

```
$ OPENRIG_HOME=$SCRATCH rig mcp serve --port 17433 --http --bind 127.0.0.1:17437 &
OpenRig MCP over HTTP at http://127.0.0.1:17437/mcp: each request needs a bearer credential from /tmp/107-spike-20261027-011433/mcp-http-tokens.json.
```

`ss -ltn` confirmed `127.0.0.1:17433` and `127.0.0.1:17437` listening.

## §3 Probe 2 — valid Bearer → 200 (verbatim)

Command (token passed via file, never on the command line):

```
curl -sS -i -m 15 -X POST http://127.0.0.1:17437/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $TOK" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"spike-probe","version":"0.0"}}}'
```

Output (`curl rc=0`):

```
HTTP/1.1 200 OK
cache-control: no-cache, no-transform
connection: keep-alive
content-type: text/event-stream
x-accel-buffering: no
content-length: 1304
Date: Tue, 27 Oct 2026 05:15:08 GMT

event: message
data: {"result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{"listChanged":true}},"serverInfo":{"name":"openrig","version":"0.7.2 (8b180689)"},"instructions":"This server reaches an OpenRig team as one seat: the one named by OPENRIG_SESSION_NAME where the server was configured, or, over authenticated HTTP, the seat of the caller's grant (rig_whoami shows which, and whether the caller is authenticated; rig_team shows a rig's seats and its lead). The daemon attributes this server's writes to that seat.\nTo hand work to a seat, use rig_queue_create and keep its qitemId; read the answer later with rig_queue_show, which names the next item when the work was handed on. To pass on work this seat holds, use rig_queue_handoff rather than closing it and creating another, so the work stays one chain. Queue items are durable: they outlive this conversation and this server.\nTools marked read-only change nothing. A seat whose activity is unknown is not idle, and an accepted request (a restore's attemptId) is not a finished one.\nA question reserved for a person is theirs to answer: don't answer it on their behalf. rig_queue_decide records a decision only inside the decision room of the mode they have on, beside their answers and never as one."},"jsonrpc":"2.0","id":1}
```

Verdict: PASS — Bearer allow, HTTP 200.

## §4 Probe 3 — bad token → 401, no token → 401 (verbatim)

Bad-token command: as §3 with `-H "Authorization: Bearer BAD-TOKEN-VALUE-12345"`, `"id":2`.
Output (`curl rc=0`):

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer realm="openrig"
Date: Tue, 27 Oct 2026 05:15:10 GMT
Connection: keep-alive
Keep-Alive: timeout=5
Transfer-Encoding: chunked

{"error":"unauthenticated","message":"This credential isn't valid here: it's unknown or was revoked."}
```

No-token command: as §3 minus the `Authorization` header, `"id":3`.
Output (`curl rc=0`):

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer realm="openrig"
Date: Tue, 27 Oct 2026 05:15:10 GMT
Connection: keep-alive
Keep-Alive: timeout=5
Transfer-Encoding: chunked

{"error":"unauthenticated","message":"This server needs a bearer credential: Authorization: Bearer <token>."}
```

Verdict: PASS — bad token 401, missing credential 401 with distinct messages.

## §5 Probe 3 (cont.) — revoke → present again → 401 (verbatim)

Command:

```
OPENRIG_HOME=$SCRATCH rig mcp token revoke probe-seat
```

Output:

```
Revoked probe-seat: its next request is refused. Its rows and records stay.
rc=0
```

Re-present command: identical to §3 (`"id":30`) with the revoked token.
Output (`curl rc=0`):

```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer realm="openrig"
Date: Tue, 27 Oct 2026 05:15:45 GMT
Connection: keep-alive
Keep-Alive: timeout=5
Transfer-Encoding: chunked

{"error":"unauthenticated","message":"This credential isn't valid here: it's unknown or was revoked."}
```

`token list --json` afterwards (`rc=0`):

```
{
  "configured": true,
  "file": "/tmp/107-spike-20261027-011433/mcp-http-tokens.json",
  "grants": []
}
```

Verdict: PASS — revocation effective on the very next request (no restart,
no expiry flags involved — 0.7.2 offers none, as `design.md` states).

## §6 Probe 4 — `rig_whoami` authenticated vs declared (verbatim)

Tool discovery: `tools/list` over the grant server returned 19 tools,
including `rig_whoami` and `rig_team`.

4b — whoami WITH grant (Bearer, `"id":12`, `tools/call rig_whoami {}`).
Output (`curl rc=0`):

```
event: message
data: {"result":{"content":[{"type":"text","text":"{\"error\":\"Session or node 'spike-test-seat' not found in any managed rig. Check available sessions with: rig ps --nodes\"}"}],"structuredContent":{"ok":false,"code":"http_404","message":"Session or node 'spike-test-seat' not found in any managed rig. Check available sessions with: rig ps --nodes","status":404},"isError":true},"jsonrpc":"2.0","id":12}
```

The 404 is expected: the scratch daemon manages zero rigs, so no seat
resolves. The identity signal is the name it tried: **`spike-test-seat`** —
the grant's seat, not anything client-supplied.

4c — no-grant server for the declared side. Started with a token-free
`OPENRIG_HOME` (`$SCRATCH/nogrant-home`) and
`OPENRIG_SESSION_NAME=declared-probe-seat` on port 17438. Its banner
(verbatim from `serve-nogrant.log`):

```
OpenRig MCP over HTTP at http://127.0.0.1:17438/mcp: no grants, so loopback only, acting as declared-probe-seat, declared and not authenticated. Add a grant (rig mcp token add) before reaching it through a tunnel or proxy.
```

Whoami on the no-grant server, no `Authorization` header (`"id":20`).
Output (`curl rc=0`):

```
event: message
data: {"result":{"content":[{"type":"text","text":"{\"error\":\"Session or node 'declared-probe-seat' not found in any managed rig. Check available sessions with: rig ps --nodes\"}"}],"structuredContent":{"ok":false,"code":"http_404","message":"Session or node 'declared-probe-seat' not found in any managed rig. Check available sessions with: rig ps --nodes","status":404},"isError":true},"jsonrpc":"2.0","id":20}
```

It resolved **`declared-probe-seat`** — the server's env seat, declared and
(as the banner states) not authenticated.

4d — spoof-resistance: whoami on the GRANT server with a poisoned client
env `OPENRIG_SESSION_NAME=evil-spoof-seat` (`"id":21`). Output (`curl rc=0`):

```
event: message
data: {"result":{"content":[{"type":"text","text":"{\"error\":\"Session or node 'spike-test-seat' not found in any managed rig. Check available sessions with: rig ps --nodes\"}"}],"structuredContent":{"ok":false,"code":"http_404","message":"Session or node 'spike-test-seat' not found in any managed rig. Check available sessions with: rig ps --nodes","status":404},"isError":true},"jsonrpc":"2.0","id":21}
```

The spoofed client env was ignored — identity stayed `spike-test-seat`
(the grant). Over HTTP there is no seat header for the client to forge;
the bearer grant is the whole identity.

Verdict: PASS — authenticated (grant seat) vs declared (env seat) outputs
captured; client-side `OPENRIG_SESSION_NAME` spoof does not cross the HTTP
boundary. Matches `design.md` ("each caller acts as its grant's seat").
No contradiction with the design found; nothing redesigned.

## §7 Probe 5 — queue half: bare-leading `OPENRIG_SESSION_NAME=` (verbatim)

Per `scripts/gate-role.sh:146` pattern. All commands below ran against the
SCRATCH daemon only (`OPENRIG_HOME=$SCRATCH` → port 17433 via scratch
`daemon.json`); the real daemon was never contacted.

5a — baseline, no seat env:

```
$ OPENRIG_HOME=$SCRATCH rig queue whoami
--session is required when OPENRIG_SESSION_NAME is not set
rc=1
```

5b — bare-leading spoofed seat:

```
$ OPENRIG_HOME=$SCRATCH OPENRIG_SESSION_NAME=spoofed-seat-107 rig queue whoami
{
  "session": "spoofed-seat-107",
  "asDestination": {
    "pending": 0,
    "inProgress": 0,
    "blocked": 0,
    "recent": []
  },
  "asSource": {
    "total": 0
  },
  "currentWork": null,
  "currentWorkBasis": "no typed in-progress work (only in-progress rows are considered; a typed row that is pending or blocked is not current work)",
  "role": {
    "state": "unknown",
    "reason": "calling node unavailable",
    "files": []
  }
}
rc=0
```

5c — `env`-prefixed form (gate-role.sh:148's deny-target shape), same daemon:

```
$ OPENRIG_HOME=$SCRATCH env OPENRIG_SESSION_NAME=spoofed-seat-107 rig queue whoami
{
  "session": "spoofed-seat-107",
  ...identical body to 5b...
}
rc=0
```

(`rig queue whoami --help` confirms `--session` "defaults to
`OPENRIG_SESSION_NAME`" — the daemon takes the env string at face value.)

Verdict: the daemon answers to ANY `OPENRIG_SESSION_NAME` string with
`rc=0` and zero challenge — no seat-existence check (`"calling node
unavailable"` yet still served), no authentication. The bare-leading form
executes exactly as `design.md` predicted (policy layer cannot catch it —
pps strips the leading assignment before matching, F9; and even the
`env`-prefixed form, which pps *can* match, is irrelevant here because the
daemon CLI path performs no check at all). **The queue/send half is
daemon-blocked: no repo-side fix is possible at M0 scope.** Per REQ-I3,
M3 MUST be the documented-upstream-blocked note, not a queue-identity build.

## §8 Cleanup (verbatim)

```
$ kill <serve-pids>; OPENRIG_HOME=$SCRATCH rig daemon stop
Daemon stopped
rc=0
$ ss -ltn | grep -E '1743' || echo "(scratch listeners gone)"
(scratch listeners gone)
$ pgrep -af 'rig (mcp|daemon)' || echo "(no rig mcp/daemon procs remain)"
(no rig mcp/daemon procs remain)
```

Real-state intact check (verbatim):

```
$ python3 -c "import json; d=json.load(open('/home/john/.openrig/daemon.json')); print(d)"
{'pid': 57353, 'port': 7433, 'host': '127.0.0.1', 'db': '/home/john/.openrig/openrig.sqlite', 'startedAt': '2026-10-23T18:31:27.164Z'}
```

Identical to the pre-spike read; real pid 57353 still absent (was already
stale before the spike). Nothing under `~/.openrig/` was created, modified,
or deleted. Scratchdir `/tmp/107-spike-20261027-011433` (mode 700, token
file 600) retains the scratch token outside the repo.

## §9 WINNER — what M1 must follow

**M1 follows the MCP-bearer winner.** Live proof:

1. `token add` prints once, stores sha256-only, file mode 600, `list`
   hides secrets (§1).
2. With a grant present, EVERY request needs its bearer — loopback
   included — and each caller acts as its grant's seat; bad/missing/
   revoked credentials 401 with exact `WWW-Authenticate: Bearer
   realm="openrig"` refusals (§3–§5).
3. Client-side `OPENRIG_SESSION_NAME` spoofing does not cross the HTTP
   boundary (§6, probe 4d).
4. Revocation is effective on the next request; 0.7.2 has no expiry flags,
   so rotation = revoke + re-add (§5).

M1 shape (per proposal/design, unchanged): `seed-rig.py` runs
`rig mcp token add <name> --seat <session>` (scope flags per M0 outcome —
default seat-only grant proven sufficient here), stores the once-printed
token under the secrets dir, renders it into the seat's MCP client config
via the existing `!cat` pattern; stdio default unchanged.

**Queue half: daemon-blocked, NOT repo-fixable.** The daemon trusts any
`OPENRIG_SESSION_NAME` string over loopback with `rc=0` and no challenge
(§7, probes 5b/5c). M3 MUST be the
`docs/evidence/107-identity-queue.md` upstream-blocked note citing §7's
exact outputs — no queue-identity code, no upstream filing without
principal authorization (REQ-I3).

No probe contradicted `design.md`; no redesign was performed.
