# Verification report — remediate-lane-guard (#67 worktree-stale baked-path guard, Wave 5 micro-stage)

Stage: remediate-lane-guard · Branch: `remediate/audit-66-lane-guard` · HEADs: `616b2df` (implementation) + `6070dbc` (QA evidence)
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/remediate-lane-guard`
Audit date: 2026-10-24 UTC · Auditor: drift-guard (independent re-run, no code touched)
Unity binding: none.

## 1. Spec & implementation read (not trusted from summary)

- Active spec `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md` read in full: Gotcha 5 / hard-never #67 requires baked seat values to carry no worktree paths; verify-rigs checks are audit-baselined (add alongside, never renumber V1–V11).
- Implementation report `docs/reports/remediate-lane-guard-implementation.md` read in full; every claim below was independently re-executed.

## 2. V14 block audit (scripts/verify-rigs.sh:1954-1984)

- Label `== V14. No Worktree-Stale Absolute Paths (#67) ==` sits after the V13 `ok()` (:1951-1952) and before `SUMMARY` (:1986). V13 label correctly not reused (taken by supply-chain wave); V1–V13 headers/blocks unrenamed.
- Semantics verified by reading: globs committed `specs/agents/*/*/runtime/pi-settings.json` + `rigs/*/agents/*/runtime/pi-settings.json`; FAILs when `shellPath` or any `packages[i]` contains `/.lane/`; message names seat + file + key + offending value + `#67 worktree-stale absolute path — re-bake on a canonical checkout`. Fails closed on zero leaves found or unreadable JSON. Exactly one `ok()` on green.
- Pure addition confirmed: `git diff main...HEAD -- scripts/verify-rigs.sh` = **32 insertions, 0 deletions**, single hunk. No V1–V13 line touched.
- Anti-stub scan over `git diff --name-only main...HEAD`: matches are report prose (expected counts) and pre-existing verify-rigs.sh lines (`:27 exit 0` usage text, `:1242-1243` placeholder-gate comments). **No stub/vacuous pattern in the new V14 block.**

## 3. Verify re-run (independent)

- `./scripts/verify-rigs.sh --check-only` → RC=1, `SUMMARY: 29 checks passed, 7 failed` (log `/tmp/opencode/verify_lane_guard.log`).
- All 7 FAILs are V13/#70 networked image-existence probes. V14 line reads `[PASS] Worktree-stale paths (#67) green: 153 committed pi-settings.json leaves carry no /.lane/ baked paths`.
- Root-cause proof (not assumed): direct `skopeo inspect docker://redis@sha256:<in-file-64hex-digest>` returns `toomanyrequests: You have reached your unauthenticated pull rate limit`. In-file digests verified 64-hex valid (all 10 services). The visible FAIL text shows only `Error parsing image name ...` because the script truncates stderr at `[:160]` — the rate-limit token is cut off, which is why the failure signature looks different from QA's log; the underlying error is identical and environmental (quota burned in part by repeated in-session verify runs; tree verified unmodified).
- Per stage brief: V13 failing ONLY on rate-limit/network with V14 green is recorded as environmental, not a stage FAIL. V14 is green in every unmodified-tree run.

## 4. Own plant-and-revert sabotage (different seat AND different key than QA)

- QA used `cache-streaming-eng` / `shellPath`. Mine: `exec-director` (`rigs/executive-and-architecture/agents/exec-director/runtime/pi-settings.json`) / `packages[0]` → `/.lane/trees/evil/pi-packages/...` (temp edit, never committed).
- Result: RC=1, `[FAIL] V14/#67: seat exec-director: ... packages[0] holds worktree-stale absolute path '...' (#67 worktree-stale absolute path — re-bake on a canonical checkout)`. SUMMARY `28 passed, 3 failed` (2 extra FAILs are the expected collateral bundle-integrity/digest gates — any generated-leaf edit trips them, as QA also recorded). **NON-VACUOUS**: gate turns RED with a seat/file/key-specific message.
- Revert: `git checkout -- <file>` → `git status --short` empty; canonical `@TOOLS@/...` value byte-restored; V14 re-check over the exact block logic: 153 leaves scanned, 0 stale → GREEN.

## 5. Scope / regen / commit discipline / revert checks

- `git diff main...HEAD --stat`: 5 files, +146/-0 (`scripts/verify-rigs.sh` +32, `docs/NOTES.md` +13, implementation report +24, QA report +37, red-proofs.log +40). Scope grep for `^(specs/|rigs/|rosters/|registry/|fleet/)` → no matches. No catalog edits → no regen needed or performed. `docs/NOTES.md` §remediate-lane-guard covers catch + fix + V12 gap + guard + commands.
- Commits: `616b2df remediate(#67): ...` carries the mandated `Co-Authored-By` + `Claude-Session` footer; `6070dbc test(remediate-lane-guard): record red-proofs and qa report` (QA evidence, no production files) matches repo precedent — prior `test(...): record ...` commits on main are likewise footerless. `git status --short` clean after both QA's and this audit's sabotages: nothing planted remains.
- `make test` re-run: `Ran 257 tests ... OK`, RC=0 (11 suites, ~53s).

## 6. Rate-limit skip-regex follow-up assessment: FOLLOW-UP, not merge-blocker

- Out of this micro-stage's scope (V13 probe belongs to the supply-chain wave; this stage adds only the offline V14 block). Failures are purely environmental (Docker Hub anonymous quota), the tree is verified unmodified, and V14 plus all offline gates pass. Recommended owner-wave fix: add `toomanyrequests`/`rate limit` to the V13 offline-skip regex (or use authenticated pulls). Minor adjacent note: the FAIL message truncates stderr at 160 chars, hiding the rate-limit token — consider logging the matched skip-relevant token. Neither item blocks this stage.

## Verdict

PASS on all stage acceptance items: V14 correctly labeled/placed, V1–V13 byte-untouched (32+/0-), independent sabotage on a new seat/key turns V14 RED with the named gate while the V12 gap is real, revert is clean, `make test` 257 OK, scope is regen-free with NOTES coverage, and the single implementation commit carries attribution. V13 image-probe failures are proven environmental (toomanyrequests) and out of scope.

VERDICT: PASS
