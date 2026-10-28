# Tasks: command-effects

- [ ] T0 — Spec gate (this change). Testable: `ls openspec/changes/command-effects/{proposal.md,design.md,tasks.md,specs/command-effects/spec.md}` exit 0.
- [ ] T1 — Implement overlay + corpus test (agency-programmer, isolated branch/worktree `.lane/trees/command-effects`, from clean `main`).
      Do: render `commandEffects` for note-value (REQ-C1) + body-file scope (REQ-C2) in seat permission output; extend checker/corpus (new gate block alongside, never renumber per REQ-G2); keep `render-seat.py:81-127` + `verify-rigs.sh:588` byte-identical per REQ-G1.
      Testable: `grep -rn commandEffects scripts/ fleet/ | wc -l` > 0; `python3 scripts/generate-rigs.py` exit 0 (or sanctioned-dirt-only); `./scripts/verify-rigs.sh --check-only` unchanged count, 0 failed.
      Acceptance command: `make verify`
- [ ] T2 — Red-proofs both directions (agency-qa, same worktree, evidence commit).
      Do: allow `--note "a/b | c"`, in-scope `--body-file` exit 0; deny `--body-file prod.env`, `/etc/passwd`, `../../etc/passwd`, symlink escape, oversize, `;`/`$`/backtick/`$(`/newline note, `OPENRIG_SESSION_NAME=` note — all non-zero with deny record. Cover REQ-C3.
      Testable: new `tests/` corpus test passes + `docs/evidence/wave-command-effects-redproofs.md` on disk with allow + deny logs.
      Acceptance command: `bash tests/command-effects-redproof.sh` (to be added by implementer; must be runnable, binary pass/fail) AND `pytest tests/test_render_seat.py tests/test_seat_sandbox.py tests/test_policy_verifier.py`
- [ ] T3 — Drift-guard + PR (agency-drift-guard, VERDICT read from disk never from summary).
      Do: audit worktree diff against `openspec/changes/command-effects/` + `AGENTS.md` one-rule (no hand-edits to `specs/ rigs/ rosters/ registry/`); write `docs/reports/wave-command-effects-verification.md` ending `VERDICT: PASS` or `VERDICT: FAIL`.
      Testable: `grep ^VERDICT docs/reports/wave-command-effects-verification.md` = `VERDICT: PASS`.
      Acceptance command: `grep ^VERDICT docs/reports/wave-command-effects-verification.md`
- [ ] T4 — (post human-merge + reseed/relaunch) Live proof: seat passes paths + `|` in `rig queue --note` without denies; `--body-file` in-scope allowed; `prod.env` + `/etc/passwd` stay denied. Keep #91 OPEN.
