# DRAFT — Proposal: issue-12-build-capability (spike, for principal approval — NOT implementation)

> **Status: DRAFT.** Produced by spike-12-builds (issues #12 + #9 + #11 design
> decisions, canary validation). Disk-side evidence only: the live fleet was
> DOWN at spike time (`rig ps`: 0 rigs running), so every live measurement is
> marked STAGED. Nothing in this package authorizes implementation; the
> implementation wave is separately gated on principal approval.

## Problem

Issue #12 reports that no seat can execute an end-to-end build. Its headline
claim — "the ONLY build-capable seat is cpp-lowlevel-eng" — is **over-narrow
and needs correction**: a fleet-wide static audit of `fleet/fleet.yaml`
(`bash_allow`, this worktree, 64 roles) shows **15 roles** hold at least one
build/test verb. The still-true core gaps are narrower and more actionable:

1. **No `git add` anywhere fleet-wide** (`grep -c "git add" fleet/fleet.yaml`
   → 0). Staging is impossible for every seat.
2. **No committer for seat-authored trees.** `git-drift-coord` (nominal
   committer) holds read-only git verbs only and is `builtin:locked` +
   `READONLY_16_ROLES`. `dependency-patcher` holds `git commit*` but without
   `git add` that grant commits only already-staged content — a dead grant
   for seat-authored work.
3. **Configure/compile dead for the engine seat.** `engine-systems-eng` holds
   `cmake --build*`, `ctest*`, `cargo test engine*`, `cargo bench*` but NOT
   `cmake --preset*` (configure), NOT a compiler invocation (only
   `cmake --version*` / `clang --version*`), NOT `./build.sh*`.
4. **`./build.sh` runnable in exactly one seat** (`cpp-lowlevel-eng`,
   via PR #13) — and that seat cannot stage/commit its output (gaps 1–2).

Related backlog (self-governance triple): #9 (operator→seat provenance) and
#11 (no single-node policy refresh). This change designs all three together
because each option below touches the same policy-propagation path.

## Already merged (do not re-litigate)

- PR #10: `engine-systems-eng.path_write` += `build.sh`, `CMakePresets.json`,
  `CMakeLists.txt`.
- PR #13: `cpp-lowlevel-eng.bash_allow` += `./build.sh*`.
- CLI 0.6.13 (`rig seat set-permissions`, `rig seat launch --stop`,
  `rig policy permissions apply --seat`) — new verbs directly relevant to #11,
  discovered during this spike (help-text verified daemon-down, behavior
  STAGED).

## Scope of the proposed change (at implementation time)

- **12a — build-runner scope.** Bounded configure/compile/test grants for a
  designated runner (options ranked in `design.md`; recommendation: extend
  the `cpp-lowlevel-eng` runner rather than widening authoring seats).
- **12b — operator-runner protocol.** Promote `scripts/send-authenticated.sh`
  + the PRE-AUTH-ENVELOPES template to the sanctioned fallback protocol with
  provenance (queue-authorized task → operator executes → log hashed into
  evidence chain), so today's ad-hoc fallbacks become a designed interface.
- **12c — committer scope.** A grant design that survives prefix-matcher
  reality (see `design.md` §4): exact-argv allowlisting, seat git identity
  without git-config widening, a non-locked non-readonly role, aligned with
  the A2 envelope model — NOT a one-line `git add*` delta.

## Non-goals

- No implementation in this change (spec + design + tasks only).
- No `fleet/fleet.yaml` edit, no regen, no re-seed, no relaunch.
- No `verify-rigs.sh` / `Makefile` edits.
- No live-seat contact (all live proof STAGED to the gated implementation
  wave).
