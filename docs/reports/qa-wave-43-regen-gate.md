# QA verdict: wave-43-regen-gate (remediate-43-regen-gate)

Stage: `wave-43-regen-gate` · Change: `remediate-43-regen-gate` · Issue: #43
Commits under test: `32c1233` + `5748758` · Base: `origin/main @ 00acda2`
Worktree branch: `remediate/43-regen-gate` · QA date (UTC): 2026-10-22
QA mode: sabotage-only edits, all reverted; no commits, no merges, no pushes.

Spec sources read from disk: `AGENTS.md`, `openspec/changes/remediate-43-regen-gate/specs/regen-gate/spec.md`
(REQ-RG1-RG4), `tasks.md` (T1-T6), `docs/reports/wave-43-regen-gate-implementation.md`, `gh issue #43`.
Full sabotage transcript: `docs/evidence/wave-43-regen-gate/red-proofs.log`.

## Verdict: QA-CLEAN (no numbered findings; one PASS-WITH-NOTE below)

| # | Check (spec) | Command | Observed output | Result |
|---|---|---|---|---|
| 1 | `make verify` 23/0 + advisory | `make verify` | `SUMMARY: 23 checks passed, 0 failed.` exit 0; LIVE-HEALTH WARN (heartbeat stale age-unknown x7, pre-existing) + SKIP seat-idleness; `sources: 4 ok, 1 skipped` | PASS |
| 2 | V1-V6 byte-identical (no renumber/reword) | `git diff 00acda2..HEAD -- scripts/verify-rigs.sh` | 0 removed lines; only `+import importlib.util` and appended V7 block with exactly one new `ok()` | PASS |
| 3 | Full suite + openspec | `make test`; `openspec validate remediate-43-regen-gate` | `Ran 58 tests ... OK` exit 0 (incl. `test_regen_gate.py` 8/8); `Change 'remediate-43-regen-gate' is valid` | PASS |
| 4a | REQ-RG1 sanctioned-only resolves, silent | synthetic /tmp repo, all 9 strays, `resolve_heretek_commit` no env | returns HEAD, stdout/stderr empty | PASS |
| 4b | REQ-RG1 tracked M refuses naming file | strays + `M fleet/fleet.yaml` | exit 2, stderr names `fleet/fleet.yaml` + remediation hint | PASS |
| 4c | REQ-RG1 non-allowlisted `??` refuses | strays + `?? scripts/evil-new-helper.py` | exit 2, stderr names the file | PASS |
| 4d | REQ-RG2 tracked-override refuses | committed `docs/evidence/kept.md` then edited (`M`) | exit 2 | PASS |
| 4e | Escape hatch unchanged | real dirt + `HERETEK_RIGS_ALLOW_DIRTY=1` | resolves, SHA == real HEAD (not SYNTHETIC) | PASS |
| 4f | REQ-RG4 V7 load-bearing | removed `".claude/"` from allowlist, then `./scripts/verify-rigs.sh --check-only` | exit 1; `[FAIL] HR-43: AGENTS.md blessed stray '.claude/' not covered...`; `SUMMARY: 22 checks passed, 2 failed` (all 22 pre-existing green); restored via `git checkout --` to 23/0 | PASS (not vacuous) |
| 4g | C-quoted edge | `_split_porcelain('?? "docs/evidence/a b.md"')` etc. | sanctioned-quoted to ignored; non-sanctioned-quoted to blocking; tracked-quoted `M` to blocking | PASS |
| 5 | Real-regen honesty, no provenance churn | `git diff 00acda2..HEAD --stat -- registry/`; grep resolvedCommit/canonicalUrl over registry diff | empty stat; 0 hunks (diff-wide hits are AGENTS.md context + report prose only) | PASS (absence-of-churn; full regen not re-executed, vendor checkouts required) |
| 6 | 22->23 consistency | `grep -rn "23 checks\|22 checks"` (code+root docs) | AGENTS.md:15, :45 to 23 OK; README.md:47 stays 22 (deliberate, see note) | PASS-WITH-NOTE |
| 7 | Hint + ALLOW_DIRTY identity | `grep -n "ALLOW_DIRTY=1 for dev regen"`; diff of `if dirty and not allow_dirty` | hint text unchanged (line 204); bypass condition unchanged; classified branch only refines the refuse path (REQ-RG3 two sections) | PASS |

## Per-requirement mapping

- REQ-RG1: checks 4a/4b/4c + unit tests `test_sanctioned_strays_only_resolves`,
  `test_tracked_modification_refuses`, `test_non_allowlisted_untracked_refuses`,
  `test_tracked_handoff_style_edit_refuses` -> PASS.
- REQ-RG2: checks 4d/4g + `test_committed_allowlisted_path_edit_is_dirt`; allowlist in-code
  constants with per-entry justification comments adjacent to `resolve_heretek_commit` -> PASS.
- REQ-RG3: checks 4b/4c (verbatim blocking lines) + 4a (happy-path silent) +
  `test_refusal_classifies_both_sections`, `test_clean_run_emits_no_dirt_output` -> PASS.
- REQ-RG4: checks 1/2/4f; V7 appended at end reading strays from the AGENTS.md bullet itself
  (not hardcoded), justification-comment assertion, synthetic-dirt gate via the unit file -> PASS.

## PASS-WITH-NOTE N1 (not a finding): README.md:47 still says "22 checks"

- The implementer deliberately left README.md:47 untouched; README.md is absent from this
  change's edited files (`git diff 00acda2..HEAD --name-only`), so REQ-RG4's
  "no stale 22 left behind by this change" holds -- the change left no stale count behind
  in any file it edited (verified: no `"22` remains in scripts/, tests/, Makefile, AGENTS.md).
- README is the user quickstart owned by another wave; updating it here would widen scope.
  Follow-up for the owning wave; does not block this stage.

## Pre-existing quirks left untouched (confirmed out of scope, not findings)

- `git status` subprocess failure defaults to `dirty=""` (proceeds) -- present before, unchanged.
- LIVE-HEALTH WARN heartbeat-stale advisory -- pre-existing, warn-first, exit 0.

## Tree state / provenance

- `git status --short` post-QA shows ONLY allowlisted untracked strays produced by QA itself:
  `?? docs/evidence/wave-43-regen-gate/` and `?? docs/reports/qa-wave-43-regen-gate.md`
  (both under sanctioned prefixes; zero tracked modifications).
- All sabotage reverted with `git checkout -- <file>`; restore verified by re-running
  `verify-rigs.sh --check-only` -> 23/0 and `git status --short` clean at restore time.
- No stubs/`|| true`/empty catches introduced (the one `except` in C-unquote is fail-closed
  to blocking); no secrets in commands/outputs (dummy fixtures only); no commit/merge/push.

## Exact commands (replay)

1. `make verify` -> SUMMARY 23/0, exit 0 (+ advisory).
2. `make test` -> 58 OK, exit 0. `openspec validate remediate-43-regen-gate` -> valid.
3. `python3 /tmp/qa_rg_sabotage.py` -> ALL A-E,G PASS, exit 0.
4. Sabotage F: removed `".claude/",` line -> `./scripts/verify-rigs.sh --check-only` exit 1,
   `SUMMARY: 22 checks passed, 2 failed`, names `.claude/` gap -> `git checkout -- scripts/generate-rigs.py` -> 23/0.
5. `git diff 00acda2..HEAD --stat -- registry/` -> empty; `git status --short` -> only QA strays.
