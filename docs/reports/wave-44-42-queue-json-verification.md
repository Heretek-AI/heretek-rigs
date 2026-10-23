# Verification: wave-44-42-queue-json (heretek-rigs #44 + #42, one upstream issue)

Stage: wave-44-42-queue-json · Worktree: `.lane/trees/wave-44-42-queue-json`
Commits audited: `9a8c272` (implementation) + `690931a` (QA evidence).
HEAD~2 = `8f6bbca` (merge base). `git status --short` clean at audit end.
Auditor: independent (no fixes made; sabotage edits restored via file copy, verified clean).

Contract: `openspec/changes/remediate-44-json-trailer/` (REQ-44-A1/A2/A3/M1) +
`openspec/changes/remediate-42-create-receipt/` (REQ-42-A1/A2/A3/M1).
Scope rule: local discipline + wrapper + EXACTLY ONE upstream issue; no CLI change (there is no CLI code in this repo).

## 1. Diff audit (base `8f6bbca..HEAD`, 192 files)

Non-leaf files (14, all justified against the two specs):
`AGENTS.md` (queue-row flag fix + both statements), `Makefile` (new test file in `make test`),
`README.md` + `docs/USER_GUIDE.md` (flag fixes + statement-appends),
`scripts/generate-rigs.py:810` (charter primer append), `scripts/send-authenticated.sh`
(flag hard-code + fail-closed receipt parse), `tests/test_queue_json_discipline.py` (new, 7 tests),
2× `proposal.md` appends (identical upstream URL), `docs/evidence/upstream-queue-stdout-issue.md`
(issue draft), plus this stage's own `docs/evidence/wave-44-42-queue-json/` logs and 2 reports.
No other non-leaf file touched. Zero hand-edits under `specs/ rigs/ rosters/ registry/`
beyond regen output (all leaf diffs are primer-statement appends and digest/provenance churn).

Generated leaves: `git diff --numstat` census over `specs/ rigs/ rosters/ registry/` =
304 added / 304 deleted, symmetric line-swap shape. Sampled 8+ leaf hunks across
rigs/specs/registry: every hunk is (a) the primer sentence appended in `context.md`
charters, or (b) `resolvedCommit: 39e45b6… → 8f6bbca…` / `packageDigest` value rotation.
No substantive leaf change found. `resolvedCommit` advances exactly to the pre-merge
base HEAD (`8f6bbca`), matching the accepted re-lag convention — not a hand-fudge.

## 2. Wrapper audit (`scripts/send-authenticated.sh`, read fully)

- Single execution line `:175` hard-codes `rig queue create --json --verify …`; no
  env var, flag, or config path can downgrade or strip the flags (grep for
  `VERIFY|CREATE_FLAGS|RIG_FLAGS` alternatives: none). `--dry-run` (`:159-166`)
  prints the flagged invocation and `exit 0` before any execution.
- Fail-closed parse is real: `json.loads` on stdout; `JSONDecodeError` → stderr +
  exit 3; missing/empty `qitemId`/`state` → stderr + exit 4 with raw stdout echoed
  (`:197-201`); upstream create failure propagates its exit code with "no delivery
  claimed" (`:176-179`). Success shape requires non-empty string `qitemId` AND `state`.
- No secrets/credential handling anywhere in the script (grep for
  token/secret/password/api-key: no hits) — pre-auth wrapper, nothing to leak.
- Only live-create path is the wrapper's own intended purpose (run by an operator,
  not by tests). Stage tests use fake-`rig`-on-PATH exclusively; see §6.
- Informational only: `:52` help prose recounts the pre-wrapper bare pattern as
  history. It is prose inside `print_help`, not an invocation, and out of the T1
  grep scope (generator + 3 guides + AGENTS.md). Not a finding.

## 3. Upstream issue (independently confirmed)

- `mvschwarz/openrig#1806` resolves, state OPEN. Body (2900 bytes) carries byte-exact
  evidence (3628 bytes, char 3472), file/line cites, and all three asks (trailer +
  compact notice + create receipt to stderr).
- Twin-hunt: `gh search issues --repo mvschwarz/openrig "bounded preview"` returns
  1806 ALONE; topic search returns []. EXACTLY ONE issue exists. No duplicates.
- Both packages cite the identical URL (`…/issues/1806` in both `proposal.md` files
  and the evidence doc); repo-wide grep for other `openrig/issues/` URLs: none.

## 4. Discipline tests (independent spot-checks, both directions)

- `python3 -m unittest tests/test_queue_json_discipline.py` → 7/7 OK (mine).
  Full suite `python3 -m unittest discover -s tests` → 153 OK (mine).
- Sabotage 1 (auditor): appended bare `rig queue list` line to README →
  `test_every_queue_example_carries_json` FAILED (failures=1). Restored, clean.
- Sabotage 2 (auditor): neutered both `sys.exit(3)/sys.exit(4)` in wrapper parse →
  wrapper suite FAILED (failures=1; the malformed path still exits non-zero via
  NameError, so only the identity-less test RED — still RED, tests non-vacuous).
  Restored, `bash -n` clean, `git status` clean.
- Wave-6 overlap: pre-commit `README:61` and `USER_GUIDE:215` already carried
  `--json` (genuinely wave-6 work); this wave's diffs there are statement-appends
  only — no flag churn, no duplication. `AGENTS.md` queue row and `USER_GUIDE`
  create example were still bare pre-commit; this wave's flag fixes are new work.

## 5. Gates run by auditor

- `make verify` → `SUMMARY: 25 checks passed, 0 failed`, exit 0 (live-health
  heartbeat WARN is advisory, exit 0; spec text says "22 checks" but the tree
  baseline is 25 — pre-existing drift, no gate added/renumbered per the
  never-renumber rule; zero regressions either way).
- `openspec validate remediate-44-json-trailer` → valid; `openspec validate
  remediate-42-create-receipt` → valid (both emit the pre-existing informational
  archive-refusal INFO for new specs — present for all new-spec changes, not a failure).
- Secrets scan over the full diff: only false positives (`HERETEK_SECRETS` env-var
  name in pre-existing AGENTS.md context, "command-backed secrets" in verify output
  prose, "tokenization" skill name + digest hashes). No credential-shaped strings.

## 6. No-scope-creep / no-live-mutation

- No CLI/runtime change: `dist|src|cli|lib` paths untouched (none exist in repo);
  executable-semantics changes are exactly the wrapper + tests + generator primer.
- Auditor's own live commands were read-only: bare `rig queue show <qitem>` →
  exit 0, 3628 bytes stdout / 0 stderr, tail is the bounded-preview trailer,
  `json.loads` → `JSONDecodeError: Extra data: line 96 column 1 (char 3472)`
  (byte-exact match to report); same + `--json` → exit 0, 2953 bytes, parses
  first try, stderr empty. Plus one `--dry-run` (executes nothing).
- Wrapper tests shadow via fake-`rig`-on-PATH; QA's tripwire-rig proof (7/7, zero
  hits) stands uncontradicted by code reading (single execution line, dry-run
  short-circuit). No live `queue create`/`send` attributable to this stage.

## Findings

None blocking. Two informational notes (pre-existing, not findings):
1. Spec "22 checks" vs tree baseline "25 checks" — pre-existing drift.
2. `openspec validate` archive-refusal INFO — pre-existing, informational.

VERDICT: PASS
