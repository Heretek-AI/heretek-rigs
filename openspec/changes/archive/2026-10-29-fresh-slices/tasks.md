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

- [x] TPM designates the real slice at kickoff (TBD until then; MUST compile
  green standalone first; Build agent never picks). Composition: 1-real +
  2-probe, fallback 3-probe if none certified ready; runbook records which
  composition ran. ; outcome: 3-probe fallback, TPM-confirmed 2026-10-30, no slice certified ready (designation line stays empty per fallback rule)
- [x] Pre-exercise `rig ps` health snapshot vs Phase-A baseline (NO-GO on
  unexpected state until TPM clears) ; outcome: GO — 51+4, 111 lines, WORK pattern matches baseline (runbook §1)
- [x] Fan-out: 3 synthetic rows (`FRESH-SLICES-*`), base SHA pinned per
  slice, ≤6 launches (3 workers + 3 fresh-relaunch spares); abort on first
  RED ; outcome: 3 rows pending/cold, base e5cd3d6, 0 launches used, no RED (runbook §2)
- [x] Join: per-slice proofs + integration commit (none green until join);
  failed slice pins base, no mid-exercise rebase — proofs filed
  (join.json); join-row deviation disclosed in runbook §4; outcome: integration close-out = commit 67cae8d (proofs + join.json + metrics + #18 report in one commit; close-out PR to follow)
- [x] #17 metrics captured, first-degrading metric named (claim latency,
  stuck-sweep volume, snapshot cost, daemon responsiveness, ACTIVE/queue
  samples) ; outcome: "none degraded in this run" + watched-candidate
  projection (claim latency at higher concurrency); field consumption done
  read-only (metrics.log)
- [x] #18 report: costed (a) + costed (b) (exact steps, pins, spend),
  explicit (c) decision, frame proof tracked Sprint-blocking; zero
  provisioning side effects ; outcome: provisioning-report-18.md final
  (dossier-sourced, UNVERIFIED marks preserved, skeleton deleted); (c)
  recorded; hosts ls empty, $0 spend
- [x] Post-exercise `rig ps` snapshot + zero-residue cleanup verified ; outcome: post ps byte-identical to kickoff, 3 rows done/no-follow-on, /tmp clean (runbook §6)
- [x] V32 decision: append ONLY if a live behavior gap is proven (V19-freeze
  39→40 note + live-count docs), else 39/0 stands ; outcome: NOT appended —
  no live gap proven, 39/0 stands (runbook §7)
- [x] Triad (agency-qa red-proof + agency-drift-guard audit) → `VERDICT: PASS`
  before any PR (Refs #16, Refs #17, Refs #18 — never Closes); outcome: agency-qa PASS (red-proofs.log) + agency-drift-guard VERDICT: PASS (fresh-slices-verification.md), both committed pre-merge
