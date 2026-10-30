# Proposal: 2026-10-29-fresh-slices — bounded joint live exercise (#16 + #17) + costed provisioning report (#18)

## Goal

Run ONE bounded joint live exercise (Stage B, NOT this stage) in which 3 slices
execute concurrently against the live fleet, proving the #16 parallel-slice
execution model and collecting the #17 utilization/throughput telemetry in a
single controlled run; and deliver a COSTED (a)/(b) provisioning report for #18
with an explicit option-(c) decision and the frame proof tracked as
Sprint-blocking. Refs #16, Refs #17, Refs #18 — never Closes (all three issues
stay open until the triad records `VERDICT: PASS` on live behavior).

## Non-goals

- No provisioning, no spend in Wave 3. The #18 (a)/(b) paths are REPORTED
  (exact steps, pins, spend) — never executed.
- No auto-dispatch: every Stage-B seat launch and queue write happens under the
  recorded approval below, by explicit runbook step, never self-dispatched.
- No real tracker writes: Stage B uses synthetic queue rows only
  (`FRESH-SLICES-*`), never real tracker rows; reconcile stays propose-only.
- Never `Closes #16/#17/#18` (not in this package, not in the Stage-B PR).
- No V32 gate in Stage A. V32 MAY be appended in Stage B ONLY if the exercise
  proves a live behavior gap (with V19-freeze 39→40 note + live-count docs).
- No #78 (own later arch spec, untouched).

## Sensitive-action approval (recorded)

GRANTED by the principal (2026-10-29 grilling outcome, Q4): the bounded Stage-B
joint live exercise is explicitly approved — at most 6 seat launches (3 workers
+ 3 fresh-relaunch spares, Wave-2 F2 lesson), synthetic queue rows only, abort
on first RED, pre/post `rig ps` health snapshots, zero-residue cleanup. This
approval covers Stage B execution only; Stage A performs zero live execution
(read-only recon).

## Composition and fallback

- Planned composition: 1-real + 2-probe slices, concurrent.
- Deterministic fallback: if NO slice is certified ready at Stage-B kickoff,
  the exercise runs 3-probe. The runbook records which composition ran.
- Base SHA is pinned per slice; none cited green until the join.

## TPM-designation procedure

At Stage-B kickoff the TPM names the single real slice. It MUST compile green
standalone first. The Build agent never picks the real slice. The designation
line stays TBD in `tasks.md`/runbook until kickoff.

## Auditable overrides (recorded verbatim in design.md)

- (i) #17's "No load-testing against the live build fleet now" out-of-scope is
  WAIVED by the principal for this bounded exercise.
- (ii) #16's "S03 stays serial / revisit when green" precondition is PARTIALLY
  WAIVED for probes only.

## Acceptance

- Compound green in the worktree (39/0, `openspec validate`, self-test,
  idempotent); `make test` skipped with reason iff `git diff --name-only`
  shows zero code/test/script changes.
- Phase-A recon evidence filed with GO/NO-GO per Stage-B step; stop on RED.
- Stage B (separate execution): per-slice proofs + integration commit, #17
  metrics with the first-degrading metric named, #18 costed report, triad
  `VERDICT: PASS` before any PR.
