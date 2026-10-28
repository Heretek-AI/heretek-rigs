# Proposal: ops-sweep-111 — one-time legacy seatjail sweep (no code)

Status: scope approved (HANDOFF P0-2 + operator "Execute the remainder", 2026-10-24).
Issue: #111. Closes #111 on completion. Notes to #66/#68.

## Root cause (verified read-only 2026-10-24, Wave B recon)

- `/var/tmp/seatjail.*` today = 21 entries (HANDOFF/#110 claimed 408 — delta unexplained in-tree; bounds today's sweep to 21).
- All 21 = legacy `seatjail.XXXXXX` (zero pid-namespaced `seatjail.<pid>.XXXXXX`); all `john:john` (1000:1000, invoking `id -u` = 1000); 14 node-compile-cache at 126,936 B + 3 other-sized cache dirs (146,612 / 148,464 / 168,140 B) + 4 tiny 2-byte `x`-only; total 560 files / ~2.1 MiB.
- Secrets scan (names + content patterns): 0 hits. `lsof`/`fuser`: no holders. No mount refs.
- Creator/sweeper `scripts/seat-sandbox.sh:51-66` self-sweeps own pid-namespaced dirs only; `:54` deliberately leaves legacy alone. Provenance: old `mktemp …/seatjail.XXXXXX` form (`docs/REMEDIATION_IMPLEMENTATION_PROMPT.md:213`).

## Change (ops only, NO code)

One-time host sweep of the 21 legacy dirs with guards (re-verify liveness + ownership + non-symlink immediately before delete; legacy pattern only, never `seatjail.<pid>.*`, never other `/var/tmp` entries). Afterwards confirm zero `seatjail.*` remain and that future runs cycle only pid-namespaced dirs. Explicitly NO change to `seat-sandbox.sh` sweeper, no regen, no deny/policy edits.

## Acceptance

1. Pre-sweep count-log on disk (21, with ownership/age/content classes).
2. Sweep exits 0 with per-dir guarded deletes; post-sweep `ls -d /var/tmp/seatjail.*` = 0 (exit 1, no output).
3. Evidence file `docs/evidence/wave-b1-seatjail-sweep.md` with before/after logs committed.
4. #111 closed with count + evidence ref; notes on #66/#68.
