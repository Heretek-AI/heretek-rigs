# ST-1 Proposal Package — system-architect — 2026-10-21

Slice qitem: qitem-20261021160248-4365c8029efc8222
Source slice: qitem-20261021155313-fe1742ceba05b628
Operator rule: qitem-20261021160234-e304e6d8e1094b9a, held by TPM
Spec: docs/sprints/SELF-TAKEOVER-SPRINT.md section ST-1
Seat: exec-system-architect@heretek-omni-fleet
HEAD at authoring: 5af469f, read-only git log this turn

Verdict: CANNOT-STATE both hunks exactly. Precise handback below per the
operator rule: no approximate diffs authored, catalog structure never
reconstructed from memory.

## Hunk A — grafana binding for load-stress-tester in fleet/fleet.yaml

Target path: fleet/fleet.yaml, load-stress-tester seat entry.

Exact hunk with 3-plus context lines, old and new quoted verbatim:
CANNOT STATE. Every line of this hunk is unstated, for this reason: the
source file fleet/fleet.yaml is not readable in this seat, so the seat entry
key, the bindings list shape, indentation, and surrounding context lines are
unknown and will not be guessed. Live denial this turn:

  [pi-permission-system] Denied by policy: 'path_read' for tool 'read' for path 'fleet/fleet.yaml' (rule 'fleet/*').

Evidence basis, per line:
- Intended new line, UNVERIFIED at source: a grafana binding on the
  load-stress-tester seat, expected one-line shape per B2 ledger
  docs/sprints/TOOLING-B2-RIG6.md line 21, which records Row 42
  load-stress-tester Grafana as DEFERRED with the note that binding
  post-B1-merge is a one-line follow-up. Ledger section read directly
  this turn via grep.
- Catalog pin basis, verified via generated mirrors this turn: sibling seats
  render grafana/mcp-grafana 2.0.2, seen at
  rigs/heretek-omni-fleet/agents/sre-incident-eng/runtime/mcp.json line 29,
  rigs/heretek-omni-fleet/agents/observability-eng/runtime/mcp.json line 35,
  and rigs/heretek-omni-fleet/agents/analytics-metrics-eng/runtime/mcp.json
  line 38. Mirror presence only; catalog source UNVERIFIED.
- Need basis, verified via generated mirror this turn: read
  rigs/heretek-omni-fleet/agents/load-stress-tester/runtime/mcp.json shows
  only k6 plus codebase-memory, no grafana. Binding still needed at mirror
  level; source edit still required.
- Merged-commit basis: UNVERIFIED as a specific SHA. HEAD is 5af469f. B1
  merged state appears present via the mirrors above; the B1 merge commit
  itself was not identified from this seat.
- sabotage-qa-tester grafana binding decision: NOT RECORDED here. No hunk
  was requested for it under ST-1P, and the fleet file is unreadable, so no
  charter-based decision is stated. Recommending the implementing owner
  checks the sabotage charter before deciding, per ST-1.

## Hunk B — sabotage-qa-tester pi_packages pin swap

Target path: fleet/fleet.yaml, sabotage-qa-tester seat entry, pi_packages list.
Expected old values pi-lsp-extension@1.4.0 and pi-ast-grep@0.1.0; expected new
values @narumitw/pi-lsp@0.49.10 and @nicknisi/pi-ast-grep@0.3.1.

Exact hunk with 3-plus context lines, old and new quoted verbatim:
CANNOT STATE. Every line of this hunk is unstated, for this reason: the
source file is the same unreadable fleet/fleet.yaml, so the pi_packages key,
list shape, indentation, and context lines are unknown and will not be
guessed. Same live denial as Hunk A, plus the companion source denial:

  [pi-permission-system] Denied by policy: 'path_read' for tool 'read' for path 'fleet/mcp-servers.yaml' (rule 'fleet/*').

Evidence basis, per line:
- Pin values basis, verified via ledger this turn: docs/sprints/TOOLING-B1-RIG5.md
  line 26 records dependency-patcher pi_packages bump row 30 with old
  pi-lsp-extension@1.4.0 going to @narumitw/pi-lsp@0.49.10 and old
  pi-ast-grep@0.1.0 going to @nicknisi/pi-ast-grep@0.3.1, both pins verified
  live on npm 2026-10-20, both MIT. Line 27 records the required companion
  fix in scripts/render-seat.py: the has_ast_lsp allowlist keyed on legacy
  bare names, extended with the two scoped prefixes so rendered allows stay
  intact. Ledger sections read directly this turn via grep.
- Need basis, verified via generated mirror this turn: grep over
  rigs/heretek-omni-fleet/agents/sabotage-qa-tester/runtime/policy-enforcement.json
  shows line 8 pi-lsp-extension@1.4.0 and line 9 pi-ast-grep@0.1.0. Stale pins
  still rendered; bump still needed at mirror level; source edit required.
- Companion-fix basis: UNVERIFIED at source. scripts/render-seat.py is not
  readable in this seat; live denial this turn:

  [pi-permission-system] Denied by policy: 'path_read' for tool 'read' for path 'scripts/render-seat.py' (rule 'scripts/*').

  The load-tester handback qitem-20261021155527-46779bc3 claims the scoped
  names confirmed via grep at lines 314-317; that claim is accepted as premise
  only, not verified from this seat.
- Merged-commit basis: UNVERIFIED as a specific SHA, same as Hunk A.

## What could NOT be checked from this seat

- Render output: no regen run; python regen is outside seat scope and no
  edits exist to render. Stated plainly: post-edit rendered allows for
  sabotage-qa-tester are UNCONFIRMED.
- Verify gate: verify-rigs.sh --check-only NOT run; nothing to verify with
  zero edits. The 22/0 gate is unattempted, not passed.
- Cross-seat impact: UNASSESSED. ST-2 through ST-4 sequencing stays in force;
  same-file contention rules still apply to the implementing owner.
- Exact source text: both hunks unstated for the reasons above. No
  approximate diff is offered; approximate diffs will be rejected per rule.

## Basis claims accepted as premise only

- Load-tester handback qitem-20261021155527-46779bc3 body, read in full this
  turn: B1 merged-state appearance via mirrors, runtime mcp.json contents,
  stale-pin contents, and its own verbatim fleet denials. Its mirror claims
  were re-verified above where readable; its scripts claim was not.
- B1 and B2 ledger sections cited above, read directly this turn.
- No catalog structure was reconstructed from memory at any point.

## Handoff

Proposal path on disk: docs/architecture/ST-1-PROPOSAL-2026-10-21.md, the
single proposal file for ST-1P. Returned to delivery-tpm-scrum-lead for
routing to a fleet-scoped implementing seat or to the operator. No commits,
pushes, merges, or generated-leaf edits performed. Root AGENTS.md untouched.
No secrets in any output, file, or command line.
