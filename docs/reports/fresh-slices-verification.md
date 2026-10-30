# Drift-guard binding verification — Wave 3 / stage fresh-slices (change 2026-10-29-fresh-slices)

Auditor: agency-drift-guard (independent; no production code changed).
Worktree: `.lane/trees/fresh-slices` (branch `feat/fresh-slices`, HEAD `9aede98`).
Stage id: `fresh-slices`. Date (UTC): 2026-10-30.
Prior QA: `agency-qa` PASS with 3 non-blocking findings (see §7 for fix verification).

All spec/evidence paths below were read directly from disk in this worktree.
All gates in §3 were re-run by the auditor at HEAD (true exit codes, no pipes).

## 1. Scope & One Rule

- `git diff main...HEAD --name-only` = 18 files, all allowlisted: `AGENTS.md`
  (1 docs-map row), `docs/evidence/fresh-slices-2026-10-29/*` (10 files),
  `docs/evidence/fresh-slices/red-proofs.log`, `docs/reports/fresh-slices-implementation.md`,
  `openspec/changes/2026-10-29-fresh-slices/*` (5 files). 1329 insertions, 0 deletions of prior content.
- `git diff main...HEAD --name-only -- fleet/ scripts/ tests/ specs/ rigs/ rosters/ registry/ archive/ openspec/specs/ openspec/changes/archive/` → EMPTY. **One Rule holds** (no hand-edited generated leaves; V19-freeze intact).
- `git status --short` → clean (nothing uncommitted; QA sabotage canaries all reverted).
- Refs-only: the sole `(Closes|Fixes|Resolves) #N` match in the package is
  `proposal.md:21` "Never `Closes #16/#17/#18`" — inside a backtick code span
  (excluded from GitHub closing-keyword parsing), in an openspec file (not a PR
  body), matching archived-wave precedent. Commit subjects/bodies on the branch
  (`e5cd3d6`, `67cae8d`, `93d7f2d`, `9aede98`) contain Refs-only language, no
  closing keywords. Coordinator must keep the PR body Refs-only.

## 2. Spec acceptance per REQ

### REQ-F0 (safe-check + recon) — SATISFIED
- Auditor re-verified: secrets dir `700 john`, both keys `600 john` (stat-only);
  `render-seat.py --dry-run` → rc=0 with `!cat` references only (true rc, head-truncated display only).
- Phase-A recon filed (`phase-a-recon.md`): rig 0.7.5, go 1.27.3, python 3.15.2,
  pytest 9.1.1, cmake 4.3.0; `rig ps` baseline 51 fleet + 4 kernel, 111 lines.
  No launches/writes/installs in Stage A. Scenario checks all met.

### REQ-F1 (joint exercise: proofs + integration join) — SATISFIED with disclosed deviation
- Composition: 3-probe fallback, TPM-confirmed (no slice certified ready at
  kickoff; designation line empty per the proposal's deterministic fallback rule). Recorded in runbook §1 + tasks.md.
- Fan-out: 3 synthetic rows `FRESH-SLICES-{A,B,C}` (`--json --verify --no-nudge`,
  `--source fresh-slices-stage-b`), base SHA `e5cd3d6` pinned per slice, 0 of 6
  launches used (≤6 bound respected), no RED (abort path correctly not taken).
- Proofs: `proof-{a,b,c}.json` substantive (timed samples, UTC windows, full 3-way
  overlap 03:43:15–03:43:54Z). Auditor hashed all three: `872aa9b2…fb3059` /
  `d9e73ab9…bba6d0` / `74d386f8…f3d44` — match `join.json` byte-for-byte.
- "None cited green until join": `join.json` verdicts read "GREEN at join"; the
  integration commit `67cae8d` (on-branch, 11 files: proofs + join.json + metrics
  + #18 report) is the single close-out artifact. Scenario's "proofs AND the
  integration commit" holds.
- Join-row deviation (design item 2 envisioned a FOURTH join queue row): runbook §4
  discloses no fourth row was created, with factual rationale (post-hoc row would be
  theater + extra live writes outside the approved window); close-out is `join.json` +
  the coordinator's integration commit. Judgment: honest satisfaction — the REQ-F1
  Scenario binds on proofs + integration commit, not on the queue-row mechanism, and
  the deviation is disclosed, not papered over. No rows created to hide it.
- Failure-isolation rule: untested (no failures) but armed; disclosed in runbook §4;
  no mid-exercise rebase performed. Acceptable — luck of a green run, not a gap in the rule.
- Queue close: rows closed under the exercise's own declared source identity
  (`fresh-slices-stage-b`); QA log records the first close attempt without a seat
  identity failed closed, then the attributable retry succeeded. No live-seat
  impersonation. `claimedAt: null` throughout is consistent with the cold-row design.
- Post/pre snapshots: auditor hashed `ps-kickoff.txt` and `ps-post.txt` —
  identical `1a282dc3…403c8205` both, `cmp` BYTE-IDENTICAL, 111 lines each.
  Zero fleet footprint confirmed from disk, not on trust.

### REQ-F2 (#17 metrics) — SATISFIED, scope-narrowed (binding caveat below)
- `metrics.log` records per-metric observations: queue reads 0.29–0.40 s, ps
  snapshots 0.36–0.63 s, create→receipt ~0.2 s, overdue 0 rows (0.26 s), self-test
  53.9 s pass; stuck-sweep 0 attributable (7 pre-existing stalled, untouched);
  51/51 correctly-idle, 0 spuriously-idle. First-degrading metric: **"none degraded
  in this run"** with observed ranges listed.
- Claim latency recorded UNOBSERVED-WITH-REASON (cold rows by design, zero seat
  claims), per the Scenario's "or records which metric could not be observed and why".
- Watched-candidate projection (claim latency at higher concurrency) is explicitly
  labeled "WATCHED-CANDIDATE PROJECTION (labeled projection, not observation)" with a
  promote-or-retire obligation for the next N>3-slice run. Projection, not fabrication.
- Field consumption real: `attribute_idle_latency` (`:665`, comment `:668`) called on
  the actual row-A transition trail (created→done) yielding all-null while parked —
  exactly the function's specified semantics; `attribute_premise_age` (`:902`,
  comment `:808-810`) on the exercised window yielding `premise_age_s 214.83`.
  Read-only (import + in-memory call). Line refs verified from disk (`def` at 665/902,
  comments at 668/808-810).
- **Binding scope caveat (carried from QA F2, endorsed):** what this run proved is
  3-way concurrent daemon-READ load with zero disturbance — NOT seat-execution
  parallelism, NOT the full #16 execution model (no real slice, disjoint scopes
  trivially satisfied read-only). "None degraded" is honest ONLY with "in this run"
  attached. The triad VERDICT and PR body MUST state: daemon-read concurrency proven;
  seat-execution parallelism and claim-latency-under-contention NOT proven (still open).

### REQ-F3 (#18 report) — SATISFIED
- `provisioning-report-18.md` (FINAL): costed (a)-virtual ($0 lavapipe recipe, exact
  steps + pins), (a)-physical gap disclosed with NO invented SKU/price, costed (b)
  with secondary-source prices flagged re-verify-at-spend-time, explicit (c) decision
  (sequence non-visual slices first), frame proof tracked Sprint-blocking.
- UNVERIFIED marks intact: auditor spot-confirmed setup-env.sh/glslc layout,
  vkcube/Xvfb flags, Debian shaderc alternative, lavapipe version string (ll.43–47),
  physical SKU gap (l.53), Azure price + region/transport (ll.69–70, 79–80) — all
  preserved as UNVERIFIED, none upgraded. Report matches dossier without invention.
- Zero side effects: `rig host ls` empty, hosts.yaml absent, no installs in the
  recorded command set, $0 spend. Dossier-§4 verbatimness is now auditable on disk.

## 3. Gates re-run by the auditor at HEAD 9aede98 (true exit codes)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed, 0 failed`, TRUE rc=0.
- `grep -c V32 scripts/verify-rigs.sh` → 0 (V32 correctly absent; no live gap proven, runbook §7).
- `openspec validate 2026-10-29-fresh-slices` → valid, rc=0.
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED, TRUE rc=0.
- `make test` skipped: valid reason — diff shows zero code/test/script changes
  (docs + openspec only; Wave-2 precedent). QA additionally ran the full suite: 634 tests OK.
- Idempotence side-effect behavior noted in red-proofs.log (host asset drift, reverted twice); status clean.

## 4. Secrets hygiene + anti-stub

- Secrets verified stat-only (`700`/`600`/`600`, owner-only) plus `--dry-run`
  (`!cat` refs only, rc=0). No secret values printed anywhere in this audit.
- Bearer-shape scan over all evidence/report/spec files → 0 hits (the only matches
  anywhere are the self-referential grep-pattern documentation strings, per QA RP3).
- Anti-stub scan over all changed files (`|| true`, TODO/FIXME/STUB, vacuous asserts) → clean.
  All evidence files substantive (smallest: proof-c.json 656 bytes of timed samples;
  largest: ps snapshots 14835 bytes each).

## 5. Red-proof audit

- `docs/evidence/fresh-slices/red-proofs.log` records 8 sabotage proofs (RP1 spec-validator
  rc=1/0; RP2 scope-gate trip/clean; RP3 bearer-scan flag/clean; RP4 Refs-detector flag/clean
  + code-span precedent analysis; RP5 queue-detector 0-live/1-fixture; RP6 digest-gate
  rc=1 tree-hash FAIL / 39-0 rc=0; RP7 self-test rc=1 missing-input / rc=0; RP8 idempotence
  natural-drift non-vacuity). Every critical check has a recorded RED (failure signature
  non-vacuous: true rc=1 / trip / flag) followed by GREEN with restore-to-clean
  (`cmp` byte-identical, `git status` clean).
- QA ran at `93d7f2d`; HEAD `9aede98` adds only the F1/F3 fixes + the log itself.
  The auditor re-ran every green side at HEAD (§3) — all green. The delta was
  diff-inspected (§7), not trusted.

## 6. Honesty stress (adversarial questions, answered)

- 0-of-6 launches: bound respected (0 ≤ 6). The exercise tests a shadow of #16/#17 —
  but the shadow is the one the proposal explicitly approved (3-probe fallback when no
  slice is certified ready) and the spec's Scenarios explicitly accommodate
  (fallback-composition recording; unobservable-with-reason). No overclaim survives in
  the evidence; the scope caveat above is binding on triad/PR language.
- "None cited green until join": holds (verdicts "GREEN at join", single close-out commit).
- Queue close under own source identity: holds (fail-closed first attempt recorded; no impersonation).
- Snapshots byte-identical: independently hashed, holds.
- Failure-isolation untested-but-armed: disclosed, acceptable.
- Join-row deviation: disclosed with rationale, acceptable (see §2 REQ-F1).

## 7. Prior QA findings — fix verification (all three closed)

1. F1 stale-prefix/DEFERRED fill — FIXED at HEAD: tasks.md Join box no longer contains
   "UNCHECKED:" (diff `93d7f2d..9aede98` confirms the strike); `join.json`
   `integration_commit` now `67cae8d … — value filled at close-out (was DEFERRED pre-commit)`.
   Content correct; labels no longer lag.
2. F2 scope caveat — CARRIED, not fixable by editing: the wave's claims stay inside scope
   ("none degraded IN THIS RUN" + unobservable-with-reason + labeled projection throughout
   runbook/metrics/implementation report). Endorsed as binding triad/PR language (see §2 caveat).
3. F3 dossier-off-disk — FIXED: `dossier-18-research.md` filed (62 lines, dated fetches,
   Tavily+jina fallback disclosed, §4 gaps enumerated); UNVERIFIED marks intact in the
   report; report matches dossier without upgrades (prices, pins, caveats all correspond).

No new findings. No FAIL-grade items.

VERDICT: PASS
