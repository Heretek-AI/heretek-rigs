# Tasks: ops-sweep-111

- [ ] T0 — Spec gate (this change). Testable: `ls openspec/changes/ops-sweep-111/{proposal.md,design.md,tasks.md,specs/sweep/spec.md}` exit 0.
- [ ] T1 — Sweep with guards (ops, host /var/tmp, no worktree).
      Do: re-verify `lsof`/`fuser` negative; for each legacy dir check `-d && ! -L && -O`; log bytes; `rm -rf`; post-check `ls -d /var/tmp/seatjail.*` empty.
      Testable: before log = 21, after log = 0.
      Acceptance command: `ls -d /var/tmp/seatjail.* 2>&1; echo "count: $(ls -d /var/tmp/seatjail.* 2>/dev/null | wc -l)"`
- [ ] T2 — Evidence `docs/evidence/wave-b1-seatjail-sweep.md` with before/after logs, committed.
- [ ] T3 — Close #111 (human or seat with gh), note #66/#68. No PR for code (none); evidence rides the Wave B PR or a docs PR.
