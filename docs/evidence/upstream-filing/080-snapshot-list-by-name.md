<!-- DRAFT ONLY — NOT FILED. Filing requires a separate explicit per-issue approval. -->
<!-- Post at: https://github.com/mvschwarz/openrig/issues/new (suggested template: bug_report.yml) -->
<!-- Our tracker: https://github.com/Heretek-AI/heretek-rigs/issues/80 -->

# [Draft] `snapshot list <rig-name>`: verify fix release vehicle (follow-up)

## Problem (original report, observed on 0.6.13)

`rig snapshot list <rig-name>` silently reported `No snapshots` for a rig
that had them; only the rig ID form worked, which is easy to mistake for
"the fleet has no rollback point". `rig ps` shows only the name, so the
working handle was undiscoverable from normal output. Companion ask: fail
with "unknown rig" instead of `No snapshots` when the handle matches
nothing.

## What changed upstream (verified from outside on 2026-10-30)

- **#1681 is the covering fix — not a non-covering delta.** Upstream PR
  `https://github.com/mvschwarz/openrig/pull/1681` ("accept a rig name in
  rig snapshot, snapshot list, export and restore --rig", merged to main
  2026-10-21) resolves the argument with the same `resolveRigHandle` used
  by `rig down`/`grow`/`remove`, and reports an unmatched handle as
  `Rig '<handle>' not found` (exit 1) instead of `No snapshots`. This
  addresses both the original symptom and the companion ask. (Recording
  this plainly: an earlier internal note listed #1681 alongside #1707/#2168
  as deltas proving non-coverage — that was wrong for #1681, which covers
  the issue directly.)
- **Genuinely adjacent, non-covering:** PR
  `https://github.com/mvschwarz/openrig/pull/1707` (merged 2026-10-21)
  only sizes snapshot-list columns (cosmetic); PR
  `https://github.com/mvschwarz/openrig/pull/2168` (merged 2026-10-27,
  milestone v0.7.5) only scopes the `periodicSnapshotActive` flag to
  scheduler-snapshotted rigs. Neither touches name resolution.
- **Verified fixed on the pinned release.** On `rig 0.7.5`, 2026-10-30
  (read-only checks against a healthy fleet): `rig snapshot list
  <fleet-name>` returns snapshot rows, and `rig snapshot list
  no-such-rig-xyz` prints `Rig 'no-such-rig-xyz' not found` with exit 1.

## The one fact we cannot confirm from outside

The v0.7.4...v0.7.5 compare's commit-message list does not visibly contain
the #1681/#1707 changes, so we cannot tell from outside which release
vehicle carries the name-resolution fix (cherry-pick under a different
message, or release line already containing equivalent behavior).

## Ask

Please confirm which release carries the #1681 name-resolution behavior. If
confirmed in 0.7.5 (matching our observation), this can close as
fixed-upstream with no further action; if it is main-only, we will track
our issue `#80` (linked above) until the carrying release ships.

## Environment observed

- `rig 0.7.5`, loopback daemon, Linux. Checks above are read-only
  (`snapshot list` by name and by unknown handle).
