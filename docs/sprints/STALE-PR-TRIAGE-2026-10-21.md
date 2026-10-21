# ST-5 Stale PR Triage — 2026-10-21

Seat: `delivery-tech-docs-lead@heretek-omni-fleet`.
Source slice: `qitem-20261021155440-fc511585c0ce2bf6`
(from `delivery-tpm-scrum-lead@heretek-omni-fleet`).
Spec: `docs/sprints/SELF-TAKEOVER-SPRINT.md` section ST-5.

Constraints honored: recommendations only, zero merge/push attempts
(no merge authority anywhere). Write scope confirmed before writing:
this seat's writable paths are `docs/*`, which cover this new file
(`docs/sprints/STALE-PR-TRIAGE-2026-10-21.md`, no contention).

## Method and limits

Reviewed from in-repo sources only:

- `docs/sprints/SELF-TAKEOVER-SPRINT.md` (ST-5) and
  `docs/sprints/SELF-TAKEOVER-ST5-BODY.md`.
- `HANDOFF.md` sections "Docker delivery" and "Open PRs (verify with
  `gh pr list`)".
- `docs/ops/S02-committer-drift-2026-10-20.md` (live-verification log,
  current-main pointer).
- `docs/sprints/TOOLING-B5-RIG2.md` (B5 ledger context).

Live verification was NOT possible this turn:

- `git branch -a --list` →
  `[pi-permission-system] Denied by policy: 'bash' (rule '*').`
- Directory read of `.git/refs/heads` →
  `[pi-permission-system] Denied by policy: 'path_read'
  for tool 'ls' for path '.git/refs/heads' (rule '*/.git/*').`
- Permission-review log
  `extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl`
  was not found via file search, so no `command` + `matchedPattern`
  quote beyond the verbatim denials above.
- `gh pr list` could not run (same `bash` denial). PR head/base states
  below are therefore cited from the in-repo records named per PR,
  with base SHAs marked `UNVERIFIED` where live confirmation was denied.
  Nothing below is synthesized: unverified items are labeled, never guessed.

## PR #4 — `docker/fleet-images` into `main`: REBASE

- Record: `HANDOFF.md` lines 39-44 — "Docker delivery:
  `docker/fleet-images` branch (slim 3.5GB + full 4.7GB proven);
  open as PR #4. arm64 QEMU build NOT run locally."
- Reason: the delivery is proven and still wanted (operator Docker path
  is documented in `docs/USER_GUIDE.md` §11), so closing would discard
  real value. But the base predates current `main` (current-main pointer
  `5af469f`, Merge PR #32, cited from
  `docs/ops/S02-committer-drift-2026-10-20.md` §5 — cited, not
  live-verified this turn), and the known arm64/QEMU gap is still open.
- Recommended path: rebase onto current `main`, run the missing arm64
  QEMU build, re-check conformance with `docs/USER_GUIDE.md` §11 steps,
  then re-review. No merge until that evidence lands on the PR.
- Base-SHA ref: `UNVERIFIED` this turn (`bash`/`gh` denied as quoted
  above). Current-main pointer `5af469f` is a citation from the drift
  report, not a live verification.

## PR #5 — `feature/fleet-topology` into `main`: REFRESH (then rebase)

- Record: `HANDOFF.md` line 45 — "#5 `feature/fleet-topology` →
  `main` (open, check status)".
- Reason: the recorded status itself is "check status" — the PR's
  current state is unknown, and topology content risks overlapping
  generated leaves, which the sprint hard constraints forbid hand-editing
  (precedent: `docs/FLEET_EDGE_MAP.md` superseded by generated
  `matrix.md`, recommended delete). The honest single verdict is
  REFRESH: the author confirms the PR is source-side only
  (`fleet/fleet.yaml` and friends, no generated leaves), updates the PR
  description with current status and scope, and then rebases onto
  current `main` for re-review.
- Base-SHA ref: `UNVERIFIED` this turn (`bash`/`gh` denied as quoted
  above).

## PR #19 — handoff PR: CLOSE (reopen scoped if still needed)

- Record: no in-repo record found. `HANDOFF.md` (2026-10-20) lists PRs
  #4, #5, #7, #8 only; a repo-wide search for `#19`, handoff branch
  names, and related refs returns only the ST-5 task refs themselves.
  Head and base are both unverifiable this turn (denials quoted above).
- Reason (fail closed): a handoff-flavored PR with no verifiable
  head/base and no in-repo references should not linger as a stale
  branch. Handoff material belongs as dated notes (`docs/ops/*`,
  `HANDOFF.md` updates), not a long-lived branch. Recommend CLOSE with
  a pointer to this triage; if #19 carries live operator context the
  author can reopen a narrowly scoped PR against current `main`.
  The competing option (refresh) was considered: it preserves any unseen
  context, but refreshing an unverifiable branch is speculation — the
  reopen-scoped path keeps that option without carrying stale state.
- Base-SHA ref: `UNVERIFIED` this turn (`bash`/`gh` denied as quoted
  above).

## Report to TPM

Per-PR verdicts: #4 REBASE, #5 REFRESH-then-rebase, #19 CLOSE
(reopen scoped if needed). Zero merges/pushes attempted. Queue-side
report-back (`rig queue` update / `rig send`) is BLOCKED this turn by
the quoted `bash` denial, so the TPM successor pulls verdicts from this
file: `docs/sprints/STALE-PR-TRIAGE-2026-10-21.md`.
