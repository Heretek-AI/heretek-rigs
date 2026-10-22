# Implementation report — wave-37-id-discipline (remediate-37-id-discipline)

- Stage/wave id: `wave-37-id-discipline` (change `remediate-37-id-discipline`)
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-37-id-discipline`
- Branch: `remediate/37-id-discipline` (base `origin/main @ 39e45b6`)
- GitHub issue: #37 — "Queue list view truncates qitem IDs; pasted IDs fail not-found"
- Date (UTC): 2026-10-22

## 1. What was done (claims)

Implemented seat-side qitem ID discipline per `tasks.md` T1–T5. No upstream
change: rig CLI 0.6.13 already emits full 37-char IDs (refutation
re-confirmed live, §5), so the fix is local — copy IDs only from `--json`
output, never retype.

1. **T1 — generator primer**: `scripts/generate-rigs.py` startup-context
   template now emits `rig queue list --json` plus the never-retype sentence
   ("Copy `qitem-...` ids verbatim from that `--json` output -- never retype
   or reconstruct them").
2. **T2 — operator guides**: `--json` on every queue-read example plus a
   copy-never-retype sentence in `docs/USER_GUIDE.md`, `README.md`, and the
   root `AGENTS.md` queue-workflow row.
3. **T3 — regen + verify**: regenerated with the vendor-pin workaround
   below; `make verify` green.
4. **T4 — live proof**: full 37-char ID copied from list output resolves in
   `rig queue show` (exit 0); a 30-char truncation fails closed with
   `qitem_not_found` (exit 1).
5. **T5 — this report**.

Deliberately NOT changed (out of scope, documented): `docs/USER_GUIDE.md`
`rig queue create` example (write op — REQ-37-A2 mandates `--json` only on
`list`/`show`; adding a flag there would change the example's semantics),
`docs/sprints/SEAT-REFRESH-RUNBOOK.md` and `docs/TECHNICAL_DOCUMENTATION.md`
bare mentions (not in the spec's file list), and the `openspec validate`
archive-time INFO (pre-existing packaging note, §6).

## 2. Per-anchor grounding (grep-verified before edit)

| # | File:line (pre-edit) | Bare form found | Fix applied |
|---|---|---|---|
| T1 | `scripts/generate-rigs.py:810` (spec cited ~701; anchor had moved — reported, not invented) | `` check your queue (`rig queue list`) `` in startup `context.md` template | `rig queue list --json` + never-retype sentence |
| T2a | `docs/USER_GUIDE.md:215` | `rig queue list --destination … --limit 100` | appended `--json` + copy-verbatim comment |
| T2b | `docs/USER_GUIDE.md:226` | `rig queue create …` (write example, already parameterised) | untouched — `--json` not applicable to a create example |
| T2c | `README.md:61` | `rig queue list --destination …` | appended `--json` + copy-verbatim comment |
| T2d | `AGENTS.md:29` queue row | `` rig queue list [--destination S] [-a] `` | `rig queue list --json [--destination S] [-a]` + "(copy qitem IDs only from `--json` output — never retype)" |

Post-edit grep: no `rig queue list` / `rig queue show` line without `--json`
in any of the four files (pinned by `tests/test_queue_id_discipline.py`).

## 3. Regen record

- Plain `python3 scripts/generate-rigs.py` refused (exit 2): dirty-checkout
  guard fired on my own source edits — correct behaviour (issue #43 domain).
- Retry with `HERETEK_RIGS_ALLOW_DIRTY=1` failed (exit 2) on a missing
  `.scratch/vendor/obra_superpowers` — the worktree has no `.scratch/`
  (gitignored, not cloned into worktrees). Resolved by pointing at the main
  checkout's pins read-only:
  `HERETEK_RIGS_ALLOW_DIRTY=1 python3 scripts/generate-rigs.py --vendor-dir
  /home/john/Projects/heretek-rig-workspace/heretek-rigs/.scratch/vendor`
  → exit 0 ("wrote 51 specialist AgentSpecs, 68 shared skills, 8 RigBundles…").
- Diff: 182 files — 4 source files + Makefile/test/report plus 153
  `startup/context.md` leaves (specs/ + rigs/) carrying the new primer, plus
  mechanical digest consequences (`packageDigest` in `registry/*`,
  `integrity` hashes in `rigs/*/bundle.yaml`).
- Provenance check: `resolvedCommit` moved `bae5d3a… → 39e45b6…` (== worktree
  HEAD) in 16 spots, but **no file is provenance-only churn** — every touched
  registry/bundle file also carries required digest updates, so per the
  stage brief's revert condition ("ONLY if the churn is purely the known
  re-lag pattern") nothing was reverted. All generated-leaf bytes are
  regen output; no hand-edits to `specs/`, `rigs/`, `rosters/`, `registry/`.

## 4. Tests

- New `tests/test_queue_id_discipline.py` (TDD: failed 4/4 pre-fix,
  passes 4/4 post-fix + regen):
  1. no bare `rig queue list`/`show` example without `--json` in the 4 files;
  2. generator snippets `shlex`-parse with `--json` as a real argv token;
  3. never-retype rule present in the generator;
  4. all 153 rendered `startup/context.md` leaves contain the primer.
- Wired into `make test` (Makefile `test:` recipe gains the new file).
- `make test`: 63 tests, OK, exit 0.
- Full suite (`make verify`): **SUMMARY: 25 checks passed, 0 failed**,
  exit 0 — no new gate added (spec mandates none), zero regressions.

## 5. T4 live transcript (read-only; no queue/seat mutations)

```console
$ rig queue list -A --limit 1            # exit 0
[{"qitemId": "qitem-20261022111416-78213c07c3272cbc", …}]
$ rig queue show qitem-20261022111416-78213c07c3272cbc   # exit 0
# 96 lines; output contains "qitemId": "qitem-20261022111416-78213c07c3272cbc"
$ rig queue show qitem-20261022111416-78213c07c          # 30-char truncation → exit 1
{"error": "qitem_not_found", …}
```

- Full 37-char ID (`len=37`) copied from list output resolves first try:
  zero `qitem_not_found` — confirms list output carries full IDs (the #37
  truncation premise stays refuted) and the copy discipline holds.
- Deliberately truncated ID fails closed (`qitem_not_found`, exit 1) —
  red-proof that the rule is load-bearing.
- Note: bare `rig queue show` output carries the known #44 JSON trailer
  (`json.load` reports "Extra data"); exit code is 0 and the item resolves.
  Trailer parseability is wave-44's remit, not this change.

## 6. Acceptance outputs

- `make verify` → exit 0, `SUMMARY: 25 checks passed, 0 failed`.
- `make test` → exit 0, 63 tests OK.
- `openspec validate remediate-37-id-discipline` → exit 0,
  "Change 'remediate-37-id-discipline' is valid" (plus a pre-existing
  archive-time INFO: the delta spec's MODIFIED block targets a spec that
  does not exist yet — packaging note from the spec author, untouched as
  out of scope).

## 7. Self-audit / skipped items

- Skipped: `USER_GUIDE.md:226` create example (`--json` inapplicable to a
  write; REQ-37-A2 covers reads only), runbook/TECHNICAL_DOC bare mentions
  (outside spec file list), new verify gate (spec mandates none — SUMMARY
  stays 25/0), `openspec` spec-text edits (spec package only).
- Secrets: none touched, printed, or committed. Live queue access was
  read-only (`list`, `show`); no items created, claimed, or mutated.
- No merges, no pushes (per stage instructions — human merges).
