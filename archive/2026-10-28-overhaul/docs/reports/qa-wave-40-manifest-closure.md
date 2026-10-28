# QA report — wave-40-manifest-closure (issue #40)

Stage: `wave-40-manifest-closure` · Branch: `remediate/40-manifest-closure`
Change: `remediate-40-manifest-closure` · Commit under test: `9eb5171`
Date: 2026-10-22 (UTC) · Verdict: **QA-CLEAN** (1 advisory, no findings)

## 1. Checks run (exact commands, worktree root, unmodified tree)

| # | Command | Result |
|---|---------|--------|
| 1 | `make verify` | PASS — `SUMMARY: 24 checks passed, 0 failed.`, exit 0; V8 present; live-health advisories only (heartbeat WARNs, same as baseline) |
| 2 | `make test` | PASS — `Ran 59 tests / OK`, exit 0 |
| 3 | `python3 -m unittest tests/test_manifest_closure.py` | PASS — `Ran 17 tests / OK`, exit 0 |
| 4 | `openspec validate remediate-40-manifest-closure` | PASS — valid, exit 0 |
| 5 | `make manifest-closure` (empty stage) | PASS — `no staged manifests; zero undeclared.`, exit 0 |
| 6 | T5 re-run: lint over the 7 live mission files (read-only) | PASS — `42 entry point(s) checked; zero undeclared.`, exit 0 (reproduces claim exactly) |
| 7 | `git diff d863df0..HEAD` review (Makefile, verify-rigs.sh, allowlist) | PASS — additive only (details §3) |

V1–V7 behavior-identical: the verify-rigs.sh diff is a pure 33-line V8 append
(zero removed/modified lines); Makefile diff is +5/−1 where the single modified
line is the `.PHONY` token addition. The `SUMMARY 24/0` line is the only
output-shape change, which is the mandated new gate itself.

## 2. Red-proof results (all 7 sabotage steps per check; full log in `docs/evidence/wave-40-manifest-closure/red-proofs.log`)

| Probe | Sabotage | Check run | RED? | Restored clean? |
|-------|----------|-----------|------|-----------------|
| (a1) types:node w/o @types/node | fixture omits dep | lint exit 1, names `@types/node` + tsconfig | YES | n/a (synthetic /tmp) |
| (a2) bare eslint/prettier w/o dep | fixture omits deps | lint exit 1, names `eslint` + `prettier` | YES | n/a |
| (a3) vitest w/o dep | fixture omits dep | lint exit 1, names `vitest` | YES | n/a |
| (a4) JSX w/o @types/react | fixture omits dep | lint exit 0 (**contractual** — T4/REQ-C5/design.md require PASS); `tsc --noEmit` on equivalent fixture exit 1 with TS7026+TS2875 | COVERED (see §4) | n/a |
| (b) fixed pins | none (control) | lint exit 0, no false positives | GREEN (control) | n/a |
| (c) one-shots | `pnpm dlx cowsay hi` / `npx serve` | exit 1, names package/binary | YES ×2 | n/a |
| (d) recursion | remove eslint behind `pnpm check` indirection | exit 1, names `eslint` via `check (lint)` chain — recursion load-bearing | YES | n/a |
| (d) cycle | `a→pnpm b→pnpm a` | exit 1, names `INDIRECTION CYCLE` | YES | n/a |
| (e) allowlist | `curl`/`docker` scripts | exit 1, names both | YES | n/a |
| (e) allowlist control | `git`/`node`/`rig` scripts | exit 0 | GREEN (control) | n/a |
| (f) malformed pkg/tsconfig | invalid JSON | exit 1, names file (`UNREADABLE MANIFEST`) | YES ×2 | n/a |
| (g) alias | removed `"tsc":"typescript"` from BIN_ALIASES (in-tree) | g-alias fixture exit 1 naming `tsc` | YES | YES (`git checkout`, status clean, re-run exit 0) |
| (h) unit suite | renamed vitest dep in test fixtures (in-tree) | `FAILED (failures=2, errors=1)`, exit 1 | YES | YES (`git checkout`, status clean, 17 OK) |
| V8 --staged half | staged bad `package.json` in index | `--staged` exit 1 naming binary | YES | YES (unstaged + deleted, status clean) |
| tokenizer | `echo "lock round-trips; ok" 2>&1` shape | exit 0, no false positive | GREEN (control) | n/a |
| allowlist file | missing / empty allowlist | exit 2, `MISSING ALLOWLIST`, no default-allow | YES ×2 | n/a |

Restore proof: after every in-tree sabotage, `git status --short` was empty and the
check re-ran green. Final `git status --short` shows only the two intended new paths
(`docs/evidence/wave-40-manifest-closure/`, this report).

## 3. Makefile / allowlist / deviation review

- **Makefile**: one additive target + one `.PHONY` token; no existing target touched; non-masking (`manifest-closure` is a new name). PASS.
- **Allowlist** (`fleet/allowed-system-tools.txt`, 8 entries): every entry grounded —
  node/npm/pnpm/yarn (workflow pins NODE 22 / PNPM 9, `pnpm install --frozen-lockfile`),
  git (VCS seam), cargo (`cargo fetch --locked` / `fmt` steps, Cargo.toml on disk),
  echo (POSIX shell builtin), rig (REQ-C2(d) operator CLI). `curl`/`docker` correctly
  absent and proven to fail. PASS.
- **24-vs-23**: tasks.md T3 and REQ-C4 mandate the additive gate; design.md anticipated
  the count bump. 24/0 with byte-identical V1–V7 is the legitimate reading; the brief's
  "23/0" is the stale no-regression baseline. DEVIATION LEGITIMATE — no finding.

## 4. The (a4) question, answered independently

I determined it myself rather than taking the report's word: the spec as written does
**not** demand the lint catch JSX-without-@types/react. REQ-C2's fail-named scenario
enumerates only vitest / eslint-prettier / @types/node omissions; REQ-C5 covers
`types`-array entries and explicitly leaves ambient-JSX to the `tsc` gate; design.md
and tasks.md T4 **require** the lint to pass instance #2 ("expected to PASS the lint
... MUST instead fail the `tsc` typecheck gate"). The implementation matches the
contract, and I independently verified the covering gate: a no-`@types/react` JSX
fixture fails `tsc --noEmit` with TS7026 + TS2875 (the issue's TS7016/7026 class).
If the intent had been "lint must catch it," that would be a spec bug, not an
implementation bug — as written: PASS, no finding.

## 5. Live-mission honesty (T5)

- Re-ran the lint read-only against all 7 live mission files: exit 0, zero undeclared,
  `42 entry point(s)` — exact match to the implementation report.
- Mission repo never written: `git status --short` before/after identical, still zero
  commits by design, no new files, empty stash. The only files created by this QA are
  `/tmp/qa40-red/*` (scratch) and the two evidence/report paths below.

## 6. Findings

- No FAILs. No vacuous checks (every check turned RED under sabotage except the two
  contractual greens, both justified above).
- Advisory (non-blocking): worktree `AGENTS.md` still says "expect: 23 checks passed"
  and "23 checks are audit-baselined." Post-stage the true count is 24. Updating that
  doc was out of the stage's touch-only scope, so it is correctly left stale here, but
  a follow-up should refresh the two numbers to avoid operator confusion.

## 7. Verdict

**QA-CLEAN** — ship it. Do NOT commit (per work order; report + logs left uncommitted).

Paths:
- Evidence: `docs/evidence/wave-40-manifest-closure/red-proofs.log`
- Report: `docs/reports/qa-wave-40-manifest-closure.md`

---

## 8. Re-verification of review-fix commit `65035a1` (2026-10-22 UTC, second pass)

Stage: `wave-40-review-reverify` · Commit under test: `65035a1`
(`fix(40-manifest-closure): address PR review - extends types, ownership, tokenizer,
run-strip, JSONC, staged context, unreadable test` on top of `0ae18c5/d4a55ef/9eb5171`;
`git log --oneline -4` confirmed). Original §§1–7 above left intact.
Verdict for this pass: **QA-CLEAN** (1 observation, 1 carried advisory, no findings).

### 8.1 Checks run (exact commands, worktree root, unmodified tree first)

| # | Command | Result |
|---|---------|--------|
| 1 | `make test` | PASS — `Ran 59 tests / OK`, exit 0 |
| 2 | `make verify` | PASS — `SUMMARY: 24 checks passed, 0 failed.`, exit 0; V8 present; live-health advisories only (heartbeat WARNs + seat-idleness SKIP, same as prior baseline) |
| 3 | `openspec validate remediate-40-manifest-closure` | PASS — valid, exit 0 |
| 4 | `python3 -m unittest tests/test_manifest_closure.py` | PASS — `Ran 28 tests / OK` (17 → 28 via the 11 new review-driven tests), exit 0 |

### 8.2 Red-proof results (per new behavior; full log appended to `docs/evidence/wave-40-manifest-closure/red-proofs.log` R15–R21)

| Item | Sabotage | RED? | Restored clean? |
|------|----------|------|-----------------|
| (a) extends types | nested `merged_types` read back under `if merged_doc is None:` (first-doc-only revert) → base fixture flips exit 1 → exit 0 (PASS) | YES | YES (`git checkout`, status clean, base fires again) |
| (a) leaf-wins control | none — leaf `{types:["node"]}` + `@types/node`, base mystery entry → exit 0 | GREEN (control) | n/a |
| (b) ownership | restored `reversed(Path(path).parents)` → false `UNDECLARED TYPES ENTRY '@types/inner-lib'` attributed to `root`, exit 1; unit test FAILs | YES | YES (status clean, exit 0 again) |
| (c) tokenizer | deleted backslash-newline join → `cmd arg \\\nmore` splits to `['cmd arg \\', 'more']`; 2 unit tests FAIL | YES | YES (status clean, both OK) |
| (d) run-strip | restored pre-fix raw-args `run` strip → go-only fixture flips exit 1 → exit 0 (must NOT fire); committed fixture loses `(script 'go')` chain finding | YES | YES (status clean, exit 1 + chain back) |
| (e) JSONC | `load_tsconfig_text` → `load_json_text` → commented tsconfig goes `UNREADABLE MANIFEST`, exit 1 (parse fails); unit test FAILs. Commented `package.json` control still `UNREADABLE` on clean tree (strict held) | YES | YES (status clean, types finding back) |
| (f) staged context | dropped `context_manifests` → workflow-context unit test FAILs; scratch repo `--staged` false-fires on child `eslint` (exit 1) | YES | YES (status clean, 3 staged tests OK, scratch `--staged` exit 0) |
| (f) context-only control | scratch repo: full-tree scan fires on committed root `leak` (exit 1); `--staged` with only clean child staged → exit 0 (root not finding-checked) | GREEN (control, as reasoned) | n/a (scratch `/tmp` repo) |
| (g) unreadable | removed `IsADirectoryError` branch **and** generic `OSError` fallback → raw `IsADirectoryError` escapes, unit test ERRORs. (Removing only the specific branch still passes via the `OSError` fallback — message-precision defense-in-depth, recorded honestly.) Old directory-discovery test shape grep → ABSENT | YES | YES (status clean, unit OK) |

### 8.3 Scope

`git show --stat 65035a1`: exactly two files — `scripts/manifest-closure.py`
(+130/−10), `tests/test_manifest_closure.py` (+324/−6). No `specs/` / `openspec/`
content change, no `registry/` / `fleet/` / `rigs/` / generated-dir drift in the fix
commit. Full-wave diff `d863df0..HEAD` remains additive-only.

### 8.4 Observation (advisory, not a finding)

The committed `test_pnpm_filter_run_recurses_into_script` asserts only exit≠0 +
names `secrettool` on a fixture where `build` is itself a staged script — that
assertion PASSES under both old and new run-strip logic (old code still fires via the
direct `build` entry point). The new behavior is proven load-bearing by this pass's
go-only exit-flip (R18) and the `(script 'go')` chain-attribution flip; a future
strengthening could assert the chain string or add a go-only fixture. Behavior
correct — test could be sharper.

### 8.5 Carried advisory (from §6, still open)

Worktree `AGENTS.md` still says "expect: 23 checks passed" / "23 checks are
audit-baselined" while post-stage truth is 24. Out of this stage's touch-only scope;
follow-up should refresh the two numbers.

### 8.6 Verdict

**QA-CLEAN** — the review fix is load-bearing on all seven behaviors, scope is clean
(two files, no drift), no vacuous checks. Do NOT commit (per work order; report + log
appended, uncommitted).

Paths:
- Evidence: `docs/evidence/wave-40-manifest-closure/red-proofs.log` (appendix R15–R21)
- Report: `docs/reports/qa-wave-40-manifest-closure.md` (§8, this section)
