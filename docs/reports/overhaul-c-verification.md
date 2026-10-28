# overhaul-c M6–M8 drift-guard verification (independent adversarial audit)

- Stage/wave: overhaul-c M6-M8. Worktree: `.lane/trees/overhaul-c` (branch `feat/overhaul-c`).
- Base: `b5b5b2b`. Commits audited: `253413f` feat + `04137c9` chore regen + `166d4c7` test evidence. Tree clean (`git status --short` empty at audit start and end).
- Spec: `openspec/changes/overhaul-c/{proposal.md,design.md,tasks.md,specs/archive/spec.md}` (REQ-C6/C7/C8/G1). Implementation claim: `docs/reports/overhaul-c-implementation.md`. QA red-proofs: `docs/evidence/overhaul-c/red-proofs.log`. Brief under test: `docs/IMPLEMENTATION_PROMPT.md`.
- Auditor made zero source edits and zero commits. All commands re-run on the archived tree; real output quoted.

## REQ-C6 — move set is stale-only (PASS)

- Keep-list intact, byte-identical: `git diff b5b5b2b...HEAD -- docs/evidence/107-identity-rotation.md openspec/changes/107-identity openspec/changes/102-closeout docs/reports/overhaul-b-verification.md` → empty (exit 0). `openspec/changes/` holds exactly the 6 allowed dirs (`102-closeout`, `107-identity`, `overhaul-a`, `overhaul-b`, `overhaul-bump`, `overhaul-c`). `docs/reports/` keeps 25 files matching `*102-closeout*|*107-identity*|*overhaul-*`. `docs/evidence/` keeps the 12 matching entries incl. `107-identity-rotation.md` in place; `run-records.json` absent as designed (V13 reads it only when harness claims exist — nothing to move, no empty file created). No live content moved.
- All moves are renames at R100 with history: `git diff -M --name-status` shows every rename as `R100`; non-rename entries are exactly the expected `M` ×5 (`.gitignore`, `AGENTS.md`, `README.md`, `scripts/audit_loop.py`, `scripts/verify-rigs.sh`) + `A` (fresh prompt, 2 reports, 4 own-spec files) + `M` registry provenance (below). `git log --follow` spot-checked on 3 archive paths resolves pre-move history (`REMEDIATION_LOG.md` → `c20dddc`, spoonfeeder → `c32a73e`, `checker-batch-d/proposal.md` → `b9008b4`).
- `.gitignore` additions exact: `+.opencode/`, `+.lane/`, `+st2p-proposal-package-lock.json` (3 lines, nothing else).

## REQ-C7 — prompt fresh, repoint complete, deviation justified (PASS)

- `docs/IMPLEMENTATION_PROMPT.md` (5217 bytes) is the fresh reconciled brief: pins `@openrig/cli@0.7.4`, 35-gate SUMMARY with V19 freeze + FAIL-ONLY V22–V27, wave triad, secrets rules. Stale-claim scan for `0.7.2|0.6.11|31|32|34|36 checks` → zero hits. Header explicitly supersedes (not copies) the archived pre-#122 upload. Not the stale upload.
- Root `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`: `git diff b5b5b2b...HEAD` empty — byte-identical, kept as-is.
- `audit_loop.py` repoint complete: `IMPLEMENTATION_PROMPT_FILE` and `REMEDIATION_PROMPT_FILE` both → `docs/IMPLEMENTATION_PROMPT.md`; `--run-implementation-first` help → new path; execution read follows the constant (self-test shows two `[PASS] Found docs/IMPLEMENTATION_PROMPT.md` presence+exec checks); remediation message no longer cites `REMEDIATION_LOG.md` as live — single sanctioned occurrence now directs a dated append to `archive/2026-10-28-overhaul/REMEDIATION_LOG.md` (archived, append-only). Greps: `PROMPT_SPOONFEEDER…` zero hits, root-relative `PROMPT_FLEET_AUDIT_REMEDIATION.md` zero hits, bare `REMEDIATION_LOG` only the sanctioned line (plus one prose comment in `verify-rigs.sh:2505` that is history-scope narration, not a read).
- Deviation judgment (explicit, as tasked): pointing `REMEDIATION_PROMPT_FILE` at the archived remediation file — the literal "constants → archive" reading — would itself violate the REQ-C7 scenario ("no code path reads an archived location as live input") and would trip the new fail-closed guard (`"archive" in p.resolve().parts` → exit 1, proven RED in S2). The single live brief driving both phases, with the remediation call's task instruction preserved, satisfies the scenario; the T2 sabotage semantics ("point const at archived file must RED") are preserved by the guard. Deviation ACCEPTED as required by the scenario, not a violation.
- Note (non-finding): the `audit_loop.py` diff carries ~6 black-style whitespace-only reflows alongside the functional hunks. Behavior-neutral (self-test + verify green); style nits alone are not findings per the severity rule.

## REQ-C8 — M8 gates green, regen no-op beyond provenance (PASS, re-run)

- `bash ./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed, 0 failed.` (V22–V27 green lines present). Exit 0.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED` with `[PASS] Found docs/IMPLEMENTATION_PROMPT.md (5217 bytes)` ×2 and the 20-vector evaluator green. Exit 0.
- `python3 -m unittest tests.test_schema_contracts` → `Ran 10 tests … OK`.
- Canary (archived tree, untouched): `pytest tests/test_build_canary.py -k test_canary_scope_only` → `2 passed, 10 deselected` (`CanaryCatalogPins::test_canary_scope_only` + `_fixture_fallback`). (First attempt with a guessed `CanaryScopeTests::` class path collected 0 items — wrong class name on my part, not a code failure; the `-k` run is the valid result.)
- Full `make test` (504 tests) was evidenced in `red-proofs.log` baseline; per tasking only the canary subset was re-run here.
- Regen no-op: `git diff b5b5b2b...HEAD --stat -- specs rigs rosters` → empty. Registry: 16 files, 24+/24-, every hunk is `resolvedCommit` + `canonicalUrl` commit-pin re-pointing `6781e0e… → 253413f…` only (provenance, lockstep); `grep -c DIRTY` over the registry diff → 0.

## REQ-G1 — gates and generator rule intact (PASS)

- `scripts/verify-rigs.sh` diff is exactly 1 line (HR-8.4 scan list dropping the two moved root prompt entries; `docs/OSINT…`, `docs/OPENRIG…`, `PROMPT_ADVERSARIAL…` entries verified still in place). No V1–V27 renumber/reword. SUMMARY frozen at 35, V22–V27 FAIL-ONLY green.
- `specs/`, `rigs/`, `rosters/` empty diff; `registry/` provenance-only via `generate-rigs.py` (no hand edits). AGENTS.md/README/diff maps are surgical line updates pointing at archive locations.

## Programmer self-audit flags — judged (accepted with reason, not findings)

1. Dangling symlink `archive/2026-10-28-overhaul/.opencode/skills -> ../.agents/skills`: accepted archival artifact. It preserves the moved symlink as-is (target was always an untracked stray); no gate reads it; fixing it would falsify the archived layout.
2. Stale prose/path-grant refs left untouched (`fleet/fleet.yaml` grants for `docs/{sprints,architecture,ops,perf}/*`, `schemas/rigspec-keys.pinned.json` provenance prose): deliberately untouched is CORRECT. Grants are inert when paths are absent, provenance is historical prose read by no gate, and any edit would dirty generator inputs and break the M8 no-op requirement.
3. `REMEDIATION_PROMPT_FILE` deviation: judged above — required by the REQ-C7 scenario; accepted.

## Placed-brief duplication check (PASS)

- `docs/IMPLEMENTATION_PROMPT.md` restates reconciled-plan content (0.7.4 toolchain, 35-gate SUMMARY, V22–V27, 51-seat triad, queue/secrets discipline) with zero stale claims (scan above). §7 live/archived companion table is accurate: audit protocol live at root, remediation protocol + log correctly cited as archived reference/append-only.

## Red-proofs audit (non-vacuous, PASS)

- `docs/evidence/overhaul-c/red-proofs.log` records baseline green (verify 35/0, self-test PASSED on new path, 504-test OK, topology OK), keep-identical spot-checks (empty diff + sha256 `e92208…`), 3 history-follows, exclusion inventory, and three sabotages each RED→restore→GREEN with exact signatures and exit 1: S1 keep-move → V24 rotation unreadable FAIL; S2 archived const → `[FAIL] Archived path referenced as live input` guard; S3 re-added stale HR-8.4 entry → `FileNotFoundError` fail-closed. Restores verified (`git status` clean, sha256 match, green re-runs). `git status --short` clean at end; sabotage never committed. No vacuous checks.

VERDICT: PASS
