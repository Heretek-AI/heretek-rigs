# overhaul-bump implementation report (Wave M1)

- **Stage/wave id:** overhaul-bump — stack pin 0.7.4 + ledger (contract sync explicitly Wave B)
- **Worktree:** `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/overhaul-bump` (branch `feat/overhaul-bump`, base `main` `88cd930`)
- **Date:** 2026-10-27/28 UTC
- **Deliverables:** host toolchain @ 0.7.4, bump ledger, operator-doc pin updates, this report. No commit (leave dirty for coordinator commit, per stage orders).

## 1. Toolchain install (halt-gate: passed)

- `npm install -g @openrig/cli@0.7.4` → exit 0 (one `allowScripts` postinstall notice only).
- `rig --version` → `0.7.4 (6d9e8e27)` (binary `/home/john/.npm-global/bin/rig`). Ledger NOT faked: stamp comes from the installed binary.
- Tarball independently re-verified: `npm pack @openrig/cli@0.7.4` in `/tmp/opencode/bump-verify/` → sha256 `d11dd8a6fc78f0c4d7afeae462c07c2af0fb9fe460990950be495016734920a1` — matches the coordinator-provided value byte-for-byte. (0.7.2 tarball re-packed as control: `42b4d4980c062f49f99db7e843a2ba96c0066a420cbaace381f435e22699d4c5`, matches the 0.7.2 ledger.)

## 2. Files changed + reason per line

**Updated (true toolchain pins only — every line asserts the installable/active toolchain version):**

| File:line | Old → New | Reason |
|---|---|---|
| `AGENTS.md:4` | `@openrig/cli@0.7.2` → `@openrig/cli@0.7.4` | Stack line asserts the toolchain. |
| `README.md:9` | stack table `0.7.2` → `0.7.4` | Same. |
| `README.md:39–40` | prereqs `rig 0.7.2` + `npm install -g @openrig/cli@0.7.2` → `0.7.4` | Install instruction must install the pinned toolchain. |
| `Makefile:3` | `Target Framework: OpenRig v0.7.2` → `v0.7.4` | Same. |
| `docker/Dockerfile:16` | `ARG OPENRIG_VERSION=0.7.2` → `0.7.4` | True image-toolchain pin; paired with V13 below. |
| `scripts/verify-rigs.sh:1838–1839` | V13 assert/message `0.7.2` → `0.7.4` | Paired with Dockerfile; gate name/number untouched, SUMMARY frozen. Also the sabotage target QA should use (restore-test). |
| `scripts/verify-rigs.sh:2463` | V18 ok-message `installed 0.7.2` → `installed 0.7.4` | Status string asserted a false installed version; no gate logic touched. |
| `docs/USER_GUIDE.md:3` | `built on OpenRig v0.7.2` → `v0.7.4` | Operator manual stack assertion. |
| `docs/USER_GUIDE.md:14` | `Required by @openrig/cli@0.7.2` → `@0.7.4` | Node-requirement attribution. |
| `docs/USER_GUIDE.md:21,24,25` | install block → `0.7.4`, `Expect: 0.7.4 (6d9e8e27)` | Install instruction + expected stamp (stamp from live binary). |
| `docs/USER_GUIDE.md:473` | Docker `:latest` table `rig 0.7.2` → `0.7.4` | Describes the image the Dockerfile builds (paired). |
| `docs/TECHNICAL_DOCUMENTATION.md:4` | target framework `v0.7.2 … commit 8b180689` → `v0.7.4 … commit 6d9e8e27` | Framework header (commit from live binary). |
| `PROMPT_ADVERSARIAL_FLEET_AUDIT.md:5` | stack definition `0.7.2` → `0.7.4` | Audit prompt must describe the stack under audit. |
| `PROMPT_ADVERSARIAL_FLEET_AUDIT.md:16` | baseline `rig --version` from `0.7.2` → `0.7.4` | The tool the auditor will actually run. |
| `PROMPT_ADVERSARIAL_FLEET_AUDIT.md:40` | "real thing it plugs into" `0.7.2` → `0.7.4` | Same. |
| `PROMPT_ADVERSARIAL_FLEET_AUDIT.md:70` | Alpha focus `OpenRig v0.7.2` → `v0.7.4` | Validation runs on the 0.7.4 CLI (green verify proves it). |
| `PROMPT_ADVERSARIAL_FLEET_AUDIT.md:167` | `Real @openrig/cli@0.7.2 offline validation` → `@0.7.4` | Runs against the installed CLI. |

**Created:** `docs/sprints/CLI-0.7.4-BUMP.md` (ledger, 0.7.2-ledger pattern: version facts, 0.7.2→0.7.4 tarball delta, pin table, verify output, not-verified-here, rollback).

**Deliberately NOT changed (deferred, with reason):**

- `scripts/generate-rigs.py` (`OPENRIG_VERSION`/`OPENRIG_COMMIT`), `fleet/fleet.yaml` (header), `fleet/mcp-servers.yaml` (`builtin:rig-mcp-serve-http@0.7.2`) — generator inputs. Changing any of them obligates a regen, and the default `openrig-core` resolver now points at installed 0.7.4 skills, so a regen would vendor Wave B contract content. **No generator input changed → no regen; leaves clean.**
- `schemas/rigspec-schema.pinned.ts`, `schemas/rigspec-keys.pinned.json`, `schemas/contract-schemas.sha256`, `verify-rigs.sh` key-set/provenance strings — provenance of still-0.7.2 bytes; editing without re-vendoring would be false provenance.
- Generated leaves (`registry/*`, `rigs/*/bundle.yaml`, `rigs/*/SETUP.md`, `fleet/skills-lock.json`) — one-rule.
- Vendored-byte descriptions (`USER_GUIDE.md:368`, `TECHNICAL_DOCUMENTATION.md:12,22,384`, `PROMPT…:85`) — still factually true (bytes are 0.7.2 until Wave B re-vendors).
- Dated records (`CLI-0.7.2-BUMP.md`, `PI-1.4.0-BUMP.md`, `HANDOFF.md`, `docs/evidence/*`, `docs/reports/*`, `openspec/changes/107-identity/*`, this change's own proposal/design/tasks) — history never rewritten.

## 3. Tarball delta 0.7.2 → 0.7.4 (read-only, for the ledger + Wave B handoff)

- Skill directory set identical (18/18 names). 3 bodies changed: `claude-compaction-restore` (session-file naming prose), `messaging-the-human` (`rig gateway participants` + channel-policy guidance), `queue-handoff` (receiver-actionable writing guidance). 5 skill bodies reference `codex`.
- `MEMBER_KEYS` gains exactly one key: `codex_permissions` (9 refs in 0.7.4 `rigspec-schema.js`, 0 in 0.7.2). No RIG/POD/EDGE change. → Wave B material, confirmed out of scope.

## 4. M0 probe forms on 0.7.4 (scratch env ONLY)

Isolated `OPENRIG_HOME=/tmp/opencode/bump-m0-20261027-155536` (mode 700), scratch ports daemon `127.0.0.1:18433` / serve `127.0.0.1:18437`, real `~/.openrig/daemon.json` read before/after (byte-identical: stale pid 57353/port 7433). Probes mirror `docs/evidence/107-identity-m0.md` §1–§4:

- `token add --help`: flags identical to 0.7.2 (`--seat/--rig/--root/--workspace/--owner`). No surface delta.
- `token add probe-seat --seat spike-bump-seat`: once-printed token (scratch-only; redacted first/last-2 `or…2A`), sha256-only mode-600 store, `rc=0`.
- Grant serve: valid Bearer → HTTP 200 (`serverInfo.version "0.7.4 (6d9e8e27)"`); bad token → 401 with the exact 0.7.2 message; missing credential → 401.
- **One CLI-surface delta recorded (no redesign):** `rig_whoami` for an unmanaged seat returns `ok:true` with `caller:{authenticated:true, principal:<grant>}` + "This seat has no session here…" message on 0.7.4, vs the `isError:true` 404-session text on 0.7.2. Identity signal (grant's seat) unchanged.
- Cleanup: serve killed, scratch daemon stopped, listeners gone, no `rig` procs remain, probe token file removed. Scratch DB/logs remain under `/tmp` only (never committed). Note: one `pkill -f` matched my own shell command string and killed the invoking shell (known `pgrep -f`-self-match footgun); recovery via direct `rig daemon stop` with explicit `OPENRIG_HOME`, verified clean afterwards.

## 5. Exact commands + exit codes

| Command | Exit |
|---|---|
| `npm install -g @openrig/cli@0.7.4` | 0 |
| `rig --version` → `0.7.4 (6d9e8e27)` | 0 |
| `npm pack @openrig/cli@0.7.4` + `sha256sum` → `d11dd8a6…` | 0 |
| `make verify` (after edits) | 0 — `SUMMARY: 35 checks passed, 0 failed.` (+ V22/V23/V24 info lines; live-health SKIP lines, real daemon untouched) |
| `./scripts/verify-rigs.sh --check-only` (after edits) | 0 — 35/0 |
| `python3 ./scripts/audit_loop.py --self-test` | 0 — SELF-TEST PASSED |
| `make test` (full suite) | **2 — 359 tests, 358 pass, exactly 1 failure: `test_canary_scope_only`** (see §6; verified 2×, 99.8–99.9 s) |
| `python3 scripts/generate-rigs.py --check-idempotent` | **deliberately NOT run** — default `openrig-core` resolver now points at installed 0.7.4 (would vendor Wave B content); no generator input changed so no regen owed — see §6.2 |

## 6. Self-audit notes (unfinished / anomalous — stated plainly)

1. **`make test`: 359 tests, exactly 1 failure — proven PRE-EXISTING, out of scope, Wave B M5 owns the fix.** `test_canary_scope_only` (`tests/test_build_canary.py:142–183`) diffs current `fleet/fleet.yaml` role permissions against the FIXED wave-base blob `a33f3bb:fleet/fleet.yaml` (test lines 158–171) and expects the changed-role list to equal exactly `[engine-systems-eng + 5 M4 roles + cpp-lowlevel-eng]` (test lines 149–157, 181–182). Actual: **51 roles differ — the 7 expected plus 44 extra** (`a11y-specialist`, `analytics-metrics-eng`, … — full list reproducible via the one-liner in the diagnosis below).
   - **File:line WHY the base comparison can no longer hold:** every one of the 44 extra roles differs from the base in exactly one key — an added `bash_deny: ["rig queue list", "rig queue create", "rig send"]` triple (verified 44/44, zero non-conforming: strip `bash_deny` from current permissions and each role equals its base byte-for-byte; e.g. `a11y-specialist` base keys `[bash_allow, path_write]` vs current `[bash_allow, bash_deny, path_write]`, `git-drift-coord` likewise).
   - **Who landed it:** `git log --oneline a33f3bb..HEAD -- fleet/fleet.yaml` lists 9 commits, but `git log --oneline -S 'bash_deny' -- fleet/fleet.yaml` returns exactly ONE: `892e1a7 feat(102-closeout): implement stage requirements` — the 102-closeout HR-F18 triple, `+      bash_deny:` × 51 in that commit's `fleet/fleet.yaml` hunk, landed on all 51 roles AFTER the `a33f3bb` base. (The M4 / wave-12 / command-effects / path-arg-91 commits account for the 7 roles the test already expects.)
   - **Pre-existing by logic (no stash needed, none performed):** this wave does not touch `fleet/fleet.yaml` — `git diff HEAD -- fleet/fleet.yaml` and `git diff 88cd930 -- fleet/fleet.yaml` are both empty, and the test reads ONLY `fleet/fleet.yaml` + the immutable git object `a33f3bb` (test lines 39, 158–171). Untouched input ⇒ byte-identical outcome without these changes ⇒ the failure exists on clean `main` (`88cd930`) exactly as observed. Per stage orders the test was NOT modified, the canary was NOT fixed, `fleet/fleet.yaml` was NOT touched.
   - **Handoff:** the canary rework (re-pinning the scope bound to a post-closeout base) is explicitly Wave B M5 scope. All other 358 tests pass.
2. **`--check-idempotent` not run, by design (idempotence holds vacuously).** Executing it regenerates into `--root` using the default `openrig-core` resolver, which prefers the globally installed package (`scripts/generate-rigs.py:623–643` — `npm root -g` candidate first, now 0.7.4 skills) — it would vendor Wave B content into the tree. No generator input changed (`OPENRIG_VERSION`/`OPENRIG_COMMIT` still `0.7.2`/`8b180689` at `generate-rigs.py:60–61`; `fleet.yaml` header + `mcp-servers.yaml:273` still `0.7.2`; `git diff 88cd930 -- specs rigs rosters registry fleet/skills-lock.json schemas fleet/fleet.yaml fleet/mcp-servers.yaml scripts/generate-rigs.py` empty), so no regen is owed and determinism is undisturbed — no 0.7.2-era `openrig-core` source exists on this host to run it against (workspace checkout is 0.6.11-era). Wave B re-runs it after the generator bump. QA/drift-guard: do not misread this as skipped.
3. **Intentional doc/leaf skew until Wave B.** Operator docs now say 0.7.4 while generator inputs + generated leaves + vendored bytes still say 0.7.2. This is the approved split (proposal: "No contract sync here"); the ledger §3 names every deferred location. Drift-guard/QA: do NOT "fix" the skew by hand-editing leaves — one-rule.
4. **No commit made.** Tree left dirty (8 modified + `docs/sprints/CLI-0.7.4-BUMP.md` + this report untracked; `openspec/changes/overhaul-bump/` was already untracked coordinator input) for the coordinator chore commit. No `git add`/`commit` performed.
5. **Secrets hygiene:** no real credentials touched. Only scratch tokens used (mode-600 files under `/tmp/opencode`, removed); reports carry first/last-2 redaction only. Real `~/.openrig` read-only (one JSON parse) and byte-identical after.
6. **Self-audit (continuation pass, 2026-10-27):** no stubs added (`git diff` adds zero `TODO`/`FIXME`/`NotImplemented`/skip/`|| true` — the two `|| true`/`TODO`-mention hits in the tree are pre-existing intentional content outside this wave's hunks); no secrets in the diff; SUMMARY frozen (`SUMMARY: 35 checks passed, 0 failed`, no V1–V24 renames — `git diff scripts/verify-rigs.sh` touches zero `== V` lines, only the V13 assert/message pair + V18 info string); remaining `0.7.2` strings in wave files are all intentional still-true provenance (pinned-schema key-sets, `verify-rigs.sh` provenance recipe, `USER_GUIDE.md:368` vendor-checkout line, `TECHNICAL_DOCUMENTATION.md:12,22,384`, `PROMPT…:85` skills-lock pin list, generator inputs, dated records) as ledgered in §2/ledger-§3; `git status` shows ONLY the 8 true-pin files modified plus untracked ledger + spec + this report. `make test` re-run 2× foreground: `Ran 359 tests`, `FAILED (failures=1)`, `make` exit 2, single failure `test_canary_scope_only` both times. `npm pack` SHA re-verified live in `/tmp/opencode/bump-sha` (scratch removed after).
