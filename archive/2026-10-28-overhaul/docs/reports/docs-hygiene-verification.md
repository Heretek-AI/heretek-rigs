# docs-hygiene verification (scoped docs-only audit)

- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/docs-hygiene`
- Stage/wave id: `docs-hygiene-audit`
- Base: `50d39b0` (Merge PR #58)
- Commits under audit (confirmed via `git log --oneline -3`):
  - `a98a285 docs(hygiene): refresh live check-counts to 26, annotate runbook qitem placeholder`
  - `14b4bbc test(docs-hygiene): record verification log` (evidence commit on top)
  - `50d39b0` base below them
- Auditor re-ran everything below; nothing was fixed (auditor writes only this report, uncommitted).

## 1. Diff audit — file set is exactly 4 doc files + verify log

`git diff 50d39b0..HEAD --name-only` returns exactly:

1. `AGENTS.md` (2 insertions, 2 deletions — 2 lines changed)
2. `README.md` (1/1 — 1 line changed)
3. `docs/USER_GUIDE.md` (1/1 — 1 line changed)
4. `docs/ops/typed-external-block-runbook.md` (2/0 — 1 sentence added)
5. `docs/evidence/docs-hygiene/verify.log` (71/0 — new evidence log)

Forbidden-path check (`git diff 50d39b0..HEAD --name-only | grep -E '^(specs/|rigs/|rosters/|registry/|scripts/|fleet/|Makefile|makefile|GNUmakefile|scripts/verify-rigs.sh)'`): **no matches → FORBIDDEN_CLEAN**.
Zero changes under `specs/`, `rigs/`, `rosters/`, `registry/`, `scripts/`, `fleet/`, and zero to `Makefile`/`verify-rigs.sh`. Generators, schemas, gates, and build files are untouched, so this change **cannot alter runtime/verify behavior** by construction. `git status --short` in the worktree is clean (evidence log is committed as `14b4bbc`, not left as dirt).

Full per-file diff (from `git diff 50d39b0..HEAD`):

- `AGENTS.md:15`: `# expect: 23 checks passed` → `# expect: 26 checks passed` (number refresh only).
- `AGENTS.md:45`: `` `verify-rigs.sh`'s 23 checks are audit-baselined `` → `26 checks` (number refresh only; sentence otherwise byte-identical).
- `README.md:47`: `# 2. Verify the checkout (expect: 22 checks passed, 0 failed)` → `26 checks` (stale-count refresh; note README lagged at 22 while AGENTS.md was at 23 — both now 26).
- `docs/USER_GUIDE.md:127`: `` `SUMMARY: 22 checks passed, 0 failed.` `` → `26 checks` (same stale-count refresh).
- `docs/ops/typed-external-block-runbook.md:52`: added `(Paste \`<qitemId>\` as the full ID copied from \`rig queue list --json\` output — never retype it.)` (annotation only, 2+/0-).

## 2. Semantic check — no instruction changed meaning

- `AGENTS.md:45` before: "`verify-rigs.sh`'s 23 checks are audit-baselined: add new gates alongside (new script or new block), don't renumber/reword existing checks casually."
  After: identical with `26` substituted. The audit-baseline rule still says what it said (add alongside, don't renumber/reword). **Meaning preserved.**
- `AGENTS.md:15` is a shell-comment expectation, not an instruction; number-only change. **Meaning preserved.**
- `README.md` / `USER_GUIDE.md` edits are expected-output strings only. **Meaning preserved.**
- Runbook annotation does not introduce a new rule: it restates the existing `AGENTS.md:29` queue rule ("copy qitem IDs only from `--json` output — never retype; bare queue output … MUST NOT be parsed"). The added sentence is consistent with, and narrower than, the standing instruction. **No conflict, no meaning change.**
- Total: 5 textual edits across 4 doc files, all number refreshes or consistent annotations. No rule text changed meaning.

## 3. Count 26 is TRUE — independently re-run

Auditor ran `make verify` in the worktree (not trusting the log):

- `SUMMARY: 26 checks passed, 0 failed.` — matches the committed `docs/evidence/docs-hygiene/verify.log` SUMMARY line exactly.
- `live-health.py` advisory WARN/heartbeat section is exit-0 advisory only, same as the log.
- The committed `verify.log` additionally records a stale-count grep probe (`grep exit=1`, zero stale matches) and a red-proof probe on a `/tmp` copy (stale `22` string caught, `probe grep exit=0`), proving the check is non-vacuous without touching the worktree.

Count claim **26: TRUE**.

## 4. Secrets scan over the diff

`git diff 50d39b0..HEAD` grepped for `sk-|ghp_|github_pat|AKIA|aws_secret|BEGIN.*PRIVATE|password\s*=\s*[^ ]|api[_-]?key\s*[:=]` (case-insensitive): **no matches → SECRET_CLEAN**. The only key-like text in the diff context is the pre-existing dummy placeholder `<opencode-go-key>` in `README.md` (unchanged line context, not a real credential).

## 5. Ruling on the honest caveat (no automated guard for counts)

The branch honestly notes there is no automated guard pinning doc check-counts to `verify-rigs.sh` output, so counts can drift stale again. Ruling: **acceptable for a docs-only change → PASS, not a FAIL condition.** Rationale: (a) this change provably cannot alter behavior (forbidden-path clean, `make verify` green before and after); (b) wiring a new grep-test into `make test` would expand scope beyond the docs-hygiene brief and touch execution paths this branch deliberately avoids; (c) the evidence commit already demonstrates the guard shape (stale-count grep + red-proof probe) any future change can reuse. Recommendation (non-blocking): a future change that next edits `verify-rigs.sh` check counts may add a stale-count grep assertion to the test suite, but it is **not required** for this verdict.

## Binding verdict

No stubs, no behavior change, no secrets, count verified true, semantics preserved, evidence committed, worktree clean.

VERDICT: PASS
