# Verification report — wave-37-id-discipline (change `remediate-37-id-discipline`)

- Stage/wave: `wave-37-id-discipline` — commits under audit `c350b39` (implementation) + `c066272` (QA evidence)
  (`git log --oneline -3`: `c066272 / c350b39 / 39e45b6`, as expected)
- Worktree: `.lane/trees/wave-37-id-discipline` (branch `remediate/37-id-discipline`, base `origin/main @ 39e45b6`)
- Auditor date (UTC): 2026-10-22. No commits made by auditor. No source files modified. No pushes.
- Spec contract: `openspec/changes/remediate-37-id-discipline/` (proposal.md, specs/queue-id-discipline/spec.md,
  design.md, tasks.md T1–T5). Binding rules: `AGENTS.md` (merge-conflict rule, committed-provenance re-lag known/accepted,
  packageDigests self-consistent — DO NOT hand-fix).
- GitHub issue #37: "Queue list view truncates qitem IDs; pasted IDs fail not-found" (OPEN, no assignee).
  Ask was upstream (`--full-ids` flag / full-ID rendering); the spec refutes the premise live and mandates local-only discipline.

## 1. Diff audit (`git diff 39e45b6..HEAD`, 187 files)

Non-leaf files (32), each justified against `tasks.md` / mechanical regen consequences:

- `scripts/generate-rigs.py` (T1) — exactly one line: primer `rig queue list` → `rig queue list --json` + never-retype sentence.
- `docs/USER_GUIDE.md` (T2), `README.md` (T2), `AGENTS.md` (T2) — `--json` on every queue-read example + copy-never-retype sentence.
- `tests/test_queue_id_discipline.py` (new) — the 4 pinning tests. `Makefile` (1 line: adds the new module to `make test`) —
  NOT in the spec file list, but pure mechanical test wiring, disclosed in the implementation report. Justified.
- `docs/reports/wave-37-id-discipline-implementation.md` (T5 report) + QA-committed `docs/reports/qa-wave-37-id-discipline.md`
  and `docs/evidence/wave-37-id-discipline/red-proofs.log` — evidence, not production.
- 8× `registry/entries/*.yaml`: `resolvedCommit bae5d3a→39e45b6` + digest `value` change only.
- 8× `registry/views/*/behaviour.json`: same + derived `canonicalUrl`. `registry/status.json`: listing-hash/`bodyDigest` only.
- 8× `rigs/*/bundle.yaml`: per-leaf sha256 integrity entries for changed `context.md` files only.
- Zero changes in `rosters/`. Zero changes in any `specs/` file other than the 51 leaves. No hand-edits anywhere under
  generated trees (see leaf-shape proof below).

Generated leaves (153 `startup/context.md`: 51 specs/ + 102 rigs/, all 8 rigs) — verified programmatically, not by sampling
alone: every leaf diff is exactly one `-` line and one `+` line (`leaves=153 odd=0`), and every `[-+]` line in the combined
leaf diff contains only the primer change (`rig queue list` → `rig queue list --json` + never-retype sentence) — zero
substantive content beyond the single template edit. 8 leaves spot-read across cloud-sre, executive, game-dev, omni-fleet
(×2), systems, gamedev-spec, qa-spec: identical hunk shape. **No leaf carries anything but the primer churn: PASS.**

## 2. Provenance / digest integrity

- `resolvedCommit` advanced `bae5d3a→39e45b6` (== base/worktree HEAD at branch time) in 16 registry spots — the known
  per-merge re-lag pattern, explicitly blessed by `AGENTS.md`. Correct direction, correct value.
- No provenance-only churn: every touched registry/bundle file also carries required digest updates (entry `packageDigest`,
  view `canonicalUrl`+digest, status listing-hashes, bundle per-leaf integrity). Nothing reverted, nothing to revert.
- Digests self-consistent: `make verify` digest gates pass (25/0, §6). Generator recomputes digests deterministically, so a
  green digest gate IS the no-hand-fudge proof; no independent recomputation needed.
- `ALLOW_DIRTY` use was legitimate: fired only on the implementer's own tracked source edits (dev-iteration rule expressly
  permits this). Committed tree regenerates clean without it — QA's plain-regen run on the clean tree exited 0 with ONLY
  the 16-file known re-lag churn and zero specs/rigs/rosters/bundle.yaml movement. I did not re-run regen myself (it would
  dirty the audited tree); QA's logged run plus my green `make verify` is sufficient evidence. Concur with reasoning stated.

## 3. The 4 new tests — spot-read both directions

Read `tests/test_queue_id_discipline.py` in full (103 lines, hermetic, no daemon) and re-ran: `Ran 4 tests … OK`.

- Test 1 (no bare `list`/`show` without `--json` in the 4 files) × Test 2 (generator snippets `shlex`-parse with `--json` as
  a real argv token): complementary, not redundant. QA sabotage B1 proves the direction: stripping `--json` from the
  generator line trips Test 2 RED while Test 1 stays green (line still mentions `--json` later). Conversely sabotage B1b
  (bare `README.md:61`) trips Test 1 RED naming the file:line. Each catches a regression class the other misses. Real coverage.
- Test 3 (never-retype rule present): sabotage B2 (neutered to "always retype them from memory", 1-line diff) → RED. Non-vacuous.
- Test 4 (all rendered leaves carry primer): sabotage A (one bare leaf) → RED naming the exact leaf; restored → 4/4 OK.
  Genuinely leaf-wide (globs `specs/**/…` + `rigs/**/…`), closing the line-scoped-vs-leaf-wide gap QA noted.
- Stub scan of the new test file: no TODO/FIXME/skip/bare-pass/vacuous-assert patterns. CLEAN.

## 4. No CLI / upstream change (local-only scope held)

- Diff touches no CLI code, no queue runtime, no vendored upstream: the only filename matching `cli|queue*.py|upstream` grep
  is the new test file itself (name false-positive on "discipline"). No wrapper, no flag request, no alias scheme.
- No upstream issue filed or referenced as filed (issue #37 remains OPEN, untouched — correct: filing for non-buggy output
  would be the scope creep `design.md` explicitly rejects).
- `gh issue view 37` confirms the issue's live premise (4× `qitem_not_found` from reconstructed suffixes) is an operator
  habit failure, matching the spec's refutation. Local discipline is the complete fix. Scope held.

## 5. Skipped items — independent rulings

- `docs/USER_GUIDE.md:226` (`rig queue create …`) untouched: **AGREE.** A create is a write op; REQ-37-A2 covers `list`/`show`
  reads only. Appending `--json` there would change the example's semantics. Correctly out of scope.
- Runbook bare mentions (lines 119, 146, 254, 327) + `TECHNICAL_DOCUMENTATION.md:131`: **CONCUR with QA pass-with-note.**
  Independent reasoning: (a) none are in the spec's file list, so leaving them violates no requirement; (b) every normative
  surface a seat actually reads first — charter primer in all 153 leaves, root `AGENTS.md` queue row, `README.md`,
  `USER_GUIDE.md` queue section — teaches the rule; (c) bare `list` output carries full IDs live (refutation re-confirmed
  live in §7), so following a runbook bare example still yields a working ID — no seat is taught a failing habit.
  Recommend (non-blocking) follow-up micro-edit appending `--json` to runbook 119/146 and TECHDOC:131. Not a finding.

## 6. Re-run (auditor-executed, not trusted)

- `make verify` → `SUMMARY: 25 checks passed, 0 failed`, exit 0. (Live-health heartbeat WARN is advisory-by-design, exit 0;
  pre-existing stale-seat advisory, unrelated to this change.)
- `openspec validate remediate-37-id-discipline` → `Change 'remediate-37-id-discipline' is valid`, exit 0, plus the
  pre-existing archive-time INFO (delta MODIFIED block targets a not-yet-existing spec — packaging note from the spec
  author, disclosed by implementer and QA, out of scope).
- `make test` equivalent (new module): `python3 -m unittest tests/test_queue_id_discipline.py` → 4 tests OK.
- `git status --short` → clean (empty). Both audited commits present; no stray modifications.
- Note: `AGENTS.md` says "expect 23 checks" while SUMMARY is 25 — pre-existing doc drift, untouched by this change
  (spec mandates no new gate; none added). Not a finding.

## 7. Live grounding (auditor-executed, read-only `list` calls, zero mutations)

- `rig queue list --json -A --limit 1` → exit 0, `qitemId: qitem-20261022111416-78213c07c3272cbc`, `len=37` — the same live
  item cited by implementer and QA, independently re-observed. Full ID resolves from JSON output.
- Bare `rig queue list -A --limit 1` → same full 37-char ID in output. The #37 truncation premise stays refuted on the
  live fleet; the only thing changed by this wave is which form seats are taught to copy from. No behavior change to
  `rig` invocation semantics beyond examples. (The known #44 JSON trailer on `show` output is wave-44's remit; not touched.)

## 8. Secrets scan over the diff

Grep of the full `39e45b6..HEAD` diff for secret-shaped patterns (`sk-`, `ghp_`, `github_pat_`, `AKIA`, `xox*`,
`BEGIN PRIVATE KEY`, `AIza`, secrets-path references): **zero hits**. Live access throughout was read-only
(`list`/`show`); no items created, claimed, or mutated. No credentials printed or committed.

## Findings

None. Zero numbered findings. Every deliverable in `tasks.md` T1–T5 is met with testable evidence; every non-leaf file is
justified; all 153 leaves carry exactly the primer churn; provenance/digest integrity holds per the repo's own blessed
rules; the 4 tests are non-vacuous and complementary; no scope creep toward CLI/upstream; skipped items independently
concurred; gates re-run green by the auditor; secrets clean; tree clean.

VERDICT: PASS
