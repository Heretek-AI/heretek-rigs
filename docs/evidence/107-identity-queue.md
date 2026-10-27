# 107-identity M3 — queue-half disposition: documented-upstream-blocked (REQ-I3)

Date: 2026-10-27. Worktree: `.lane/trees/107-identity` (branch
`feat/107-identity`).

## Verdict

**The queue/send spoofability half (`OPENRIG_SESSION_NAME` bare-leading
form) is daemon-blocked: no repo-side fix is possible at this scope.**
Per REQ-I3, this note is the M3 deliverable: **no queue-identity code was
added, and no upstream filing was made** (filing needs principal
authorization, which was not granted).

## Evidence (M0 §7, `docs/evidence/107-identity-m0.md`, quoted)

M0 probed a scratch-isolated daemon (`OPENRIG_HOME=/tmp/107-spike-...`,
port 17433; the real daemon was never contacted). Baseline without seat
env fails closed as designed:

```
$ OPENRIG_HOME=$SCRATCH rig queue whoami
--session is required when OPENRIG_SESSION_NAME is not set
rc=1
```

With a spoofed bare-leading seat env, the daemon answers with `rc=0` and
zero challenge — no seat-existence check (`"calling node unavailable"` yet
served), no authentication:

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

The `env`-prefixed form (`env OPENRIG_SESSION_NAME=...`, the shape the
policy layer *can* match) behaves identically (`rc=0`, same body), and
`rig queue whoami --help` confirms `--session` "defaults to
`OPENRIG_SESSION_NAME`" — the daemon takes the env string at face value.

## Why no repo-side fix exists

- The policy layer cannot catch the bare-leading form: pps strips the
  leading `VAR=` assignment before matching (F9), so the
  `*OPENRIG_SESSION_NAME=*` deny never fires on it (see
  `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md:131`, `scripts/gate-role.sh:146`).
- Even the matchable `env`-prefixed form is irrelevant here: the daemon CLI
  path performs no check at all — it serves any string over loopback.
- The MCP HTTP adapter is the authentication boundary (M1/M2 in this
  change); the daemon's loopback trust of the seat header is upstream
  OpenRig behavior, not fleet configuration. Changing fleet files cannot add
  a challenge the daemon never issues.

The current mitigations stay as-is: `scripts/send-authenticated.sh` refuses
when the var is set, and `--source` is `claimed:v1` (claim-only). The queue
half remains claim-only until upstream changes the daemon.

## Scope compliance

- REQ-I3 scenario "blocked half documented, not built": satisfied by this
  note citing the exact M0 probe outputs above.
- `verify-rigs.sh` V22 + `tests/test_bare_queue_send_deny.py` continue to
  guard the seat-map deny side (bare `rig queue list/create` and `rig send`
  denied in every seat's bash map); that guard is unchanged by this change.
- Revisit only if: upstream OpenRig adds daemon-side seat authentication, or
  the principal authorizes an upstream filing. Until then M3 is closed as
  documented-upstream-blocked.
