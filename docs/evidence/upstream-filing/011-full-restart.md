<!-- DRAFT ONLY — NOT FILED. Filing requires a separate explicit per-issue approval. -->
<!-- Post at: https://github.com/mvschwarz/openrig/issues/new (suggested template: feature_request.yml) -->
<!-- Our tracker: https://github.com/Heretek-AI/heretek-rigs/issues/11 -->

# [Draft] Support relaunching / refreshing a single running node without a fleet-wide restart

## Problem

`rig launch` cannot refresh a single running node. A policy rollout (charter
change re-seeded to seat files on disk) leaves the running session enforcing
the old policy, and there is no supported path to reload exactly the affected
seat:

- `rig launch <rigId> <nodeRef>` answers `Node <node> is already running in
  rig <rigId> (not relaunched)` — while the help text promises `Launch **or
  relaunch** a node in a running rig`.
- There is no `rig stop/restart <node>` verb (only whole-rig `down`, or
  destructive `remove`).

## Live impact

After a merged charter change plus full re-seed on a 51-seat fleet, the
affected seat's fate depended on unverified luck (the running session
happened to pick up the new policy). Had it not, the only operator options
were a whole-fleet `down`+`up` mid-flight or leaving the seat stale. The
same refusal class re-appeared on current tooling: a fresh `rig up` against
a stale existing rig is refused (`docs/reports/fleet-proofs-implementation.md`
line 59, restored non-destructively). Full write-up in our issue `#11`
(linked above).

## Adjacent upstream issue (accurately distinguished)

Upstream `#2200` (`rig seat restart --keep-conversation` refuses a Codex
seat launched by a 0.6.x tmux-send script — still OPEN, filed 2026-10-27
against 0.7.4, no fix in the v0.7.4...v0.7.5 compare) shows a restart verb
exists but fails for exactly the long-lived-seat population an upgrade
targets: detection looks only at the pane process and its direct child,
while these seats run the agent one level deeper (grandchild of the pane).
That is a detection bug in an existing verb — this request is the broader
missing capability (relaunch-on-`launch`, or a supported single-node
refresh), for which no upstream commit exists in the current release line.

## Existence proof that refresh-without-restart is achievable

On our fleet we refresh one seat's live policy with a member-fragment
refresh and no relaunch: the refresh exits 0, the live config carries the
new rule, the running seat enforces it on its next action, and reverting
returns the live config to semantic-equal under both rig bindings
(`docs/evidence/fleet-proofs-2026-10-30/runbook.md:51-64`, Step 5). So the
mechanism is feasible — it is just not a supported upstream verb.

## Ask

Either (a) make `rig launch` actually relaunch a running node (graceful
drain + restart with fresh seed), or document a supported single-node policy
refresh; or (b) correct the help text and provide a restart verb that also
covers grandchild-launched seats (the `#2200` class). Goal: charter changes
propagate to exactly the affected seats without fleet-wide restarts.

## Environment observed

- `rig 0.7.5`, loopback daemon, Linux, 51-seat fleet. All observations are
  read-only except the documented member-fragment refresh cycle on our own
  fleet (fully reverted, semantic-equal verified).
