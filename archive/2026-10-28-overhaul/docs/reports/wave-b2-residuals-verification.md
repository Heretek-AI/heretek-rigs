# Verification: Wave B2 residuals-107 (T3 drift-guard audit)

Scope: stage `residuals-107`, T3 audit only. Worktree `.lane/trees/residuals-107`,
branch `feat/residuals-107` @ `3966850` (T1 `503629c` + T2 evidence `3966850`).
Spec read from disk: `openspec/changes/residuals-107/{proposal.md,design.md,tasks.md,specs/residuals/spec.md}` + `AGENTS.md`.
Unity binding: N/A. No code fixed by auditor; report only, uncommitted.

## 1. Spec deliverables vs code

- REQ-R1 (V13 rate-limit skip, `scripts/verify-rigs.sh:1781`): PASS. Diff is exactly
  1 line: skip regex gains `|toomanyrequests|rate limit`, `re.IGNORECASE` retained,
  surrounding fail-closed logic byte-identical. `grep -n toomanyrequests scripts/verify-rigs.sh` → `:1781`.
- REQ-R2 (live-doc counts → 31): PASS. `AGENTS.md:15,46`, `docs/USER_GUIDE.md:127`,
  `README.md:47` all state 31. `grep -rn "26 checks" AGENTS.md docs/USER_GUIDE.md README.md` → 0 hits (exit 1);
  `grep -rn "31 checks" ...` → 4 hits. numstat confirms counts-only (AGENTS 2/2, USER_GUIDE 1/1, README 1/1).
- REQ-R3 (firecrawl pin): PASS. `docs/TECHNICAL_DOCUMENTATION.md:408` =
  `ghcr.io/firecrawl/firecrawl:2.10.19`; `grep -n mendable/firecrawl` → 0 hits;
  matches `docker-compose.sidecars.yml:93` + `docs/NOTES.md:305` per evidence §1.
- REQ-G1 (no renumber / no policy loosening): PASS. `git diff --name-only main...feat/residuals-107` touches only
  `AGENTS.md README.md docs/TECHNICAL_DOCUMENTATION.md docs/USER_GUIDE.md
  docs/evidence/wave-b2-residuals.md docs/reports/wave-b2-residuals-verification.md
  scripts/verify-rigs.sh` (6 source/evidence files + this report); governance probes
  (`check-envelope.py`, `reconcile_model.py`, `send-authenticated.sh`), seat-sandbox,
  denies, `docs/reports/*` untouched (grep over diff file list → clean).
- REQ-G2 (no history rewrites): PASS. No `docs/reports/*` in diff; evidence §5 records
  `nx9` canonical in B2 evidence only, both historical footers byte-identical.

## 2. Riding B1 (audit presence only)

- `openspec/changes/ops-sweep-111/proposal.md` + `docs/evidence/wave-b1-seatjail-sweep.md`
  present (committed `20d43b3`), not in `main...feat/residuals-107` diff. No code claims
  exceed them; B2 diff makes no seatjail/sweeper claims. PASS (presence only).

## 3. Stub hunt

- `git diff -U0 main...feat/residuals-107` scanned for TODO/FIXME/stub/`|| true`/bare-pass/skip markers → single hit is this report's own prose naming the pattern (self-reference, not a stub).
- numstat shows minimal touch (1-line V13, count/pin lines, 89-line evidence file). No vacuous
  test additions, no skipped tests in scope. PASS.

## 4. Re-run (auditor-executed)

- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 31 checks passed, 0 failed.`, exit 0
  (tail V14/V15 PASS observed). PASS.
- Proposal Acceptance 2/3 greps re-run by auditor (see §1): all hold. PASS.
- T2 acceptance also cites `pytest tests/test_policy_verifier.py tests/test_render_seat.py`
  = 46 passed (evidence §1); auditor did not re-run pytest (T2 evidence + green verify gate
  suffice for T3 scope; no code changed since T2 except evidence file).

## 5. Red-proof audit (`docs/evidence/wave-b2-residuals.md`)

- V13 arm both directions: sabotage (arm removed) → both `toomanyrequests`/`rate limit`
  fixtures RED (harness exit 1, fail-closed), control `connection refused` still SKIP
  (targeted, non-vacuous); restore → both SKIP (exit 0), `git status` clean. Signatures
  non-vacuous (RED message `FAIL V13/#70: sidecar image does not resolve (fail-closed RED)`).
- Doc-count guard both directions: sabotage (`31`→`26` in README) → grep guard RED exit 1;
  restore → GREEN (`26` absent, `31` 4 hits), status clean. Non-vacuous.
- Sabotage log lists 11 commands with exits + `git checkout --` restores; scratch cleanup
  outside worktree. `git status --short` clean at audit time (verified). PASS.

Findings: none. All REQ-R1/R2/R3/G1/G2 hold; V13 1-line only, counts in 3 docs only,
pin line only, governance/seat-sandbox/denies/reports untouched; verify green; red-proofs non-vacuous.

VERDICT: PASS
