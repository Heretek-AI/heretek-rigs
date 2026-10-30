# fresh-slices Specification

## Purpose
Bounded joint live exercise proving the #16 parallel-slice execution model and
collecting #17 utilization telemetry in one controlled run, plus the #18
costed provisioning report. Each requirement is a runbook obligation with
binary evidence (rc=0 artifact or named follow-up). Stage A authors the
package and performs read-only recon; Stage B executes under the approval
recorded in `proposal.md`.

## Requirements

### Requirement: REQ-F0 — read-only safe-check and recon first

Stage A MUST prove secret hygiene and host state WITHOUT live execution:
`stat` on `~/.config/heretek-rigs/secrets/github.pat` and `opencode-go.key`
MUST show `600` owner-only (dir `700`); one `render-seat.py --dry-run` MUST
render `!cat` references only (rc=0); `rig ps --nodes -A` MUST be captured as
the pre-exercise health baseline. No seat launch, no queue write, no install
in Stage A. Any violation MUST stop the run.

#### Scenario: safe-check green

- When the safe-check runs, both files stat `600`, the dir stats `700`, the
  dry-run exits 0 with `!cat` references only, no secret value appears in any
  output or file, and the `rig ps` baseline is filed under
  `docs/evidence/fresh-slices-<date>/`.

### Requirement: REQ-F1 — #16 joint exercise: per-slice proofs plus integration join

Stage B MUST run 3 slices concurrently (1-real + 2-probe; 3-probe fallback per
`proposal.md`) as synthetic queue rows only (`FRESH-SLICES-*`, never real
tracker rows), abort on the first RED, and close with per-slice proof
artifacts PLUS one integration commit joining all three. No slice is cited
green until the join. The base SHA MUST be pinned and recorded per slice; a
failed slice pins the base — the others keep working on the pinned base, no
mid-exercise rebase. At most 6 seat launches (3 workers + 3 fresh-relaunch
spares).

#### Scenario: join or honest abort

- When the exercise finishes, either every slice has a proof artifact AND the
  integration commit exists (all green only at the join), or the runbook shows
  the abort point, the failing slice, and the pinned base SHA — with pre/post
  `rig ps` snapshots and zero residue (no live seats left running, no
  synthetic rows left open).

#### Scenario: fallback composition recorded

- When no slice is certified ready at Stage-B kickoff, the runbook records
  the 3-probe composition and proceeds; the real-slice designation line stays
  TBD only until kickoff, then names the TPM-designated slice and its
  standalone green compile evidence.

### Requirement: REQ-F2 — #17 metrics: name what degrades first

Stage B MUST record, across the full 3-slice lifecycle: queue-claim latency,
stuck-sweep volume, periodic snapshot cost, and daemon responsiveness; MUST
sample `rig ps` ACTIVE counts + queue depth to distinguish correctly-idle
(blocked on the join) from spuriously-idle (eligible work unclaimed); and
MUST consume the report-only fields from prior waves as inputs —
`attribute_idle_latency` park-to-wake (`scripts/reconcile_model.py:665`) and
`attribute_premise_age` premise age (`scripts/reconcile_model.py:902`) —
read-only, never writing tracker or queue state. The report MUST name the
first-degrading metric.

#### Scenario: metrics with a named bottleneck

- When the exercise closes, the evidence file states per-metric observations
  (claim latency, stuck-sweep volume, snapshot cost, daemon responsiveness,
  ACTIVE/queue-depth samples with idle classified) and names exactly one
  first-degrading metric, or records which metric could not be observed and
  why.

### Requirement: REQ-F3 — #18 report: costed (a)/(b) plus (c) decision

Wave 3 MUST deliver a provisioning report (no provisioning, no spend)
containing: exact steps, pins, and spend for option (a) display/GPU-capable
runner AND option (b) cloud GPU reference machine; the explicit option-(c)
decision (sequence non-visual slices first); and the frame proof
(`vulkaninfo` SDK 1.3.296 + headers, `vkcube` frame, `s02-window.png`)
tracked as Sprint-blocking.

#### Scenario: report complete, nothing provisioned

- When Wave 3 closes, the report exists with costed (a) and (b), the (c)
  decision, and Sprint-blocking frame-proof tracking — and the host shows
  zero provisioning side effects (no installs, no new hosts, no spend).
