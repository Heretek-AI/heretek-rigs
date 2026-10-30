# seat-hygiene independent verification (drift-guard, stage: seat-hygiene, 2026-10-30)

Change: `openspec/changes/2026-10-30-seat-hygiene/`. Worktree `.lane/trees/seat-hygiene`
(branch `feat/seat-hygiene`, HEAD `f307916`). Scope: AUDIT ONLY — no repairs,
no launches, no V-gate. Refs #147 — never Closes. Read-only live ops only;
no commits by drift-guard; no secrets printed.

Prior QA verdict: PASS (3 non-blocking findings + RP-1 qualification). Post-QA
micro-pass (HEAD `f307916` over QA HEAD `ac5375d`): FINDING-01 path base
(`../../` form), F2 split numbers, F3 backticks, 3 log redactions.

## 1. Scope / One Rule / Refs-only

- `git diff main...HEAD --name-only`: 11 files — `AGENTS.md` (+1 docs-map row
  only, confirmed by diff), 4 openspec files (proposal/design/spec/tasks), 4
  evidence files (`audit.md`, `dangling-seats.json`, `ps-pre/post.txt`), QA log,
  implementation report. No other paths touched.
- Guarded scope gate
  (`git diff main...HEAD --name-only -- fleet/ scripts/ tests/ specs/ rigs/
  rosters/ registry/ archive/ openspec/specs/`): EMPTY, rc=0. Guarded paths clean.
- One Rule: zero generator inputs touched; no hand-edits under `specs/ rigs/
  rosters/ registry/` (guarded diff empty proves it).
- `Closes #147`: occurrences are `proposal.md:28` (backticked), implementation
  report `:15` (backticked after micro-pass — FINDING-03 fixed and verified) and
  `:41` (backticked). All inside docs code spans; commit subjects use
  `Refs #147`. Zero `Fixes/Resolves/Close #147` variants. Zero GitHub closure risk
  (no occurrence in a PR body or commit message). Refs-only posture holds.

## 2. Spec acceptance REQ-H1/H2/H3 (spec has 3 Requirements, 4 `#### Scenario:` blocks — counted by direct read)

- REQ-H1 completeness: per-seat table has 51 data rows (recounted); 24 DANGLING
  (2 lobotomized + 22 stale) + 27 clean = 51, reconciles exactly with
  `dangling-seats.json` (JSON valid, 24 entries, 2/22 split, all 11 schema keys
  present + top-level `generated`/`issue`/`stale_shell_target`/`expected_shell`).
  Independent live re-reads: 2 lobotomized + 1 stale seat still carry the
  fleet-proofs `shellPath`; 1 clean seat carries the in-repo wrapper. Daemon root
  holds 70 dirs = 54 with `agent/settings.json` + 16 sessions-only; 3 orphaned
  `command-*` dirs carry NO `shellPath` key — all recorded with reason, none skipped.
  MCP column recount: 37 ok + 10 dis + 4 mix = 51. PASS.
- REQ-H2 repair input: `stale_value` (`.lane/trees/fleet-proofs/...`) resolves
  ABSENT (host-verified); `expected_shell` (`scripts/seat-sandbox.sh`) resolves
  EXISTS (host-verified); `launch_cwd` two-level form `../../heretek-asset-manager`
  resolves to the live sibling-checkout launch_cwd value (verified EXISTS on this host)
  which EXISTS (host-verified), matching every live `seat status --json`
  `launch_cwd`. F2 re-scan from disk reproduces the corrected split exactly:
  21 missing binaries / 16 state dirs (14 live + 2 orphaned) / 7 binary names /
  11x(False,deferred) + 4x(absent,deferred) + 3x(absent,direct) + 3x(False,direct),
  including the live direct-exposure `qa-api-contract-tester` openapi case
  (binary confirmed absent) correctly bucketed as provisioning, not dangling.
  The repair wave can scope from this file with zero re-inspection. PASS (with
  advisory OBS-01 below on transcript strings).
- REQ-H3 zero mutation: `sha256sum` both snapshots =
  `1a0b936e…6c6726` (matches QA-logged prefix); `cmp` rc=0 IDENTICAL; 111 lines
  each. Queue: 100 qitems, ZERO containing `seat-hygiene`. Live re-read confirms
  the 2 lobotomized seats STILL carry the dangling `shellPath` — the wave left
  them exactly as found and claims no repair credit (proposal §Non-goals +
  audit text disclaim repairs explicitly). PASS.

## 3. Gates re-run (this audit, unmodified tree)

- `./scripts/verify-rigs.sh --check-only`: `SUMMARY: 39 checks passed, 0 failed`, rc=0. No new gate (V31 entry is the pre-existing 15-auth-envelope wave's).
- `openspec validate 2026-10-30-seat-hygiene`: `Change is valid`, rc=0.
- `python3 scripts/audit_loop.py --self-test`: SELF-TEST PASSED, rc=0.
- `generate-rigs.py --check-idempotent`: byte-identical, rc=0; side-effect leaf
  modifications (pre-existing staleness, same class as QA §A.5) reverted via
  `git checkout -- .`; `git status --short` clean afterwards (0 lines).
- `make test` skip legitimate: committed diff contains zero `*.py`/`*.sh`/
  `Makefile`/`tests/` diffs (guarded gate EMPTY proves it).

### RP-1 judgment (content-insensitive validator)
QA proved `openspec validate` stays GREEN under requirement/scenario removal, so
it guards change-recognizability only. For THIS audit-only wave that does not
weaken acceptance: the acceptance-bearing artifacts are the evidence files, and
the 4 Scenarios + REQ-H1/H2/H3 were verified by direct read (this report §2 —
`grep -c '#### Scenario:'` = 4, 3 `### Requirement:` headers). Content verified,
not validator-inferred. Sufficient — not a FAIL. Future behavior-changing waves
must not rely on `openspec validate` alone (QA qualification endorsed).

## 4. Drift-guard's own red-proof (evidence-tamper probe, RP-DG-1)

- Baseline `sha256` of `dangling-seats.json`: `92cc97d8…04fe4f` (backup to /tmp).
- Tamper: dropped 1 entry (24→23) + flipped 1 impact stale→lobotomized.
- Detection path (reconcile script): JSON 23 vs table DANGLING 24 → MISMATCH
  DETECTED; JSON lobotomized 3 vs table 2 → MISMATCH DETECTED. RED proven live
  (check is not vacuous — it fires on both count and label corruption).
- Restore: `cp` backup back → `cmp` byte-identical, sha256 `92cc97d8…04fe4f`
  matches baseline; `git status --short` clean. GREEN restored.

## 5. Secrets / anti-stub / machine-usability

- Secret sweep over all wave files: zero token-shaped matches
  (`ghp_|sk-|xox[bap]-` patterns); only pattern-literal self-mentions and the
  prose "Bearer-shaped strings: none" remain. The redacted canary is GONE.
  No private keys, no secret values, no `!cat` dereferences. PASS.
- Stub sweep (`TODO|FIXME|XXX|HACK|placeholder|not implemented`): zero hits in
  change package + evidence. No vacuous `|| true`, no skipped checks. PASS.
- JSON genuinely usable: parsed, schema-complete, both critical paths resolved
  against the repo root on this host (§2). PASS.

## 6. Honesty / repair-input actionability

- Counts verified by independent recount: 24 = 2+22; 51 = 24+27; mcp 37+10+4 = 51;
  F2 11+4+3+3 = 21; queue 100 with 0 wave-attributable. No overclaim found in
  repair-critical numbers.
- OBS-01 (advisory, non-blocking): audit §2 "The ONLY `.lane/trees/` reference
  anywhere in live daemon state is the one stale shellPath value" is exact for
  config fields (all 24 `settings.json` hits are the fleet-proofs value; full
  host grep finds 28 files, the extra 4 being historical session transcripts of
  the 2 racers — records of past launches, not path fields, and all pointing at
  the same pruned tree). Prune-safety conclusion ("pruning `seat-hygiene` later
  orphans nothing") verified: every `.lane/trees/` string host-wide references
  only `fleet-proofs`, no existing worktree. Repair wave unaffected.
- OBS-02 (advisory, non-blocking): implementation-report "Sole `Closes #147`
  occurrence" phrasing remains numerically loose (2 backticked occurrences: :15
  and :41) but both are backticked code spans with zero closure risk; FINDING-03's
  substance (backticking) is fixed.
- Repair-wave input contract (design §"Repair-wave input contract") is actionable:
  schema, impact labels with provenance, stale/expected shells, and the launch
  budget/scoping deferral are all explicit. No repair credit claimed anywhere.

## 7. V-absence

Correct for an audit wave: no behavior change, no new gate (39/0 stands, no new
`V*` block), `tasks.md` triad box stays UNCHECKED. No V-gate owed.

## Findings

None blocking. OBS-01 and OBS-02 are repair-wave advisories / prose nits, not
audit defects: every stub, vacuous-check, failing-command, missing-deliverable,
and mutation test passes.

VERDICT: PASS
