# Tasks: 107-identity

- [x] T0 — Spec gate (this change). Testable: `ls openspec/changes/107-identity/{proposal.md,design.md,tasks.md,specs/identity/spec.md}` exit 0.
      Acceptance command: `ls openspec/changes/107-identity/proposal.md openspec/changes/107-identity/design.md openspec/changes/107-identity/tasks.md openspec/changes/107-identity/specs/identity/spec.md`

- [x] M0 — Live spike (agency-programmer, worktree `.lane/trees/107-identity`, isolated env ONLY).
      Do: scratch `OPENRIG_HOME`, non-default loopback port, `token add` + `serve --http` probes (Bearer 200 / bad 401 / revoked 401 / whoami authenticated-vs-declared) + queue-half probe. Write `docs/evidence/107-identity-m0.md` verbatim. NEVER touch real `$OPENRIG_HOME` or a running daemon.
      Testable: evidence log exists with all four live outputs + queue probe; script exits 0 only if all probes behave as specified.
      Acceptance command: `ls docs/evidence/107-identity-m0.md`

- [x] M1 — Grants + seed issuance. Do: follow M0 winner; `seed-rig.py` issuance, secrets-dir storage, `!cat` render; stdio unchanged; tests + appended gate.
      Testable: own-seat Bearer allows, cross-seat/revoked deny; `make verify` green.
      Acceptance command: `make verify`

- [x] M2 — Rotation runbook. Do: revoke + re-add executed live; docs.
      Testable: revoked token 401s; runbook exists.
      Acceptance command: `./scripts/verify-rigs.sh --check-only`

- [x] M3 — Queue disposition. Do: implement + gate if M0 allows, else `docs/evidence/107-identity-queue.md` upstream-blocked note (no upstream filing without authorization).
      Testable: note exists with exact probe output, or gate green.
      Acceptance command: `ls docs/evidence/107-identity-queue.md`

- [x] T2 — Red-proofs (agency-qa, same worktree, evidence commit).
      Do: sabotage every new grant/check both directions; evidence `docs/evidence/107-identity/red-proofs.log`.
      Acceptance command: `./scripts/verify-rigs.sh --check-only AND grep -c 401 docs/evidence/107-identity/red-proofs.log`

- [x] T3 — Drift-guard (VERDICT from disk) → PR (Refs #107; Closes #107 only if MCP path fully fixed).
