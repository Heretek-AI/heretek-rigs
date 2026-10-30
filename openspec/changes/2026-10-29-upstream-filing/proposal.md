# Proposal: 2026-10-29-upstream-filing — three upstream draft bodies, PREPARE-ONLY

## Goal

Author three self-contained upstream issue draft bodies under
`docs/evidence/upstream-filing/` against `mvschwarz/openrig`, one per
repo-side gap: (a) queue/send daemon caller attestation (Refs #127);
(b) `snapshot list <name>` verification + release-vehicle confirmation
(Refs #80); (c) single-node relaunch / policy refresh (Refs #11, adjacent
upstream #2200). Each draft carries its file-to-file posting URL, a problem
statement a maintainer can understand without our repo, repo-side evidence
citations with file:line or commit refs, and an explicit ask.

## Non-goals

- NO filing. Not one draft is posted, and no upstream API write of any kind
  is performed in this stage (no POST/PATCH/PUT/DELETE to api.github.com or
  github.com — read-only GETs only, listed in the stage report).
- No daemon edits, no local mitigations removed, no behavior-code changes of
  any kind. Docs and OpenSpec package only.
- No new V-gate (39/0 stands).
- Never `Closes #127/#80/#11` (not in this package, not in any filing PR).

## Sensitive-action approval (recorded)

Filing each draft requires a separate explicit principal approval
(per-issue). This gate is verbatim: no draft may be filed, in whole or in
part, until the principal approves that specific draft. Preparation of the
draft bodies is approved; transmission is not.

## Acceptance

- Three draft files exist, each self-contained, each containing: the
  upstream new-issue URL, the problem statement, repo-side evidence
  citations, the draft-specific mandatory note ((a) "attribution, not
  authentication"; (b) #1681/#1707/#2168 deltas with the #1681 discrepancy
  recorded, not cited as non-coverage; (c) upstream #2200 + the #96
  live-refresh route), and zero secrets / Bearer material / machine-local
  paths.
- `openspec validate 2026-10-29-upstream-filing` exits 0.
- Compound green in the worktree (39/0, self-test, idempotent);
  `make test` skipped with reason iff `git status --short` shows zero
  code/test/script diffs.
- Negative check: the stage report lists every upstream interaction as a GET
  with its output; QA re-verifies zero filed issues.
- Triad `VERDICT: PASS` before any PR (Refs #127, Refs #80, Refs #11 —
  never Closes).
