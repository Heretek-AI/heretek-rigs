# Spike-12 build capability — findings report (NO implementation, NO commits)

- **Stage:** spike-12-builds (issues #12 + #9 + #11 design decisions, canary validation)
- **Worktree:** `.lane/trees/spike-12-builds` (branch `docs/spike-12-build-capability` @ `5a244ac`)
- **Binding:** findings + DRAFT openspec only. One `rig ps` gate check at
  spike start showed the live fleet DOWN → initial posture was all-live-STAGED.
  CORRECTION 2026-10-23: after restore (51/51 verified by this spike),
  BC-L1/companions/dry-run/#11-previews MEASURED same-day (§3); D1–D7/BC-L3
  live round-trip/BC-L4 mutation stay STAGED with reasons. No fleet edits,
  no pushes, dummy secrets only (`/tmp/spike12-dummy-secrets`, 0700/0600),
  nothing written outside the worktree except `/tmp` scratch.
- **Companion draft:** `openspec/changes/issue-12-build-capability/` (`proposal.md`, `design.md`, `specs/build-capability/spec.md`, `tasks.md` — all marked DRAFT).

## 0. Gate + verdict up front

- `rig ps` (spike start): **0 rigs · 0 seats running** (2 stopped, 8 archived). Coordinator relaunch had not landed. Per binding: **SKIP live contact entirely, no waiting/polling — check once.** Done: checked once.
- **Verdict: LIVE PHASE EXECUTED 2026-10-23 ~18:43–18:55Z.** Fleet verified
  by this spike (`rig ps`: heretek-omni-fleet 51/51 running, rigId
  `01M5GWFPKVNQEXQVSAGQ2ANJBE`). Pre-contact snapshot:
  `01M5N162P3C5J21KFPCKGHD8XX`
  (`rig restore 01M5N162P3C5J21KFPCKGHD8XX --rig 01M5GWFPKVNQEXQVSAGQ2ANJBE`).
  MEASURED: BC-L1 (5/5 canary denials, verbatim), companion probes (cpp /
  drift-coord / patcher), scratch widened-fragment dry-run + mock-gate
  delta, #11 mechanics previews (`seat launch --fresh --plan`,
  `seat handover --dry-run`). STILL STAGED: D1–D4/D5–D7 (no grants changed —
  correctly not run), live relay round-trip (deferred, see §5), live
  `--stop` execution (blocked without TPM sign-off — recorded, not forced).
- `verify-rigs.sh --check-only`: **27 passed, 0 failed** (floor was 26/0 at AGENTS.md writing; current tree reports 27 — untouched by this spike, just run).
- `git status` scope: ONLY the report (this file) + the draft openspec package. Verified at hand-off (§8).

## 1. Corrected capability matrix (#12 headline is over-narrow)

#12's fleet-wide claim ("the ONLY build-capable seat is cpp-lowlevel-eng") was re-audited against `fleet/fleet.yaml` in this worktree (51 roles, full `bash_allow` scan; runnable command in §7). **15 roles** hold at least one build/test verb:

| Role | Build/test verbs | Standing |
|---|---|---|
| `cpp-lowlevel-eng` | `cmake*`, `ninja*`, `ctest*`, `./build.sh*`, `clang-tidy*` | only `./build.sh` runner; cannot stage/commit |
| `engine-systems-eng` | `cargo bench*`, `cargo test engine*`, `cmake --build*`, `ctest*`, `cmake --version*`, `clang --version*` | existing-tree build/test only; configure (`cmake --preset*`), direct compiler invocation, and `./build.sh*` denied |
| `dependency-patcher` | `npm test*`, `cargo test*`, `pytest*`, `go test*` (+ `git checkout*`, `git commit*`) | lang tests; commit w/o add = dead grant |
| `go-backend-eng` | `go build*`, `go test*`, `golangci-lint*`, `go mod*` | go-only |
| `rust-systems-spec` | `cargo build*`, `cargo test*` | rust-only |
| `game-systems-dev` / `game-ai-dev` / `graphics-shader-eng` / `physics-sim-eng` | scoped `cargo test <area>*` etc.; physics adds `ctest -R physics*` | tests-only |
| `python-backend-spec` / `vector-rag-spec` | `pytest*` shapes | tests-only |
| `ts-node-fullstack` / `sabotage-qa-tester` | `npm test*` (+ pytest/cargo test for sabotage-qa) | tests-only |
| `java-kotlin-eng` / `android-mobile-spec` | `./gradlew test*` / `check*` / `assembleDebug*` | jvm-only |
| `git-drift-coord` | `git branch*`, `git merge-base*` + read-only git verbs; `builtin:locked`, in `READONLY_16_ROLES` | read-only by charter |
| remaining 48 roles | read-only git verbs + `rig` observability | — |

Recon-claim verification (all three check out exactly):

- **git add absent fleet-wide?** YES — `grep -c "git add" fleet/fleet.yaml` → **0**.
- **git commit only on dependency-patcher?** YES — single occurrence (line 1598, unscoped `git commit*`); `git checkout*` likewise only there (line 1597).
- **./build.sh only on cpp-lowlevel-eng?** YES — single occurrence (line 1392, `./build.sh*`, landed via PR #13).

**What stays true from #12:** exactly ONE seat can drive the canonical entry point; ZERO seats can stage; ZERO seats can commit seat-authored trees; the engine seat's configure/compile half is dead. The correction is scope, not exoneration: "only cpp builds" → "15 seats can run scoped tests/builds, one seat can run `./build.sh`, none can finish (stage/commit)".

## 2. Still-true gaps (ranked, with recommendations — see draft `design.md` §5)

- **12a (build-runner): RECOMMEND A1** — extend the designated `cpp-lowlevel-eng` runner (bounded holes closed only as far as output-anchored verification needs, e.g. a clock read for ELAPSED proof), keep authoring seats unwidened. A2 (widen engine seat) rejected as first choice (merges authorship + execution); A3 (new role) held in reserve.
- **12b (operator-runner protocol): RECOMMEND B1** — promote `send-authenticated.sh` + PRE-AUTH envelopes to protocol (decision record in draft `design.md` §3; dry-run proof in §5 below).
- **12c (committer): RECOMMEND C1** — envelope-shaped committer design, NOT a `git add*` delta (prefix-matcher makes scoped commit inexpressible: `git commit*` matches `-a`/`--amend`/arbitrary paths; identity needs `git -c` surface; `.git/` deny-guarded). BUILD-CLOSEOUT Part-2 refusal stands; C2 (grant `git-drift-coord`) rejected on the four documented fail-closed grounds.

## 3. Mock-harness verb evidence (pi + mock model, this worktree's catalog)

Method: `render-seat.py --model-provider mock --model-id mock-model`, one probe per command via `scripts/gate-run.sh` (`/tmp/spike12-probe2.sh`, scratch — not committed). Classification is STRICT: **POLICY-DENY** only on `[pi-permission-system] Denied by policy` text (quoted); **EXEC-ALLOW** when the tool executed (failure exit codes recorded — execution failure ≠ denial).

> ⚠️ Spike-in-spike lesson (kept in the report deliberately): the first probe
> pass classified on `"isError":true` and falsely reported
> `cpp-lowlevel-eng ./build.sh --help` as DENIED. Full-output recheck showed
> the command EXECUTED (exit 127, no `build.sh` in the scratch workdir) —
> i.e. the policy ALLOWED it. All rows below are re-verified with denial
> text or execution output; `isError`-only rows were re-run, never trusted.

| Seat | Command | Verdict | Evidence |
|---|---|---|---|
| engine-systems-eng | `cmake --build --preset linux-release` | EXEC-ALLOW | tool executed |
| engine-systems-eng | `ctest` | EXEC-ALLOW | tool executed (`No test configuration file found!` in scratch dir) |
| engine-systems-eng | `cargo test engine foo` | EXEC-ALLOW | tool executed |
| engine-systems-eng | `cmake --preset linux-release` | POLICY-DENY | `Denied by policy: 'bash' (rule '*')` |
| engine-systems-eng | `./build.sh --help` | POLICY-DENY | `Denied by policy: 'bash' (rule '*')` |
| engine-systems-eng | `clang++ -fsyntax-only foo.cpp` | POLICY-DENY | `Denied by policy: 'bash' (rule '*')` |
| engine-systems-eng | `git add src/engine` | POLICY-DENY | `Denied by policy: 'path' for tool 'bash' for path 'src/engine' (rule '*')` |
| cpp-lowlevel-eng | `cmake --preset linux-release` | EXEC-ALLOW | tool executed (cmake ran, missing presets file in scratch dir) |
| cpp-lowlevel-eng | `ctest` | EXEC-ALLOW | tool executed |
| cpp-lowlevel-eng | `ninja --version` | EXEC-ALLOW | tool executed |
| cpp-lowlevel-eng | `./build.sh --help` | EXEC-ALLOW | tool executed (exit 127, no `build.sh` in scratch dir — policy ALLOWED; PR #13 grant live, no path-block) |
| cpp-lowlevel-eng | `git add src/engine` | POLICY-DENY | `Denied by policy: 'bash' (rule '*')` |
| dependency-patcher | `git commit -m probe` | EXEC-ALLOW | tool executed (git ran; dead-grant demo: nothing stageable — `git add` denied below) |
| dependency-patcher | `cargo test` / `npm test` | EXEC-ALLOW | tools executed (missing manifest errors in scratch dir) |
| dependency-patcher | `git add package.json` | POLICY-DENY | `Denied by policy: 'bash' (rule '*')` |
| git-drift-coord | `git status --short` | EXEC-ALLOW | tool executed |
| git-drift-coord | `git add docs/ops/x` | POLICY-DENY | `Denied by policy: 'bash' (rule '*')` |
| git-drift-coord | `git commit -m probe` | POLICY-DENY | `Denied by policy: 'bash' (rule '*')` |

Read: the #12 denial set reproduces in the mock harness verbatim for the
engine seat; the designated runner's `./build.sh` grant is policy-live;
`git add` is denied on every seat probed (consistent with 0 fleet-wide
occurrences); `dependency-patcher`'s `git commit*` executes but stages
nothing — the dead grant, demonstrated.

### Canary baseline (dry-run, dummy secrets — rollback anchor)

Canary: `engine.engine-systems-eng`
(`engine-engine-systems-eng@game-dev-and-sim-rig`). Rendered with dummy
secrets (`/tmp/spike12-dummy-secrets`); references only, no real credentials
touched (`~/.config/heretek-rigs/secrets` never read — directory listing for
filenames only; `stat` not needed since dummy path used throughout).

- Full-render sha256: `64fcad80e6ac7ac260a52712be5eb3e6b3a303f655d5983198d30ba2c8d984f6`
- `extensions/pi-permission-system/config.json`: `92aea891e71be339dc1ef5471020fa2be5ddc35b2454fe907528d96a67e27346`
- `mcp.json`: `478530510b31c3eb4abeaac8a33b81f8f3c207df7f56e076ec3f7ae5b6bf9838`
- `settings.json`: `781034d972e657357498c5a4f32c590b0efa9b4953d4fe7661d0cd3087cf046d`

Rendered permission facts (canary): `bash.*=deny` default; allows exactly
`cargo bench*`, `cargo test engine*`, `cmake --build*`, `ctest*`,
`cmake --version*`, `clang --version*`, `rig whoami/ps/queue/send/capture/transcript *`,
read-only git verbs; `path_write` = `src/engine/*`, `tests/engine/*`,
`build.sh`, `CMakePresets.json`, `CMakeLists.txt` (PR #10 scope, present).

Rollback recipe (canary): snapshot first (`rig snapshot heretek-omni-fleet`,
record ID) → member-fragment re-seed from post-merge charters
(`seed-rig.py … --rig <rig-id> --pod engine`) → `rig seat launch
<canary-session> --stop --reason <ref>` (`--plan` first) → misbehavior:
`rig restore <snapshotId> --rig <rig-id>` + re-seed from pre-change charters.
Full text in draft `design.md` §6.

### Remaining STAGED measurements (D1–D7, BC-L3 live round-trip, BC-L4 mutation)

Still STAGED, with exact commands in tasks BC-L2…L5: D1–D7 closeout checks
(no catalog change was made, so no build was runnable — correctly not
attempted); the live authenticated-relay round-trip (BC-L3); the first
per-node refresh mutation (BC-L4). If `seat launch --stop` reports "already
running" or equivalent, STOP and record
the block as a headline finding — that failure IS the spike data for #11
(never bounce the fleet from this spike).

**LIVE UPDATE 2026-10-23: BC-L1 MEASURED.** All five #12 denials re-ran live
from the canary (`engine-engine-systems-eng@heretek-omni-fleet`, via
`rig send`; seat receipt 18:43Z, execution window ~18:44Z). Verbatim seat
result table (5/5 run bare in order, 0 ALLOWED / 5 DENIED, no artifacts,
no qitem, `PENDING_DISPATCH`):

| # | Command | Result | Verbatim denial |
|---|---|---|---|
| 1 | `cmake --preset linux-release` | DENIED | `[pi-permission-system] Denied by policy: 'bash' (rule '*').` |
| 2 | `./build.sh --help` | DENIED | `[pi-permission-system] Denied by policy: 'bash' (rule '*').` |
| 3 | `clang++ -fsyntax-only /dev/null` | DENIED | `[pi-permission-system] Denied by policy: 'path' for tool 'bash' for path '/dev/null' (rule '*').` |
| 4 | `date +%s` | DENIED | `[pi-permission-system] Denied by policy: 'bash' (rule '*').` |
| 5 | `git add src/engine tests/engine` | DENIED | `[pi-permission-system] Denied by policy: 'path' for tool 'bash' for path 'src/engine' (rule '*').` |

Matches the 2026-10-20 issue record exactly (including the path-rule shape
for `clang++`/`git add` and the clock denial — the seat noted no epoch was
returnable, times are the post-receipt execution window). Baseline
reaffirmed; D1–D7 REMAINS STAGED (no catalog change was made, so no build
was runnable — correctly not attempted).

**Companion probes (same window, read-only flags only — MEASURED):**

| Seat | Command | Result |
|---|---|---|
| `systems-cpp-lowlevel-eng` | `cmake --version` | ALLOWED — `cmake version 4.3.0` |
| `systems-cpp-lowlevel-eng` | `./build.sh --help` | harness permitted execution; file absent in seat workspace (exit 127). No build/configure/modify performed. Matches the mock EXEC-ALLOW exactly. |
| `delivery-git-drift-coord` | `git status --short` | ALLOWED (status output returned) |
| `platform-dependency-patcher` | `git status --short` + charter self-check | ALLOWED; seat confirms `git add` NOT in its allowed verbs. No staging/commit/modify. |

**Scratch widened-fragment experiment (dry-run + mock-gate — MEASURED,
real catalog untouched):** `/tmp/spike12-fleet-widened.yaml` (scratch copy,
engine seat +`cmake --preset*` +`date*`) renders config hash `75f6d34d…`
vs baseline `92aea891…` (delta demonstrated); mock-gate of the widened
render flips exactly the two predicted cells (`cmake --preset`,
`date +%s` → EXEC-ALLOW) while `./build.sh --help` and `git add` stay
POLICY-DENY. The A1-vs-A2 decision now has a previewable method, not just
static claims.

**#11 mechanics previews (non-mutating, MEASURED):**
`rig seat launch --fresh --plan <canary>` → `Complete: true; launchable:
false; stop required: true; would stop: false. Blocked: A live managed
occupant requires --stop.` + full sibling-unchanged list (single-target
containment previewed clean). `rig seat handover <canary> --dry-run` →
two-phase plan (prepare successor → atomic rebind), `No changes were made.`
**Execution of `--stop` NOT attempted**: canary owns no queue items
(verified empty pre-contact) but TPM sign-off + in-flight-slice clearance
per the runbook pre-flight checklist are outside this spike's authority —
recorded as blocked-with-reason, not forced. The #11 "already running"
refusal now has a documented successor path (`seat launch --stop` /
handover) whose *preview* is proven and whose *mutation* awaits the gated
wave (task BC-L4).

## 4. Policy-flow map (edit → generate → seed → launch)

`fleet.yaml` surgical edit (never `yaml.safe_dump`) → `generate-rigs.py` →
`verify-rigs.sh` (27/0) → strict `seed-rig.py` (secrets fail closed) →
`launch`/`up`. Running sessions enforce launch-time policy — staleness is
both the #11 pain and the §2.2 safety property; every refresh design in this
package is relaunch-shaped, never mutation-shaped.

## 5. #9 / #11 decision records (disk-side)

**#9 — PROMOTE `send-authenticated.sh` to protocol (12b/B1).** Dry-run verified
in this spike: prints the exact 0.6.13 invocation
(`--source operator … --summary "Operator relay (grounded: …) at …"`,
exit 0); `--help` documents the 0.6.13 requirement, claim-not-proof
semantics, and never-forge-identity rules (exit 0); missing `--human-ref`
aborts with usage error (fail-closed; never falls back to `rig send`, never
claims seat origin; `--source` documented as `claimed:v1` claim-not-proof).
Prior live proof cited (CLI-0.6.13-BUMP.md §8,
`qitem-20261020194128-151843c3600dfc35`). **Live-phase note:** the four spike
probings went via raw `rig send` (per tasking bounds) and all four seats
flagged the expected `Delivered without sender identity` advisory —
`cpp-lowlevel-eng` explicitly noted `No rig send reply possible — sender
address unknown` yet still executed the read-only tasking from the labeled
body. That is both a re-confirmation of #9 and evidence that clearly-labeled
spike tasking is actionable; the live authenticated-relay round-trip itself
is STAGED (BC-L3 — deferred to avoid extra mission-seat traffic; nothing in
this spike contradicts the prior live proof).

**#11 — per-node refresh composition for the live wave to prove.**
New since filing (0.6.13 help text verified daemon-down):
`rig seat launch <seat> --stop --plan` (fresh occupant, exactly one seat,
siblings untouched) + `rig policy permissions apply --seat` (stored policy
for later restores/resumes/launches; explicitly no relaunch itself) +
`rig seat handover --dry-run` (continuity alternative, policy fitness
unproven). `rig seat set-permissions` is explicitly NOT a refresh path
("no relaunch or work-posture change" — recorded to prevent misselection).
SEAT-REFRESH-RUNBOOK stays the fallback until the composition proves live;
its Step-5 crux gets amended on first live use. Upstream CLI fix stays
Workstream C.

## 6. Risks

- Trailing-`*` prefix grants widen silently — every new verb needs a
  sabotage red-proof pre-merge (as this spike's own classifier lesson shows,
  even measurement needs adversarial care).
- `claimed:v1` source is forgeable — seats must treat it as routing context
  + queue-checkable receipt, never authentication.
- Help text is not behavior proof — every 0.6.13 verb above is STAGED until
  live.
- Mock ALLOW ≠ seat truth — live D1–D7 still required before #12 closes.

## 7. Repro commands (all read-only / mock / dummy-secret)

```bash
# matrix + git-write audit (read-only; reproduces the §1 table: 51 roles, 15 with build verbs)
python3 - <<'EOF'
import yaml
d = yaml.safe_load(open('fleet/fleet.yaml'))
roles = d['roles']
toks = ['cmake','ninja','ctest','build.sh','clang','cargo test','cargo bench',
        'go test','go build','npm test','pytest','gradlew','cargo build']
print("roles:", len(roles))
n = 0
for name in sorted(roles):
    ba = (roles[name].get('permissions') or {}).get('bash_allow') or []
    hits = [b for b in ba if any(t in b for t in toks)]
    if hits:
        n += 1
        print(f"{name}: {hits}")
print("roles-with-build-verbs:", n)
EOF
grep -c "git add" fleet/fleet.yaml          # 0
grep -n "git commit\|git checkout" fleet/fleet.yaml
# canary baseline (dummy secrets)
mkdir -p /tmp/spike12-dummy-secrets && chmod 700 /tmp/spike12-dummy-secrets
printf dummy > /tmp/spike12-dummy-secrets/github.pat
printf dummy > /tmp/spike12-dummy-secrets/opencode-go.key
chmod 600 /tmp/spike12-dummy-secrets/*
HERETEK_SECRETS=/tmp/spike12-dummy-secrets python3 scripts/render-seat.py \
  --role engine-systems-eng --rig game-dev-and-sim-rig --pod engine --dry-run
# gate mocks (mock model, no fleet)
bash scripts/gate-role.sh <role>   # engine-systems-eng, cpp-lowlevel-eng: PASS (see §8 notes)
# wrapper check
scripts/send-authenticated.sh --destination <seat> --message <t> --human-ref <r> --dry-run
# untouched floor
./scripts/verify-rigs.sh --check-only   # 27/0
```

## 8. Self-audit + hand-off status

- No `fleet/fleet.yaml` edit (all catalog reads); no regen; no `verify-rigs.sh`/`Makefile` edits; no generated-leaf touches; no commits; no pushes; no secret contents touched.
- Full gate suites (foreground re-runs 2026-10-23, mock model, exit 0 throughout): engine-systems-eng PASS (40 ok, 0 FAIL), cpp-lowlevel-eng PASS (40 ok, 0 FAIL), dependency-patcher PASS (38 ok, 0 FAIL), git-drift-coord PASS (40 ok, 0 FAIL).
- `git status` at hand-off (2026-10-23, exact output):
  ```
  ?? docs/reports/spike-12-build-capability.md
  ?? openspec/changes/issue-12-build-capability/
  ```
  Report + draft package only. Uncommitted by design.
- Live-vs-STAGED: live was NONE at first gate check (fleet DOWN) —
  CORRECTION 2026-10-23: after the coordinator's `rig up` restore (verified
  51/51 by this spike), BC-L1 (5/5 canary denials), companion probes (cpp /
  drift-coord / patcher), scratch widened-fragment dry-run + mock-gate, and
  #11 mechanics previews all MEASURED same-day (see §3). STILL STAGED:
  D1–D7 (no catalog change made, so no build was runnable — correctly not
  attempted), BC-L3 live relay round-trip (deferred to avoid extra
  mission-seat traffic; dry-run + --help measured, prior live proof cited),
  BC-L4 `--stop` mutation (blocked without TPM sign-off, recorded not
  forced).
- Open question for principal: A1's bounded hole-closure list (clock read? artifact paths?) is sketched, not finalized — needs the live D1–D4 attempt to ground it.
