# Tasks: 2026-10-29-fresh-slices

## Phase A (this landing — read-only, NO live execution)

- [x] Author change package (proposal/spec/design/tasks per agreed design)
- [x] Safe-check (`stat` 700/600/600 + dry-run `!cat`-only rc=0, zero
  secret-shaped strings)
- [x] Read-only live recon (daemon up on arrival, `rig ps --nodes -A`
  baseline, tool versions) + GO/NO-GO per Stage-B step
- [x] Verify plan line refs from disk (`reconcile_model.py` premise-age /
  park-to-wake; discrepancy recorded in design.md)
- [x] Compound green (39/0, `openspec validate`, self-test, idempotent;
  `make test` skipped with reason — no code/test/script changes)

## Phase B (needs TPM designation at kickoff — NOT in this landing)

- [ ] TPM designates the real slice at kickoff (TBD until then; MUST compile
  green standalone first; Build agent never picks). Composition: 1-real +
  2-probe, fallback 3-probe if none certified ready; runbook records which
  composition ran.
- [ ] Pre-exercise `rig ps` health snapshot vs Phase-A baseline (NO-GO on
  unexpected state until TPM clears)
- [ ] Fan-out: 3 synthetic rows (`FRESH-SLICES-*`), base SHA pinned per
  slice, ≤6 launches (3 workers + 3 fresh-relaunch spares); abort on first
  RED
- [ ] Join: per-slice proofs + integration commit (none green until join);
  failed slice pins base, no mid-exercise rebase
- [ ] #17 metrics captured, first-degrading metric named (claim latency,
  stuck-sweep volume, snapshot cost, daemon responsiveness, ACTIVE/queue
  samples)
- [ ] #18 report: costed (a) + costed (b) (exact steps, pins, spend),
  explicit (c) decision, frame proof tracked Sprint-blocking; zero
  provisioning side effects
- [ ] Post-exercise `rig ps` snapshot + zero-residue cleanup verified
- [ ] V32 decision: append ONLY if a live behavior gap is proven (V19-freeze
  39→40 note + live-count docs), else 39/0 stands
- [ ] Triad (agency-qa red-proof + agency-drift-guard audit) → `VERDICT: PASS`
  before any PR (Refs #16, Refs #17, Refs #18 — never Closes)
