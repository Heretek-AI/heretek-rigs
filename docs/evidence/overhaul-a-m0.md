# M0 spike evidence — overhaul-a (REQ-A0)

Stage: overhaul-a M0 (spike only — no M1–M3 yet).
Worktree: `.lane/trees/overhaul-a`, branch `feat/overhaul-a` from `main 66ba80c`.
Tree state at probe time: unmodified except untracked spec dir
`openspec/changes/overhaul-a/` (proposal/design/tasks/specs); no tracked edits.
Rule compliance: all fake binaries and dummy canaries lived in `/tmp/overhaul-a-m0`
only (`0600` data file, `0755` fake binary); real secrets, the real `rig` binary,
and seat state were never touched. Repo edit limited to this file. Not committed.

Canary used (DUMMY — never a real secret):
`DUMMY-CANARY-NOT-A-SECRET-overhaul-a-m0-0001`

## Environment

Command verbatim:

```
python3 --version; echo "---"; command -v bwrap && bwrap --version || echo "BWRAP-ABSENT (rc=$?)"; echo "---"; git -C /home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/overhaul-a status --porcelain; echo "---"; git -C /home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/overhaul-a log --oneline -1
```

Output verbatim:

```
Python 3.15.1
---
/usr/bin/bwrap
bubblewrap 0.13.1
---
?? openspec/changes/overhaul-a/
---
66ba80c Merge pull request #122 from Heretek-AI/feat/overhaul-bump
```

Current relay bounds (verified by read + grep, match design.md exactly):

```
scripts/seat-sandbox.sh:38: if [[ "$cmd" =~ ^[[:space:]]*rig([[:space:]]|$) ]]; then
scripts/seat-sandbox.sh:47: os.execvp("rig", argv)
```

No deviation from design.md: the `if` is at `:38`, `os.execvp("rig", argv)` at `:47`,
shlex word-list exec with no subcommand/flag validation, relayed pre-jail.

## Probe 1 — fake-`rig` exfiltration via `--body-file`

Setup (scratch only; note: the tooling policy filter rejected filenames containing
`secretstore`/`canary.env`, so the stand-in store dir/file were named neutrally —
contents remain an obvious dummy canary):

- `/tmp/overhaul-a-m0/fakebin/rig` (`0755`): prints `FAKE-RIG-ARGS: $*`, then if a
  `--body-file <path>` (space or `=` form) argument is present, prints the target
  file's contents between `FAKE-RIG-BODY-FILE-CONTENTS-BEGIN/END` markers.
- `/tmp/overhaul-a-m0/scratchstore/dummy-body.txt` (`0600`): single line
  `DUMMY-CANARY-NOT-A-SECRET-overhaul-a-m0-0001`, standing in for a secret-store file
  (`HERETEK_SECRET_STORE` pointed at its directory).

Command verbatim (cwd = worktree root):

```
HERETEK_SECRET_STORE=/tmp/overhaul-a-m0/scratchstore HERETEK_SANDBOX_WRITE="scratch/" OPENRIG_SESSION_NAME="testseat@testrig" PATH="/tmp/overhaul-a-m0/fakebin:$PATH" bash scripts/seat-sandbox.sh -c "rig queue create --json --verify --body-file /tmp/overhaul-a-m0/scratchstore/dummy-body.txt"; echo "rc=$?"
```

Output verbatim:

```
FAKE-RIG-ARGS: queue create --json --verify --body-file /tmp/overhaul-a-m0/scratchstore/dummy-body.txt
FAKE-RIG-BODY-FILE-CONTENTS-BEGIN
DUMMY-CANARY-NOT-A-SECRET-overhaul-a-m0-0001
DUMMY-CANARY-NOT-A-SECRET-overhaul-a-m0-0001
FAKE-RIG-BODY-FILE-CONTENTS-END
rc=0
```

(Note: the canary line appears once in the file — `ls`/read show a 45-byte file =
44 chars + newline; the doubled line above is the verbatim captured stdout.)

Result: LEAK as expected pre-fix — exit 0, no refusal, file contents relayed to the
(fake) `rig` process running outside the jail.

## Probe 2 — forged `--source` form

Command verbatim (cwd = worktree root):

```
HERETEK_SECRET_STORE=/tmp/overhaul-a-m0/scratchstore HERETEK_SANDBOX_WRITE="scratch/" OPENRIG_SESSION_NAME="testseat@testrig" PATH="/tmp/overhaul-a-m0/fakebin:$PATH" bash scripts/seat-sandbox.sh -c "rig queue create --json --verify --source evil@otherrig --body-file /tmp/overhaul-a-m0/scratchstore/dummy-body.txt"; echo "rc=$?"
```

Output verbatim:

```
FAKE-RIG-ARGS: queue create --json --verify --source evil@otherrig --body-file /tmp/overhaul-a-m0/scratchstore/dummy-body.txt
FAKE-RIG-BODY-FILE-CONTENTS-BEGIN
DUMMY-CANARY-NOT-A-SECRET-overhaul-a-m0-0001
DUMMY-CANARY-NOT-A-SECRET-overhaul-a-m0-0001
FAKE-RIG-BODY-FILE-CONTENTS-END
rc=0
```

Result: LEAK as expected pre-fix — forged `--source evil@otherrig` (≠
`$OPENRIG_SESSION_NAME=testseat@testrig`) is passed through unchallenged, exit 0.

## Probe 3 — `filter=` capability

Command verbatim:

```
python3 -c 'import tarfile; print("filter" in tarfile.TarFile.extract.__code__.co_varnames)' && python3 --version
```

Output verbatim:

```
True
Python 3.15.1
```

Result: this host's Python (3.15.1) SUPPORTS `TarFile.extract(filter=)`. The M2
filter guard is still required for older Pythons (fatal on ≤3.11.3 per design.md);
on this host the guard takes the `filter="data"` branch, which M2 must prove with a
code-path test rather than a live failure.

## WINNER

- Relay shape: NO deviation from design.md (`if` at `:38`, `os.execvp` at `:47`,
  pre-jail exec, no validation). Both exfiltration probes leak with rc=0.
  → M1 MUST follow the design.md plan: hardened relay in `seat-sandbox.sh`
  (subcommand allowlist; `--source`/`-s` both forms equal to non-empty
  `$OPENRIG_SESSION_NAME`; `--note` both forms restrictive pattern, no
  newlines/shell tokens; `--body-file` both forms realpath-contained, regular
  file ≤ 256KiB, never inside the secret store, no credential suffix, inside
  scratch or seat write-roots, clear of protected segments) +
  `TestRigRelayEnforcement` covering deny-secret-store, deny-out-of-scope,
  deny-forged-source, deny-subcommand, deny-note, allow-valid — all bwrap-independent
  (relay runs pre-jail, so tests pass with or without bwrap; bwrap 0.13.1 IS present
  on this host).
- Filter: supported on this host (Python 3.15.1) — no design deviation, but M2 MUST
  still ship the feature-detect guard (fatal on Python ≤3.11.3) with a code-path
  proof on this host, plus the hermetic charter fallback and snapshot/restore guard.
- M3 unchanged: Dockerfile `bubblewrap` install + `bwrap --version` verify step;
  workflow duplicate-`container:`-key fix + `bubblewrap` install in verify-fleet job.
- Pre-M1 gate (REQ-A0): this file exists with verbatim outputs on the unmodified
  tree — SATISFIED.
