# Design: 2026-10-29-fresh-slices

## Topology (observed 2026-10-29, Phase A recon)

- Host: dev machine, `rig 0.7.5 (b57c4da3)`, go 1.27.3, python 3.15.2,
  pytest 9.1.1, cmake 4.3.0. Daemon was UP on arrival (no loopback start
  needed); left running, untouched.
- `rig ps --nodes -A`: 51 `heretek-omni-fleet` seats `run`/`idle`, 4 `kernel`
  rows. WORK queued on live rows (e.g. build-ts-node-fullstack 7,
  data-pipeline 2, design rows 2–3) with recent model records
  (2026-10-30T01:16Z) — other sessions are active. Nothing was touched.
- Secrets: dir `700`, both keys `600`, owner-only. Dry-run rc=0, `!cat`
  refs only, zero secret-shaped strings.

## #16's five scope items — answers for the bounded exercise

1. **Work partitioning:** the three Stage-B slices MUST hold disjoint
   `path_write` scopes (same discipline as cpp-lowlevel `src/*` vs engine
   `src/engine/*` vs architect docs-only). No slice touches the root
   `CMakeLists.txt`; build-file needs are proposed by the slice and applied
   ONLY by the TPM at the integration join, which owns the merge.
2. **Queue DAG fan-out/fan-in:** three synthetic rows `FRESH-SLICES-{A,B,C}`
   proceed in parallel; a fourth join row closes on all three proof
   artifacts. Known blockers to observe (not fix): single-owner row
   semantics, handoff chains, watchdog claim behavior. The exercise records
   what blocked, if anything — it does not redesign the queue.
3. **Verification aggregation:** the 3-slice gate is per-slice proofs PLUS
   one integration build, all committed; none cited green until the join
   (REQ-F1). The integration commit hash is the single close-out artifact.
4. **Failure isolation:** one slice fails closed → it pins the base SHA; the
   other slices keep working on that pinned base; nothing rebases
   mid-exercise. The base SHA is recorded per slice in the runbook before
   fan-out, so the failure is attributable to slice-vs-base.
5. **Operator bottleneck audit:** the runbook counts operator touches per
   slice (probes, commits, `+x`, mediation) and tags each as automatable
   under current charters or needing new scope (build-runner role from #12
   is the standing candidate). No charter changes in Wave 3.

## Failure isolation rule (normative)

Failed slice pins base. The surviving slices continue on the pinned base SHA
recorded at fan-out. Rebase requires a new exercise, never a mid-flight
mutation of the running one.

## Auditable overrides (principal-granted, recorded verbatim)

- (i) #17's "No load-testing against the live build fleet now" out-of-scope
  is WAIVED by the principal for this bounded exercise.
  Rationale: the exercise IS the load observation — 3 slices, synthetic rows
  only, abort on first RED, zero residue — so the waiver is contained to one
  approved run, not open-ended load-testing.
- (ii) #16's "S03 stays serial / revisit when green" precondition is
  PARTIALLY WAIVED for probes only.
  Rationale: probe slices carry no green claims (none cited green until the
  join), so they cannot corrupt the serial close-out chain; the real slice,
  if any, still needs its standalone green compile first.

## Telemetry inputs (read-only reuse, verified from disk)

- Park-to-wake: `attribute_idle_latency` in `scripts/reconcile_model.py:665`
  (docstring; "Pure report field (inputs for #15/#17)" comment at :668).
- Premise-age classification comment at `scripts/reconcile_model.py:808-810`
  ("inputs for #17", propose-only REQ-R2); `attribute_premise_age` defined
  at `scripts/reconcile_model.py:902`.
- Discrepancy note: the plan cited `:668,809,903`; the current file shows
  the same content at `:668` (comment), `:808-810` (comment), `:902` (def)
  — lines shifted by ~1 as the module evolved. REQ-F2 cites actual lines.

## Fail-closed modes

- Secret perm != 600/700, or any secret value in output → stop, harden,
  re-verify (as in prior waves).
- First RED in Stage B → abort the exercise, record the abort point, clean
  to zero residue. No partial-green claims.
- Any `rig ps` snapshot showing unexpected seat state at Stage-B kickoff
  (vs the Phase-A baseline) → NO-GO until the TPM clears it.
- V32: NOT appended in Stage A. MAY be appended in Stage B ONLY if the
  exercise proves a live behavior gap (with V19-freeze 39→40 note +
  live-count docs); otherwise the gate count stays 39/0.
