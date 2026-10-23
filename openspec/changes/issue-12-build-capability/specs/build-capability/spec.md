# DRAFT — Spec: build-capability (spike, for principal approval — NOT implementation)

> **Status: DRAFT.** Requirements below are proposal-grade. Every live
> acceptance is TBD-marked STAGED until the gated implementation wave runs
> them against the relaunched fleet. Static acceptances (catalog greps,
> mock-harness probes) are runnable now and cited with exact commands.

## Capability: designated build-runner execution (12a)

### REQ-BC1 — One designated seat drives the canonical build entry

The designated runner seat SHALL execute `./build.sh` (and/or the
equivalent `cmake --preset` configure + `cmake --build` + `ctest` chain)
to exit 0 with a captured build log, on a tree whose SHA is recorded
alongside the log (D1–D4 of BUILD-CLOSEOUT-CRITERIA.md).

- Static acceptance (now): `cpp-lowlevel-eng.bash_allow` contains
  `./build.sh*` + `cmake*` + `ninja*` + `ctest*` (already merged, PR #13 —
  verify with `grep -n "build.sh" fleet/fleet.yaml`).
- **TBD (STAGED):** live D1–D4 logs attached to #12 (exit 0, CTest N/N,
  tree SHA, ELAPSED). Mock-harness ALLOW is NOT accepted as build proof.

### REQ-BC2 — Runner grants are output-anchored, not trust-based

Every build-adjacent grant SHALL pair with a checkable artifact: exit code
+ committed log + no-fetch scan (no network fetch during build). A grant
without its artifact check is incomplete.

- Acceptance: design doc lists each grant → artifact pair; implementation
  wave attaches the artifacts to #12.

### REQ-BC3 — No authoring seat gains execution scope under this change

Authoring seats (notably `engine-systems-eng`) SHALL NOT receive
configure/compile/`./build.sh` grants as part of 12a. Authorship and
execution stay separated so output-anchored verification stays meaningful.

- Static acceptance (now): `engine-systems-eng.bash_allow` contains no
  `cmake --preset*`, no compiler invocation, no `./build.sh*`
  (`sed -n '/^  engine-systems-eng:/,/^  exec-director:/p' fleet/fleet.yaml`).

## Capability: operator-runner protocol with provenance (12b)

### REQ-BC4 — Sanctioned fallback path replaces ad-hoc fallbacks

Operator-executed build/commit fallbacks SHALL run only under a
pre-authorization envelope (PRE-AUTH-ENVELOPES.md template: path scope,
owning seats, enumerated COMMIT/FILE-QUEUE-ITEM actions, TPM gate, expiry,
revocation, 3-link audit trail), delivered via `send-authenticated.sh`
(queue receipt `qitemId` + state parsed fail-closed).

- Static acceptance (now): wrapper passes `--source` + `--summary` on every
  invocation; `--dry-run` prints the exact `rig queue create` form
  (`scripts/send-authenticated.sh --destination <seat> --message <t>
  --human-ref <r> --dry-run` exits 0).
- **TBD (STAGED):** one relay round-trip on the relaunched fleet with the
  seat transcript ACK quoted verbatim.

### REQ-BC5 — `rig send` never carries authority

Raw `rig send` from outside a managed seat SHALL continue to arrive (and be
treated) as UNVERIFIED. No requirement in this package changes seat
fail-closed handling of anonymous relays.

## Capability: committer scope (12c)

### REQ-BC6 — Commit path without standing broad grants

Seat-authored output SHALL reach a commit through ONE of: (a) an
envelope-authorized operator COMMIT under REQ-BC4, or (b) a future grant
design that survives prefix-matcher reality — exact-argv allowlisting (not
path-suffixed `git commit*`), seat git identity without git-config surface
widening, on a non-locked non-readonly role, aligned with the A2 envelope
model.

- Static acceptance (now): no role holds `git add*`
  (`grep -c "git add" fleet/fleet.yaml` → 0 stays 0 until the C1 design
  lands); `git-drift-coord` stays `builtin:locked` + `READONLY_16_ROLES`.
- **TBD (STAGED):** D5 exercised (scoped stage + commit on a branch,
  push-to-main never granted) + D6/D7 (human merge, post-merge re-proof).

## Capability: single-node policy refresh (#11)

### REQ-BC7 — Refresh exactly the affected seats

Charter/permission changes SHALL propagate via a documented per-node path
(recommended composition: snapshot → drain/park → member-fragment re-seed →
`rig policy permissions apply --seat` if needed → `rig seat launch --stop`
with `--plan` preview → audit + gate confirm → unpark), with the
SEAT-REFRESH-RUNBOOK remove+launch fallback retained until the composition
is proven live.

- **TBD (STAGED):** first live use records snapshot ID, `--plan` output,
  audit excerpts; if `seat launch --stop` refuses a running node, that block
  is recorded as a headline finding (never worked around by bouncing).
- Static acceptance (now): help-text verbs exist
  (`rig seat launch --help`, `rig policy permissions --help` show the flags
  cited in `design.md` §4).
