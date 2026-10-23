# DRAFT — Design: issue-12-build-capability (spike, for principal approval — NOT implementation)

> **Status: DRAFT.** Companion to `proposal.md`. All static claims verified
> read-only from disk in worktree `.lane/trees/spike-12-builds`
> (branch `docs/spike-12-build-capability` @ `5a244ac`). All live claims
> STAGED (fleet DOWN: `rig ps` → 0 rigs running at spike time). CORRECTION
> 2026-10-23: after restore (51/51 verified), BC-L1/companions/dry-run/
> #11-previews MEASURED same-day; D1–D7/BC-L3/BC-L4 stay STAGED with reasons.

## 1. Corrected capability matrix (static, verified)

Source: `fleet/fleet.yaml`, 51 roles. Method: every `bash_allow` entry
matched against build/test tokens
(`cmake`, `ninja`, `ctest`, `build.sh`, `clang`, `cargo test/bench`,
`go test/build`, `npm test`, `pytest`, `gradlew`, `cargo build`).

| Role | Build/test verbs (`bash_allow`) | Can run canonical entry? | Can stage/commit? |
|---|---|---|---|
| `cpp-lowlevel-eng` | `cmake*`, `ninja*`, `ctest*`, `./build.sh*`, `clang-tidy*` | YES (`./build.sh`) | NO (no `git add` anywhere) |
| `engine-systems-eng` | `cargo bench*`, `cargo test engine*`, `cmake --build*`, `ctest*`, `cmake --version*`, `clang --version*` | NO (no configure, no compiler, no `./build.sh`) | NO |
| `dependency-patcher` | `npm test*`, `cargo test*`, `pytest*`, `go test*` (+ `git checkout*`, `git commit*`) | partial (lang tests only) | HALF (`git commit*` w/o `git add` = dead grant) |
| `go-backend-eng` | `go build*`, `go test*`, `golangci-lint*`, `go mod*` | partial (go only) | NO |
| `rust-systems-spec` | `cargo build*`, `cargo test*` | partial (rust only) | NO |
| `game-systems-dev` | `cargo test game*`, `npm test game*`, `pytest tests/game*` | NO (tests only) | NO |
| `game-ai-dev` | `cargo test ai*`, `npm test ai*`, `pytest tests/game/ai*` | NO | NO |
| `physics-sim-eng` | `cargo test physics*`, `ctest -R physics*`, `ctest --version*` | NO | NO |
| `graphics-shader-eng` | `cargo test rendering*` | NO | NO |
| `python-backend-spec` | `pytest*`, `uv run pytest*` | NO | NO |
| `vector-rag-spec` | `pytest tests/rag*` | NO | NO |
| `ts-node-fullstack` | `npm test*` | NO | NO |
| `sabotage-qa-tester` | `npm test*`, `pytest*`, `cargo test*` | NO | NO |
| `java-kotlin-eng` | `./gradlew test*`, `./gradlew check*` | partial (jvm only) | NO |
| `android-mobile-spec` | `./gradlew testDebugUnitTest*`, `./gradlew assembleDebug*`, `./gradlew ktlintCheck*` | partial (android only) | NO |
| `git-drift-coord` | `git branch*`, `git merge-base*` + read-only git verbs; `builtin:locked`, `READONLY_16_ROLES` | NO | NO |
| all other 48 roles | read-only git verbs + `rig` observability only | NO | NO |

Fleet-wide git-write audit: `git add` → **0 occurrences**; `git commit*` →
**1 occurrence** (`dependency-patcher`, unscoped); `git checkout*` → 1
(`dependency-patcher`). The #12 recon claims check out exactly
("git add absent fleet-wide? git commit only on dependency-patcher?
`./build.sh` only on cpp-lowlevel-eng?" — YES to all three).

**Correction to #12's headline:** 15 roles (not one) hold some build/test
verb. What remains true: exactly ONE seat can drive the canonical
`./build.sh` entry point; ZERO seats can stage; ZERO seats can commit
seat-authored trees. The "cannot build" claim holds for the engine seat's
configure/compile half and for end-to-end (build→stage→commit) everywhere.

Mock-harness confirmation (pi + mock model via `scripts/gate-run.sh`,
rendered from this worktree's catalog — 18 probes, strict classification):
engine seat reproduces the #12 denial set verbatim (`cmake --preset`,
`./build.sh`, `clang++`, `git add` all POLICY-DENY with denial text);
positive controls (`cmake --build`, `ctest`, `cargo test engine`) EXEC-ALLOW;
`cpp-lowlevel-eng` EXEC-ALLOWs `./build.sh` (exit 127 in scratch dir =
policy allowed — the first-pass "DENY" was a classifier false positive,
kept as a lesson in the report); `git add` POLICY-DENY on all four roles
probed; `dependency-patcher git commit` executes but stages nothing (dead
grant demonstrated). Full table in the findings report
`docs/reports/spike-12-build-capability.md` §3.]

## 2. Policy-flow map (edit → generate → seed → launch)

```
fleet/fleet.yaml (surgical text edit; NEVER yaml.safe_dump — strips comments)
  → python3 scripts/generate-rigs.py (bakes specs/, rigs/, rosters/, registry/)
  → ./scripts/verify-rigs.sh --check-only (27/0 floor at spike time)
  → python3 scripts/seed-rig.py <member-fragment> --rig --pod (strict; secrets fail closed)
  → rig launch / rig up (running sessions keep enforcing LAUNCH-TIME policy)
```

**Staleness as safety property.** A running session never silently widens its
own permissions (Constitution §2.2). The #11 pain (one stale seat forces a
fleet-wide bounce) is the same mechanism as the safety guarantee — any
refresh design must preserve it: propagation is always relaunch-shaped, never
mutation-shaped.

## 3. #9 decision record — promote `send-authenticated.sh` to protocol

**Finding.** The #9 workaround (`scripts/send-authenticated.sh` →
`rig queue create --json --verify --source operator --destination <seat>
--summary <text> --body-file <staged>`) is the only operator→seat channel
with verifiable provenance: the queue receipt (`qitemId` + state, parsed
fail-closed) is checkable against the queue itself, unlike `rig send` (no
sender identity) or body self-claims (forgeable). CLI 0.6.13 hardened it
further: `--source` required outside a managed seat (fail-closed), `--summary`
warned-when-omitted; the wrapper already passes both on every invocation.
Live proof exists (CLI-0.6.13-BUMP.md §8: `qitem-20261020194128-151843c3600dfc35`,
seat ACK with `From: operator`).

**Decision (recommended): PROMOTE to protocol as 12b.** Keep the
never-invoke-`rig-send` and never-claim-seat-origin rules; `--source`
recorded as `claimed:v1` (a claim, not proof — documented in the wrapper
header). Remaining gap for the implementation wave: seat-side verification
wording (what a seat checks: receipt `qitemId` visible in `rig queue show` /
transcript metadata) should be pinned in one place rather than living in
wrapper comments. STAGED live item: re-run one relay against the relaunched
fleet and record the transcript ACK verbatim.

**Alternative rejected:** stamping identity via `rig send` headers — no such
verb exists upstream; body self-signing is forgeable. Queue-recorded relay
is the only checkable path with today's CLI.

## 4. #11 design — per-node refresh given CLI 0.6.13

**New verbs since #11 was filed** (help text verified daemon-down on 0.6.13;
behavior STAGED):

- `rig seat launch <seat> [--stop] [--plan] [--reason]` — "Launch a
  deliberate fresh occupant for exactly one existing seat … Sibling seats
  stay attached and untouched." With `--plan` preview. This is the closest
  thing to the missing relaunch verb #11 asks for.
- `rig policy permissions apply <name> [--seat]` — "Record a policy choice
  … with `--seat` store it on an existing seat. Restore, resume and launches
  that read the seat's stored state use the stored policy." Policy recorded
  without relaunch ("this does not relaunch seats").
- `rig seat handover <seat> --dry-run` (`fresh`/`rebuild`/`fork` sources) —
  continuity-preserving alternative, policy-change fitness unproven.
- `rig seat set-permissions` — native-permissions selection for future
  managed launches only; explicitly "no relaunch or work-posture change"
  (NOT a refresh path — recorded here to prevent misselection).

**Recommended refresh composition (for the implementation wave to prove):**

```
snapshot (rig snapshot <rig>, record ID)
  → drain/park seat queue items (queue list --destination; block/fallback)
  → re-seed member fragment from post-merge charters (seed-rig.py)
  → rig policy permissions apply --seat (if stored-policy path needed)
  → rig seat launch <seat> --stop --plan first, then execute
  → confirm: rig ps --nodes + make audit-sessions + make gate ROLE=
  → unpark HELD items
```

Rollback = `rig restore <snapshotId> --rig <rigId>` + re-seed from
pre-change charters + re-launch (existing SEAT-REFRESH-RUNBOOK §5 stands;
amend its Step 5 crux — "`launch` refuses running nodes" — with the
`seat launch --stop` alternative on first live use).

**What stays:** the SEAT-REFRESH-RUNBOOK fallback (remove+launch path) until
the composition above is proven live; the upstream CLI fix stays tracked
under Workstream C. If `seat launch --stop` also refuses or disturbs
neighbors, STOP and record — that failure is spike data, and the runbook's
when-to-bounce rules (§6) govern.

## 5. Ranked options

### 12a — build-runner scope

- **Option A1 (RECOMMENDED): extend the designated runner.** `cpp-lowlevel-eng`
  already holds `cmake*`/`ninja*`/`ctest*`/`./build.sh*`. Close its remaining
  holes ONLY as far as output-anchored verification needs (e.g. a bounded
  clock read for ELAPSED proof — `date*`-shaped grant — and any missing
  artifact-path writes), each grant paired with a checkable artifact (exit
  code + committed log + no-fetch scan). Authoring seats stay unwidened.
- **Option A2:** widen `engine-systems-eng` with `cmake --preset*` +
  compiler + `./build.sh*`. REJECTED as first choice: it merges authorship
  and execution in the seat that owns the tree it would then vouch for;
  weakens the separation that makes output-anchored verification meaningful.
- **Option A3:** new dedicated `build-runner` role. Viable but heavier
  (charter + regen + seed + seat); prefer only if A1's grant list cannot be
  bounded within cpp-lowlevel-eng's existing charter.

### 12b — operator-runner protocol

- **Option B1 (RECOMMENDED): promote `send-authenticated.sh` + PRE-AUTH
  envelopes** (§3). Process-only, no permission change, provable on the
  relaunched fleet in one relay round-trip.
- **Option B2:** new queue-native operator-runner verbs. Upstream work,
  out of scope for this repo change.

### 12c — committer scope

- **Option C1 (RECOMMENDED): envelope-shaped committer design.** Standing
  `git add`/`git commit` grants are inexpressible safely under trailing-`*`
  prefix matching (`git commit*` matches `-a`/`--amend`/arbitrary paths;
  `git -c` identity needs separate config surface; `.git/` is deny-guarded).
  Design instead: exact-argv allowlisting and/or operator-executed commits
  under A2 envelopes, on a non-locked non-readonly role, with TPM-gated
  provenance. This is a design task, not a delta — the BUILD-CLOSEOUT
  Part-2 refusal stands.
- **Option C2:** scoped `git add/commit` for `git-drift-coord`. REJECTED
  (four independent fail-closed reasons in BUILD-CLOSEOUT-CRITERIA.md §5:
  unscoped-commit-by-construction, identity surface, wrong role, A2
  pre-emption).

## 6. Canary experiment (LIVE LOG 2026-10-23 — was STAGED, now MEASURED where noted)

Canary seat: `engine.engine-systems-eng`
(`engine-engine-systems-eng@heretek-omni-fleet`). Baseline rendered
policy hashes (dry-run, dummy secrets, this worktree's catalog):

- `extensions/pi-permission-system/config.json`: `92aea891…7ae5b6` (full in report)
- `mcp.json`: `47853051…f9838` · `settings.json`: `781034d9…d3087cf`

Planned re-seed/relaunch recipe that would restore the canary (rollback —
only the named preview steps ran 2026-10-23; launch/reseed/restore NOT executed):

```bash
rig snapshot 01M5GWFPKVNQEXQVSAGQ2ANJBE   # MEASURED: snapshot 01M5N162P3C5J21KFPCKGHD8XX created
python3 scripts/seed-rig.py <member-fragment-for-engine-systems-eng> \
  --rig <rig-id> --pod engine              # NOT executed (planned: from post-merge charters)
rig seat launch engine-engine-systems-eng@heretek-omni-fleet --fresh \
  --reason "<change-ref>"                  # MEASURED: --plan preview only ("launchable: false;
                                           #  stop required: true", siblings unchanged);
                                           #  live --stop execution NOT attempted
rig seat handover engine-engine-systems-eng@heretek-omni-fleet \
  --reason "<ref>" --dry-run               # MEASURED: two-phase plan preview, no changes made
rig restore 01M5N162P3C5J21KFPCKGHD8XX --rig 01M5GWFPKVNQEXQVSAGQ2ANJBE
                                           # NOT executed (planned rollback handle)
```

Live denial baseline (BC-L1, 2026-10-23 ~18:44Z): 5/5 DENIED verbatim —
`cmake --preset`, `./build.sh --help`, `clang++ -fsyntax-only /dev/null`,
`date +%s`, `git add` — matching the 2026-10-20 issue record exactly; full
table in the findings report §3. D1–D7 REMAINS STAGED (no catalog change,
no build runnable — correctly not attempted).

## 7. Risks

- Prefix-matcher grants widen silently (`trailing-*`); every new verb needs
  a red-proof (sabotage replay) before merge.
- `claimed:v1` source is forgeable by construction — seats must treat it as
  routing context + queue-checkable receipt, never as authentication.
- Stored-policy (`apply --seat`) vs launch-time enforcementComparisons must
  be verified live; help text is not proof.
- Mock-harness allows are catalog truth, not seat truth — live D1–D7 still
  required before #12 closes.
