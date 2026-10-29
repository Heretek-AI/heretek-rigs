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

## Rework-2 (2026-10-29-bump-075 REWORK-2, branch fix/bump-075-r2 @ 51757e4): unblock PR #135 CI — missing direct `referencing` dependency

- **Symptom (verified):** PR #135 CI job "Host verification gate"
  (`.github/workflows/docker-release.yml:54`) fails at
  `./scripts/verify-rigs.sh --check-only` with
  `ModuleNotFoundError: No module named 'referencing'`. The script imports it
  directly at `scripts/verify-rigs.sh:51`
  (`from referencing import Registry, Resource`), but the workflow installed
  only `pip install --quiet pyyaml jsonschema`
  (`.github/workflows/docker-release.yml:53`, pre-fix).
- **Root cause (verified, runner-image drift — NOT a Wave-1 regression):**
  `referencing` arrived only transitively via `jsonschema`. On current
  `ubuntu-24.04` runner images a pre-installed `jsonschema` satisfies the pip
  requirement, so `pip install` is a no-op and never pulls `referencing`,
  and the heredoc import fails. Local environment confirms the packaging
  side is unchanged: installed `jsonschema` is 4.26.0 and installed
  `referencing` is 0.37.0 (`pip show`, `importlib.metadata.version`).
  `git diff main...HEAD -- scripts/verify-rigs.sh` on this branch is V13/V18
  pin strings only (`0.7.4` → `0.7.5`, three hunks) — no dependency-shape
  change from Wave-1.
- **Main-also-fails evidence (verified via `gh`, not coordinator hearsay):**
  `gh run list --workflow docker-release.yml --branch main --limit 7` shows 7
  consecutive `failure` runs on unmodified main (incl. #124/#125/#126/#128/
  #131/#132/#133 merges). `gh run view 40822422518 --log-failed` (main merge
  of PR #133) shows the identical failure:
  `Run ./scripts/verify-rigs.sh --check-only` →
  `ModuleNotFoundError: No module named 'referencing'`.
- **Fix (2 lines, bare names matching existing style, no pins invented):**
  1. `.github/workflows/docker-release.yml:53`:
     `pip install --quiet pyyaml jsonschema` →
     `pip install --quiet pyyaml jsonschema referencing`
     (direct dependency declared directly — the one-line fix).
  2. `scripts/verify-rigs.sh:34` guard:
     `python3 -c "import yaml, jsonschema"` →
     `python3 -c "import yaml, jsonschema, referencing"`
     (one-word change; a missing dep now fails with the friendly guard path
     instead of a heredoc traceback). Guard is the pre-heredoc `RUNNER`
     preamble (lines 33-38); no V-gate text altered — confirmed zero `V[0-9]`
     matches below line 40 other than header comments (lines 5-15 are the
     `#`-comment docstring), and `git diff` shows exactly these 2 lines.
- **Validation (real outputs, inside worktree `.lane/trees/bump-075-r2`):**
  `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed,
  0 failed`, rc=0; `python3 -c "import yaml, jsonschema, referencing"` →
  rc=0; direct-import proof via
  `python3 -c "import importlib.metadata;
  print(importlib.metadata.version('referencing'))"` → `0.37.0`;
  `git status --short` → only the 2 intended files
  (`.github/workflows/docker-release.yml`, `scripts/verify-rigs.sh`) plus
  this report addendum; `git diff --stat` → 2 files, 2 insertions,
  2 deletions. `make test`: SKIPPED — change is one CI pip-line plus one
  guard word (docs/CI-only, no generator/runtime/catalog code touched);
  host suite baseline green at 634/0 per coordinator, unaffected.
- **Deviations / notes (explicit):**
  (a) The coordinator's suggested probe
  `python3 -c "import referencing; print(referencing.__version__)"` FAILS
  locally with `AttributeError: module 'referencing' has no attribute
  '__version__'` (rc=1) — the module exposes no `__version__`; version proven
  via `importlib.metadata` instead (0.37.0). The direct `from referencing
  import Registry, Resource` import itself resolves (rc=0, gate green).
  (b) The `uv` fallback on `scripts/verify-rigs.sh:36`
  (`uv run --quiet --with pyyaml --with jsonschema python3`) was deliberately
  left untouched per the minimal-diff constraint (one-word guard change
  only); it does not cover `referencing` if system python lacks it — flagged
  here as a known residual, not fixed. No commit/push/merge (per instructions).

## Rework-3 (2026-10-29-bump-075 REWORK-3, branch fix/bump-075-r3 @ 14f4ee8): unblock PR #135 CI — jsonschema>=4.18 floor for `registry=` kwarg

- **Symptom:** PR #135 CI fails (after rework-2 fixed the missing
  `referencing`) with
  `TypeError: create.<locals>.Validator.__init__() got an unexpected keyword
  argument 'registry'` at verify-rigs.sh's `Draft202012Validator(schema,
  registry=...)` calls.
- **Code facts (verified in-tree before editing):**
  `scripts/verify-rigs.sh:924`
  (`val = Draft202012Validator(schemas[schema_name], registry=registry)`)
  and `scripts/verify-rigs.sh:2380-2381`
  (`_val18 = Draft202012Validator(schemas["bundle-status.v1.schema.json"],
  registry=registry)`); `.github/workflows/docker-release.yml:53`
  (`pip install --quiet pyyaml jsonschema referencing`).
- **Mechanism proof (coordinator-reproduced, confirmed consistent locally):**
  the `registry=` kwarg requires jsonschema>=4.18 — coordinator reproduced
  the EXACT `TypeError` string in a scratch venv with jsonschema==4.17.3 +
  referencing installed, and proved the floor with jsonschema==4.18.6
  (construct OK). CI runners ship system jsonschema 4.17.x, so bare
  `pip install jsonschema` is a satisfied no-op and never upgrades. Same gate
  fails on unmodified main — environmental, not a Wave-1 regression. Local
  confirmation: installed jsonschema is 4.26.0 and
  `Draft202012Validator({}, registry=Registry())` constructs OK (rc=0).
- **Fix (floor only, no exact pins, bare-name style kept):**
  1. `.github/workflows/docker-release.yml:53`:
     `pip install --quiet pyyaml jsonschema referencing` →
     `pip install --quiet pyyaml "jsonschema>=4.18" referencing`
     (specifier quoted so YAML/shell pass it literally; `yaml.safe_load`
     re-parses rc=0).
  2. `scripts/verify-rigs.sh:40-43` (preamble, before the heredoc at :45,
     NOT in any V-gate block): 4-line fail-closed floor check via the
     effective `${RUNNER[@]}` interpreter — `importlib.metadata.version`
     major/minor tuple compared against (4,18); on <4.18 (or missing) prints
     `verify-rigs.sh requires jsonschema>=4.18 for
     Draft202012Validator(registry=...); upgrade with: pip install
     "jsonschema>=4.18" referencing` to stderr and exits 1. Uses
     `importlib.metadata` (not deprecated `jsonschema.__version__`) and
     `[0-9]+` regex (no backslash-escape fragility inside bash double
     quotes). No V-gate text/markers/counts touched — `git diff` shows zero
     `V[0-9]` matches.
- **Validation (real outputs, inside worktree `.lane/trees/bump-075-r3`):**
  `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed,
  0 failed`, rc=0; `python3 -c "import yaml;
  yaml.safe_load(open('.github/workflows/docker-release.yml'))"` → `YAML OK`,
  rc=0; `bash -n scripts/verify-rigs.sh` → syntax OK; isolated floor probe
  (comparison exercised against fake tuples, tree untouched): `4.17.3` →
  reject, `4.18.0` → accept, `4.26.0` → accept; `git status --short` → only
  the 2 intended files plus this report addendum; `git diff --stat` → 2
  files, 6 insertions, 1 deletion. `make test`: SKIPPED — change is one CI
  pip-line plus a preamble-only floor check (no generator/runtime/catalog/
  V-gate code touched); 634/0 baseline stands per instructions.
- **Deviations / notes (explicit):** none — no other files touched, no exact
  pins introduced, no V-gate edits. No commit/push/merge (per instructions).

## Rework-4 (2026-10-29-bump-075 REWORK-4, branch fix/bump-075-r4 @ bea4d16): unblock PR #135 CI — bubblewrap install before verify-fleet gate

- **Mandate note:** the plan's 3-cycle rework budget was spent, but the user
  explicitly authorized continued fixes until PR #135 CI passes — this
  Rework-4 proceeds under that mandate.
- **Symptom:** PR #135 CI "Host verification gate" reaches
  `SUMMARY: 38 checks passed, 1 failed` with
  `[FAIL] tool-existence: bwrap not found on PATH`. All V22–V27 green — the
  jsonschema layers are fixed; this is the next latent environmental layer.
- **Code facts (verified in-tree before editing):**
  `scripts/verify-rigs.sh:1707-1711`
  (`if _shutil12.which("bwrap") is None:` → note-mode only when
  `HERETEK_ALLOW_NO_BWRAP=1`, else
  `fail("tool-existence: bwrap not found on PATH ...")` — fail-closed);
  `scripts/verify-rigs.sh:3032-3034`
  (`_vf27_steps = [...get("run","")...verify-fleet...steps...]` +
  `if not any("bubblewrap" in _s27 for _s27 in _vf27_steps)` — V27 asserts
  only that SOME verify-fleet step contains "bubblewrap", order-independent)
  plus the UniqueKey YAML parse at :3017-3026.
- **Mechanism:** `.github/workflows/docker-release.yml` installed bubblewrap
  via apt-get in a step AFTER `./scripts/verify-rigs.sh --check-only`, while
  fresh runners have no system bwrap → verify always fails. Pre-existing
  workflow ordering drift, NOT a Wave-1 regression (our wave never touched
  bwrap/tool-existence).
- **Fix (pure reorder, zero new content):**
  `.github/workflows/docker-release.yml` verify-fleet job: moved the
  `sudo apt-get update && sudo apt-get install -y --no-install-recommends
  bubblewrap && bwrap --version` step to BEFORE the
  `./scripts/verify-rigs.sh --check-only` step (directly after the pip-install
  step). Deliberately did NOT use `HERETEK_ALLOW_NO_BWRAP=1` note-mode in CI
  (that would weaken the gate; CI can apt-get, so verify-for-real is
  correct). Nothing else touched.
- **Validation (real outputs, inside worktree `.lane/trees/bump-075-r4`):**
  `python3 -c "import yaml; ..."` →
  `['uses', 'pip install --quiet pyyaml "jsonschema>=4.18" referencing',
  'sudo apt-get update && sudo apt-get install -y --no-install-', './scripts/verify-rigs.sh --check-only',
  'python3 ./scripts/audit_loop.py --self-test', 'if make guard-profiles ...']`
  (apt-get before verify, proven); host bwrap present:
  `/usr/bin/bwrap`, `bubblewrap 0.13.1`;
  `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 39 checks passed,
  0 failed`, rc=0; `git status --short` → only the workflow file plus this
  report addendum; `git diff --stat` → 1 file, 1 insertion, 1 deletion
  (moved block). `make test`: SKIPPED — workflow-order-only change (no
  generator/runtime/catalog/V-gate code touched); 634/0 baseline stands per
  instructions.
- **Deviations / notes (explicit):** none — reorder only, no new steps, no
  pins, no V-gate edits. No commit/push/merge (per instructions).

## Rework-5 (2026-10-29-bump-075 REWORK-5, branch fix/bump-075-r5 @ 1f23bf2): unblock PR #135 CI — lowercase ghcr.io image name

- **Mandate note:** the plan's 3-cycle rework budget was spent, but the user
  explicitly authorized continued fixes until PR #135 CI passes — this
  Rework-5 proceeds under that standing mandate.
- **Symptom:** PR #135 CI "Host verification gate" now PASSES (1m24s). New
  failure: Build slim/full fail with `invalid tag
  "ghcr.io/Heretek-AI/heretek-rigs:latest": repository name must be
  lowercase`. Fourth latent environmental layer (build never ran before
  because verify-fleet gates it and verify never passed on these runners
  until this wave fixed it). Pre-existing, NOT a Wave-1 regression (our wave
  never touched image naming).
- **Code facts (verified in-tree before editing):**
  `.github/workflows/docker-release.yml:45`
  (`IMAGE_NAME: ${{ github.repository }}` = `Heretek-AI/heretek-rigs`,
  uppercase, consumed by build tags lines 91-92 and attest subject-name line
  100) and `:114`
  (`image: ghcr.io/${{ github.repository }}:sha-...`); repo-wide grep for
  `IMAGE_NAME|github.repository` hits only the workflow file plus generated
  skill-reference docs (no gates); `scripts/`, `Makefile`, `tests/`,
  `docker/` contain no assertion on IMAGE_NAME values;
  `scripts/verify-rigs.sh:3028-3036` (V27 asserts only bubblewrap-string +
  UniqueKey parse + smoke `container`-is-dict — type-based, unaffected by the
  image string). A GITHUB_ENV-lowercasing step CANNOT fix line 114
  (`container.image` resolves before steps run), so lowercase literals are
  the correct minimal fix.
- **Fix (2 literals, zero logic change):**
  `.github/workflows/docker-release.yml:45` →
  `IMAGE_NAME: heretek-ai/heretek-rigs # ghcr.io requires lowercase
  repository names` (keeps the file's trailing-comment style); `:114` →
  `image: ghcr.io/heretek-ai/heretek-rigs:sha-${{ github.sha }}${{
  matrix.target == 'full' && '-full' || '' }}` (same tag template, only the
  repository path lowercased). Nothing else touched.
- **Validation (real outputs, inside worktree `.lane/trees/bump-075-r5`):**
  `python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/docker-release.yml')); print(d['env']['IMAGE_NAME']); print(d['jobs']['smoke']['container']['image'])"` →
  `heretek-ai/heretek-rigs` /
  `ghcr.io/heretek-ai/heretek-rigs:sha-${{ github.sha }}${{ matrix.target == 'full' && '-full' || '' }}`
  (both lowercase); UniqueKey-style safe_load re-parse → rc=0, smoke
  container is dict True; `./scripts/verify-rigs.sh --check-only` →
  `SUMMARY: 39 checks passed, 0 failed`, rc=0; `git status --short` → only
  the workflow file plus this report addendum; `git diff --stat` → 1 file, 2
  insertions, 2 deletions. `make test`: SKIPPED — workflow-literal-only
  change (no generator/runtime/catalog/V-gate code touched); 634/0 baseline
  stands per instructions.
- **Deviations / notes (explicit):** none — two literals only, no V-gate
  edits, no pins. No commit/push/merge (per instructions).
