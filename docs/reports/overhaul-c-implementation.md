# overhaul-c implementation report — M6 moves + M7 prompt (agency-programmer)

- Stage/wave: overhaul-c M6–M7 (M8 regen/gates + commits stay with coordinator).
- Worktree: `.lane/trees/overhaul-c`, branch `feat/overhaul-c` from `main` @ `b5b5b2b`.
- Date: 2026-10-28. Author: agency-programmer (Muse Spark 1.3 Contributor).
- Disposition: **dirty, uncommitted** — left for coordinator commit. Do NOT run
  `generate-rigs.py` in this stage (coordinator owns M8).

## Deliverables

- M6: 138 stale paths moved via `git mv` to `archive/2026-10-28-overhaul/`
  (245 tracked files, all renames R100, 0 insertions / 0 deletions);
  HR-8.4 file list, AGENTS.md docs map, README map, `.gitignore` updated.
- M7: fresh `docs/IMPLEMENTATION_PROMPT.md` (live operator brief, 5217 bytes);
  `scripts/audit_loop.py` repointed (constants + help + execution + remediation
  message); root `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` byte-identical.

## M6 move manifest (recounted live from disk — proposal counts not trusted)

| Category | Paths moved |
|---|---|
| `openspec/changes/` (all except `102-closeout`, `107-identity`, `overhaul-bump`, `overhaul-a`, `overhaul-b`, own `overhaul-c`) | 20 dirs: `checker-batch-d`, `command-effects`, `docs-write-scopes`, `issue-12-build-capability`, `issue-57-generate-trackers`, `ops-sweep-111`, `output-deny-76`, `path-arg-grants-91`, `provisioning-gate-74`, `remediate-37-id-discipline` … `remediate-45-live-health` (9), `residuals-107`, `topology-fix` |
| `docs/reports/` (all except `*102-closeout*`, `*107-identity*`, `*overhaul-*`) | 70 files moved, 24 kept |
| `docs/evidence/` (all except the 12 matching entries incl. `107-identity-rotation.md`) | 29 entries moved (20 dirs + 9 files), 12 kept |
| Root files | 5: `REMEDIATION_LOG.md`, `HANDOFF_CLAUDE_AUDIT.md`, `PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md`, `PROMPT_FLEET_AUDIT_REMEDIATION.md`, `st2p-proposal-package-lock.json` |
| Tracked `.opencode/` files | 3: `opencode-loop/loop.log`, `opencode-loop/ses_ead24b8daffeh8kmc6aHsmekKs.json`, `skills` symlink (target `../.agents/skills` now dangles inside archive — expected archival artifact) |
| Retired spikes | 2 dirs: `claude/`, `gemini/` |
| `docs/` files | 5: `PROMPT_FACTORY_MISSION_AUDIT.md`, `PROMPT_REMEDIATION_REAUDIT.md`, `PROMPT_REVIEW_ARGON.md`, `PROMPT_REVIEW_WEB.md`, `REMEDIATION_IMPLEMENTATION_PROMPT.md` |
| `docs/` dirs | 4: `sprints/`, `architecture/`, `ops/`, `perf/` |
| **Total** | **138 paths → 245 tracked files** |

Destination preserves relative paths: `<src>` → `archive/2026-10-28-overhaul/<src>`.
Keep set: excluded openspec dirs, 24 reports, 12 evidence entries, root live
files (`PROMPT_ADVERSARIAL_FLEET_AUDIT.md`, `AUDIT_REPORT_FINDINGS.md`,
`HANDOFF.md`, …), staying `docs/*.md`, and this change's own
`openspec/changes/overhaul-c/` (untracked, untouched).

## M6 reference updates (surgical, no renumber/reword)

- `scripts/verify-rigs.sh` HR-8.4 (`:1293`): dropped the two moved root prompt
  entries (`PROMPT_SPOONFEEDER…`, `PROMPT_FLEET_AUDIT_REMEDIATION…`); kept the
  `docs/OSINT…`, `docs/OPENRIG…`, `PROMPT_ADVERSARIAL…` entries (each verified
  in place before editing).
- `AGENTS.md` docs map (3 lines): the two `docs/PROMPT_REVIEW_*` entries and
  the `REMEDIATION_LOG.md` / `PROMPT_FLEET_AUDIT_REMEDIATION.md` refs now
  point at their `archive/2026-10-28-overhaul/…` locations.
- `README.md` (2 lines): `REMEDIATION_LOG.md` cite (§18) and the
  `PROMPT_FLEET_AUDIT_REMEDIATION.md §2` rule-set cite (§87) repointed to archive.
- `.gitignore` (+3 lines exactly): `.opencode/`, `.lane/`,
  `st2p-proposal-package-lock.json`.

## M7 prompt placement

- `docs/IMPLEMENTATION_PROMPT.md` written FRESH (reconciled plan + current
  gates: 0.7.4 / pi 1.4.0 / pps 41.0.0 toolchain, 35-gate SUMMARY with V19
  freeze + FAIL-ONLY V22–V27, wave triad discipline, secrets rules). Not the
  stale pre-#122 upload. Token-hygiene scanned (no unresolved markers).
- Root `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` untouched (zero diff).
- `scripts/audit_loop.py`:
  - `IMPLEMENTATION_PROMPT_FILE` → `docs/IMPLEMENTATION_PROMPT.md` (constant,
    `--run-implementation-first` help, Phase-0 message + execution read follow
    the constant).
  - `REMEDIATION_PROMPT_FILE` → `docs/IMPLEMENTATION_PROMPT.md`. Rationale:
    the remediation protocol file was archived per REQ-C6, so no constant may
    reference it as a live input (T2 red-proof "point const at archived file"
    must RED) and no code path may read an archived location as live input
    (REQ-C7 scenario); the single live brief now drives both loop phases, with
    the remediation call's own task instruction preserved.
  - Added fail-closed guard in `run_self_test`: any required prompt resolving
    inside `archive/` FAILs (exit 1) — makes the REQ-C7 scenario executable and
    the T2 prompt sabotage RED.
  - Remediation message (`:565`) no longer cites `REMEDIATION_LOG.md` as live:
    now directs a dated append to
    `archive/2026-10-28-overhaul/REMEDIATION_LOG.md` (archived log, append-only).

## Proofs (exact commands, exit codes)

1. `while …; do git mv …; done < move-list.txt` → `moved=138 failed=0` (exit 0).
2. Stale-absence sweep (`test -e/-L` over all 138) → zero survivors (exit 0).
3. Keep-set: 6300 file `sha256sum` before vs after → `cmp` identical; 2 keep
   symlinks (`.claude/skills`, `.github/skills`) target-identical;
   `git diff PROMPT_ADVERSARIAL_FLEET_AUDIT.md` empty (exit 0).
4. `git diff --cached -M`: 245 files, **0 insertions / 0 deletions**, every
   rename similarity 100%; `git status --short` shows only `R` lines plus the
   intended `M` ×5 and `??` ×2 (exit 0).
5. History: pre-move lineage confirmed via original paths
   (`git log -- <orig>` shows commits, e.g. `REMEDIATION_LOG.md` @ `c20dddc`);
   renames staged at R100 so post-commit `git log --follow` on the archive
   paths resolves (coordinator to re-verify after M8 commits).
6. `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`, exit 0
   (prompt presence incl. archive-guard, 20 evaluator vectors, full
   `verify-rigs.sh` gate green).
7. `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed,
   0 failed.`, exit 0 (V22–V27 green, V19 SUMMARY frozen).
8. Greps over `scripts/ Makefile tests/`:
   - `PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md` → zero hits.
   - `"PROMPT_FLEET_AUDIT_REMEDIATION.md"` (root-relative) → zero hits.
   - `REMEDIATION_LOG.md` without `archive/` prefix → zero hits (single match
     carries the `archive/2026-10-28-overhaul/` prefix: the sanctioned message).
   - `archive` in `audit_loop.py` → 3 sanctioned lines only (explanatory
     comment, self-test guard, archived-log message).

## Files changed (working tree, uncommitted)

- Renamed (staged `R`, 245 files): the 138 move paths → `archive/2026-10-28-overhaul/`.
- Modified (unstaged `M`): `scripts/verify-rigs.sh`, `scripts/audit_loop.py`,
  `AGENTS.md`, `README.md`, `.gitignore`.
- Created (untracked `??`): `docs/IMPLEMENTATION_PROMPT.md`,
  `docs/reports/overhaul-c-implementation.md` (this file),
  `openspec/changes/overhaul-c/` (pre-existing own spec, not mine).

## Self-audit notes

- `generate-rigs.py` NOT run; nothing committed (coordinator owns M8).
- `.opencode/skills` symlink now dangles inside archive (target was the
  untracked stray `../.agents/skills`) — accepted archival artifact, noted not fixed.
- `fleet/fleet.yaml` path-grant entries for `docs/{sprints,architecture,ops,perf}/*`
  and `schemas/rigspec-keys.pinned.json` provenance prose still name moved
  locations; both are inert (grants apply only if paths exist; provenance is
  historical prose, read by no gate) — deliberately untouched to keep M8 regen
  a no-op. Flagged for coordinator awareness, not changed.
- Decision on `REMEDIATION_PROMPT_FILE` (documented above) deviates from a
  literal "constants → archive" reading in favor of the REQ-C7 scenario
  ("no code path reads an archived location as live input") + T2 sabotage
  semantics; QA red-proof `red-proofs.log` should cover: (a) const pointed at
  archived spoonfeeder file → self-test RED via the new guard; (b) HR-8.4 with
  a re-added moved filename → gate RED.
