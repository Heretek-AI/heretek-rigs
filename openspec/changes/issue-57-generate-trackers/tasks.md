# Tasks: issue-57-generate-trackers

Execution waves: implement (G-T1–G-T3) → replay (G-T4) → wiring (G-T5) →
evidence (QA red-proofs) → audit (drift-guard). Map 1:1 to
`specs/generate-trackers/spec.md` (G-T1→G1+G5, G-T2→G1, G-T3→G2+G4,
G-T4→G3, G-T5→wiring+docs). Specs ONLY — do NOT implement in this change.
All fixtures live in `/tmp` (synthetic `qitem-<ts>-<hex>` ids in the live
shape); never the live mission checkout, never this repo's live files.
Every acceptance command below is binary pass/fail (exit code decides).

- [ ] G-T1 — REQ-G1 + REQ-G5: refactor `scripts/reconcile.py` row model
      (`parse_tracker`, `normalize_tracker`, `recorded_note_ids`,
      `queue_terminal`, `diff_row`, `propose_cell`,
      `normalize_proposal_note`, `refuse_out_path`,
      `write_out_exclusive`) into an importable module with NO behavior
      change, then implement the `scripts/generate_trackers.py` emitter on
      top of it (per-tracker proposals, exact Q8 cell shapes, unchanged-row
      listing). Testable ALL green in one gate:
      `python3 scripts/generate_trackers.py --tracker <fixture-tracker>
      --queue-list <canned-queue.json> --transitions <canned-trans.json>
      --out <fresh-proposal.md>` emits a paste-ready cell for every diffed
      row; `git status --short` shows no modifications; and
      `python3 -m unittest tests/test_generate_trackers.py
      tests/test_reconcile.py` passes with `tests/test_reconcile.py` still
      28/28 unmodified (no shared-model regression).
- [ ] G-T2 — REQ-G1 (`OTHER`/`NEEDS-HUMAN-REVIEW`): unknown-prose and
      orphan-qitem fixtures emit `OTHER(<raw>)` /
      `tracker-row-without-qitem` markers quoting both-side evidence with
      guessed-status nowhere and exit non-zero. Testable:
      `python3 -m unittest tests/test_generate_trackers.py` passes
      (markers present, both sides quoted, exit codes asserted).
- [ ] G-T3 — REQ-G2 + REQ-G4 red-proofs: each sabotage (missing tracker,
      short-column row, missing/invalid queue JSON, empty queue `[]`,
      unreachable rig binary, non-dict transition items, `--out` at input
      tracker / tracker-shaped path / `sprints/` path / existing file)
      produces its named exit-2 diagnostic with destination bytes untouched
      (prove each with md5 pre/post). Testable:
      `python3 -m unittest tests/test_generate_trackers.py` passes AND a
      reviewer replays any two sabotages by hand and observes exit 2 plus
      identical md5 sums.
- [ ] G-T4 — REQ-G3 convergence replay: apply every
      non-`NEEDS-HUMAN-REVIEW` proposed cell to a scratch tracker copy
      (TPM-approval simulation; `--out` MUST NOT target the copy — refuse
      rule applies), then re-run the reconcile diff. Testable:
      `python3 scripts/reconcile.py --tracker <patched-scratch-copy>
      --queue-list <canned-queue.json> --transitions <canned-trans.json>`
      exits 0 with an explicit "in sync" summary covering every parsed row.
- [ ] G-T5 — Wiring + docs: add a `make generate-tracker` target
      (`TRACKER=… [OUT=…]`, read-only `--queue-list`/`--transitions` or
      `--live` passthrough) enforcing the fresh-out guard, plus the
      `AGENTS.md` discipline row. The target name MUST stay
      `generate-tracker`: the existing `make generate` fleet target
      (`fleet/fleet.yaml` → 51 AgentSpecs / 8 RigBundles / Roster /
      Registry) MUST NOT be shadowed or overloaded. Testable:
      `make generate-tracker TRACKER=<fixture> OUT=<fresh-proposal.md>`
      writes the proposal (exit 1 on diffs, tracker bytes untouched), and
      `./scripts/verify-rigs.sh --check-only` reports SUMMARY 26 passed,
      0 failed.
