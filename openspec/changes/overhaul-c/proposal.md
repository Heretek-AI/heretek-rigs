# Proposal: overhaul-c — archive stale bloat, audit prompt, regen, PR

Status: scope approved (principal decisions 2026-10-27/28; archive-not-delete; exclusions for live artifacts; findings verified live on main `b5b5b2b` 2026-10-28).
Issues: none tracked (housekeeping; Refs #66 umbrella only if needed).

## Why

The tracked tree carries pre-overhaul session bloat alongside live wave artifacts: 22 stale `openspec/changes/` folders, ~60 stale `docs/reports/`, ~25 stale `docs/evidence/` entries, retired spikes (`claude/`, `gemini/`), old sprint/architecture/ops/perf docs, superseded prompt files, `REMEDIATION_LOG.md`, a committed `.opencode/` loop log, and a root lockfile — while `.lane/` (stage worktrees) isn't even gitignored. Archive (not delete) preserves the audit trail. Separately, `audit_loop.py` still executes `PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md` (`:40`, `:468`, `:491`) and cites `REMEDIATION_LOG.md` (`:547`), and `docs/IMPLEMENTATION_PROMPT.md` was never created.

## What Changes

- M6: move stale-only content to dated `archive/2026-10-28-overhaul/` preserving relative paths, via `git mv` (history preserved). EXCLUDED from the move (stay in place): `openspec/changes/{102-closeout,107-identity,overhaul-bump,overhaul-a,overhaul-b}`, all `docs/reports/` + `docs/evidence/` entries matching `*102-closeout*`, `*107-identity*`, `*overhaul-*`, live `rotation.md` (V24-gated), and `docs/evidence/run-records.json` semantics (absent today; V13 reads it only when harness claims exist). Update HR-8.4 file list, AGENTS.md/README maps; `.gitignore` += `.opencode/`, `.lane/`, root lockfile name.
- M7: write `docs/IMPLEMENTATION_PROMPT.md` FRESH from the reconciled plan + current gates (the Gemini upload is pre-#122 and stale — explicitly not placed verbatim); keep the existing root `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` (no updated source exists); repoint `audit_loop.py` constants/help/execution path + the `REMEDIATION_LOG.md` message to the archive location.
- M8: source commit → clean regen → leaves commit; idempotence + verify + `make test` + `make topology OUT=/tmp/topology-c` all green.
- M9: adversarial re-audit + PR.

## Acceptance

1. Stale paths gone from tracked tree (`test ! -e` each); keep-list intact and byte-identical; `archive/2026-10-28-overhaul/` holds the moved content with history (`git log --follow` works).
2. All gate references updated: HR-8.4 list, audit_loop constants/help/message, AGENTS.md/README maps.
3. `audit_loop --self-test` PASSED with the new prompt path.
4. Regen + idempotence + verify (35/0 + V22–V27) + `make test` + topology all green on the archived tree.
5. Drift-guard `VERDICT: PASS` → PR (Refs only).
