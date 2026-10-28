# Proposal: mission-row gate ownership (issue #77)

- **Change ID**: `2026-10-28-77-mission-gates`
- **Issue**: Refs #77 (stays open until a live mission proves the loop closed).
- **Scope**: the issue's three asks, nothing else. No auto-closure of rows — by safety decision, not compatibility (see `design.md`).

## Motivation

When an owner seat finishes, it can leave its parent row open "waiting for a gate" that nobody owns (issue #77, factory audit mission B2: parent `qitem-20261024023941-8685741b5ce805de`, verdict recorded, "Standing by for gate", stuck sweep fired ~7 min later, seat called it a false positive, closed the recovery item, left the parent in-progress — still open, no gate qitem, no named owner). Nothing defines who closes a parent row once its evidence is in.

Today in this repo: tracker rows live in the external mission repo and are hand-edited by the human TPM; `reconcile.py`/`generate_trackers.py` are propose-only by baselined REQ-R2/REQ-G2 (`make reconcile`, `make generate-tracker`); a `standing-by/awaiting-gate` parent matches no enum arm in `reconcile_model.py:16-17` so it lands in `OTHER(<raw>) + NEEDS-HUMAN-REVIEW` with no stalled signal; the only live auto-advancer (`sweep-typed-blocks.py`) never writes `done` and never touches tracker parents.

## Proposed change

1. **S0** — fixtures reproducing the B2 pattern (awaiting-gate parent with no gate row; recovery dismissal with no row state change), proving current tooling does NOT flag it stalled (FAIL-ONLY pre-fix evidence).
2. **S1** — charter closure-ownership rule (via `fleet/skill-patches/` + regen, never hand-edited leaves) + new `reconcile_model` diff class for gateless awaiting-gate parents (stalled signal, still propose-only).
3. **S2** — stuck-sweep recovery made non-dismissible without a row state change + appended **V29** gate + corpus.
4. **S3** — runbook/evidence, secrets-discipline intact, reports.

## Non-goals

- Auto-closing any row to `done`/`complete` (forbidden — safety, see design).
- Amending REQ-R2/REQ-G2 propose-only discipline or the sweep never-`done` rule.
- Live-fleet proofs (fixtures only — `docs/NOTES.md:364` verifiability flag stands).
- Touching V1–V28 (append-only; post-wave total becomes 37).

## Acceptance summary (binding; see `tasks.md`)

- A1: gateless awaiting-gate parent is classified stalled (red-proven: sabotage reverts it to silent-OTHER).
- A2: recovery dismissal without row state change is refused (red-proven).
- A3: `verify-rigs.sh --check-only` → 37 passed, 0 failed (V29 green, V1–V28 intact).
- A4: `make test` green with grown corpus; `audit_loop.py --self-test` PASS; `generate-rigs.py --check-idempotent` byte-identical.
- A5: zero unredacted secret-shaped strings in evidence.
