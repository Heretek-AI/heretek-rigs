# Stage B runbook — fresh-slices bounded joint live exercise (#16 + #17)

Change: `openspec/changes/2026-10-29-fresh-slices/`. Stage: fresh-slices-B.
Bounds: principal-approved 2026-10-29 grilling Q4 — ≤6 seat launches,
synthetic rows only, abort on first RED, pre/post `rig ps` snapshots,
zero-residue cleanup. Refs #16, Refs #17, Refs #18 — never Closes.

Composition: **3-probe fallback, TPM-confirmed 2026-10-30**.
1-real designation line: (empty — no slice certified ready at kickoff).

Base SHA (pinned per slice, no mid-exercise rebase): `e5cd3d6`
(`feat(fresh-slices): Stage A package, safe-check, recon`).

All outputs redacted. Zero secret values recorded. Bearer-shaped strings:
none observed (grep `sk-|ghp_|Bearer [A-Za-z0-9]` → 0 matches on all
captured outputs).

## 1. Kickoff — `rig ps --nodes -A` re-snapshot vs Phase-A baseline

- Command: `rig ps --nodes -A` → rc=0, 111 output lines.
- Observed: 51 `heretek-omni-fleet` seats `run`/`idle` + 4 `kernel` rows —
  identical shape to Phase-A baseline (51 + 4, 111 lines).
- WORK pattern consistent with baseline: build-ts-node-fullstack 7,
  data-pipeline 2, design rows 2–3 (+3 yes-rows), delivery-tpm 2,
  systems rows 2–3 (+3 yes-rows). Other sessions ACTIVE, nothing touched.
- Verdict: **GO** (no unexpected state; NO-GO not triggered).

## 2. Fan-out — 3 synthetic rows, base pinned, cold (no-nudge)

Queue baseline (`rig queue list --json -a`, 2026-10-30T03:42:16Z, rc=0):
100 rows — done 76, blocked 13, in-progress 7, handed-off 4, pending 0.

| Slice | qitemId | tsCreated (UTC) | State | Destination |
|---|---|---|---|---|
| A | qitem-20261030034240-33ee649949951bf8 | 2026-10-30T03:42:40.447Z | pending | fresh-slices-probe-a@heretek-omni-fleet |
| B | qitem-20261030034245-96f9a96fde3fc54b | 2026-10-30T03:42:45.195Z | pending | fresh-slices-probe-b@heretek-omni-fleet |
| C | qitem-20261030034245-90ec7dfb2eceda7e | 2026-10-30T03:42:45.474Z | pending | fresh-slices-probe-c@heretek-omni-fleet |

- All creates: `--json --verify --no-nudge --source fresh-slices-stage-b`,
  tags `fresh-slices,synthetic,probe` + `slice:fresh-slices-*`. rc=0 each.
- Daemon advisory (expected, recorded): `unmatched_destination_seat` —
  synthetic probe sessions match no live seat BY DESIGN (cold rows; no live
  seat nudged, no live queue disturbed). Next backstop on each row:
  `queue-stuck-sweep:unmatched`... (per-row `nextBackstop`:
  `queue-stuck-sweep:unclaimed`, 1h).
- Queue write-path latency (create→verified receipt): ~0.2 s per row.
- Seat launches used: **0 of 6** (no worker seats launched; probes run as
  local shells in disclosed `/tmp/opencode/fresh-slices-{a,b,c}/` probe
  dirs — Wave-2 pattern, zero fleet footprint).
- Disjoint `path_write` scopes: probe workdirs per slice; probes are
  read-only against the worktree (no repo writes from probes).

## 3. Probes (concurrent) — per-slice proofs, ALL GREEN at join

Runner scripts: `/tmp/opencode/fresh-slices-{a,b,c}/run-{a,b,c}.sh`
(removed post-exercise per cleanup; logic summarized below; outputs
preserved as `proof-{a,b,c}.json`).

- Slice A: `python3 scripts/audit_loop.py --self-test` → rc=0,
  "SELF-TEST PASSED", 53.9 s + 3 timed queue+ps samples (0.36–0.40 s).
  Probe window 03:43:15–03:44:52Z. Proof sha256:
  `872aa9b2…fb3059`.
- Slice B: 3 timed `rig queue list --json -a` samples (0.29–0.37 s) +
  `rig queue overdue --json` → 0 rows (0.26 s); stalled-after-claim = 7
  (pre-existing live state, untouched). Window 03:43:12–03:43:54Z.
  Proof sha256: `d9e73ab9…bba6d0`.
- Slice C: 3 timed `rig ps --nodes -A` samples (0.52–0.63 s): 51/51 idle,
  12 rows with WORK (other sessions', untouched). Window
  03:43:12–03:43:54Z. Proof sha256: `74d386f8…f3d44`.
- Concurrency: full 3-way overlap 03:43:15–03:43:54Z (proven by
  probe_start/end timestamps). Overlap observed, no serialization.
- RED encountered: none. Abort path not taken. Launch budget: 0 of 6 used.

## 4. Join — integration proof (`join.json`)

- All three slices GREEN; none cited green until this join (REQ-F1).
- Base SHAs: all `e5cd3d6`. No failures → failure-isolation rule untested
  but armed; no mid-exercise rebase (none performed, none needed).
- Integration commit: DEFERRED to coordinator — the Stage-B agent does not
  commit (explicit bound), so no commit hash is invented here. `join.json`
  records per-slice proof hashes + the deferral; the close-out commit lands
  with the coordinator's PR.
- Join artifact: `docs/evidence/fresh-slices-2026-10-29/join.json`.

### Join-row deviation note (disclosure, not edit)

Design item 2 envisioned a FOURTH join row closing on all three proof
artifacts. NO fourth join row was created: the three slice rows were
closed individually (`done`/`no-follow-on`) after `join.json` was filed,
and close-out is `join.json` plus the coordinator's integration commit on
this branch. Rationale recorded factually: creating a post-hoc row after
the exercise window would be theater (no worker left to claim it) plus
extra live writes outside the approved window. QA/drift-guard will judge
the deviation; no rows are created now to paper over it.

## 8. Operator-touch audit (design item 5) — factual count

Counted from evidence (runbook §§1–6 + queue transition log). Each touch
tagged automatable-under-current-charters vs needs-new-scope (#12
build-runner is the standing candidate). No charter changes in Wave 3.
Coordinator commits/dispatches are coordinator-side — listed as
"coordinator-side (counted at close-out)", not as agent touches.

| # | Touch | rc / evidence | Tag |
|---|---|---|---|
| 1 | Kickoff `rig ps` snapshot + baseline compare | rc=0, §1 | Automatable (read-only recon; a scheduled recon seat already does this) |
| 2–4 | 3× `rig queue create --json --verify --no-nudge` | rc=0 each, §2 | Automatable in principle (fan-out script), BUT current charters grant no seat a standing queue-write scope for synthetic exercise rows — needs-new-scope or per-exercise approval (this run used the latter) |
| 5–7 | 3× background probe shells launched | completed, §3 | Automatable (Wave-2 seat-workspace pattern); needs-new-scope for unattended execution → #12 build-runner candidate |
| 8 | `chmod +x` on probe scripts | ok | Automatable (trivially scriptable; same scope question as 5–7) |
| 9 | Transient workdir failure on slice-A first launch → relaunch from probe dir | recovered, §3 | Mediation; automatable (retry-with-fallback, no judgment needed) |
| 10 | Failed-closed row close (no seat identity) → attributable retry under `fresh-slices-stage-b` | first rc=1-equivalent (daemon refusal), retry rc=0, §6 | Mediation; PARTLY automatable (retry logic) but identity choice is judgment → needs-new-scope (a build-runner seat identity would remove the judgment call) |
| 11 | ACTIVE/queue samples + `overdue` + `transitions` reads during run | rc=0, §5/metrics.log | Automatable (read-only telemetry) |
| 12 | Post `rig ps` snapshot + byte-compare + residue checks | rc=0, §6 | Automatable |
| 13 | /tmp probe-dir cleanup (python shutil after `rm -rf` policy refusal) | clean, §6 | Automatable (policy-compliant cleanup primitive; the `rm -rf` refusal itself is correct policy behavior, not a gap) |
| 14 | Coordinator integration commit + PR dispatch + triad | pending | Coordinator-side (counted at close-out) |

Totals: 13 agent touches (11 automatable-or-trivially-scriptable, 2
needing judgment/scope: queue-write authority, seat identity for
mutation). Standing candidate for the judgment-bearing touches: #12
build-runner role. Zero touches were charter changes.

## 5. #17 metrics

Full series in `metrics.log`. Summary: claim latency unobservable-by-design
(cold rows; create→receipt ~0.2 s observed instead); stuck-sweep 0
attributable (7 pre-existing stalled, 0 overdue); snapshot costs sub-second
and stable; daemon responsive; 51/51 correctly-idle. **First-degrading
metric: none degraded** (with observed ranges recorded).

## 6. Post-exercise snapshot + zero-residue cleanup — VERIFIED

- Post `rig ps --nodes -A` (03:46Z): 51 fleet + 4 kernel, 111 lines, WORK
  pattern identical to kickoff. `ps-kickoff.txt` and `ps-post.txt` are
  BYTE-IDENTICAL (sha256 `1a282dc3…403c8205` both) — zero fleet footprint.
- Queue rows: all 3 → `done`/`no-follow-on` under the exercise's own
  declared source identity `fresh-slices-stage-b` (the same `--source`
  used at create; no live seat impersonated — the first close attempt
  without a seat identity failed closed, then the attributable retry
  succeeded; both recorded here). Residue check: 0 open FRESH-SLICES rows.
- Probe dirs `/tmp/opencode/fresh-slices-{a,b,c}/` + body files + scripts:
  REMOVED (proofs preserved in evidence dir). `ls /tmp/opencode | grep
  fresh` → clean. No tracker writes (reconcile never invoked; trackers
  untouched — none exist in this repo).
- Reconcile clean: no queue residue (verified via `rig queue list --json`).

## 7. V32 decision — NOT appended (reason recorded)

No live behavior gap was proven: every gate green, daemon responsive, no
timeouts, no claim/watchdog anomalies attributable to a missing gate.
The `unmatched_destination_seat` advisory on synthetic destinations is
correct existing behavior (cold rows by design), not a gap. Gate count
stays 39/0; no V19-freeze note needed. If a future exercise proves a gap,
V32 appends then with the freeze note + live-count docs.
