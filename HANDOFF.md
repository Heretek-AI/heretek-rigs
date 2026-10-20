# Handoff — heretek-rigs fleet operator session (2026-10-20, second session)

You are taking over an active heretek-rigs session. Repo: `Heretek-AI/heretek-rigs`.
Read `AGENTS.md` at the repo root first — it holds every workflow and hard rule.
Then verify state (branch HEAD, `make verify`, `gh pr list`, daemon/rig status);
trust nothing below without re-checking.

## Live state (last verified this message)

- Fleet is **DOWN**: all-51 omni rig stopped cleanly (snapshot `01M5C39TPWXQCQN6AC50W3FYN9`, restorable via `rig restore 01M5C39TPWXQCQN6AC50W3FYN9 --rig 01M5BWNDD71H19N6PMAZY0MQP`), daemon stopped, zero seat processes. All 51 seats idle at teardown. Kernel tmux sessions untouched.
- Fleet queue at shutdown: exactly 1 live row — `qitem-20261020060916-6bda2c374d7ab9ee` `blocked` at git-drift-coord (`external:committer-stage-denied`), STALE-fulfilled by operator commits (TPM to close on next launch). Everything else terminal.
- Workspace `/tmp/heretek-omni-51/project` kept on disk at commits `30093be` → `ae55c83` → `8706055` → `f3f5ce9` (+ `ae55c83`-amend chain `c6cce82→ae55c83` superseded). Seeded seat dirs + snapshots kept under `~/.openrig` — relaunch needs re-seed (charters changed twice since last seed).
- Repo `main` @ `88c13d7` (merge PR #13). Worktrees pruned, branches deleted. Secrets: only `opencode-go.key` at `~/.config/heretek-rigs/secrets/` (0600). Never print or copy it.
- Goal `7b4193c5…` ("drive fleet to Unity competitor, C++ base, Linux first") ACTIVE, plan rev 16, usageLimited (25 auto-continues maxed). Resume only on explicit human command.

## What happened this session

1. **Relaunch**: re-seeded 51 seats (degraded, github.pat absent — same as prior), `rig up` on existing workspace (docs preserved), 51/51 running.
2. **S01 toolchain gate → GREEN-WITH-EXCEPTIONS**: human ratified host pins (Clang 23.1.3/CMake 4.3.0/Ninja 1.13.2) + signed Vulkan exception + signed headless exception (x11/vkcube). Amendment 1 landed in ADR 0001. Engine verified 5/9 pins, zero mismatches.
3. **S02 skeleton → GREEN-CONDITIONAL** (TPM close-out `S02-CLOSEOUT-conditional-green.md`): exit 0, CTest 13/13, 600-tick determinism, ELAPSED 1s, tree `f3f5ce9`. Screenshot deferred to G0 (human-signed, no fabrication). S03 unblocked with display caveat; Sprint 1 CONDITIONAL.
4. **Two charter Triads via PRs #10 + #13** (programmer→QA PASS→drift-guard PASS each): engine-systems-eng += root `build.sh`/`CMakePresets.json`/`CMakeLists.txt`; cpp-lowlevel-eng += `./build.sh*` (designated runner). Gate line-638 interpreter ban deliberately preserved (programmer halted on `bash` form, pivoted to dot-slash).
5. **Trust incidents, all resolved**: unsigned `rig send` held as unverified (fail-closed correct) → queue-authenticated channel adopted; exec-director "AUTHORIZED operator authorship" misattributed to human chain → declined with evidence (human chose charter path); my own mislabeled commit message caught + amended before notifying anyone.
6. **Operator fallback executions** (all authorized, all reported): fleet probe evidence, S02 tree commit `30093be`, follow-ups commit `f3f5ce9`, +x landing on build.sh (amended message), no-fetch false-positive FAIL reported verbatim (note-doc tripped naive grep; engine fixed scan).
7. **GitHub issues established** (repo had zero): #9 rig-send identity, #11 no single-node refresh, #12 no seat can execute (runner PR #13 closes exec half; stays open until green build proof reviewed), #15 authorization-loop lag (first cycle already validated the pattern), #16 parallel slices (deferred), #17 utilization/throughput (deferred), #18 display/GPU runner provisioning (BLOCKS S03).

## Open PRs / decisions (verify with `gh pr list`)
- #4 `docker/fleet-images` → open, HELD (CI-only `referencing` dep fail; local 22/0 passes).
- #5 `feature/fleet-topology` → open, HELD (SonarCloud + review fails).
- #10, #13 MERGED. #9, #11, #12, #15, #16, #17, #18 = open issues.

## Pending decisions (need the human)
1. **S03 display routing**: triangle-on-swapchain has no execution home headless. Provision per #18, or sequence non-visual S03 slices first. Nothing downstream of S02 moves honestly until answered.
2. **#15 latency watch**: authorization round-trips at ~2 min (acceptable) vs stretching (trigger for standing pre-authorization envelopes).
3. **Re-seed after merges**: PRs #10+#13 changed charters post-seed; re-seed on next launch before `rig up`.

## First three things to do
1. `git pull`, `make verify` (expect 22/0), `gh pr list`, `gh issue list` for current states.
2. If relaunching: re-seed (`bootstrap-pi-seats.sh --profile all-51 --allow-missing-secrets`), `rig up rig.all-51.yaml --cwd /tmp/heretek-omni-51/project --yes` (or `rig restore 01M5C39TPWXQCQN6AC50W3FYN9`), confirm 51 `run`, close stale committer row.
3. Ask the human for the S03 display decision — it gates everything downstream.
