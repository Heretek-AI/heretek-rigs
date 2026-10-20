# Standing Pre-Authorization Envelopes

**Status:** Process-only proposal (Slice A2 of the fleet self-improvement program).
No charter changes, no permission changes, no catalog changes, no generator changes.
Live-fleet exercise deferred (fleet down at time of writing — see §6).

Related docs: `docs/USER_GUIDE.md` (operator manual), the fleet
self-improvement plan (§3 Workstream A, row A2; Constitution §2; execution
model §4). This file is self-contained and links — never duplicates — those
sources.

---

## 1. Purpose: the stale-authorization wound (issue #15)

The verify-then-authorize loop assumes a frozen tree, but seats keep
authoring during the operator round-trip. The S02 evidence made this
concrete: authorization `qitem-20261020063613-d67f57c5` scoped the approval
as "prior ae55c83 + #include hash.h one-liner, nothing else touched", while
the live `git diff --stat` at execution time showed **11 files changed,
+167/−105** — far beyond the authorized one-liner. The operator correctly
held the commit and escalated instead of executing a stale authorization.

The ask from issue #15 is therefore not "authorize faster" but "authorize
differently": **standing pre-authorization envelopes for defined slice
classes** — e.g. "commit whatever the owning seats staged under S02 paths
once the TPM verifies the close-out evidence" — so the authorization names
a *verifiable condition* (paths + owners + TPM gate) rather than a
*point-in-time diff* that rots before the operator acts.

This document defines the envelope template (§2), shows retrospectively how
one would have covered the S02 case (§3), gives the TPM execution checklist
(§4), and states the hard scope limits (§5). Envelopes authorize
COMMIT/FILE actions only. They change nothing about what any seat is
allowed to do.

---

## 2. Standing pre-authorization envelope TEMPLATE

Copy this block verbatim for each envelope. Every field is mandatory unless
marked OPTIONAL. An envelope missing a REQUIRED field is void on its face —
the operator must refuse it, not fill in the blanks.

```text
PRE-AUTH ENVELOPE <ENVELOPE-ID> — REQUIRED
Slice class:        <short class name, e.g. "engine-skeleton-commit"> — REQUIRED
Issued by:          <human operator name/handle> — REQUIRED
Issued at (UTC):    <YYYY-MM-DD HH:MMZ> — REQUIRED
Expiry:             <EITHER "single-slice: void after first execution attempt
                     (success or failure)" OR an explicit UTC deadline
                     "expires YYYY-MM-DD HH:MMZ"> — REQUIRED. Envelopes are
                     NEVER open-ended. If both are given, the earlier one
                     governs.

Path scope
(exact repo paths): <enumerated list of exact repo-relative paths and/or
                     directory prefixes, e.g. "src/engine/", "tests/engine/",
                     "CMakeLists.txt", "build.sh"> — REQUIRED. Anything not
                     listed is OUT of scope, including dotfiles, CI config,
                     fleet catalog, and permission files.

Owning seats:       <enumerated seat roles, e.g. "engine-systems-eng,
                     cpp-lowlevel-eng"> — REQUIRED. Only diffs authored
                     (staged) by these seats qualify. Operator-authored or
                     third-seat content is OUT of scope.

Permitted operator
actions:            <subset of EXACTLY these verbs — REQUIRED, enumerate,
                     nothing else is permitted under any envelope>:
                       - COMMIT  (create a local commit of in-scope paths)
                       - FILE-QUEUE-ITEM <queue-name>  (file a signed queue
                           item recording the decision/execution)
                     PUSH is permitted ONLY if listed explicitly as
                     "PUSH <branch-ref>" with the exact branch named.
                     Any action not named here (rebase, merge, relaunch,
                     seed, permission change, fleet command) is FORBIDDEN
                     under this envelope.

TPM verification
gate:               BEFORE the operator executes, the TPM (or delegated
                     verifier named here) MUST verify and record — REQUIRED:
                       1. WHAT:  <artifacts to inspect, e.g. "seat close-out
                                 doc + CTest log + tree SHA">
                       2. BY WHOM: <verifier role/name — must not be an
                                 owning seat for its own work>
                       3. ARTIFACTS: <where the verification record lives —
                                 queue item id / doc path / log path>
                     No verification record → no execution. Verification
                     older than the last tree mutation is STALE (see §4
                     fail-closed rule).

Revocation:         May be revoked at any time by the ISSUER or by ANY HUMAN
                    OPERATOR senior to the executor — REQUIRED field naming
                    the revocation channel (e.g. "signed queue item to the
                    operator channel, or direct order in session").
                    Revocation takes IMMEDIATE effect, including
                    mid-checklist: if revoked after verification but before
                    execution, the envelope is VOID and execution is
                    FORBIDDEN. The operator checks for revocation
                    immediately before executing.

Audit trail:        Record all three links — REQUIRED:
                       1. This envelope (where filed: queue item id or doc
                          ref + SHA).
                       2. The TPM verification record (artifact links/ids).
                       3. The execution record (commit SHA or queue item id,
                          with timestamp and executor).
                     Missing any link = incomplete execution; report it as
                     such, do not backfill.

OPTIONAL notes:     <context the issuer wants the operator to have; never
                     overrides any REQUIRED field>
```

**Why expiry and revocation are REQUIRED (template is unusable without
them):** an envelope without expiry is a standing permission in disguise,
and a permission without revocation is irrevocable by construction. Both
violate the program Constitution (seats never widen their own permissions;
human gates never automate away). Any envelope lacking either field must be
treated as if it did not exist.

---

## 3. Worked example (retrospective): the S02 case

Filled as the envelope *would have read* had it existed before the S02
round-trip. This is a reconstruction for illustration — it authorized
nothing retroactively.

```text
PRE-AUTH ENVELOPE S02-ENGINE-001
Slice class:        engine-skeleton-commit
Issued by:          <human operator>
Issued at (UTC):    <issue date>  (illustrative)
Expiry:             single-slice: void after first execution attempt
                    (success or failure).

Path scope
(exact repo paths): src/engine/
                    tests/engine/
                    CMakeLists.txt
                    build.sh
                    (Illustrative of the S02 class. Any file outside these
                    four entries — docs, CI, fleet catalog, unrelated
                    src/ paths — would have been OUT of scope.)

Owning seats:       engine-systems-eng, cpp-lowlevel-eng
                    (Only staged content authored by these two seats
                    qualifies.)

Permitted operator
actions:            COMMIT (in-scope paths only).
                    FILE-QUEUE-ITEM ops-log (execution record).
                    PUSH is NOT granted — a further human merge gate applies.

TPM verification
gate:               1. WHAT: seat close-out doc (scope claimed vs. paths
                                 touched) + CTest log (green) + tree SHA
                                 at verification time.
                    2. BY WHOM: TPM (not an owning seat).
                    3. ARTIFACTS: verification queue item + attached log
                                 paths, filed BEFORE execution.

Revocation:         Issuer or any senior human operator, via signed queue
                    item to the operator channel or direct session order.
                    Immediate effect; mid-checklist revocation voids the
                    envelope.

Audit trail:        (1) envelope queue item, (2) TPM verification record,
                    (3) commit SHA + executor + timestamp in the ops log.
```

**How this would have prevented the stale-authorization incident.**
The actual authorization (`qitem-20261020063613-d67f57c5`) described a
point-in-time tree: "prior ae55c83 + #include hash.h one-liner, nothing
else touched." When the live tree showed 11 files / +167−105, the premise
was false but the authorization had no vocabulary for that — the operator
had to improvise the hold. Under envelope S02-ENGINE-001, the TPM
checklist (§4, steps 1–4) would have **failed closed at step 1**: the
recorded diff stat would not match the authorized premise, the paths would
be checked against scope rather than assumed, and the rule "stale premise
VOIDS the envelope" would have made the hold the *prescribed* outcome, not
a judgment call. The round-trip would still have cost a re-verification —
but the decision procedure would have been written down in advance instead
of discovered under pressure.

**What it would NOT have prevented (honest limits).**

1. **The drift itself.** Seats authoring 11 files while an authorization
   names one is a coordination failure (concurrency without partitioning —
   the #16/#17 lesson). The envelope catches the mismatch at execution
   time; it does not stop seats from diverging during the round-trip.
2. **Out-of-scope content inside the diff.** Had any of the 11 files fallen
   outside `src/engine/`, `tests/engine/`, `CMakeLists.txt`, `build.sh`,
   the envelope would void *that execution*, but disposition of the
   out-of-scope work (split commit? new envelope? rejection?) still needs a
   fresh human decision.
3. **Non-authorship problems.** A green TPM gate on broken, unreviewed, or
   malicious content is still broken content — the envelope scopes
   *authority to commit*, never *correctness*. `make verify`, QA red-proof,
   and human merge still apply in full (§5).
4. **Urgency pressure.** Nothing in the template stops a tired operator
   from "just committing." The mitigation is procedural (checklist order,
   revocation check, audit links), not cryptographic — it assumes an
   operator willing to follow it.

---

## 4. TPM checklist (execute in order, stop at first failure)

1. **Verify tree state.** Run `git status --short` and `git diff --stat`
   (plus `git diff --cached --stat` if staged content is claimed). Record
   the full stat output verbatim in the verification record — not a
   paraphrase. Note the tree SHA (`git rev-parse HEAD`) and timestamp.
2. **Record the diff stat.** Attach the stat from step 1 to the
   verification record with artifact links. This is the premise the rest
   of the checklist stands on; if the tree mutates after this point,
   return to step 1.
3. **Confirm paths within scope.** Every touched path must fall under the
   envelope's Path scope list. One out-of-scope file → the envelope does
   not cover this execution. Stop; escalate for a new human decision.
4. **Confirm owning-seat authorship.** Attribute the staged/claimed diff
   to the envelope's Owning seats (seat close-out docs, session transcripts,
   or equivalent evidence). Unattributable content, operator-authored
   content, or third-seat content → out of scope. Stop; escalate.
5. **Confirm TPM gate artifacts.** The envelope's WHAT (e.g. close-out doc
   + CTest log + SHA) must exist, be linked, and be current (predating no
   tree mutation since step 1). Stale or missing artifacts → stop.
6. **Check expiry and revocation.** Confirm the envelope has not expired
   (single-slice already attempted? UTC deadline passed?) and query the
   revocation channel for any revocation. Expired or revoked → VOID. Stop.
7. **Execute within expiry.** Perform ONLY the enumerated Permitted
   operator actions, ONLY on in-scope paths. Recheck `git status --short`
   immediately before the commit: if the tree changed since step 1, the
   premise is stale — return to step 1, never proceed.
8. **Record execution with links.** File the execution record (commit SHA
   or queue item id, timestamp, executor) alongside the envelope ref and
   the verification record ref (§2 Audit trail). Three links or it did not
   happen; report incomplete executions as incomplete.

**FAIL-CLOSED STALE-PREMISE RULE: any verification premise that goes stale
before execution VOIDS the envelope for that execution. A premise goes
stale when the tree mutates after the diff stat was recorded, when a gate
artifact is superseded, when expiry passes, or when revocation issues. On
a stale premise the operator must RE-VERIFY from step 1 under a live
envelope — never proceed on a stale premise, never "adjust" the premise to
fit the tree, never execute first and record later.**

---

## 5. Scope limitation (what envelopes can never do)

- **Envelopes authorize COMMIT/FILE actions only** (and PUSH only when an
  exact branch is named in the envelope). They are execution-scoped
  commit authority, not policy.
- **They never grant seats new permissions.** No envelope widens what any
  seat may do, access, or invoke. Permission changes follow the
  Constitution path only: PR → human merge → re-seed → relaunch.
- **They never waive `make verify`.** The 22-check floor applies before
  and after every change, envelope or not.
- **They never substitute for human merge.** Nothing under an envelope
  lands on `main` without the human merge gate (one branch per change,
  PR before merge, never push straight to `main`).
- **They never transfer across slices.** An envelope names one slice
  class; a new slice needs a new envelope. Expiry is per-envelope and
  non-renewable by the operator — only the issuer may issue a fresh one.

When in doubt, the operator holds and escalates — exactly as happened with
`qitem-20261020063613-d67f57c5`. The envelope system exists to make that
hold decision faster, clearer, and auditable — not to eliminate it.

---

## 6. Deferred live proof

No live-fleet exercise was performed for this slice: the fleet daemon was
stopped and the fleet stays down per program constraints (process-only
slice; no seats launched, no branches beyond this worktree, no commits).
Live proof — exercising an envelope against a relaunched fleet with
recorded evidence per the S01b/S02 evidence standard — is **deferred** to
a future slice with an authorized live window, and is explicitly NOT
claimed here.
