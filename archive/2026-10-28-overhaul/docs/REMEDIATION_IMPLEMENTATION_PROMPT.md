# Remediation Implementation Prompt — heretek-rigs audit findings (#66)

## Mission

Fix the 5 P0 and 11 P1 findings from the Oct 23–24 fleet audit ([tracking issue #66](https://github.com/Heretek-AI/heretek-rigs/issues/66)) so the 51-seat fleet can operate as a self-governing factory: least-privilege that is real and fail-closed, gates that catch what they claim to, and a dispatch→build→test→deliver path that needs no operator. **Read this entire file before writing any code.** Your training data is out of date for this repository: the stack is `@openrig/cli@0.6.13`, `@earendil-works/pi-coding-agent@1.3.0`, `@gotgenes/pi-permission-system@41.0.0`, and there are 68 vendored skills, not 64. Every fact in "Verified facts" below was checked by running it on 2026-10-24; trust it over memory.

## How to work

1. **Do the milestones in order.** Each builds on the last. M1 (sandbox spike) must be reproduced by you before you touch M4.
2. **An acceptance check must pass before you move on.** Every acceptance check here is a literal command with an expected result. Run it. If it does not pass, stop and fix, do not proceed.
3. **One commit per milestone,** with explicit `git add <files>` (never `git add -A`; never `git add .`). Commit message `remediate(#<issue>): <what>`. End every commit message with the two attribution lines in "Paths and setup".
4. **Never skip, delete, weaken, or `@skip` a test** to make a gate pass. If a test is wrong, fix the code; if the test is genuinely stale, change it in its own commit with a one-line reason in `docs/NOTES.md`.
5. **Never invent an API, flag, path, or config key.** Look it up in this order: (a) this file's "Verified facts"; (b) the installed package's `.d.ts` / source under `node_modules/`; (c) a throwaway experiment in a scratch dir. Record what you find in `docs/NOTES.md`.
6. **Log every discovery and every discrepancy** in `docs/NOTES.md` with the command and its output. If reality contradicts this brief, write it down and fix the brief's assumption in your PR.
7. **Stop after 3 failed attempts on the same error.** Write what you tried in `docs/NOTES.md` and move the milestone to a "blocked" list; do not thrash.
8. **The one rule (AGENTS.md):** never hand-edit `specs/`, `rigs/`, `rosters/`, `registry/`. Edit `fleet/fleet.yaml`, `fleet/mcp-servers.yaml`, or `scripts/`, then run `python3 ./scripts/generate-rigs.py`. Use surgical text edits on `fleet/fleet.yaml`; never `yaml.safe_dump` it (it strips comments).
9. **verify-rigs checks are audit-baselined.** Add new checks alongside existing ones (a new `== V12 ==` block, or new `ok()`/`fail()` lines inside an existing block). Never renumber or reword V1–V11.
10. **Hard nevers this audit uncovered** (each is a finding if reintroduced):
    - Never write a seat `packages[]`, MCP command, or granted binary path without checking it exists on disk (#67, #74).
    - Never grant a `builtin:locked` seat an interpreter or test-runner verb (#68).
    - Never leave a test file unwired from both `make test` and verify-rigs (#82).
    - Never commit a real secret into any workspace tree; the git-diff read-deny (#69) only covers the flags it lists.
    - Never run a factory mission with real credentials; use dummy values in a 0600 scratch dir.

## Paths and setup

These are **your** machine's paths — adjust the repo root to wherever your checkout lives; everything else is relative to it.

- **Repo root:** the heretek-rigs checkout (`git rev-parse --show-toplevel`).
- **Branch:** `git checkout -b remediate/audit-66-p0-p1` off the latest `main`. One PR per milestone cluster, or one PR for the set — your call, but never push to `main`.
- **Toolchain (install the pinned versions; these are what the audit ran against):**
  ```bash
  npm i -g @openrig/cli@0.6.13 @earendil-works/pi-coding-agent@1.3.0 @gotgenes/pi-permission-system@41.0.0
  rig --version    # expect: 0.6.13 (9eeb2e42)
  pi --version     # expect: 1.3.0
  python3 --version  # expect: 3.11+ (audit ran 3.13.17)
  python3 -c 'import jsonschema,yaml'   # must not error
  ```
  The permission system and pi are also resolvable per-seat under `$HERETEK_TOOLS/pi-packages/node_modules/`.
- **Sandbox dependency (M1):** `bubblewrap` (`bwrap`). On Fedora: `sudo dnf install bubblewrap`. Expect `bwrap --version` ≥ 0.9.0. The host must allow unprivileged user namespaces: `unshare --user --map-root-user true` prints nothing and exits 0.
- **Scratch dir for spikes:** a git-ignored dir outside the repo (e.g. `$(mktemp -d)`). Never put experiments in the repo tree.
- **Attribution — end every commit message with exactly:**
  ```
  Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_014wevSWHET5eqHNVNTYZnx9
  ```
  And every PR description with:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  https://claude.ai/code/session_014wevSWHET5eqHNVNTYZnx9
  ```

### Files you will touch

| File | Findings | What changes |
|---|---|---|
| `scripts/render-seat.py` | #67, #69, #72 | fail-closed on missing pps; emit `shellPath` sandbox + `HERETEK_SANDBOX_WRITE`; add git-diff-read terminal denies; deny env-assignment prefixes |
| `scripts/seat-sandbox.sh` (new) | #68 | bubblewrap jail wrapper, invoked as the seat shell |
| `fleet/fleet.yaml` | #68, #73 | strip runner verbs from locked seats; strip `git commit*`/`git checkout*` from dependency-patcher; add per-mission write roots |
| `scripts/verify-rigs.sh` | #67, #69, #70, #71, #82, #86, #87 | new `== V12 ==` checks (tool existence, git-diff denies, image existence, MCP flags, orphan suites, roster/command-pod, stub scan) |
| `scripts/audit_loop.py` | #79 | header/ledger/matrix/sabotage detection + self-test vectors |
| `scripts/sweep-typed-blocks.py` | #83 | actor + exact-blocker + evidence-resolve checks on `auth:` parks |
| `scripts/reconcile_model.py` | #84 | negation-aware terminal/placed detection |
| `scripts/check-envelope.py` | #92 | path-scope, PUSH-branch, time-ordering, marker validation |
| `scripts/send-authenticated.sh` | #72, #93 | unset/refuse `OPENRIG_SESSION_NAME`; require `persisted:true`; reject member-id sources |
| `scripts/generate-rigs.py` | #85, #97, #99 | `git archive` vendoring (or clean-tree check); real/empty attestation; `DIRTY-` provenance stamp |
| `Makefile` | #82 | add the three orphan suites to `test` |
| `docker-compose.sidecars.yml`, `docker/Dockerfile` | #70, #100 | real image digests; OpenRig 0.6.13; generated install lists |
| `docs/NOTES.md` (new) | all | your discovery + discrepancy log |

## Verified facts

All verified on 2026-10-24 against the pinned stack. Commands are runnable from the repo root unless noted.

### F1 — pi routes every bash command through `shellPath` (this is the sandbox hook)
`@earendil-works/pi-coding-agent@1.3.0` reads `shellPath` from the seat's `settings.json` and spawns the bash tool through it: `dist/utils/shell.js:58` `getShellConfig(customShellPath)` returns `{shell, args:["-c"]}` for a custom path, and `dist/core/agent-session.js:2937,3134` pulls `settingsManager.getShellPath()`. A **missing** shellPath fails closed:
```
settings.json shellPath -> "/path/that/does/not/exist"
pi bash "date +%s"  ->  isError:true  "Custom shell path not found: /path/that/does/not/exist"
```
Verified live, on the operator's machine, that a launched seat honors it: OpenRig's `pi-runner` spawns stock `pi --mode rpc` with `PI_CODING_AGENT_DIR=<state>/pi/<seat>/agent` and `buildPiChildArgs` passes no settings override, so the seat reads `agent/settings.json`; a `shellPath` wrapper set there intercepted the seat's allowed bash command (`agent-session.js:2937-2945` → `tools/bash.js:133,159`). **The enforcer runs first** — a policy-denied command never reaches the wrapper, so the sandbox only ever sees commands that already passed policy. A missing `shellPath` fails closed (no `/bin/bash` fallback). The wrapper receives exactly `-c <command>`.

**THREE design facts that follow (do not miss these):**
- **`settings.json` is NOT hot-reloaded.** pi reads it at startup and only on an explicit RPC `reload` (`rpc-mode.js:252` → `agent-session.js:2978`). The permission `config.json` DOES hot-reload on mtime (#96), but `shellPath` lives in `settings.json`. So the sandbox rollout needs each seat **relaunched or sent an RPC reload** — it is NOT a no-bounce change, unlike the git-diff / policy fixes. Plan the rollout accordingly (see M4/rollout).
- **The wrapper covers only pi's bash tool**, not the MCP servers pi starts nor pi's own file tools (those go through the enforcer's path checks). Don't claim the jail contains MCP-server behaviour.
- **The wrapper path must sit outside every seat's write scope**, and `bwrap` must exist at that path on every host (tool-existence gate, M3). bwrap confirmed at `/usr/bin/bwrap` on the operator's machine.

### F2 — bubblewrap confines writes, network, and the real secret store (verified)
With `bwrap --ro-bind / / --dev /dev --proc /proc --unshare-net --bind <writeroot> <writeroot> --tmpfs <secret-store-dir> --chdir <cwd>`:
```
echo ok > tests/t.txt      -> rc=0  (tests/ is a bound write root)
echo x > root.txt          -> rc=1  Read-only file system   (outside write roots)
cat ~/.config/.../secrets/opencode-go.key -> "No such file or directory"  (tmpfs masks the store)
curl https://example.com   -> net=000 / blocked
git status / git log       -> work normally (repo is readable)
```
**Two things bubblewrap does NOT fix, and you must not claim it does:**
- A secret **committed into the workspace** (e.g. `prod.env` in the repo) stays readable by an in-scope subprocess — the sandbox only masks the out-of-tree secret store. That vector is closed by F3 (git-diff denies) plus "never commit secrets", not by the jail.
- See Gotcha 1 about `/tmp`.

### F3 — the bash terminal-deny list and where it is emitted
`scripts/render-seat.py` (~line 410) appends terminal denies **last** (last-match-wins) to every seat's `bash` map. Current set:
```python
("*--output*", "*;*", "*|*", "*>*", "*<*", "*&*", "*`*", "*$*", "*(*", "*)*",
 "* -p*", "*\t-p*", "*--patch*", "*--full-diff*", "*--textconv*")
```
`verify-rigs.sh:588` holds a mirror tuple `_TERMINAL_BASH_DENIES` and `:1158` asserts the renderer emits each one. **Both lists must stay in sync** — change them together or verify-rigs fails.
Verified bypass (#69): on a committed `prod.env`, `git log --oneline -u`, `-U1`, `--unified=1`, `--cc`, and `git show --stat -u`/`--cat` all printed the secret; only `-p`/`--patch`/`--full-diff`/`--textconv` are denied today.

### F4 — audit_loop evaluator internals (#79)
`scripts/audit_loop.py:79-98` `evaluate_audit_status(report_text, agent_output, gate_passed)`:
- `re.findall(r"^###\s+HR-[A-Za-z0-9._-]+:", combined, re.MULTILINE)` — needs exactly `###` and a trailing colon.
- `re.findall(r"\|[^\n]*\|\s*(BROKEN|PARTIAL)\s*\|", combined, re.IGNORECASE)` — misses decorated cells (`**BROKEN**`, `BROKEN ❌`, `BROKEN (see notes)`).
- The Defect Matrix and Sabotage tables are never read.
- An explicit `STATUS: FINDINGS_DETECTED` short-circuits to findings (verified).

### F5 — verify-rigs structure (#67, #70, #71, #82, #86, #87)
`scripts/verify-rigs.sh` is a bash harness that heredocs a Python block (`ok(msg)` at :58, `fail(msg)` at :64, `failures`/`passes` globals, `SUMMARY: N checks passed, M failed`, `sys.exit(1)` if any failure). Checks are grouped `== V1 ==` … `== V11 ==`. The clean tree is **27 passed, 0 failed**. The append convention (used by V8–V11) is: do work, and if `len(failures) == _before`, call `ok(...)` once. Add your checks as `== V12 ==` (and beyond) at the end.

### F6 — Makefile test target (#82)
`Makefile:37-38` `test:` runs 7 suites: `test_render_seat test_sweep_typed_blocks test_regen_gate test_queue_id_discipline test_queue_json_discipline test_reconcile test_generate_trackers`. **Orphaned** (in no gate): `test_check_envelope.py`, `test_build_canary.py`, `test_live_health.py`. `check-envelope.py` has no caller at all (`grep -rn check-envelope scripts Makefile lefthook.yml .github` is empty).

### F7 — locked seats that hold runner verbs (#68)
`fleet.yaml` `roles.<id>.permissions.bash_allow`. `sabotage-qa-tester` is `builtin:locked` (via `permission_policy`) with `path_write: [tests/chaos/*, docs/qa/*]` yet holds `npm test*`, `pytest*`, `cargo test*`, `npx stryker run*`, `cargo mutants*`, `mutmut run*`. The 18 locked seats are listed in finding #68 / the report. `static-analysis-lead` is locked and holds no runner verb.

### F8 — dependency-patcher commit grants (#73)
`fleet.yaml` `roles.dependency-patcher.permissions.bash_allow` contains `git checkout*` and `git commit*`. Verified: `git commit -a -m x` committed `fleet/fleet.yaml` + `src/main.c`; `git commit --amend -a` and `git checkout -f` also ran; `git checkout -- <path>` is denied by path-arg policing. It is the only seat with any `git commit` grant; 0/51 have `git add`.

### F9 — identity forgery (#72) — NO POLICY-RULE FIX EXISTS
`OPENRIG_SESSION_NAME=<seat> rig queue create --json …` records `identityProvenance: transport:v1` (the high-trust tier) with no live session. pi-permission-system **strips a leading `VAR=value` assignment before matching**, so a seat's `rig queue *` grant matches `OPENRIG_SESSION_NAME=… rig …` and a `"*OPENRIG_SESSION_NAME=*"` deny rule does **not** catch it (that rule only stops the `env OPENRIG_SESSION_NAME=… rig …` form). Verified by the live run. So #72 cannot be closed in the permission layer. The achievable mitigations are: harden `send-authenticated.sh` (`unset OPENRIG_SESSION_NAME`; reject member-id sources; receipt fail-closed), and file an OpenRig upstream request for daemon-issued per-seat identity tokens. Treat both provenance tiers as claims in charters until upstream lands.

### F10 — `commandEffects` cleanly fixes queue-note content (#75, part of #91)
pi-permission-system supports a `commandEffects` declaration. Declaring `rig queue` as a **read** (not a path-write) lets a seat put paths and `|` in a `--note`, and use `--body-file <path>` inside its own write scope, while `--body-file prod.env` and `--body-file /etc/passwd` stay denied. Verified live. This is the fix for #75 and the note half of #91, preferred over loosening the terminal denies.

### Not verified, be careful — check these early and record answers in docs/NOTES.md
- **F1 daemon path:** does `rig up` honor per-seat `settings.json shellPath`? (M1 acceptance proves it.)
- **Image digests (#70):** the exact `@sha256:` for each replacement image — resolve with `docker manifest inspect` / `skopeo inspect` on your network, do not copy a digest from memory. Known-good tags confirmed existing: `tecnativa/docker-socket-proxy:v0.5.0`, `radare/radare2:5.9.8`, `sonarqube:25.10.0.114319-community`, `redis:8.0.3`, `qdrant/qdrant:v1.15.3`, `budtmo/docker-android:emulator_14.0`; searxng/browserless/firecrawl/ghidra need a real tag chosen on-host.
- **Config.json hot-reload (#96):** pps re-reads config on mtime change, so a re-seed may refresh a live seat without a bounce. Confirm on one live seat before relying on it for rollout.

## Target layout (new/changed files)

```
scripts/
  seat-sandbox.sh        # NEW: bwrap jail, invoked as each seat's shell (M1)
  render-seat.py         # fail-closed pps check; emit shellPath + write-roots; new denies (M2,M4,M5)
  verify-rigs.sh         # + == V12 == tool-existence/image/MCP/orphan/roster/stub checks (M3,M6,M8,M9)
  audit_loop.py          # evaluator hardening + self-test vectors (M7)
  sweep-typed-blocks.py  # auth-park actor/evidence checks (M10)
  reconcile_model.py     # negation-aware detection (M11)
  check-envelope.py      # semantic validation (M12)
  send-authenticated.sh  # env-forgery + receipt fail-closed (M5)
  generate-rigs.py       # git-archive vendoring; real attestation; DIRTY stamp (M13)
fleet/fleet.yaml         # strip locked-seat runners; strip patcher commit; write-roots (M2,M4)
Makefile                 # wire 3 orphan suites into test (M6)
docs/NOTES.md            # NEW: discovery + discrepancy log
```

## Milestones

### M0 — Baseline and NOTES
**Do:** create `docs/NOTES.md`. Run `./scripts/verify-rigs.sh --check-only` and `make test`; record the counts.
**Acceptance:** `./scripts/verify-rigs.sh --check-only` ends `SUMMARY: 27 checks passed, 0 failed.`; `make test` ends `OK`. Both recorded in NOTES.

### M1 — Reproduce the sandbox hook yourself (spike)
**Do:** in a scratch dir, render one seat (`engine-systems-eng`), set its `settings.json` `shellPath` to a trivial wrapper that echoes a marker to stderr then `exec /bin/bash "$@"`, and drive it with `scripts/gate-run.sh`. Confirm the marker appears for an allowed command and that a policy-denied command never reaches the wrapper. (The daemon-honors-shellPath question is already answered — see F1 — so you need not relaunch a live seat; just reproduce the mechanism.) Record outputs in NOTES.
**Acceptance:** the marker appears for an allowed command; a denied command shows no marker (enforcer-first). Record in NOTES that `settings.json` is not hot-reloaded, so M4's rollout needs a relaunch/RPC reload.

### M2 — Fail-closed on a missing permission extension (#67)
**Do:** in `render-seat.py`, after `pps_pkg` is built (~line 130) and before it is written into `packages` (~line 309):
```python
if check_secret_fs and not (Path(pps_pkg) / "package.json").is_file():
    die(f"{pps_pkg} missing: @gotgenes/pi-permission-system is mandatory")
# and assert the pinned version:
_pps_ver = json.loads((Path(pps_pkg) / "package.json").read_text()).get("version")
if check_secret_fs and _pps_ver != "41.0.0":
    die(f"{pps_pkg} version {_pps_ver}, need 41.0.0")
```
There is **no** `--allow-missing` escape for this (unlike secrets).
**Acceptance:**
```bash
HERETEK_TOOLS=/nonexistent HERETEK_SECRETS=$(mktemp -d) python3 scripts/render-seat.py \
  --role exec-director --rig executive-and-architecture --pod exec --allow-missing-secrets --out $(mktemp -d); echo $?
# must be non-zero, with the "mandatory" message
```
A render with the real `HERETEK_TOOLS` still exits 0.

### M3 — Tool-existence gate + wire the canary suite (#67, #74, #82)
**Do:** add `== V12 ==` to verify-rigs: for every seat, assert `settings.json packages[0]` exists (when rendered against a real tools dir), and for every MCP server bound to a seat assert its `command` resolves (`shutil.which` or path check) — report missing per seat. Add `tests/test_build_canary.py`, `tests/test_check_envelope.py`, `tests/test_live_health.py` to `Makefile:38` `test:`.
**Acceptance:** `make test` runs all 10 suites and ends `OK`. Rendering with `HERETEK_TOOLS=/nonexistent` makes M2's check fire. The V12 tool-existence check lists any missing binary (on a host missing r2mcp, it names `radare2`).

### M4 — Sandbox every execution-capable seat (#68)
**Do:**
1. Add `scripts/seat-sandbox.sh` (reference below, already run and verified).
2. In `render-seat.py`, set `settings.json["shellPath"]` to the absolute path of `seat-sandbox.sh`, and write `HERETEK_SANDBOX_WRITE` (the seat's `path_write` roots, colon-joined) into the seat's env so the wrapper binds exactly those.
3. In `fleet.yaml`, **remove every runner/interpreter verb from all 18 `builtin:locked` seats** (start with `sabotage-qa-tester`: drop `npm test*`, `pytest*`, `cargo test*`, `npx stryker run*`, `cargo mutants*`, `mutmut run*`; also `ai-red-teamer` garak/pyrit/promptfoo and `static-analysis-lead` `cargo clippy` which runs build scripts — per decision #68(a)). Regenerate.
4. **Rollout is NOT no-bounce.** Because `shellPath` lives in `settings.json` (not hot-reloaded, F1), applying the sandbox to live seats needs each seat relaunched or an RPC `reload`. Do NOT claim canary-then-fleet hot-reload for the sandbox — that applies only to the permission `config.json` changes (git-diff denies, locked-seat verb removal, MCP flags). State this split in the PR and the rollout prompt.
**Acceptance:** `scripts/gate-role.sh sabotage-qa-tester` shows no runner verb allowed. A sandboxed `pytest` that writes outside `path_write` or reads the masked secret store **fails** (reproduce the F2 corpus). `python3 scripts/generate-rigs.py` leaves the tree clean after a second run.

`scripts/seat-sandbox.sh` (verified 2026-10-24 — writes confined, net blocked, secret store masked, git works; copy verbatim):
```bash
#!/usr/bin/env bash
# seat-sandbox.sh — wrap every seat bash command in a bubblewrap jail.
# pi invokes this as the seat's shell: `seat-sandbox.sh -c "<command>"`.
# Writable roots: HERETEK_SANDBOX_WRITE, colon-separated, relative to cwd.
# Secret store to mask: HERETEK_SECRET_STORE (absolute dir), tmpfs'd away.
set -euo pipefail
if [[ "${1:-}" != "-c" || $# -ne 2 ]]; then
  echo "seat-sandbox: expected -c <command>" >&2; exit 126
fi
cmd=$2; cwd=$PWD
# Scratch MUST NOT overlap cwd or any write root (see Gotcha 1).
scratch=$(mktemp -d "${HERETEK_JAIL_SCRATCH:-/var/tmp}/seatjail.XXXXXX")
trap 'rm -rf "$scratch"' EXIT
binds=()
IFS=':' read -ra roots <<< "${HERETEK_SANDBOX_WRITE:-}"
for r in "${roots[@]}"; do
  [[ -n "$r" ]] || continue
  abs="$cwd/$r"; mkdir -p "$abs"; binds+=(--bind "$abs" "$abs")
done
mask=()
[[ -n "${HERETEK_SECRET_STORE:-}" && -d "$HERETEK_SECRET_STORE" ]] && mask+=(--tmpfs "$HERETEK_SECRET_STORE")
exec bwrap \
  --die-with-parent --new-session \
  --unshare-pid --unshare-ipc --unshare-uts --unshare-net \
  --ro-bind / / --dev /dev --proc /proc \
  --bind "$scratch" "$scratch" --setenv TMPDIR "$scratch" \
  "${binds[@]}" "${mask[@]}" --chdir "$cwd" \
  /bin/bash -c "$cmd"
```

### M5 — Close the git-diff read bypass + identity forgery (#69, #72, #93)
**Do:**
1. In `render-seat.py` F3 tuple **and** `verify-rigs.sh:588` mirror tuple, add (keep them identical): `"* -u*"`, `"*\t-u*"`, `"* -U*"`, `"*\t-U*"`, `"*--unified*"`, `"*--cc*"`, `"* -c *"`, `"* -m *"`, `"* -W*"`, `"*--function-context*"`, `"*--word-diff*"`, `"*--color-words*"`, `"*--binary*"`, `"*--raw*"`. Also add a leading-env-assignment deny (a key that denies commands beginning `VAR=`): add `"* -c core.*"` is **not** enough — add `"*OPENRIG_SESSION_NAME=*"`, `"*OPENRIG_URL=*"`.
2. In `send-authenticated.sh`: `unset OPENRIG_SESSION_NAME` at the top (or exit non-zero if set); require the receipt has `persisted == true` and `state in {pending,in-progress}` and no `createWarning`; reject any `--source` equal to a fleet member id.
3. Update `gate-role.sh` with deny probes for `git log --oneline -u`, `--cc`, and `OPENRIG_SESSION_NAME=x rig whoami`.
**Acceptance:** `gate-role.sh go-backend-eng` denies all the new git-diff forms and the env-prefixed `rig` call. `send-authenticated.sh` with `OPENRIG_SESSION_NAME` set refuses. A fake receipt `{"state":"failed","persisted":false}` makes it exit non-zero.

### M6 — Harden the audit_loop evaluator (#79)
**Do:** in `audit_loop.py`, match `^#{1,6}\s*HR-[\w.-]+`; treat any `\bP[0-3]\b` Defect-Matrix cell, any BROKEN/PARTIAL token after stripping `*_~` and emoji, and any Sabotage row whose last cell ≠ `yes` as findings. Add all 8 vectors from #79 to `run_self_test`.
**Acceptance:** `python3 scripts/audit_loop.py --self-test` exits 0, and each of the 8 vectors returns `FINDINGS_DETECTED` (add them as asserts in the self-test).

### M7 — Governance gates (#83, #84)
**Do:** `sweep-typed-blocks.py` — for `auth:` blockers require `actorSession` ∈ {operator, TPM seat}, exact blocker-string equality (no token overlap), and a resolvable evidence qitem. `reconcile_model.py` — count a queue item terminal only on `state`; accept notes only matching `^QA PASS\b` with no negator (`not|no|never|n't`) or fail token; apply the same to tracker cells.
**Acceptance:** the #83 cases A and B return stay-blocked; the #84 fixture ("QA pass NOT granted; NOT placed", state in-progress) exits 1 NEEDS-HUMAN-REVIEW. Existing `test_sweep_typed_blocks.py` and `test_reconcile.py` still pass.

### M8 — Envelope semantics (#92)
**Do:** `check-envelope.py` — deny path scopes with leading-dot/`.git`/`.pi`/`.agents`/`fleet/`/`scripts/`/`AGENTS.md`/leading `-`/`:`/non-ASCII/`%`; refuse `PUSH` to `main|master|HEAD`; parse all deadlines and govern by `min()`, require `issued_at <= now < deadline <= issued_at + 14d`; validate seats against `fleet.yaml`; require BY WHOM = TPM seat or named human; require link-shaped audit values.
**Acceptance:** every row in #92 returns REFUSE (rc=1); the existing 49 `test_check_envelope.py` tests still pass (now wired into `make test` from M3).

### M9 — Supply-chain + registry gates (#70, #71, #85, #86, #87, #97, #99, #100)
**Do:**
- #70/#100: pin every sidecar image by real `@sha256:` (resolve on-host, see "Not verified"); set Dockerfile `OPENRIG_VERSION=0.6.13`; generate install lists from the catalog. Add a V12 networked image-existence check (skippable offline with a recorded skip).
- #71: V12 asserts exact per-server security args/env (`radare2.args==["-R"]`, k8s `--read-only`, postgres `--access-mode=restricted`, ClickHouse write `"false"`, AWS `READ_OPERATIONS_ONLY=="true"`), pin==args-pin, and deny-lists `r2mcp`/`aws-mcp`/`pi-subagents`/`pi-lsp@0.1.7`.
- #85: vendor skills with `git archive <sha> <path>` (or fail if any pinned clone is dirty) in `generate-rigs.py`.
- #86: V12 asserts roster seat-set == 51 fleet sessions and omni command pod == {exec-director, system-architect, tpm-scrum-lead} lead exec-director.
- #87: V12 scans `specs/agents/*/<role>/` (excluding `skills/`, `@TOOLS@/@SECRETS@/@SEAT@`) for `\b(TODO|FIXME|TBD|PLACEHOLDER)\b|\{\{[A-Za-z_]+\}\}`.
- #97/#99: derive attestation from real run records or emit "Not tested"; stamp `DIRTY-<sha>` under ALLOW_DIRTY and reject it in verify.
**Acceptance:** each sabotage listed in those issues now makes `./scripts/verify-rigs.sh --check-only` exit 1. Clean tree still 27+N passed, 0 failed. `generate-rigs.py` twice → clean tree.

### M10 — Final pass + PR
**Do:** re-run `./scripts/verify-rigs.sh --check-only`, `make test`, `python3 scripts/audit_loop.py --self-test`, and `python3 scripts/generate-rigs.py` (twice, confirm clean). Walk every finding #67–#102 and tick its "Verify the fix" command. Open the PR with the body format below.
**Acceptance:** all gates green; every P0/P1 "Verify the fix" command passes; `docs/NOTES.md` lists every discrepancy found. PR body lists each issue with its verify command and result.

## Gotchas (re-read before every milestone)

1. **`--tmpfs /tmp` (or any tmpfs/bind over a parent of cwd) shadows the workspace.** The audit's first wrapper put the jail scratch under `/tmp` and the workspace vanished inside the jail. `seat-sandbox.sh` puts scratch under `/var/tmp` and binds write roots explicitly. If a seat workspace ever lives under `/tmp`, the scratch dir must move.
2. **The sandbox does not mask secrets committed into the workspace.** Only the out-of-tree secret store is tmpfs'd. In-tree `prod.env` is closed by the git-diff denies (#69) plus never committing secrets — say so, don't claim the jail covers it.
3. **render-seat.py and verify-rigs.sh hold mirror copies of the terminal-deny tuple** (F3). Change both or verify-rigs fails at `:1158`.
4. **Never `yaml.safe_dump` `fleet/fleet.yaml`** — it strips the comments the file depends on. Surgical text edits only.
5. **A missing `shellPath` fails closed** ("Custom shell path not found") — good, but it means `seat-sandbox.sh` must exist at the absolute path you write, on every host. The tool-existence gate (M3) must cover it.
6. **pi `quietStartup: true`** hides startup notices, which is why #67 was silent. Don't rely on a startup warning; assert at render time.
7. **`rig bundle check` does not validate `rig.all-51.yaml`** and returns an object, not `[]` (#96 P3 / audit HR-2.5). Use `rig spec validate` for all-51.
8. **gate-role.sh seeds a committed `fleet/fleet.yaml` canary** in its scratch work tree so patch-exfil probes are decisive — keep that when you add git-diff probes.

## Definition of done

- [ ] M1 proved shellPath is honored by both the CLI and a daemon-launched seat (or the fallback is documented).
- [ ] #67: a missing pps path makes render exit non-zero; no `--allow-missing` escape.
- [ ] #68: no `builtin:locked` seat holds a runner verb; the F2 escape corpus fails under the sandbox.
- [ ] #69: all git-diff read forms denied on all 51 seats (gate-role green with new probes).
- [ ] #70/#100: every sidecar image resolves; Dockerfile on 0.6.13.
- [ ] #71: each MCP-flag sabotage turns verify-rigs red.
- [ ] #72/#73: env-prefix forgery denied; dependency-patcher cannot commit.
- [ ] #79: 8 evaluator vectors return FINDINGS_DETECTED; self-test covers them.
- [ ] #82: all 10 suites run in `make test` and in verify-rigs.
- [ ] #83/#84/#92: governance and envelope fixtures fail closed.
- [ ] #85/#86/#87/#97/#99: each listed sabotage turns verify-rigs red.
- [ ] `verify-rigs --check-only`, `make test`, `audit_loop --self-test`, `generate-rigs` (×2) all green/clean.
- [ ] `docs/NOTES.md` logs every discrepancy; PR opened, not merged.

## PR body format

```
## Remediation: audit #66 P0/P1

Fixes: #67 #68 #69 #70 #71 #72 #73 #79 #82 #83 #84 #85 #86 #87 #92 #93 #97 #99 #100

| Issue | Fix | Verify command | Result |
|---|---|---|---|
| #67 | render fails closed on missing pps | (command) | PASS |
| ... | | | |

Gates: verify-rigs 27+N/0, make test OK (10 suites), audit_loop self-test OK, generate-rigs clean ×2.
Not done / follow-up: <list P2/P3 deferred, link #102>.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014wevSWHET5eqHNVNTYZnx9
```
