# ST-4 Proposal Package — system-architect — 2026-10-21

Slice qitem: qitem-20261021180558-1f2fb3fd280b160b
Source slice: qitem-20261021155313-fe1742ceba05b628
Operator rule: qitem-20261021180541-57b61b487a7d12a8, held by TPM
Spec: docs/sprints/SELF-TAKEOVER-SPRINT.md section ST-4
Seat: exec-system-architect@heretek-omni-fleet
HEAD at authoring: 96f3a96, read-only git log plus git show --stat this turn

Sequencing verified at HEAD: ST-1 landed 5c35a73, ST-2 landed 5c5b46e, ST-3
landed 96f3a96, all visible in this checkout. ST-3 touched
fleet/mcp-servers.yaml with a 2-line change and landed the context7 bump
4.4.2 to 4.4.4 exactly per the ST-3 proposal. Nothing is queued behind ST-4.

Verdict: CANNOT-STATE every hunk exactly. Precise handback below per the
operator rule: no approximate diffs authored, generator structure never
reconstructed from memory.

## Hunks — generator pins-dict surgery plus three new pinned clones

Target path: scripts/generate-rigs.py. Expected mechanism change, on ledger
premise only: add three vendor sources to the generator pins dict — prisma
skills, supabase skills, mattpocock skills — plus one new pinned clone each,
following the existing clone convention.

Exact hunks with 3-plus context lines, old and new quoted verbatim:
CANNOT STATE. Every line of every hunk is unstated, for this reason: the
source file scripts/generate-rigs.py is not readable in this seat, so the
pins-dict location, key shape, clone-stanza shape, indentation, and context
lines are all unknown and will not be guessed. Live denial this turn:

  [pi-permission-system] Denied by policy: 'path_read' for tool 'read' for path 'scripts/generate-rigs.py' (rule 'scripts/*').

This covers the pins-dict surgery hunk and each of the three pinned-clone
hunks individually: all four are unstated for the same reason.

Evidence basis, per line:
- Mechanism basis, read directly this turn: docs/sprints/TOOLING-B1-RIG5.md
  records that prisma skills and supabase skills as new vendor sources would
  require generator pins-dict surgery plus new pinned clones, deferred as out
  of minimal-batch scope. The same ledger records the standing convention
  that vendor SHAs must match pins, with the current SHAs enumerated.
- Mechanism basis, read directly this turn: docs/sprints/TOOLING-B4-RIG1.md
  row 6 records mattpocock/skills as not vendored, needing generator
  pins-dict surgery plus a new pinned clone, deferred on the B1
  prisma/supabase precedent. Row 5 records the same mechanism for a git-named
  skill source, resolved as no-action on redundancy grounds.
- Missing-input basis, stated plainly: the three new vendor SHAs are UNKNOWN
  from this seat. No SHA, no license confirmation, and no freshness check is
  offered here. The implementing seat or operator must resolve each vendor
  source to a pinned SHA, confirm licenses, and record them before editing.
- Post-ST-3 tree basis, verified via read-only git this turn: HEAD is 96f3a96
  with ST-1, ST-2, ST-3 all landed; none of the three landed slices touched
  scripts/generate-rigs.py, so the generator stands at its pre-program state
  plus provenance relags. Generator content itself UNVERIFIED at source.

## Rollback statement — mandatory, before any operator action

If the ST-4 generator change is applied and must be undone, in this order:

1. Revert scripts/generate-rigs.py to its post-ST-3 state, commit 96f3a96,
   with no other file changed in the revert.
2. Remove any new pinned vendor-clone directories the change introduced, so
   no new vendor source remains on disk.
3. Re-run the generator on a clean tree, then run verify-rigs.sh
   --check-only and require 22 checks passed, 0 failed.
4. Confirm vendor SHAs still match pins with no new vendor sources present,
   and confirm no seat lost rendered allows in the regen diff.
5. If any step fails, stop: do not hand-edit generated leaves to force the
   tree green. Re-run generate-rigs.py from the reverted generator instead;
   generated leaves are never patched by hand.

Rollback is stated here BEFORE any operator action, per the operator extra
requirement. It has NOT been exercised: no edits exist, so there is nothing
to revert yet.

## What could NOT be checked from this seat

- Regen output: no generator run; nothing to render with zero edits.
  Fleet-wide rendered impact across all 51 seats plus 8 bundles UNASSESSED.
- Verify gate: verify-rigs.sh --check-only NOT run; nothing to verify with
  zero edits. The 22/0 gate is unattempted, not passed.
- Vendor SHAs, licenses, and freshness for prisma, supabase, and mattpocock
  sources: UNKNOWN, as stated above. The B1 ledger convention requires SHAs
  to match pins; that check is unperformed here.
- Exact source text: all hunks unstated for the reason above. No approximate
  diff is offered; approximate diffs will be rejected per rule.

## Blast-radius note

This is the highest-blast-radius slice in the program by the operator's own
statement: a generator change affects all 51 seats plus 8 bundles. The
one-slice-at-a-time rule on fleet files plus generator files must hold; no
concurrent ST-4 work may overlap the operator's application of this batch.
The implementing seat must hold scripts write scope, which this seat does not
hold and does not request.

## Handoff

Proposal path on disk: docs/architecture/ST-4-PROPOSAL-2026-10-21.md, the
single proposal file for ST-4P. Returned to delivery-tpm-scrum-lead for
routing to the operator or a scripts-scoped implementing seat. No commits,
pushes, merges, or generated-leaf edits performed. Root AGENTS.md untouched.
No secrets in any output, file, or command line.
