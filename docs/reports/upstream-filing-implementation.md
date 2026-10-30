# Stage report: upstream-filing implementation

- Stage id: `upstream-filing`. Change id: `2026-10-29-upstream-filing`.
- Worktree: `.lane/trees/upstream-filing` (branch `feat/upstream-filing`,
  from `main` 677466e). No commit made (per stage instruction: do NOT
  commit). No `openspec archive` run.
- Mode: PREPARE-ONLY. Zero upstream filing occurred; zero daemon edits; no
  mitigations removed; no new V-gate.

## Deliverables (all in-worktree)

1. `openspec/changes/2026-10-29-upstream-filing/proposal.md` — goal (3
   drafts), non-goals (NO filing, no daemon edits, no mitigations removed,
   no V-gate), per-issue filing gate recorded verbatim.
2. `openspec/changes/2026-10-29-upstream-filing/specs/upstream-filing/spec.md`
   — REQ-U0 (prepare-only negative gate) + REQ-U1/U2/U3 (one per draft),
   each with `#### Scenario:` blocks.
3. `openspec/changes/2026-10-29-upstream-filing/design.md` — why
   prepare-only, verified upstream facts, must-NOT-contain rules, later
   filing procedure.
4. `openspec/changes/2026-10-29-upstream-filing/tasks.md` — package, issue
   verification, 3 drafts, negative-content sweep, gates; triad box left
   unchecked (needs qa/drift-guard verdicts).
5. `docs/evidence/upstream-filing/127-queue-send-attestation.md` — draft (a).
6. `docs/evidence/upstream-filing/080-snapshot-list-by-name.md` — draft (b).
7. `docs/evidence/upstream-filing/011-full-restart.md` — draft (c).
8. `AGENTS.md` — one docs-map row added (1 line, conventions verbatim).

## Upstream GETs performed (read-only; NO POST/PATCH/PUT/DELETE anywhere)

1. `gh api repos/mvschwarz/openrig --jq ...` → `full_name:
   mvschwarz/openrig`, `default_branch: main`. Repo resolves.
2. `gh api repos/mvschwarz/openrig/issues/2200 --jq ...` → open issue (not
   a PR), title "`0.7.4: 'rig seat restart --keep-conversation` refuses a
   Codex seat launched by a 0.6.x tmux-send script ...", created
   2026-10-27T21:03:41Z, state open. Relevant to restart behavior; distinct
   mechanism from #11 (recorded as adjacent in draft (c)).
3. `gh api .../issues/2200/comments --jq ...` → one maintainer comment
   requesting pane process-tree detail (PID/PPID/comm, no env/args); no fix
   merged; still open after the 0.7.5 release (2026-10-29T07:38Z).
4. `gh api repos/mvschwarz/openrig/issues/{1681,1707,2168}` → all three are
   CLOSED MERGED PRs to main: #1681 merged 2026-10-21 (rig-name resolution
   for snapshot/snapshot-list/export/restore --rig via `resolveRigHandle`);
   #1707 merged 2026-10-21 (column widths, cosmetic); #2168 merged
   2026-10-27, milestone v0.7.5 (`periodicSnapshotActive` scoping).
   Verified merged via `gh api .../pulls/<n> --jq .merged` → true for all.
5. `gh api repos/mvschwarz/openrig/releases/tags/v0.7.5` → tag `v0.7.5`,
   "OpenRig 0.7.5", published 2026-10-29T07:38:44Z.
6. `gh api 'repos/mvschwarz/openrig/compare/v0.7.4...v0.7.5'` → diverged,
   41 ahead; commit-message grep finds NO `rig launch` relaunch / restart /
   policy-refresh fix (#11's ask open upstream); #2168 present; #1681/#1707
   messages absent (release-vehicle question recorded in draft (b)).
7. `gh api repos/mvschwarz/openrig/contents/.github/ISSUE_TEMPLATE` →
   `bug_report.yml`, `config.yml`, `feature_request.yml`.
8. Our issues read live: `gh issue view {127,80,11} --json` → titles/bodies
   cited verbatim in drafts (127 "[P2] Queue/send identity is daemon-side
   on 0.7.x..."; 80 "rig snapshot list <rig-name> prints 'No snapshots';
   only rig ID works"; 11 "rig launch refuses running nodes despite 'or
   relaunch' help; no single-node policy refresh").

## Read-only live checks (own fleet, no writes)

- `rig --version` → `0.7.5 (b57c4da3)`.
- `rig snapshot list heretek-omni-fleet` (by NAME) → returns snapshot rows
  (rc=0). #80 primary symptom behaves FIXED on pinned 0.7.5.
- `rig snapshot list no-such-rig-xyz` → `Rig 'no-such-rig-xyz' not found:
  no rig has that name or id. ...`, exit 1. Error-path ask behaves FIXED.

## Upstream fact contradicting the plan (correction applied)

Plan §Wave-4 described #1681/#1707/#2168 as "deltas proving non-coverage"
of #80. Verified otherwise: **#1681 directly COVERS #80's core ask**
(merged PR implementing name resolution + not-found error path), and local
0.7.5 checks confirm both behaviors working. Draft (b) records this
discrepancy instead of citing #1681 as non-coverage; #1707 (cosmetic) and
#2168 (scheduler flag) are cited as genuinely adjacent. Draft (b)'s ask is
accordingly release-vehicle confirmation + close-out, not a new fix request.
Also: the plan text rendered #80's title as `[object Object]`; the real
title (above) is cited in all artifacts.

## Validation (in worktree)

- `openspec validate 2026-10-29-upstream-filing` → `Change ... is valid`,
  rc=0.
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed, 0
  failed`, rc=0.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`, rc=0.
- `python3 scripts/generate-rigs.py --check-idempotent` → rc=0
  (byte-identical; new untracked dirs reported as ignored sanctioned
  strays only).
- `make test`: SKIPPED with reason — `git status --short` shows zero
  code/test/script diffs (`M AGENTS.md` 1-line docs-map row + 2 new
  docs/package dirs only); nothing executable changed.
- `git diff --stat AGENTS.md` → 1 insertion (≤15-line budget).
- Negative-content sweep over drafts + package: secret-shaped
  (`[A-Za-z0-9_-]{40,}`), Bearer/key patterns, and machine-local path
  patterns (`/home/`, `/tmp/`, `~/`, host/qitem ids) → zero hits
  (grep rc=1). No secrets printed, logged, or committed at any point;
  dummy keys not needed (no tests authored).

## Negative check (acceptance-critical)

Zero upstream filing occurred: (1) no POST/PATCH/PUT/DELETE calls to
api.github.com or github.com were made during the entire stage — every
upstream interaction above was a GET, each listed with its output; (2) per
the stage brief, before/after issue-count comparison was NOT performed
(races with other humans) — instead the shell discipline stands: all
upstream commands were `gh api ... GET`s plus read-only local `rig snapshot
list` / `rig ps` queries. QA to re-verify.

## Self-audit / unfinished

- Triad `VERDICT: PASS` NOT yet obtained (needs agency-qa red-proof +
  agency-drift-guard audit); `tasks.md` triad box intentionally unchecked.
- No commit pushed (stage instruction). Worktree left with the 8
  deliverables above; `git status --short` shows only intended files.
- Draft (b)'s release-vehicle question is genuinely unconfirmed from
  outside — flagged in the draft, not papered over.
