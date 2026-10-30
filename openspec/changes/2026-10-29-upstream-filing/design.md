# Design: 2026-10-29-upstream-filing

## Why prepare-only

Upstream filing is an irreversible public act under another project's
governance. The principal approved preparing the three draft bodies, NOT
transmitting them. Each draft therefore stays a file in
`docs/evidence/upstream-filing/` until a separate, per-issue explicit
approval names that draft. The negative check (REQ-U0) is acceptance-critical:
the stage report must list every upstream interaction as a read-only GET, and
QA re-verifies zero filed issues before any PR.

## Upstream facts (verified read-only 2026-10-30, all via `gh api` GETs)

- Repo resolves: `mvschwarz/openrig` (`default_branch: main`).
  New-issue URLs: `https://github.com/mvschwarz/openrig/issues/new`
  (templates: `bug_report.yml`, `feature_request.yml`).
- Latest release: `v0.7.5` ("OpenRig 0.7.5", published 2026-10-29T07:38Z).
  Local host pins `rig 0.7.5 (b57c4da3)`.
- Upstream #2200 is an OPEN issue (not a PR), filed 2026-10-27 against 0.7.4:
  `rig seat restart --keep-conversation` refuses a Codex seat launched by a
  0.6.x tmux-send script (Codex is a grandchild of the pane). One maintainer
  comment requests process-tree detail; no fix merged (absent from the
  v0.7.4...v0.7.5 compare). Still open after the 0.7.5 release.
- Upstream #1681 / #1707 / #2168 are all MERGED PRs to main, not open gaps:
  #1681 (merged 2026-10-21) implements rig-name resolution for `snapshot`,
  `snapshot list`, `export`, `restore --rig` via shared `resolveRigHandle`,
  including unknown-handle `not found` exit-1 behavior; #1707 (merged
  2026-10-21) sizes snapshot-list columns (cosmetic); #2168 (merged
  2026-10-27, milestone v0.7.5, present in the v0.7.4...v0.7.5 compare)
  scopes `periodicSnapshotActive` to scheduler-snapshotted rigs.
- Discrepancy vs the plan (recorded, not hidden): the plan described
  #1681/#1707/#2168 as "deltas proving non-coverage" of #80. Verified
  otherwise — #1681 directly COVERS #80's core ask. Draft (b) cites #1681
  as the covering fix and asks only for release-vehicle confirmation.
  #1707 and #2168 are genuinely adjacent/non-covering (cosmetic columns;
  scheduler flag) and are cited as such.
- v0.7.4...v0.7.5 compare (41 commits ahead): no commit addresses `rig
  launch` relaunching a running node or single-node policy refresh (#11's
  ask stays open upstream). Adjacent: #2159 (launch evidence for fresh
  handovers), #2157 (409 for runtime send refusals), #2198 (send waits for
  slow results) — none is a relaunch path.
- Local 0.7.5 verification (2026-10-30, read-only): `rig snapshot list
  <fleet-name>` returns rows; `rig snapshot list no-such-rig-xyz` prints
  `Rig 'no-such-rig-xyz' not found...` with exit 1. #80's primary symptom
  and its error-path ask both behave fixed on the pinned release.

## What each draft MUST NOT contain

- Secrets: no tokens, keys, key files, or redacted-with-length Bearer
  material. Sender bindings are described by name/scope only.
- Machine-local paths: no home-directory paths, no scratch-dir paths, no
  hostnames, no qitem hex IDs, no daemon host IDs. Repo-side evidence is
  cited as repo-relative `docs/...` paths with `:line` refs plus our public
  issue URLs — resolvable by us, opaque-but-honest to the maintainer.
- Claims beyond what was verified: the drafts state exact versions,
  dates, and the one unconfirmed fact (the #1681 release vehicle).

## Filing procedure (for later, NOT this stage)

1. Principal approves draft (a), (b), or (c) individually, by name.
2. Human opens the draft's upstream new-issue URL (base
   `https://github.com/mvschwarz/openrig/issues/new`, template per draft
   header), pastes the draft body, submits.
3. Human links the filed upstream issue from our tracker issue (#127, #80,
   or #11) with a `Refs` line — never `Closes` until live behavior proves
   the fix on our fleet.
