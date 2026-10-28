# QA report — 77-mission-gates, wave 4 (Refs #77)

Verifier: acceptance verifier subagent. Worktree
`.lane/trees/77-mission-gates`, branch `feat/77-mission-gates`, tip
`e5cfa44`, base `main @ 6fe665f`. Read from disk: `AGENTS.md`, the wave
spec (`openspec/changes/2026-10-28-77-mission-gates/`), the implementation
report (`docs/reports/77-mission-gates-implementation.md`); nothing below
is trusted from summary. No commits, no pushes; sabotage temporary and
fully reverted (`git status --short` clean between proofs; only this
report and `docs/evidence/77-mission-gates/red-proofs.log` modified at
close).

## 1. Full battery (current tip)

| # | Check | Result |
|---|---|---|
| 1 | `./scripts/verify-rigs.sh --check-only` | PASS — `SUMMARY: 37 checks passed, 0 failed`, `[PASS] V29 mission-gate ownership (77-mission-gates S2) green: stalled diff + charter markers in 9 leaves + refusal guard + 16 corpus tests pass + S0 evidence present`. V1–V28 headers intact (spot-check): `== V22. Bare Queue/Send Deny in Seat Maps (#102/HR-F18) ==`, `== V23. Per-Seat MCP Bearer Grants (107-identity M1) ==`, `== V24. Rotation Runbook Step-3 --rig Mandate (107-identity R1) ==`, `== V28. Send-Identity Attestation (09-send-identity S1) ==` — titles unrenamed. |
| 2 | `make test` | PASS — exit 0, `Ran 558 tests in 114.231s / OK` (matches the 558-family claim). |
| 3a | `python3 -m unittest tests.test_mission_gates -v` | PASS — exit 0, `Ran 16 tests / OK`: 3 charter-closure (REQ-M1: destination-seat rule, gate exemption, no-gateless-waiting), 7 stalled-awaiting-gate (REQ-M2: B2 flagged, diff names missing gate, live-gate quiet, dead-gate stalled, awaiting-without-gate quiet, sabotage-returns-silent, generator review + exemption), 6 non-dismissible-recovery (REQ-M3: refused + row untouched, allowed-on-change, redaction, bypass-restores-B2, no-writes/never-done, and dismissal-shape pin). |
| 3b | `python3 -m unittest tests.test_mission_gates_prefix -v` | PASS — exit 0, `Ran 6 tests / OK` (B2 fixture genuineness pins + frozen S0 evidence pins: reconcile silence, dismissal-ALLOWED, no 40+ runs). |
| 4 | `python3 scripts/audit_loop.py --self-test` | PASS — `SELF-TEST PASSED` (fail-closed sentinel vs 20 adversarial vectors; verify-rigs static/schema/digest/security checks green). |
| 5 | `python3 scripts/generate-rigs.py --check-idempotent` | PASS — `idempotence check passed (two consecutive runs byte-identical)`. Side effect: `registry/` provenance re-lag only (`resolvedCommit` + `canonicalUrl` b17d83d → e5cfa44, 16 files) — verified provenance-only, reverted via `git checkout -- registry/`; status clean. |
| 6 | `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/77-mission-gates-prefix.md docs/evidence/77-mission-gates-runbook.md` | PASS — no output, exit 1 (zero secret-shaped strings). |
| 7 | Safety audit (CRITICAL) | PASS — (a) `git diff 6fe665f..HEAD --name-only` (50 files): generated paths limited to 9 `mission-slice-sop/SKILL.md` leaves (specs + 8 rigs, each exactly +1/-0 lines — the single closure-ownership bullet), 8 `bundle.yaml` digest re-hashes, `registry/` provenance/digest re-lag; `rosters/` untouched; zero hand-edits beyond regen churn. (b) State-writing sweep over the wave `scripts/` diff: zero matches for `update --state` / `queue (update|close)` / `--state (done|complete|closed)`; no done-emission tokens. `check_recovery_dismissal` returns data or raises `RecoveryDismissalRefused` — no rig write, never done; `check_unpark_argv` refuses any state != in-progress and any `done`. The sweep refusal only REFUSES. No auto-closure path exists — no blocking finding. |
| 8 | Charter check | PASS — `fleet/skill-patches/mission-slice-sop.yaml` carries the source patch (exact fail-closed single-hit `replacements:` append); 9/9 rendered leaves contain `Closing your row (gate ownership)` with the `--gate <role>` live-owner exemption; patch-to-leaf bullet text corresponds exactly. Runbook `--gate` count = 2 (>= 1). |

## 2. Red-proofs (QA series appended to `docs/evidence/77-mission-gates/red-proofs.log`; priors untouched)

| ID | Sabotage | RED (must fail) | GREEN (restored) |
|---|---|---|---|
| QA-a (REQ-M2) | `diff_row` tail `return stalled_awaiting_gate_diff(...)` -> `return None` in `scripts/reconcile_model.py` | B2 fixture CLI exit 0: `reconcile: in sync — 1 rows ... agree with queue state`; `diff_row -> None` — silent, no stalled signal | `git checkout` -> CLI exit 1 with `DIFF [stalled-awaiting-gate]` naming the missing gate |
| QA-b (REQ-M3) | Guard equality branch neutered (`... and False`) in `scripts/sweep-typed-blocks.py` | Identical snapshots -> `dismissal-without-change: ALLOWED {'dismissal': 'permitted', ...}` — B2 bury-the-stall outcome restored, proving the guard is what refuses | `git checkout` -> `RecoveryDismissalRefused` with redacted line, row untouched |
| QA-c (V29 non-vacuous) | Closure bullet removed from 1 of 9 leaves | Full verify exit 1: three `[FAIL] V29 ... lost charter marker` lines; `SUMMARY: 35 checks passed, 5 failed` | `git checkout` -> full re-run exit 0: `[PASS] V29 ...` + `SUMMARY: 37 checks passed, 0 failed` |

Each restore proven by `git checkout -- <file>` + `git status --short` clean
(empty after each proof; re-verified at close). Verbatim RED + GREEN
transcripts live in the log, not here.

## 3. Findings

No blocking findings. No numbered findings (F-series empty):

- Vacuous-check sweep: none — QA-a/QA-b/QA-c each flip their check RED under
  minimal targeted sabotage, so no acceptance check is vacuous.
- Auto-closure sweep: none — see check 7.
- Hand-edit sweep: none — see check 7(a); `rosters/` untouched.
- Secrets sweep: none — see check 6; refusal-line redaction covered by corpus
  (`test_refusal_log_line_redacted`) and V29 live behavior.

Non-findings (recorded for the coordinator, no action): `HANDOFF.md` still
states 36 checks (prior-session file, deliberately untouched — matches the
implementation report); provenance re-lag class on every regen (accepted,
reverted after each gate run).

## 4. Closeout state

`git status --short` at close shows only:

```
 M docs/evidence/77-mission-gates/red-proofs.log
?? docs/reports/77-mission-gates-qa.md
```

Verdict: wave-4 acceptance battery green, red-proofs complete, no vacuous
checks, no blocking findings. (Refs #77; issue stays open for the
live-mission proof by design.)
