# Proposal: command-effects — scoped queue-note + body-file effects without loosening denies

Status: scope approved (operator delegation "I trust you", 2026-10-24; HANDOFF P0-1).
Issue: #106 (implementation). GitHub #75 CLOSED = problem statement; #106 OPEN = this implementation. Keep #91 OPEN (path-half remains after).

## Root cause (verified read-only 2026-10-24, ses recon)

- `grep -rn commandEffects scripts/ fleet/ tests/` = exit 1, no output. CONFIRMED zero implementation. Only doc mentions: `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md:133-134`, `docs/PROMPT_REMEDIATION_REAUDIT.md:25`, `docs/NOTES.md:362`, `docs/reports/*`, `HANDOFF.md`.
- `--note` value flows as opaque argv string through pps `bash` matching today, so `*|*`, `*>*`, path substrings trip terminal denies. Wrappers only passthrough: `scripts/send-authenticated.sh:89-113,193-197`, `scripts/park-typed-block.py:50-68,71-73,118-119,151`, `scripts/sweep-typed-blocks.py:108-153`. No sanitization, no path check.
- `--body-file` path is opened by `rig` daemon (`@openrig/cli@0.6.13`), not repo code. `send-authenticated.sh:193-197` only checks `-f` + `cat`; no `realpath` / `O_NOFOLLOW` / `..` / scope check anywhere.
- Deny definitions: `scripts/render-seat.py:81-127` (38 entries, single source of truth) + `scripts/verify-rigs.sh:588` (38-entry ordered-identical mirror, enforced `verify-rigs.sh:1738-1742`). CORRECTION to HANDOFF: HANDOFF says "31 terminal denies" — STALE. Source is 38; test corpus `tests/test_render_seat.py:172-205` is 31 (missing 7 tab/space variants `*\t-c *`, `* -c\t*`, `*\t-c\t*`, `*\t-m *`, `* -m\t*`, `*\t-m\t*`, `*\t-W*`). Test-side drift belongs to #102, out of scope here.
- Own-write-scope exists as two layers: catalog `permissions.path_write` (`fleet/fleet.yaml:29-44`, `write_roots_source`) + jail `HERETEK_SANDBOX_WRITE` (`scripts/render-seat.py:130-150,443-447`, `scripts/seat-sandbox.sh:4-110,170-182`). No `commandEffects`-aware scope — that is the #106 gap.

## Change (scope-locked to #106 alone)

Add declarative `commandEffects` overlay to seat permission rendering (no deny-list edits, no wrappers, no per-tool arg grants beyond this):

- `note-effect`: `--note` single-argv value allowing literal `| / . - _ :` + alphanumerics + space, never as shell control (argv, not `sh -c`).
- `body-file-effect`: `--body-file P` allowed only when `realpath(P)` is inside own scope (seat `cwd` incl. its `.lane/trees/<stage>` worktree when cwd is there, plus `path_write`-expanded roots, plus pid-namespaced `/var/tmp/seatjail.<pid>.*` scratch), regular file, ≤256KiB, no symlink escape, no `..` escape.
- Everything else stays denied, including `prod.env` outside scope, `/etc/passwd`, absolute `/tmp` escapes.

Explicitly out of scope: #91 path-half builds, #76 `*--output*` policy, any deny removal/renumber, `.lane/` baked-config grants (V14 forbids baked `/.lane/` in `shellPath`/`packages[]` — runtime cwd coverage only).

## Acceptance

1. Wave 0 — spec exists: `ls openspec/changes/command-effects/{proposal.md,design.md,tasks.md,specs/command-effects/spec.md}`.
2. Wave 1 — implement: `grep -rn commandEffects scripts/ fleet/ | wc -l > 0`, `make verify` green with deny count unchanged (38 source / 38 mirror), no check renumber.
3. Wave 2 — red-proofs both directions into `docs/evidence/wave-command-effects-redproofs.md`: allow `--note "a/b | c"`, in-scope body-file exit 0; deny `prod.env`, `/etc/passwd`, `../../etc/passwd`, symlink escape non-zero with deny record.
4. Wave 3 — drift-guard `VERDICT: PASS` read from `docs/reports/wave-command-effects-verification.md` on disk (never from summary) → PR, human merges.
