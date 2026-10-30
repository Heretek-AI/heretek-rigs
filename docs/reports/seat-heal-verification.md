# seat-heal independent verification (agency-drift-guard, 2026-10-30, Refs #147 — never Closes)

Stage: seat-heal. Change: `openspec/changes/2026-10-30-seat-heal/`.
Worktree: `.lane/trees/seat-heal`, branch `feat/seat-heal`, HEAD `dd95efc8daa25ec8a45655ef741f738d4c3dabd1` (unmoved by this audit; zero commits made).
Prior QA: `docs/evidence/seat-heal/qa-red-proofs.log` → PASS. This report independently re-verifies every axis read-only (no launches, no queue writes, no seat sends issued by the auditor).

## 1. Scope / One Rule / Refs-only

- `git diff main...HEAD --name-only` = 20 files: `AGENTS.md` (1 docs-map row), `docs/evidence/seat-heal-2026-10-30/` (13 files), `docs/evidence/seat-heal/qa-red-proofs.log`, `docs/reports/seat-heal-implementation.md`, change package (4 files). No code, test, or script diffs.
- Protected-path filter `git diff main...HEAD --name-only -- fleet/ specs/ rigs/ rosters/ registry/ archive/ openspec/specs/` → EMPTY. One Rule holds: zero hand-edits to generated leaves.
- Closing-keyword sweep: zero bare `Closes|Fixes|Resolves #147` in wave files. Only hits are negated/backticked (`never \`Closes #147\``, `Never Closes #147`, `never Closes`), matching merged-wave precedent.
- `tasks.md` triad box stays UNCHECKED — correct, this audit is the triad's second half and the coordinator commits.

## 2. Spec acceptance REQ-SH1/2/3 + seed-mechanism (independently verified — AGREE with QA)

- REQ-SH1: kickoff table in `runbook.md` §0 matches evidence files on disk (`ps-kickoff-pre.txt` 55 rows, `live-health-kickoff.txt` names exactly the 2, `queue-pre.json` 263 rows). GO criteria (set == 2, both idle, ≤ cap 4) satisfied on the evidence.
- REQ-SH2: per-seat rcs + sessionIds + before/after shellPath + reply excerpts all recorded (`runbook.md` §§2–3, `relaunch-sh2.json`, `send-sh1/2.json`, `probe-reply-sh1/2.json`). SH1 native occupant `01a18e92-f120-76af-915a-886d1e544f1c`, SH2 tmux `01M679DC8YV74MEC39AYQBDSY2` — both confirmed live in daemon state (session files present, continuity fresh).
- REQ-SH3: post-run `live-health-post.txt` shows `[PASS] seat-shell-paths: all 51 assessed seat path(s) resolve`; `queue-post.json` 263 rows; ps pre/post reconciled per runbook. No V-gate appended (V31 remains last) — correct, live state isn't repo state.
- Seed-mechanism claim, verified from repo source (not from testimony): `scripts/render-seat.py:1089-1090` bakes `shellPath` from the seeding checkout (`Path(__file__).resolve().parent / "seat-sandbox.sh"`); `render-seat.py:1458-1471` shows `--policy-only` rewrites only `extensions/pi-permission-system/config.json` and **returns before** the `settings.json` write loop (lines 1473-1486). `scripts/seed-rig.py:605` forwards `--refresh-policy-only` to `--policy-only`. Therefore `--refresh-policy-only` is structurally incapable of fixing `shellPath`, and the full member-fragment re-seed from the durable checkout was the necessary mechanism. QA's finding is CONFIRMED; the auditor concurs.

## 3. Live re-verification of the 2 healed seats (read-only, this audit)

- `settings.json shellPath` (daemon-state filesystem read): both seats → `<repo>/scripts/seat-sandbox.sh` (durable wrapper); target exists (`-rwxr-xr-x`, 2026-10-28). Pre-seed value was the pruned `.lane/trees/fleet-proofs/...` path per runbook — re-resolution proven.
- `rig seat status --json` both seats: `launch_cwd` `../../heretek-asset-manager` exists; `session_status running`, `startup_status ready`, `occupant_lifecycle active`, `continuity_outcome fresh`.
- `rig ps --nodes --json --no-cleanup -A`: 55 rows; both targets `running` / `idle` (post-heal park, probes complete).
- Kickoff "same 2, no drift" cross-checked against the audit source: `docs/evidence/seat-hygiene-2026-10-30/dangling-seats.json` = 24 rows, exactly 2 `lobotomized` (`build-java-kotlin-eng`, `build-python-backend-spec`) — identical to the kickoff set.

## 4. Bounds

- Relaunches: exactly 2 (cap 4 untriggered, 0 spares used). Sends: exactly 2 (`send-sh1/2.json`, both rc=0 `rendered-unconfirmed` — the known sender-identity advisory, same as the repair wave).
- Idle-only: both targets `running/idle` at kickoff and per-seat re-check; zero ACTIVE touches, zero skips needed.
- Zero queue writes: live `rig queue list --json -a -A --limit 10000` → 263 rows, 0 `seat-heal`/`SEAT-HEAL` hits; evidence pre/post 263→263 with only ambient `pickup.evidence` minute-counter ticks.
- Abort rule untripped — credible: every re-seed/relaunch rc=0, both config-clean checks GREEN, both probes PASS, fleet shape held (55 rows pre/post), no non-target seat disturbed.

## 5. Class-level proof (auditor's own run)

- `make live-health` executed read-only by the auditor: advisory exit 0; `[PASS] seat-shell-paths: all 51 assessed seat path(s) resolve`. "Zero dangling" is the TRUE live post-state, confirmed now, not just on paper.
- Remaining WARNs (`heartbeat` 5 age-unknown, `seat-idleness` 5 holders of old claimed rows — none are the healed seats, `tool-provisioning` 7 missing host artifacts) are pre-existing ambient conditions, honestly recorded in runbook §4 and outside this wave's scope.

## 6. Gates re-run

- `./scripts/verify-rigs.sh --check-only` → SUMMARY: 39 checks passed, 0 failed; no new V-block (V28–V31 intact, nothing appended). V-absence correct.
- `openspec validate 2026-10-30-seat-heal` → valid, rc=0.
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED.
- `python3 scripts/generate-rigs.py --check-idempotent` → rc=0, "two consecutive runs byte-identical". Auditor note (informational, not a wave defect): the flag compares run-to-run, not vs HEAD, and it rewrites leaves as a side effect — this audit's run dirtied `fleet/ registry/ rigs/ specs/` (e.g. re-rendered `queue-handoff` skill text, registry digests). All restored via `git checkout --` to byte-identical HEAD state; final `git status --short` EMPTY, `git rev-parse HEAD` = `dd95efc…` unmoved. The wave's own diff never touched those paths (protected filter EMPTY before and after).
- `make test` SKIPPED — accepted as valid: the branch diff contains zero code/test/script paths (verified from the full name-only listing), re-seed usage is an operation through existing tooling, and the `seat-shell-paths` class check plus unit/corpus suites (V6–V11 inside verify-rigs) already cover the class. F1 validate-weakness weighed: `openspec validate` guards "each requirement ≥1 Scenario" (proven RED below) but not scenario counts — single-scenario removal is caught by reviewer diff, and the spec file here is intact (sha256 `e4f87844…`, all 3 requirements × 2 scenarios present). Narrow, not vacuous; compensated.

## 7. Auditor's own red-proof (sabotage → RED → byte-identical restore → GREEN)

- Baseline sha256 of `openspec/changes/2026-10-30-seat-heal/specs/seat-heal/spec.md`: `e4f87844a496e8a2d5aec8133963d05ff6c32b5bbe79f7bcc66325abc6a2d37f` (matches QA baseline).
- Sabotage: removed both REQ-SH1 Scenario blocks → `openspec validate 2026-10-30-seat-heal` → rc=1 RED (`ADDED "REQ-SH1 …" must include at least one scenario`).
- Restore: `git checkout -- <spec.md>` → sha256 `e4f87844…` byte-identical → validate rc=0 GREEN. `git status --short` clean, HEAD unmoved. QA's RP-1 independently reproduced and confirmed.

## 8. Secrets / anti-stub

- Branch-diff sweep for `ghp_*`, `github_pat_*`, `sk-ant-*`, `xox*`, `Bearer` → 0 hits. Evidence/report/change-package sweep → 0 matches (`SEAT-HEAL-OK` is the wave's explicit dummy token per design, not a bearer).
- No `TODO`/`FIXME`/`placeholder`/trailing-`pass` in the branch diff. No swallowed errors, no dummy passes in evidence (rcs recorded, denial quoted verbatim, genuine whoami JSON present).

## 9. Honesty (overclaim check)

- Counts hold: 2/2 HEALED; launches 2/4 cap; sends 2; skips 0; 24/24 audit-listed seats resolved (22 stale under seat-repair + 2 lobotomized here — arithmetic matches the hygiene audit's 24).
- The echo-fallback probe PASS is NOT post-hoc: the fallback branch is written in the wave's own `design.md` §2 probe text ("If your shell policy denies echo, reply with the whoami output plus the line SEAT-HEAL-OK typed in your reply") and PASS criteria ("reply carries SEAT-HEAL-OK together with a plausible `rig queue whoami` output"). Both transcripts satisfy the letter: seat-identifying whoami JSON + verbatim denial quote + typed token. No D1-equivalent deviation occurred, and claiming none is accurate.
- No "zero" claim overreaches: `seat-shell-paths` PASS re-confirmed live by the auditor; queue-diff and ps-diff claims match the snapshots and the live queue count.

Informational notes (not findings): (a) `openspec validate` is narrow on scenario counts — reviewer diff compensates; (b) `--check-idempotent` has working-tree side effects — restore after running; (c) ambient WARNs (heartbeat/idleness/tool-provisioning) pre-date this wave and are honestly scoped out.

No FAIL-severity items. No `file:line` findings to list.

VERDICT: PASS
