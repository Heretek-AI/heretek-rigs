# Tasks: docs-write-scopes
- [ ] T1 — Edit fleet/fleet.yaml: six surgical path_write additions (REQ-S1..S3).
      Testable: grep shows each grant exactly once under the right role.
- [ ] T2 — Regen: python3 scripts/generate-rigs.py (clean tree required).
      Testable: exit 0; git status shows regenerated leaves only.
- [ ] T3 — Acceptance: make verify (22/0) + tests/test_render_seat.py (7/7) +
      seed dry-run grep proves rendered grants in seat configs.
- [ ] T4 — Report: docs/reports/docs-write-scopes-implementation.md.
- [ ] T5 — (post human-merge + reseed/relaunch) Live proof: each of the six
      roles writes its slice area; overreach denials confirmed; blocked
      asset-manager slices self-deliver. QA red-proofs both directions.
