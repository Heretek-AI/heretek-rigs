# Delta spec: command-effects for queue note + body-file

## ADDED Requirements

### REQ-C1: note-value effect
Seat permission rendering MUST include a `commandEffects` entry classifying `rig queue --note <value>` (including via `block` / `update --reopen --note` argv built by `park-typed-block.py` / `sweep-typed-blocks.py`) as allow-effect when `<value>` matches `^[A-Za-z0-9 _\-/.:|]+$` AND is passed as a single argv element to `--note` (no `sh -c` interpolation). Rationale: relieves #91 note-half without touching denies.

### REQ-C2: body-file scoped effect
Seat permission rendering MUST include a `commandEffects` entry classifying `rig queue --body-file <P>` (including `--source` staged relay in `send-authenticated.sh:206-240`) as allow-effect only when ALL hold:
- `realpath(P)` starts with `realpath(CWD)` (seat workspace, including its `.lane/trees/<stage>` worktree when that is cwd) OR with a `path_write`-expanded root OR with pid-namespaced scratch `/var/tmp/seatjail.<pid>.*`;
- `P` is a regular file, size ≤ 256KiB;
- no symlink escape, no `..` traversal outside scope, no absolute `/tmp` non-pid path.
Rationale: least privilege matching existing `path_write` + `HERETEK_SANDBOX_WRITE` layers.

### REQ-C3: deny directions (fail-closed)
The following MUST remain denied with a deny record, even with commandEffects present:
- `--body-file prod.env` outside scope, `--body-file /etc/passwd`, `--body-file ../../etc/passwd`, symlink-escape body-file, oversize body-file;
- `--note` values containing `;`, `$`, backtick, `$(`, newline, or `OPENRIG_SESSION_NAME=` / `OPENRIG_URL=` assignments.
Scope-resolution error, missing file, or oversize MUST deny (fail-closed).

## MODIFIED Requirements

### REQ-G1: denies frozen
`TERMINAL_BASH_DENIES` in `scripts/render-seat.py:81-127` (38 entries) and mirror `scripts/verify-rigs.sh:588` (38 entries, ordered-identical per `verify-rigs.sh:1738-1742`) MUST remain byte-identical in this change. No entry added, removed, reordered, or reworded. Test corpus `tests/test_render_seat.py:172-205` (31 entries, stale vs source) MUST NOT be edited here — its 7-entry drift belongs to #102.

### REQ-G2: no new check numbers
`verify-rigs.sh` check count MUST NOT be renumbered or reworded in this change. New coverage MUST be a new gate block alongside (or corpus test + red-proof), never a renumber.
