# Verification report: stage upstream-filing (change 2026-10-29-upstream-filing)

- Auditor: agency-drift-guard (independent triad audit; no fixes applied).
- Worktree: `.lane/trees/upstream-filing`, branch `feat/upstream-filing`, HEAD `5dd1ec0`
  (`ffca5d6` package + `5dd1ec0` QA red-proofs commit). `git status --short` clean at sign-off.
- Prior QA: agency-qa PASS (`docs/evidence/upstream-filing/qa-run.log`, 4 red-proofs in
  `red-proofs.log`) + 1 non-blocking advisory (proposal.md:22 negation-prose).

## 1. Scope / One Rule / Refs discipline

- `git diff main...HEAD --name-only` = 11 files, all allowlisted docs/package:
  `AGENTS.md` (1-line docs-map row), 3 drafts under `docs/evidence/upstream-filing/`,
  `qa-run.log` + `red-proofs.log`, `docs/reports/upstream-filing-implementation.md`,
  4 files under `openspec/changes/2026-10-29-upstream-filing/`.
- Guarded paths empty (rc=0, 0 bytes):
  `git diff main...HEAD --name-only -- fleet/ scripts/ tests/ specs/ rigs/ rosters/ registry/ archive/ openspec/specs/` → EMPTY.
- One Rule holds: no hand-edits to generated leaves in the diff (the
  `--check-idempotent` run rewrote digest/timestamp fields in `registry/`/`rigs/`/`specs/`/`fleet/skills-lock.json`;
  consecutive runs byte-identical, rc=0; all generator dirt reverted, tree clean — pre-existing
  environment drift, not a stage defect; stage touches no generator inputs).
- Refs-only: zero `(Closes|Fixes|Resolves) + #N` hits in the three drafts (rc=1, clean).
  The only `Closes #127/#80/#11` occurrences in the diff are (a) proposal.md:22 negation-prose
  in backticks inside a repo file (inert — GitHub automation reads only PR bodies/commit
  messages), and (b) QA/red-proof log records of planted-then-restored sabotage. All live
  tracker links are `Refs #127` / `Refs #80` / `Refs #11`.

## 2. Spec acceptance REQ-U0..U3 (Scenario checks)

- REQ-U0 (prepare-only; zero writes): PASS. Report lists every upstream interaction as a GET
  with output; scope gate empty; newest upstream issues (#2294–#2299: slack/export/OpenShell/
  hook topics) unrelated to drafts; no draft-attributable filings. My own upstream interactions
  were read-only GETs only (§3). No POST/PATCH/PUT/DELETE tooling in the diff — the only
  matches for write-verb strings are prose prohibitions ("NO POST/PATCH/PUT/DELETE"), not commands.
- REQ-U1 draft (a) `127-queue-send-attestation.md`: PASS — new-issue URL + template (line 2),
  spoof problem (9–16), wave-9/#127 evidence pointers with file:line refs (19–36),
  "Attribution, not authentication" note (46–49), daemon-attestation ask (53–58),
  per-issue filing-gate header (line 1). Self-contained for a maintainer.
- REQ-U2 draft (b) `080-snapshot-list-by-name.md`: PASS — URL (line 2), original 0.6.13
  symptom + companion ask (7–14), #1681 recorded as the COVERING fix with the plan
  discrepancy explicitly corrected (18–27), #1707/#2168 as genuinely adjacent (28–33),
  2026-10-30 local 0.7.5 verification (34–37), release-vehicle ask (46–51). The one
  unconfirmable fact (release vehicle) is flagged, not papered over (39–44).
- REQ-U3 draft (c) `011-full-restart.md`: PASS — URL (line 2), launch-refusal problem (9–18),
  live impact (22–29), upstream #2200 accurately distinguished as adjacent detection bug (31–41),
  #96 member-fragment refresh as existence proof with file:line refs (45–50), relaunch /
  refresh / help-text ask (52–58).

## 3. Independent upstream re-verification (GETs only, 2026-10-30)

- `repos/mvschwarz/openrig` → `mvschwarz/openrig`, `default_branch: main`. Matches.
- `releases/tags/v0.7.5` → tag `v0.7.5`, published `2026-10-29T07:38:44Z`. Matches.
- `pulls/1681` → merged `2026-10-21T11:43:45Z`, "accept a rig name in rig snapshot, snapshot
  list, export and restore --rig"; body confirms `resolveRigHandle` shared with
  down/grow/remove and unknown-handle `not found` exit 1. #1681 COVERS #80 — draft (b)'s
  reframing is honest. `pulls/1707` → merged, column-widths (cosmetic). `pulls/2168` →
  merged `2026-10-27`, `periodicSnapshotActive` scoping. Matches design §Upstream facts.
- `issues/2200` → open issue (not a PR), created 2026-10-27, Codex grandchild-of-pane
  restart refusal; still open after 0.7.5. Draft (c)'s "adjacent, distinct mechanism"
  treatment is accurate.
- `compare/v0.7.4...v0.7.5` → `ahead_by: 41`, `status: diverged`; message list contains
  #2168, no #1681/#1707 lines, no `rig launch` relaunch / restart / policy-refresh fix.
  Matches (release-vehicle question genuinely open from outside).

## 4. Re-run gates (in worktree, this audit)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed, 0 failed`, rc=0.
- `openspec validate 2026-10-29-upstream-filing` → `is valid`, rc=0.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`, rc=0.
- `generate-rigs.py --check-idempotent` → byte-identical, rc=0 (generator dirt reverted, clean).
- `make test` skip VALID: `git diff main...HEAD --name-only -- scripts/ tests/ src/ Makefile`
  empty — nothing executable changed, nothing to run.
- Red-proofs audited: RP-1 (Scenario removal → validate rc=1 with non-vacuous
  `REQ-U2 must include at least one scenario` signature → byte-identical restore → rc=0),
  RP-2 (scope gate GREEN + discrimination via non-empty AGENTS.md control), RP-3/RP-4
  (planted token / planted Closes → grep rc=0 RED → restore → rc=1 clean). Baseline
  sha256 recorded; `git status` clean after each. Zero vacuous checks.

## 5. Secrets / anti-stub / honesty

- Drafts: zero `ghp_|gho_|Bearer <token>` hits, zero 40+-char alnum tokens, zero
  machine-local paths (`/home/`, `/tmp/`, host/qitem ids) — all rc=1 clean. (The only
  long-token hits repo-wide are sha256 baselines and pattern-description prose, not secrets.
  Never printed secrets.)
- Anti-stub: no TODO/FIXME/NotImplemented/placeholder/empty-catch patterns in changed files;
  drafts are substantive (63/56/64 lines, each with problem, evidence, note, ask).
  `make test` skip is reasoned, not a fake pass.
- Honesty: no draft asserts an unverified fact — versions/dates exact, the #1681 vehicle
  labeled unconfirmed, #1707/#2168 labeled adjacent-not-covering, #2200 labeled adjacent
  with distinct mechanism. Per-issue filing gate unambiguous in three places (proposal
  §Sensitive-action approval, design §Filing procedure, per-draft `DRAFT ONLY — NOT FILED`
  header): preparation approved, transmission requires separate explicit per-issue approval.
- Advisory confirmed understood: proposal.md:22 negation-prose is inert in-repo but MUST NOT
  be pasted into any PR body (repo convention: only `Refs #127/#80/#11`). Not a finding.

## Findings

None. All deliverables present, all gates green, all upstream facts independently confirmed,
negative check holds, red-proofs non-vacuous, tree clean.

VERDICT: PASS
