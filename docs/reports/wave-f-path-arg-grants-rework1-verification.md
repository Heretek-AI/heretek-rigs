# Verification addendum: wave-f-path-arg-grants rework 1 (rework cycles used: 1 of 3)

Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/path-arg-grants-91`
Branch: `feat/path-arg-grants-91` @ `b6be829` (S6-completion commit on top of `5f4a530`).
Prior report: `docs/reports/wave-f-path-arg-grants-verification.md` (VERDICT: FAIL, single finding: truncated S6 entry) — still present, untracked, untouched.
Scope of this re-audit: verify the S6 entry is now complete, spot re-run acceptance, confirm no other changes since last audit. No code fix by auditor.

## 1. S6 evidence completeness (prior finding 1 — CLOSED)

File `docs/evidence/wave-f-path-arg-grants.md`, S6 block (lines 98-108), read from disk:

- Size now 6711 bytes (was 5907 at FAIL); ends with newline (`ends-newline: True` via `read_bytes`); zero `truncated` markers (case-insensitive scan).
- Full RED signature present: injected `if w == "-o": i += 2; continue` ahead of the `-o`/`-I`/`-isystem`/`-L` operand pairing in `classify_gcc_command` (`scripts/render-seat.py`), so `-o` values bypass `classify_scoped_path_value` → `bash tests/command-effects-redproof.sh` exit **1** (`[FAIL] deny gcc ['-c', 'src/foo.c', '-o', '/tmp/evil.o'] — got allow-effect`, `redproof: 1 failures`; `pytest tests/test_command_effects.py` exit **1** — `1 failed` on the same `-o /tmp/evil.o` deny direction, `120 subtests passed`). Non-vacuous: exact failing vector named with exit codes and failure counts on both harnesses.
- Revert proof present: `git checkout -- scripts/render-seat.py`, `git status --short` clean (only untracked T3 verdict report), redproof exit **0** (`redproof: 0 failures`).
- Closing notes present: `-o` operand scope check load-bearing for REQ-A1/A2 — without it an in-scope compile masks an out-of-scope write escape, the exact `-o /tmp/evil.o` vector; `Reverted clean.`
- `git diff 5f4a530..HEAD` confirms the delta is exactly this completion: 1 file changed, 12 insertions, 2 deletions, replacing the 2-line truncated stub (`...[truncated 890 chars]`, no trailing newline) with the 12-line complete entry.

Prior finding is resolved. No truncation remains.

## 2. Spot re-run acceptance (witnessed by auditor, exit codes real)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed, 0 failed`, exit 0 (V20 `#91` block green).
- `python3 -m pytest tests/test_command_effects.py -q` → `37 passed, 121 subtests passed`, exit 0.
- Both match the prior-audit green baseline; no regressions from the evidence-only delta (expected — evidence file is not code).

## 3. No other changes since last audit

- `git diff 5f4a530..HEAD --name-only` → exactly `docs/evidence/wave-f-path-arg-grants.md`. `git diff 5f4a530..HEAD --stat` → 1 file, 12+/2-. `git show --stat HEAD` agrees (commit `b6be829 evidence(path-arg-grants-91): complete S6 entry (Refs #91)`).
- `git status --short` → exactly `?? docs/reports/wave-f-path-arg-grants-verification.md` (the prior untracked verdict report, left untouched). No tracked dirt; no new code, catalog, script, test, or leaf changes.
- `git log --oneline main..HEAD` → `b6be829`, `5f4a530`, `2441a93`, `703bb83`, `05324a8`, `266c61e`, `710b2ae` (+ spec base) — no unexpected commits.
- All prior-audit PASS clauses (REQ-A0/A1/A2/A3/A4/G1, Refs posture, Canary 12) stand unmodified; no re-audit of code substance was needed or performed beyond the spot acceptance above.

## Findings

None. Zero open findings.

Report written to `docs/reports/wave-f-path-arg-grants-rework1-verification.md`, uncommitted by design. Prior report file(s) untouched. `git status --short` at write time: `?? docs/reports/wave-f-path-arg-grants-verification.md` plus this new untracked addendum.

VERDICT: PASS
