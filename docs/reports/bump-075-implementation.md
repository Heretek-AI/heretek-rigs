# Implementation report — Wave 1 `2026-10-29-bump-075` (0.7.5 bump-eval ledger)

- **Stage:** Wave 1 `2026-10-29-bump-075` · **Branch:** `feat/bump-075` @ `c1da1fb`
- **Worktree:** `.lane/trees/bump-075` (repo-relative)
- **Role:** agency-programmer · **Method:** test-first (RED baseline → GREEN pins → red-proof sabotage)
- **Commit:** none (coordinator commits per wave instructions)

## Deliverables

1. `openspec/changes/2026-10-29-bump-075/` — `proposal.md`, `specs/bump/spec.md`
   (RFC 2119 deltas REQ-BUMP3/REQ-BUMP4 + REQ-G1 updated to V1–V31/SUMMARY 39),
   `design.md` (live upstream facts + tarball-diff disposition table +
   fail-closed modes), `tasks.md` (all boxes checked; T2 acceptance uses `&&`).
2. `docs/sprints/CLI-0.7.5-BUMP.md` — ledger (version, two-fetch sha, tag,
   8 true-pin files, disposition, verify output, rollback).
3. Host toolchain pins updated in exactly the 8 true-pin files (same set as
   the 0.7.4 precedent): `AGENTS.md` (surgical), `README.md`, `Makefile`,
   `docs/USER_GUIDE.md`, `docs/TECHNICAL_DOCUMENTATION.md`,
   `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`, `docker/Dockerfile`,
   `scripts/verify-rigs.sh` (V13 + V18 pin strings only).
4. This report.

## Files changed

- Modified (8): `AGENTS.md`, `README.md`, `Makefile`, `docs/USER_GUIDE.md`,
  `docs/TECHNICAL_DOCUMENTATION.md`, `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`,
  `docker/Dockerfile`, `scripts/verify-rigs.sh`
- Created (6): `openspec/changes/2026-10-29-bump-075/{proposal.md,design.md,
  tasks.md,specs/bump/spec.md}`, `docs/sprints/CLI-0.7.5-BUMP.md`,
  `docs/reports/bump-075-implementation.md`
- Untouched by design: `fleet/*` (never `yaml.safe_dump`; no edit at all),
  `scripts/generate-rigs.py`, `schemas/*`, all generated leaves
  (`specs/`, `rigs/`, `rosters/`, `registry/`), canonical `openspec/specs/`,
  dated records, `docs/IMPLEMENTATION_PROMPT.md` (not a true-pin file).

## Live evidence (training data NOT trusted; all captured 2026-10-29)

- `npm view`: `0.7.5` published `2026-10-29T07:36:19.571Z`; tarball
  `https://registry.npmjs.org/@openrig/cli/-/cli-0.7.5.tgz`.
- Two independent `npm pack` fetches → sha256
  `22d67c2c7e0d0ab4a5ec9faac0a725d54f9ead2c0f71564985cf4ae240bb9754`
  (identical); control re-fetch of 0.7.4 reproduces `d11dd8a6…` (method sound).
- `git ls-remote https://github.com/mvschwarz/openrig`: `refs/tags/v0.7.5`
  = `e9b05fda…`, peeled `v0.7.5^{}` = `b57c4da3c3ac3fb420a09e5a169d3e85f9529e93`
  (confirms plan claim `b57c4da`, tag date 2026-10-28 per plan — tag date not
  directly verifiable via ls-remote, noted here). npm metadata carries NO
  `gitHead` (0.7.4 has none either); `dist.shasum 00ef5b67…` is the tarball
  sha1, not a commit — recorded to prevent misreading.
- `npm install -g @openrig/cli@0.7.5` → `rig --version` = `0.7.5 (b57c4da3)`
  (binary stamp corroborates the peeled commit).
- Tarball diff 0.7.4→0.7.5: MEMBER_KEYS permission sets IDENTICAL;
  run-record + all five bundle/registry schemas byte-IDENTICAL (installed
  copies equal tarball copies); 19/19 skill dirs, only `queue-handoff/SKILL.md`
  +parking prose (deferred); new one-way DB migration 126; #2200 still open
  per upstream whats-new. → **zero generator-input changes demanded.**

## Commands run (real outputs, exit codes)

| # | Command | Output / exit |
|---|---|---|
| 1 | `./scripts/verify-rigs.sh --check-only` (baseline, rig 0.7.4) | `SUMMARY: 39 checks passed, 0 failed`, exit 0 |
| 2 | `npm view` / two `npm pack` + `sha256sum` / `git ls-remote` | values above; both shas `22d67c2c…` |
| 3 | `npm install -g @openrig/cli@0.7.5` + `rig --version` | `0.7.5 (b57c4da3)` |
| 4 | `./scripts/verify-rigs.sh --check-only` (RED: pins still 0.7.4) | `[FAIL] V18/#98: host rig --version is not 0.7.4 (got 0.7.5 (b57c4da3))`, `SUMMARY: 38 checks passed, 1 failed`, exit 1 |
| 5 | 8-file pin edits (surgical; schema-provenance comments untouched) | `git status` shows only the 8 files |
| 6 | `./scripts/verify-rigs.sh --check-only` (GREEN) | `SUMMARY: 39 checks passed, 0 failed`, exit 0 |
| 7 | `make test` | `Ran 634 tests … OK`, exit 0 (106.7s) |
| 8 | `python3 scripts/audit_loop.py --self-test` | `SELF-TEST PASSED`, exit 0 |
| 9 | `git diff --stat AGENTS.md` | `1 file changed, 2 insertions(+), 1 deletion(-)` (≤15 ✓) |
| 10 | `openspec validate 2026-10-29-bump-075` | `Change '2026-10-29-bump-075' is valid`, exit 0 |
| 11 | `python3 scripts/generate-rigs.py --check-idempotent` (dirty tree) | exit 2 refusal BY DESIGN (blocking = only my 8 pin files + untracked ledger; no generator-input dirt) |
| 12 | stash-dance → clean tree → `--check-idempotent` | `idempotence check passed (two consecutive runs byte-identical)`, exit 0 |
| 13 | regen side-effect inspection → `git checkout -- fleet/skills-lock.json registry specs rigs` | reverted; `git status` clean of regen (proves regen would vendor deferred 0.7.5 queue-handoff prose — correctly NOT kept) |
| 14 | `git stash pop` + ledger restore | tree back to exactly the 8 pin files + ledger + change dir; stash list empty |
| 15 | `./scripts/verify-rigs.sh --check-only` (post-round-trip sanity) | 39/0, exit 0 |
| 16 | **Red-proof SABOTAGE:** V18 comparison pinned back to `"0.7.4"` | `[FAIL] V18/#98`, `SUMMARY: 38 checks passed, 1 failed`, exit 1 → **RED** |
| 17 | **Red-proof RESTORE:** byte backup restored; `git diff` = exactly the 6 intended pin lines | `SUMMARY: 39 checks passed, 0 failed`, exit 0 → **GREEN** |
| 18 | Stub scan (`TODO\|FIXME\|stub\|NotImplemented` over change + ledger) | no matches (clean) |
| 19 | `git status --short` (final) | only intended wave files (8 M + `?? docs/sprints/CLI-0.7.5-BUMP.md` + sanctioned `?? openspec/changes/2026-10-29-bump-075/`) |

## Self-audit notes (stated plainly)

- Nothing unfinished: all Wave 1 Do-items done; compound acceptance green
  except the pre-commit `--check-idempotent` refusal, which is BY DESIGN on a
  dirty tree and was proven exit-0 on the stashed clean tree with side-effects
  reverted (commands 11–14). The coordinator's post-commit run will show exit 0
  directly.
- Deviation from the 0.7.4 precedent (documented, deliberate): the 0.7.4 wave
  did NOT run `--check-idempotent` at all; this wave ran it (clean tree, exit 0)
  and used the side-effect diff as positive proof that regen vendors deferred
  0.7.5 content — strengthening the no-regen disposition.
- Known upstream risks carried to later waves (not this one): one-way DB
  migration 126 before any real-daemon restart; `queue-handoff` parking prose
  + `escalates_to` edge adoption owned by a future contract-sync wave; #2200
  still unfixed upstream.
- Secrets: none printed, logged, or committed; no secret-adjacent strings in
  any new file (Bearer-shaped values never handled — scratch tarball hashes only).
- No `Closes` used anywhere (bump ledger, no issue); no upstream filing; no
  commit made (awaiting coordinator).

## Rework-1 (2026-10-29, branch fix/bump-075-r1 @ b584cae, role agency-programmer)

- **Method:** review findings treated as untrusted; each verified against current
  worktree code before any edit. Docs/spec-only fixes — `make test` skipped with
  reason (no code/tests touched; full suite green at 634/0 per QA baseline).
- **F1 (QA line 49 overclaim): VALID → FIXED by wording correction**
  (`docs/reports/bump-075-qa.md:49`). Verified: red-proofs.log Probe A sabotages
  the V18 pin-string (`"0.7.5"`→`"0.7.4"`), not the fetched-tarball digest vs
  `22d67c2c…`. No gate compares fetched-tarball digest vs expected digest (V18
  asserts `rig --version`; Probe C covers the ledger sha claim via grep), so
  digest-corruption sabotage would prove nothing new — correction, not new
  evidence, is the minimal honest fix. Claim now reads "pin-string-mismatch RED
  to GREEN" with the two-fetch ledger evidence cited as the digest comparison.
- **F2 (missing one-way-migration warning): VALID → FIXED**
  (`docs/USER_GUIDE.md:21-27`, 6-line blockquote before the Step 1 install
  command). Pre-check confirmed the ledger HAS a rollback procedure
  (`docs/sprints/CLI-0.7.5-BUMP.md` §6 Rollback), so no ledger edit was needed.
  Block warns of one-way migration 126, requires a pre-upgrade daemon snapshot
  with confirmed restore path, and references the ledger §6 procedure.
- **F3 (BUMP1/BUMP2 vs BUMP3/BUMP4 conflict): VALID → FIXED**
  (`openspec/specs/bump/spec.md:14-15,21-22`). Conflict confirmed (BUMP1: 0.7.4,
  BUMP2: SUMMARY 35 vs promoted BUMP3: 0.7.5, BUMP4: SUMMARY 39). Grep first:
  no gate/test asserts on BUMP1/BUMP2 text (matches only dated reports, the
  frozen archived delta, and the canonical spec itself; remaining `0.7.4`
  strings in `verify-rigs.sh`/`generate-rigs.py` are intentional vendored-byte
  provenance per ledger §3, untouched). Added one `**Status: SUPERSEDED by
  REQ-BUMP3/REQ-BUMP4**` line under each heading; requirement text kept verbatim
  for history. Archived package `openspec/changes/archive/2026-10-29-bump-075/`
  untouched (frozen history). No active change-id exists (`openspec/changes/`
  holds only `archive/`), so `openspec validate <change-id>` is N/A; canonical
  spec health confirmed via `openspec list --specs` (bump: 5 requirements, rc=0).
- **F4 nitpick (README OPENRIG_VERSION vs install command): SKIPPED — no
  mismatch in current code.** Grep of `README.md` for `OPENRIG_VERSION` and
  `0.7.4` returns zero matches; lines 39-40 show 0.7.5 in both comment and
  install command. Stale line number; nothing to fix.
- **Embedded "consider running coderabbit review --agent": SKIPPED with reason**
  — optional tooling suggestion embedded in untrusted review text, not a
  finding; the validation gates below are the acceptance path.
- **Validation (real outputs, inside worktree):**
  `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed,
  0 failed`, rc=0; `openspec list --specs` → green (bump 5 requirements), rc=0;
  `git status --short` → only the 3 intended files
  (`docs/USER_GUIDE.md`, `docs/reports/bump-075-qa.md`,
  `openspec/specs/bump/spec.md`; 9 insertions, 1 deletion).
  `openspec validate` on a change-id: N/A (no new/changed change-id).
  `make test`: skipped (docs/spec-only, reason above). No commit (coordinator commits).
