# overhaul-bump rework report — cycle 1 of 3 (post-PASS review findings)

- **Stage/wave id:** overhaul-bump rework cycle 1 (review findings F1–F3)
- **Worktree:** `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/overhaul-bump` (branch `feat/overhaul-bump`)
- **Date (UTC):** 2026-10-27
- **Rule compliance:** finding text treated as UNTRUSTED — each verified against current code before acting. No V1–V24 renumber (zero `== V` header lines touched), SUMMARY frozen, one-rule upheld (no `specs/`/`rigs/`/`rosters/`/`registry/` edits), no secrets touched, nothing committed (left dirty for coordinator commit).

## Per-finding verdict

### F1 — REQ-BUMP2 HOLD basis (empty leaf diff vs `--check-idempotent`): VALID → fixed by spec narrowing (no code, no live run)

- **Verified the cited claims:** verification report line 23 does rest HOLD on the deliberately-skipped `--check-idempotent` run; implementation report §6.2 + spec `REQ-BUMP2` (`openspec/changes/overhaul-bump/specs/bump/spec.md:12`) require the check to pass.
- **Resolver code-path decision (no worktree mutation):** `scripts/generate-rigs.py:1999` defaults `--openrig-core` to `resolve_default_openrig_core()` (`generate-rigs.py:623-643`), which inserts the npm-global install path at `candidates[0]` and returns the first existing entry; `--root` defaults to the repo root (`generate-rigs.py:2004`); `--check-idempotent` calls `generate_all()` **into `--root`** (`generate-rigs.py:2044-2051`), and `generate_all()` copies `openrig_core` skill bodies into `specs/agents/_shared/` + rewrites `fleet/skills-lock.json` (`generate-rigs.py:1129-1231`). A run on this worktree would therefore rewrite generated leaves with 0.7.4 bytes → Wave B vendoring. Per finding orders it was NOT run on the worktree.
- **Empirical corroboration (read-only):** live resolver output `RESOLVED_CORE: /home/john/.npm-global/lib/node_modules/@openrig/cli/daemon/assets/plugins/openrig-core/skills` (installed 0.7.4), while `OPENRIG_VERSION` in the generator is still `0.7.2` (`generate-rigs.py:60`); `diff -q` proves the tree's vendored `specs/agents/_shared/skills/messaging-the-human/SKILL.md` and `queue-handoff/SKILL.md` **differ** from the installed 0.7.4 copies — pass 1 would rewrite them. Claim proven without mutating the tree.
- **Fix:** `spec.md:12` now carries the deferral parenthetical (`idempotence-with-0.7.4-vendor deferred to Wave B … this wave holds by empty leaf diff`, citing `generate-rigs.py:623-643`); scenario `spec.md:15` updated to match. Recorded as **HOLD-with-deferral**.
- **tasks.md:** no idempotence acceptance line exists there (only T2 verify+self-test, M1 rig+verify), so no F1-driven tasks.md change was owed — nothing to update.

### F2 — `tasks.md:14` literal `AND`: VALID → fixed (one-line doc fix)

- **Verified:** line 14 read `./scripts/verify-rigs.sh --check-only AND python3 scripts/audit_loop.py --self-test` — not runnable as written. Fixed to `&&`.
- **Same-pattern sweep:** `grep AND` over `openspec/changes/overhaul-bump/` (proposal.md + tasks.md) finds no other literal-`AND` acceptance joins. No other changes' files touched (102-closeout, 107-identity explicitly out of scope).
- **Proof the fixed command runs:** `./scripts/verify-rigs.sh --check-only && python3 scripts/audit_loop.py --self-test` executed end-to-end → `SUMMARY: 35 checks passed, 0 failed` + `SELF-TEST PASSED`, exit 0.

### F3 — V18 `installed 0.7.4` claim without host version check: VALID → fixed (minimal fail-closed gate)

- **Verified the claim lines:** `scripts/verify-rigs.sh:2388-2392` (`which("rig")`; absent → NOTE only) and `:2461-2464` ok-message `… clean on installed 0.7.4` — reached on **both** paths, so (a) a wrong-version host still printed the 0.7.4 claim, (b) a rig-less host printed NOTE *and* the 0.7.4 claim.
- **RED (before fix, unmodified script):**
  - Wrong-version shim (`rig --version` → `0.7.2 (8b180689)`, all other verbs delegate to the real binary): exit 0, `SUMMARY: 35 checks passed, 0 failed`, PASS line claimed `clean on installed 0.7.4` — false claim, no trip. Bug reproduced.
  - Rig absent (`PATH=/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin`, `which rig` → not found): exit 0 with NOTE *plus* the same false `installed 0.7.4` PASS claim. Bug reproduced.
- **Fix (GREEN, minimal):** version probe at the top of the rig-present branch (`scripts/verify-rigs.sh:2394-2411`) — runs `rig --version`, regex-extracts `\d+\.\d+\.\d+`, `fail("V18/#98: host rig --version is not 0.7.4 …")` on nonzero rc / unparseable / mismatch (fail-closed, incl. exception → `unreadable`). ok-message split: rig-present branch keeps the original string **byte-identical**; rig-absent branch now prints `… native-verb validation skipped (no rig on PATH)` with no installed-version claim. Exactly one `ok()` executes per run (SUMMARY count frozen); zero `== V` header lines touched; all pre-existing V18 fail conditions unchanged.
- **No corpus test added/extended:** grepped `tests/` for `V18|Upstream contracts|installed 0\.7|verify-rigs` — only unrelated hits (`test_regen_gate.py:190` comment, `test_bare_queue_send_deny.py:10` V22 comment). Per finding orders, no new harness invented; proof by direct before/after runs instead:
  - Wrong-version shim after fix → exit 1: `[FAIL] V18/#98: host rig --version is not 0.7.4 (got 0.7.2 (8b180689)); validation claim requires installed 0.7.4` (+ expected V19 live-count cascade `33 passed, 4 failed` — the failure is non-vacuous).
  - Rig absent after fix → exit 0, `SUMMARY: 35 checks passed, 0 failed`, PASS line carries the skipped-claim, no `installed 0.7.4` string.
  - Correct host (`rig --version` → `0.7.4 (6d9e8e27)`) after fix → exit 0, `SUMMARY: 35 checks passed, 0 failed`, original claim string intact.

## Files changed (3, all minimal)

| File:line | Change |
|---|---|
| `openspec/changes/overhaul-bump/specs/bump/spec.md:12,15` | REQ-BUMP2 idempotence clause narrowed with deferral parenthetical; scenario matched. |
| `openspec/changes/overhaul-bump/tasks.md:14` | T2 acceptance `AND` → `&&`. |
| `scripts/verify-rigs.sh:2394-2411` + ok-split (`:2479-2488`) | V18 host-version fail-closed gate; absent-path claim omitted. |

## Exact commands + exit codes

| Command | Exit |
|---|---|
| Wrong-version shim run, unmodified script (`PATH=<shim>:$PATH ./scripts/verify-rigs.sh --check-only`) | 0 — false `installed 0.7.4` claim (RED proof) |
| Rig-absent run, unmodified script (`env PATH=/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin ./scripts/verify-rigs.sh --check-only`) | 0 — NOTE + false claim (RED proof) |
| Wrong-version shim run, fixed script | 1 — new `[FAIL] V18/#98: host rig --version is not 0.7.4 …` (GREEN proof) |
| Rig-absent run, fixed script | 0 — 35/0, skipped-claim, no version string (GREEN proof) |
| Normal run, fixed script (`./scripts/verify-rigs.sh --check-only`) | 0 — 35/0, original claim intact |
| Fixed T2 acceptance (`./scripts/verify-rigs.sh --check-only && python3 scripts/audit_loop.py --self-test`) | 0 — 35/0 + SELF-TEST PASSED |
| `make verify` | 0 — `SUMMARY: 35 checks passed, 0 failed` |
| `make test` | **not re-run** — single `test_canary_scope_only` failure stays pre-existing/out-of-scope per wave orders (Wave B M5 owns it); this wave touches neither `fleet/fleet.yaml` nor the test |

## Self-audit notes

- Nothing skipped as "already fine": every finding verified against disk first; F1's risky live check replaced by code-path + diff evidence per the finding's own no-mutation rule.
- Zero stubs added; no secrets in diff; `git status --short` shows exactly the 3 intended modified files (plus pre-existing untracked spec/report/ledger inputs); no commit made — tree left dirty for coordinator commit.
- V19 self-inclusion intact: pass counts unchanged in all green paths (35/0 + live-count docs match); the shim-RED run's V19 cascade is that gate's designed behavior, not a regression.
