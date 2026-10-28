# QA verdict: wave-37-id-discipline (change `remediate-37-id-discipline`)

- Stage/wave: `wave-37-id-discipline` — commit under test `c350b39`
  (`feat(37-id-discipline): copy qitem IDs only from --json output, never retype`)
- Worktree: `.lane/trees/wave-37-id-discipline` (branch `remediate/37-id-discipline`, base `origin/main @ 39e45b6`)
- QA date (UTC): 2026-10-22. No commits made by QA. All sabotage reverted.
- Evidence: `docs/evidence/wave-37-id-discipline/red-proofs.log` (companion log)

## Verdict: QA-CLEAN (PASS-with-note, 0 blocking findings)

All acceptance checks pass, every check red-proofs (fails closed under sabotage),
and the 185-file diff contains nothing outside the spec's file list plus
mechanical regen/test-wiring consequences (each justified below).

## 1. Acceptance suite

| Check | Result | Exact command / output |
|---|---|---|
| `make verify` | PASS | `make verify` → `SUMMARY: 25 checks passed, 0 failed`, exit 0 (live-health advisory WARN on stale heartbeats only, exit 0 as designed). No new gate added — V1–V9 behavior-identical, per spec (no gate mandated). |
| `make test` | PASS | `make test` → `Ran 63 tests / OK`, exit 0 (includes new `tests/test_queue_id_discipline.py`, 4 tests). |
| `openspec validate` | PASS | `openspec validate remediate-37-id-discipline` → valid, exit 0, plus one pre-existing packaging INFO (delta MODIFIED block targets a not-yet-existing spec — spec-author note, out of scope). |
| `make check` | N/A | No such target in this repo. Canonical gates are `make verify` / `make test`, both run. |

## 2. Red-proof sabotage (all RED as required, all restored)

| # | Target assertion | Injected defect | Result |
|---|---|---|---|
| A | Test 4 guards ALL leaves: `test_regen_carries_primer_into_rendered_leaves` | Bare `rig queue list` (no --json) in ONE leaf (`specs/agents/web-design/a11y-specialist/startup/context.md`) | RED exit 1 — failure names the exact leaf. Restored via `git checkout`, retest 4/4 OK. |
| B1 | Test 2 (shlex --json flag token) non-vacuous | Stripped --json from generator line 810 snippet | RED exit 1 — `test_charter_example_parses_as_json_invocation` FAIL. Test 1 stayed green (line still mentions --json later), proving tests 1+2 complementary. Restored, green. |
| B1b | Test 1 (no bare read examples) non-vacuous | Stripped --json from `README.md:61` | RED exit 1 — failure names `README.md:61`. Restored, green. |
| B2 | Test 3 (never-retype rule) non-vacuous | Neutered sentence to `always retype them from memory` (1-line diff) | RED exit 1 — `test_charter_states_never_retype_rule` FAIL. Restored, green. |
| C | Regen idempotency / honesty | `python3 scripts/generate-rigs.py --vendor-dir <main-checkout>/.scratch/vendor` (plain, exit 0 — NO ALLOW_DIRTY needed on clean tree) | 16 registry files changed; EVERY hunk is `resolvedCommit 39e45b6→c350b39` + derived `canonicalUrl` (known per-merge re-lag). Zero changes in specs/rigs/rosters/bundle.yaml. Reverted via `git checkout -- registry/`; discipline tests 4/4 OK on regenerated leaves (proves regen carries the primer). |
| D | Live read-only copy discipline (REQ-37-A3) | None (live probe, zero mutations) | `list --json` exit 0 → `qitem-20261022111416-78213c07c3272cbc` (len 37). `show <full> --json` exit 0, ID matches. 30-char truncation → exit 1 `qitem_not_found`. |

Observation (not a finding): test 1 scans only the 4 source files, so a bare
example added to a leaf alongside the primer would not trip any test — but leaves
are pure regen output of a template with no bare form, and sabotage A proves any
primer regression in any leaf is caught.

## 3. Regen honesty audit (`git diff 39e45b6..HEAD`, 185 files)

- 153 `startup/context.md` leaves (51 specs/ + 102 rigs/ copies, all 8 rigs):
  programmatically verified — every leaf diff is exactly one -/+ line pair
  (bare primer → --json + never-retype sentence). Sampled across security,
  gamedev, cloud-sre, qa, systems rigs/domains — identical hunk shape everywhere.
- Non-leaf files (32), each justified:
  - `scripts/generate-rigs.py` (T1), `docs/USER_GUIDE.md` (T2), `README.md` (T2),
    `AGENTS.md` (T2) — spec file list; diffs are exactly the discipline change.
  - `tests/test_queue_id_discipline.py` (new) — the pinning test.
  - `Makefile` (1 line: adds new test module to `make test`) — NOT in spec file
    list, but mechanical test wiring disclosed in the report; justified.
  - `docs/reports/wave-37-id-discipline-implementation.md` (new) — T5 report.
  - 8x `registry/entries/*.yaml`: `resolvedCommit bae5d3a→39e45b6` + digest `value`.
  - 8x `registry/views/*/behaviour.json`: same + `canonicalUrl` + digest.
  - `registry/status.json`: listing-hash `value`s + `bodyDigest` (mechanical JCS).
  - 8x `rigs/*/bundle.yaml`: per-leaf sha256 integrity entries for changed context.md only.
- Zero changes in `rosters/` and in any `specs/` file other than the 51 leaves:
  no hand-edits under generated trees; all bytes are regen output.

## 4. Skipped items — PASS-with-note

- `docs/USER_GUIDE.md:226` (`rig queue create …`) untouched: correctly out of scope.
  REQ-37-A2 covers `list`/`show` reads only; a create is a write op.
- Runbook bare mentions (lines 119, 146, 254, 327) and `docs/TECHNICAL_DOCUMENTATION.md:131`:
  confirmed outside the spec file list. Judgment: PASS-with-note. Normative surfaces
  (charter primer in all 153 leaves, root AGENTS.md, README.md, USER_GUIDE queue
  section) all teach the rule; bare `list` already emits full IDs (truncation premise
  refuted live). Residual: runbook line 119's pre-refresh listing is ID-reuse-adjacent.
  Recommend a follow-up micro-edit appending --json to runbook 119/146 (and TECHDOC:131);
  leaving them does not break the discipline for any seat that reads its charter first.

## 5. Moved anchor (spec ~701 → actual ~810): confirmed correct

Primer template is `scripts/generate-rigs.py:810` in the
`(adir / "startup/context.md").write_text(f'You are {rid} …')` block — the exact
startup-context primer, drifted by later generator additions. Template→leaf identity
proven: rendered leaf line 1 equals the f-string with `{rid}`/`{r["title"]}`
substituted; QA regen re-rendered all 153 leaves and the leaf-coverage test passes.

## 6. Final tree state

`git status --short` shows only `?? docs/evidence/wave-37-id-discipline/` (QA logs)
and `?? docs/reports/qa-wave-37-id-discipline.md` (this report) — nothing modified.
No commits, no pushes. Live access was read-only (`list`/`show`).
