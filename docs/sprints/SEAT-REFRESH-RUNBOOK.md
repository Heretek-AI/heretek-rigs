# Seat-Refresh Runbook — refreshing ONE stale seat without bouncing the fleet

**Slice:** A4 (Workstream A, repo-owned painkiller) · **Tracks:** Issue #11
**Status:** FALLBACK procedure, daemon-down drafted — every live-mutation step is
marked `[UNVERIFIED — confirm on live fleet]` until exercised against a running
daemon. This slice performs NO live execution (fleet is DOWN by program design).
**Out of scope:** any charter/permission/catalog/`rig`-CLI change. The CLI fix
belongs upstream (Workstream C).

Related: `docs/USER_GUIDE.md` (operator manual), `docs/sprints/PRE-AUTH-ENVELOPES.md`
(A2, pre-authorization envelopes — a parked queue item created by this runbook
should reference its envelope where one applies).

---

## 1. Purpose

Issue #11 ("`rig launch` refuses running nodes despite 'or relaunch' help; no
single-node policy refresh") records a real operational gap: after a charter or
permission change lands (PR merge) and the fleet is re-seeded, a **running**
session keeps enforcing the **old** policy — there is no supported way to refresh
exactly one node. The only certain remedies today are a whole-fleet `down`+`up`
(every seat bounces, all in-flight work stops) or destructive per-node surgery.

We felt this concretely around PR #10: after the merge plus a full re-seed, the
engine seat *happened* to pick up the new policy — by luck of its restart timing,
not by procedure. Had the fleet been busy, that one stale seat would have forced
a choice between a fleet-wide bounce for a single seat's staleness, or leaving a
seat enforcing superseded policy indefinitely. This runbook is the documented
fallback for that dilemma until the upstream CLI fix lands: a step-by-step,
single-seat refresh path built **only** from verbs that exist today, with every
unprovable step honestly marked.

---

## 2. The upstream gap (stated honestly)

What `rig launch --help` *claims* (verified daemon-down, `@openrig/cli@0.6.11`):

> `launch [options] <rigId> [nodeRef]` — "Launch or relaunch a node in a
> running rig"

What Issue #11 *observes*: invoked against an already-running node, `rig launch`
reports the node as **"already running (not relaunched)"** and changes nothing —
the "or relaunch" in the help text notwithstanding. The running session keeps
enforcing its launch-time policy (a staleness that is, per the program
Constitution §2.2, a *safety property* — sessions must never silently widen
their own permissions — but it cuts both ways when the charter legitimately
changed underneath them).

What does **not** exist today (verified by enumerating `rig --help` command
list — there is no `stop <node>`, `restart <node>`, or per-node `start`; bare
`start` is daemon-only: "Start the daemon, verify kernel, and restore rigs"):

- No `rig stop|restart <node>` verb of any spelling.
- `rig up <rig-name> --existing` explicitly "refuses while any of its seats is
  live" (quoted from `rig up --help`), so the resume path cannot be used for a
  hot single-seat swap either.
- Hence the current dilemma: **whole-fleet bounce vs. one stale seat.**

The CLI-side fix (true relaunch semantics for `rig launch`, or a dedicated
per-node restart verb) is tracked **upstream** in `@openrig/cli` under
Workstream C. **This runbook is the repo-side fallback until then** — procedure,
not tooling — and must be retired or rewritten once upstream ships.

---

## 3. Fallback procedure: refresh ONE stale seat

Notation: `<rig>` rig ID, `<seat>` canonical session name
(`<pod>-<member>@<rig>`), `<node>` logical node ID, `<role>` seat role.

All `rig` verbs below were verified to exist via `--help` run daemon-down on
2026-10-20 (fleet DOWN; `rig status` → "Daemon not running"). Anything requiring
a live daemon for *behavioral* proof is marked
`[UNVERIFIED — confirm on live fleet]` and must NOT be asserted as proven.

### Step 0 — Identify the stale seat (observation only, safe while down or live)

```bash
rig ps --nodes --rig <rig>
# Verified: "Show per-node detail (current rig; -A for all rigs)"
# Per AGENTS.md: outside a managed session, --rig <name> (or -A) is required.
```

Confirm the seat is actually stale (old charter hash / old permission bundle in
its session artifacts) rather than merely busy. Do not proceed on suspicion
alone — a needless refresh is itself a disruption.

### Step 1 — Snapshot the rig and record the ID (pre-flight artifact)

```bash
rig down <rig> --snapshot --json   # NO — see warning below. Use snapshot form:
rig snapshot <rig>
# Verified: `snapshot [options] <rigId>` — "Manage rig snapshots";
# `rig snapshot list <rigId>` — "List snapshots for a rig".
```

> ⚠️ Do **not** reach for `rig down --snapshot` here: `rig down` "stops every
> agent in the rig" (quoted from `rig down --help`) — that is the fleet bounce
> this runbook exists to avoid. Snapshot **without** teardown.

Record the snapshot ID in the change log (Constitution §2.7: snapshot before
every relaunch; the ID is your rollback handle). List to confirm:

```bash
rig snapshot list <rig>
```

`[UNVERIFIED — confirm on live fleet]`: exact JSON shape of the snapshot-create
output and which field carries the restore-usable ID. Capture it verbatim on
first live use and amend this runbook.

### Step 2 — Drain / park the seat's queue items

List what the seat owns before touching it:

```bash
rig queue list --destination <seat> --rig <rig>
# Verified verbs/flags: `queue list` — "List qitems";
# `--destination <session>` — "Filter by destination session".
# (Current-rig derivation comes from OPENRIG_SESSION_NAME; pass scope
# explicitly from the operator shell. Local `queue-transitions` behavior
# beyond flags above is UNVERIFIED live.)
```

For each active qitem owned by the seat, choose one (verified subcommands,
quoted from `rig queue --help`):

- **Reroute** to a live fallback seat:
  `rig queue fallback <qitemId>` — "Reroute a qitem to a fallback destination
  (e.g. unreachable seat)". `[UNVERIFIED — confirm on live fleet]`: flag
  spelling for naming the destination; read `rig queue fallback --help` live
  before use.
- **Park** with a wake (preferred when the work must resume on the refreshed
  seat itself):
  `rig queue block <qitemId>` — "Park a qitem as HELD with a continuation and
  wake." `[UNVERIFIED — confirm on live fleet]`: `--on`/`--wake-*` flag details.
- **Or** use the node-level escape hatch: `rig remove --fallback <live-seat>`
  (next step) reroutes active qitems automatically — but explicit per-item
  triage above is preferred because it leaves a readable record.

Verify the drain before proceeding:

```bash
rig queue list --destination <seat>
# Expect: zero active items (only closed/done with -a). Non-empty = STOP,
# return to triage. Do not remove a seat that still owns live work.
```

### Step 3 — Remove ONLY the stale node

```bash
rig remove <rigId> <nodeRef> [--fallback <live-seat>]
# Verified, quoted from `rig remove --help`:
#   "Remove a node from a running rig"
#   "--fallback <live-seat>  Reroute active qitems to this running seat
#    before removal"
```

Scope-containment facts (from verified help text, not live proof):

- `remove` takes a **single** `<nodeRef>` — it is node-scoped by construction,
  unlike `rig down <rig>` which "stops every agent in the rig" and unlike
  `rig shrink <rigId> <podRef>` which removes "an entire pod". This is why
  `remove` (not `shrink`, not `down`) is the correct verb for the single-seat
  path.
- `[UNVERIFIED — confirm on live fleet]`: that `remove` leaves all other nodes
  running and attached (belief: yes, per single-target signature — but the first
  live use must watch `rig ps --nodes --rig <rig>` throughout and abort on any
  collateral state change).

Alternative worth evaluating live ( NOT the default path):
`rig handover <seat>` — "Hand a seat to a successor: create -> deliver context
-> verify continuity -> rebind" with `--source fresh|rebuild|fork:<id>` and
`--dry-run` (all verified in `rig handover --help`). Handover may subsume
remove+launch with continuity guarantees, but its seat-continuity semantics
against a *policy* change are unproven. `[UNVERIFIED — confirm on live fleet]`:
run `rig handover <seat> --dry-run` first on a live fleet and compare before
blessing it as the preferred path.

### Step 4 — Re-seed THAT seat's directory from post-merge charters

The refreshed node must be born from current generated leaves — never copy the
old seat dir forward. Re-seed the single member fragment (verified from
`scripts/seed-rig.py --help`):

```bash
python3 scripts/seed-rig.py <member-fragment.yaml> --rig <rig-id> --pod <pod-id> [--allow-missing-secrets]
# Verified usage line: "seed-rig.py <rig.yaml | pod-fragment.yaml | member-fragment.yaml>
#   [--rig <rig-id>] [--pod <pod-id>] [--dry-run] [--allow-missing-secrets]"
#   "member fragment   needs --rig and --pod (the rig add target)"
```

Seeding is strict by default (missing secrets fail closed — that is the safe
direction; do not override with `--allow-missing-secrets` unless the seat
genuinely needs no secret-backed servers, and record the choice). Confirm the
seeded permission config matches the post-merge charter before launching
anything from it.

### Step 5 — Launch the single node back

```bash
rig launch <rigId> <nodeRef> --plan     # preview first (verified flag)
rig launch <rigId> <nodeRef>
# Verified, quoted from `rig launch --help`:
#   "Launch or relaunch a node in a running rig"
#   "--seats <ids>   Comma-separated logical IDs for subset launch"
#   "--plan          Show subset selection and non-target effects without mutation"
#   "--snapshot-id <id>  Use this exact restore-usable snapshot"
```

- Always run `--plan` first and read the non-target effects: any mention of
  seats other than your target = STOP, escalate to TPM, fall back to §5
  (bounce) deliberation.
- `[UNVERIFIED — confirm on live fleet]`: whether `launch` against the
  just-removed node ID re-launches cleanly with the re-seeded config, or
  whether it reports "already running (not relaunched)" per Issue #11 even
  after `remove`. **This is the crux the runbook cannot prove daemon-down.**
  If `launch` still refuses: the single-seat path is blocked for that daemon
  version — restore per §6 or bounce per §5, and file the evidence upstream
  (Workstream C).
- `--snapshot-id` pins a restore source if the launch needs to start from the
  Step-1 snapshot rather than fresh state; prefer fresh-from-reseed (stale
  state is what you are escaping), keeping the snapshot purely as rollback.

### Step 6 — Confirm `run` + policy probe

A refreshed seat is guilty until proven innocent. Both checks are repo-native
(verified in `Makefile` / `scripts/`):

```bash
rig ps --nodes --rig <rig>            # seat present, lifecycle sane
make audit-sessions [WORKSPACE=/path/to/seat-workspace]
# Makefile: "Detect misattributed denials + false delivery claims"
make gate ROLE=<role>                 # or: bash ./scripts/gate-role.sh <role>
# Makefile: "Gate-test one role against mock OpenAI + pi-permission-system"
```

- The audit must show the seat enforcing the **new** policy (no stale-policy
  denials attributable to it); the gate must pass for its role.
- `[UNVERIFIED — confirm on live fleet]`: exact "new policy active" signal
  strings in `audit_sessions.py` output for a post-refresh seat — record them
  here on first live use.
- Only after both checks pass: unpark the Step-2 HELD items (owner resumes) or
  leave rerouted items where they landed — decision recorded in the change log.

---

## 4. Pre-flight checklist (all boxes checked before Step 3)

- [ ] **Snapshot taken + ID recorded** in the change log (`rig snapshot <rig>`,
  confirmed via `rig snapshot list <rig>`).
- [ ] **Queue items for the seat parked or rerouted**: `rig queue list
  --destination <seat>` shows zero active items.
- [ ] **No in-flight slice depending on the seat**: no Triad, QA, or red-team
  step lists this seat as executor/owner; no HELD wake points at it as
  blocker. Check with the slice TPM, not just the queue.
- [ ] **TPM sign-off recorded** (who approved the refresh, which charter change
  motivated it, post-merge commit hash).
- [ ] **Post-merge charters verified**: the change is merged to `main` and the
  re-seed source (Step 4) is generated from that merge — never from a branch.
- [ ] **`--plan` preview read** (Step 5) with no non-target effects.

---

## 5. ROLLBACK — restoring the pre-refresh state

1. **Restore the snapshot ID** recorded in Step 1 (Constitution §2.7: a bad
   change is one restore away from undo):
   `rig restore <snapshotId> --rig <rigId>`
   (usage line verified in `rig restore --help`: "Direct restore:
   `rig restore <snapshotId> --rig <rigId>`").
   `[UNVERIFIED — confirm on live fleet]`: restore granularity (whole-rig vs
   node-selective) — if restore is whole-rig, it *is* a bounce; say so in the
   change log and prefer §5 deliberation first.
2. **Re-seed from pre-change charters** if the refresh seeded bad config:
   check out the pre-merge commit's generated leaves into a scratch dir (do NOT
   hand-edit live leaves — the One Rule), re-run the Step-4 member-fragment
   seed from those, then re-launch per Step 5.
3. **Detecting a half-refreshed seat** (old code, new config, or vice versa):
   run `make audit-sessions` — a half-refreshed seat shows as policy
   disagreement (denials the new charter should allow, or allows the new
   charter should deny). Any disagreement = seat is NOT healthy; either
   complete the refresh (Steps 4–6 again) or roll back (steps 1–2 above).
   `[UNVERIFIED — confirm on live fleet]`: canonical half-refresh signature in
   audit output — append it here after first observation.
4. **Record the outcome**: snapshot ID used, restore result, audit output
   excerpt, decision (retry refresh vs. accept rollback vs. bounce fleet).

---

## 6. When-to-bounce: abandon the single-seat path

Do a full fleet bounce (`rig down <rig> [--snapshot]` then re-seed all and
`rig up`, per the AGENTS.md seed-then-launch row) instead of this runbook when
**any** of the following holds:

1. **More than ~2 stale seats** (rule of thumb: N>2, or >10% of the rig,
   whichever is smaller) — per-seat surgery stops being contained and starts
   being a slow-motion bounce with extra risk.
2. **The charter change touches shared skills, MCP servers, or permission
   profiles** (`fleet/mcp-servers.yaml`, guard profiles, sidecar matrix) —
   scope cannot be contained to one seat by construction; every seat's runtime
   inherits the shared surface.
3. **`rig launch --plan` shows any non-target effect**, or Step-5 `launch`
   reports "already running (not relaunched)" after `remove` — the fallback
   path is blocked on this daemon version; stop forcing it.
4. **Any doubt about scope containment** — a `remove` that disturbs neighbors,
   a drain that cannot reach zero active items, a snapshot that fails. The
   runbook's premise is surgical containment; without containment it is just
   risk without benefit. Bounce, re-seed all, verify 22/0, relaunch.
5. **Constitution §2.6 human gate**: fleet relaunch is human-gated regardless —
   a bounce needs explicit human approval; a single-seat refresh needs TPM
   sign-off (§4). Neither path runs on seat authority alone.

---

## Appendix — verification ledger (daemon-down, 2026-10-20)

| Verb / command | Source | Standing |
|---|---|---|
| `rig launch <rigId> [nodeRef]` + `--seats/--plan/--snapshot-id/--hold-reason` | `rig launch --help` output, run live | Help text VERIFIED; relaunch-on-running behavior UNVERIFIED (daemon down; Issue #11 reports refusal) |
| `rig remove <rigId> <nodeRef>` + `--fallback` | `rig remove --help` output, run live | Help text VERIFIED; neighbor-safety UNVERIFIED |
| `rig snapshot <rigId>` / `snapshot list` | `rig snapshot --help`, `rig snapshot list --help` | VERIFIED (existence + syntax) |
| `rig restore <snapshotId> --rig <rigId>` | `rig restore --help` usage line | VERIFIED (syntax); granularity UNVERIFIED |
| `rig queue list --destination` / `create/claim/update/block/fallback/handoff` | `rig queue --help`, `rig queue list --help` | VERIFIED (existence); drain semantics UNVERIFIED |
| `rig ps --nodes --rig` | `rig ps --help` output, run live | VERIFIED |
| `rig up <source> --existing` refuses while seats live | `rig up --help` output, run live | VERIFIED (refusal text) |
| `rig down <rig> [--snapshot/--force/--delete]` stops every agent | `rig down --help` output, run live | VERIFIED |
| `rig handover <seat> [--source/--dry-run]` | `rig handover --help` output, run live | VERIFIED (existence); policy-change fitness UNVERIFIED |
| No `stop/restart <node>` verb | full `rig --help` command enumeration | VERIFIED (absent) |
| `seed-rig.py <member-fragment> --rig --pod` | `python3 scripts/seed-rig.py --help` | VERIFIED |
| `make audit-sessions [WORKSPACE=...]` / `make gate ROLE=` | `Makefile` targets, `scripts/gate-role.sh` present | VERIFIED (existence) |
| End-to-end single-seat refresh on a live fleet | — | **DEFERRED: fleet DOWN; no live execution in this slice** |

*Deferred live-proof note: per the slice brief, no fleet was launched and no
seat was refreshed. The first live use of §§3–5 must be treated as the
procedure's shakedown: an operator runs it against a live daemon, confirms or
corrects every `[UNVERIFIED]` mark in place, and records the evidence (snapshot
IDs, `--plan` output, audit excerpts) in the change log.*
