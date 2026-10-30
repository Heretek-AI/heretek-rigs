# upstream-filing Specification

## Purpose
Prepare (never file) three upstream issue drafts for `mvschwarz/openrig`
that a maintainer can act on without access to our repo. Each requirement is
one draft with binary content obligations: URL, problem, evidence, the
draft-specific mandatory note, and an explicit ask. A fourth requirement pins
the prepare-only negative gate.

## Requirements

### Requirement: REQ-U0 — prepare-only; zero upstream writes

The stage MUST NOT file anything upstream and MUST NOT perform any upstream
API write. All upstream interactions are read-only GETs, each listed in the
stage report with its output. No daemon edits, no mitigations removed, no
new V-gate. Filing any single draft requires a separate explicit principal
approval (per-issue) — preparation approval never implies transmission
approval.

#### Scenario: negative check passes

- When QA audits the stage, the report lists every upstream interaction as a
  GET command with its observed output, `git status --short` shows only the
  intended docs/package files, and no new issue exists upstream attributable
  to this stage.

### Requirement: REQ-U1 — draft (a): queue/send daemon caller attestation (Refs #127)

`docs/evidence/upstream-filing/127-queue-send-attestation.md` MUST contain:
the upstream new-issue URL; the problem (daemon accepts queue/send sender
claims with zero challenge — forged `--source` / env-claimed identity is
recorded as-is); repo-side evidence citations with file:line refs
(wave-9 spoof proof, #127 M0 probe, rework refutation); the note that our
repo-side per-seat sender bindings provide attribution, not authentication;
and the ask (daemon-issued caller attestation for queue operations, or
equivalent).

#### Scenario: maintainer reads only draft (a)

- When a maintainer reads ONLY the draft file, they understand what is
  spoofable, what we proved (with cited evidence pointers), what our
  repo-side mitigation does and does not do, and exactly what upstream
  change is requested — without needing our repo.

### Requirement: REQ-U2 — draft (b): snapshot-list-by-name verification (Refs #80)

`docs/evidence/upstream-filing/080-snapshot-list-by-name.md` MUST contain:
the upstream new-issue URL; the problem (original #80 repro: name form
prints `No snapshots`, only rig ID works); the #1681/#1707/#2168 deltas with
the verified discrepancy recorded — #1681 is a MERGED PR implementing the
name-resolution ask (not non-coverage), #1707 is cosmetic column widths,
#2168 is the `periodicSnapshotActive` projection flag — plus the 2026-10-30
local 0.7.5 verification (name form works; unknown handle fails closed);
and the ask (confirm the release vehicle carrying the fix; close-out if
confirmed).

#### Scenario: maintainer reads only draft (b)

- When a maintainer reads ONLY the draft file, they see the original
  symptom, which upstream change addresses it, what we verified on the
  pinned release, the one fact we could not confirm from outside (release
  vehicle), and the precise confirmation requested.

### Requirement: REQ-U3 — draft (c): single-node relaunch / policy refresh (Refs #11)

`docs/evidence/upstream-filing/011-full-restart.md` MUST contain: the
upstream new-issue URL; the problem (`rig launch` refuses running nodes
despite "or relaunch" help; no supported single-node policy refresh; live
impact observed); upstream #2200 cited accurately (open `rig seat restart`
refusal for Codex seats launched by 0.6.x scripts — adjacent restart-path
evidence, distinct mechanism); our #96 live-refresh route as the working
existence proof (member-fragment refresh, no relaunch, running seat
enforces the new rule, revert to semantic-equal); and the ask (relaunch
running node with fresh seed, or a supported single-node refresh, or
corrected help text plus a restart verb that covers grandchild-launched
seats).

#### Scenario: maintainer reads only draft (c)

- When a maintainer reads ONLY the draft file, they understand the missing
  operator capability, the live consequence, the adjacent upstream restart
  issue and how it differs, the proof that refresh-without-restart is
  achievable, and the exact upstream change requested.
