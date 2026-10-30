# Seat-heal runbook — bounded heal of 2 lobotomized seats (Refs #147)

Change: `openspec/changes/2026-10-30-seat-heal/`. Stage: seat-heal.
Bounds: ONLY the 2 lobotomized seats
(`build-java-kotlin-eng`, `build-python-backend-spec` @
`heretek-omni-fleet`), cap 4 relaunches (2 used). Zero queue writes.
Never Closes #147. All outputs redacted; no secret values.
Path notation (wave-established): in-repo paths are repo-root-relative
(`scripts/seat-sandbox.sh` = the expected durable shell; the stale
pruned-worktree value is `.lane/trees/fleet-proofs/scripts/seat-sandbox.sh`);
the sibling checkout resolves as `../../heretek-asset-manager` (two levels
up from the repo root). Machine-local absolute literals are redacted to
this notation throughout, including in the captured `live-health-kickoff.txt`
advisory line (redaction note: `shell_path->` field values only; verdict
and seat names verbatim).

Probe task text (bare `rig` commands only — seat-race §3 F2 sandbox
lesson):

> Seat-heal probe #147: in your shell run
> `rig queue whoami` and then `echo SEAT-HEAL-OK`. Reply here with
> both outputs verbatim: the whoami output first, then the exact line
> SEAT-HEAL-OK. If your shell policy denies echo, reply with the
> whoami output plus the line SEAT-HEAL-OK typed in your reply.

PASS = transcript shows SEAT-HEAL-OK + genuine `rig queue whoami`
output identifying the seat.

## 0. Kickoff re-verification (governs per REQ-SH1 — GO, no drift)

| Check | Observed | Verdict |
|---|---|---|
| `rig ps --nodes --json --no-cleanup -A` → `ps-kickoff-pre.txt` | 55 rows = 51 fleet seats running/idle + 4 detached `@kernel` system rows (`advisor-lead`, `operator-agent`, `operator-human`, `queue-worker` — not fleet seats) | fleet shape HOLDS |
| `build-java-kotlin-eng` activity | running / idle | repairable, in cap |
| `build-python-backend-spec` activity | running / idle | repairable, in cap |
| `settings.json shellPath` both targets | `.lane/trees/fleet-proofs/scripts/seat-sandbox.sh` (pruned-worktree repo-relative path, target missing) | STILL-DANGLING, as audited |
| `make live-health` → `live-health-kickoff.txt` | `seat-shell-paths` WARN names EXACTLY the 2 targets; other 49 clear; exit 0 | set == expected 2, ≤ cap 4 → GO |
| Queue pre → `queue-pre.json` (`-a -A --limit 10000`) | 263 rows; zero in-progress held by either target | clean baseline |

Dangling set: same 2 as the audit. No drift, no ACTIVE targets.
Wave proceeds with the 2-seat plan (cap 4 untriggered).

## 1. Pre-wave validation (repo change gate)

- `openspec validate 2026-10-30-seat-heal` → valid, rc=0.
- `./scripts/verify-rigs.sh --check-only` → 39 passed / 0 failed
  (NO new V-block) — run at close-out (§4).
- `make test` → SKIPPED with reason (zero code/test/script diffs;
  re-seed usage is an operation, not a code change; the
  `seat-shell-paths` class check from the prior wave already covers
  the class).
- `python3 scripts/audit_loop.py --self-test` → SELF-TEST PASSED —
  run at close-out (§4).
- `python3 scripts/generate-rigs.py --check-idempotent` →
  byte-identical, rc=0 — run at close-out (§4).

## 2. SH1 build-java-kotlin-eng@heretek-omni-fleet (pod build / member java-kotlin-eng)

- Per-seat activity re-check (`ps-sh1-pre.txt`): running/idle →
  proceed. No held queue rows on this target (queue-pre).
- Pre-seed shellPath: `/home/.../heretek-rigs/.lane/trees/fleet-proofs/scripts/seat-sandbox.sh`
  (dangling, as listed).
- Re-seed (cwd = main checkout):
  `python3 scripts/seed-rig.py
  rigs/heretek-omni-fleet/members/java-kotlin-eng.yaml --rig
  heretek-omni-fleet --pod build` → rc=0 ("no seat-grant binding,
  ordinary seed path (no grant issued)").
- Post-seed settings.json shellPath: `scripts/seat-sandbox.sh`
  (durable main-checkout wrapper) → target EXISTS → pre-check GREEN.
- Fresh relaunch: `rig seat launch ... --fresh --stop --reason
  "seat-heal #147: re-resolve dangling shellPath (Refs #147)" --json`
  → rc=0, status ready; superseded tmux occupant
  `01M66REP1QFV0DT1D76GR2D56Y`; fresh native occupant
  `01a18e92-f120-76af-915a-886d1e544f1c`
  (runner-state.json + sessions dir).
- Config-clean (T+25s): running/active/ready; continuity fresh;
  shellPath clean + exists; launch_cwd `../../heretek-asset-manager`
  exists → GREEN.
- Probe: `rig send ... --verify --json` → `send-sh1.json`, rc=0,
  rendered-unconfirmed (known sender-identity advisory, same as
  repair wave). Reply (T+~4min, `probe-reply-sh1.json`): `rig queue
  whoami` ran successfully with verbatim JSON output identifying
  `build-java-kotlin-eng@heretek-omni-fleet`; `echo SEAT-HEAL-OK`
  denied by seat policy (`[pi-permission-system] Denied by policy:
  'bash' (rule '*')` — seat-race §3 F2 class); seat typed
  SEAT-HEAL-OK per fallback. Seat confirms no queue work claimed.
  Verdict: HEALED (probe PASS via fallback branch).

## 3. SH2 build-python-backend-spec@heretek-omni-fleet (pod build / member python-backend-spec)

- Per-seat activity re-check: running/idle → proceed. No held queue
  rows on this target.
- Pre-seed shellPath: same dangling pruned-worktree path.
- Re-seed (main checkout,
  members/python-backend-spec.yaml --rig heretek-omni-fleet --pod
  build) → rc=0, ordinary path. Post-seed shellPath
  `scripts/seat-sandbox.sh` + exists → pre-check GREEN.
- Fresh relaunch (`relaunch-sh2.json`) → rc=0, status ready, new
  tmux sessionId `01M679DC8YV74MEC39AYQBDSY2` (generation
  `c4ce1d13-...`), supersedes `01M66RET4ETMF47CJFR2Z3A2C8`; fresh
  native occupant file
  `2026-10-30T20-53-23-327Z_01a18e96-b2fe-7482-9d03-3b56adea7159.jsonl`.
- Config-clean (T+25s): running/active/ready; continuity fresh;
  shellPath clean + exists; launch_cwd exists → GREEN.
- Probe: send → `send-sh2.json`, rc=0, rendered-unconfirmed. Reply
  (T+~3min, `probe-reply-sh2.json`): `rig queue whoami` exit 0 with
  verbatim JSON identifying the seat; echo denied by policy
  (denial quoted verbatim); typed SEAT-HEAL-OK per fallback; seat
  confirms no artifacts, no queue work claimed. Verdict: HEALED.

## 4. Close-out (wave complete)

- `ps-post.txt`: 55 rows, zero added/removed. Diffs vs kickoff
  confined to ambient `identityVerdict`/`lastActivity` observation
  ticks on all seats + `modelObservation` refresh on the 2 healed
  seats (fresh occupant activity). No non-target seat disturbed →
  fleet shape HOLDS, not a RED.
- `queue-post.json` (`-a -A --limit 10000`, 263 rows): ZERO added,
  ZERO removed, ZERO state changes vs pre. Only diff: ambient
  `pickup.evidence` minute-counter ticks on 10 pre-existing stuck
  rows (derived wall-clock annotations). ZERO wave writes.
- `make live-health` → `live-health-post.txt` (exit 0):
  `[PASS] seat-shell-paths: all 51 assessed seat path(s) resolve`
  — CLASS PROOF: zero dangling seats. Remaining WARNs are
  pre-existing ambient conditions outside this wave's scope,
  recorded honestly: `heartbeat` (5 seats age-unknown),
  `seat-idleness` (5 idle-at-prompt holders of old claimed rows —
  none are the healed seats), `tool-provisioning` (7 missing host
  tool artifacts).
- Launches: 2 (cap 4, untriggered). Sends: 2 (all rc=0
  rendered-unconfirmed). No queue writes, no installs, no upstream
  posts, no non-target seats touched, no skips, no D1-equivalent
  deviations (both probes PASS via the repair-wave fallback branch).

## 5. Wave totals

- 2/2 lobotomized seats HEALED (re-seed rc=0 × 2, relaunch rc=0 × 2,
  config-clean GREEN × 2, probe PASS × 2 via echo-fallback branch).
- 0 skips, 0 abort conditions tripped.
- Post-run class state: `seat-shell-paths` PASS — the #147 dangling
  class is fully clear (22 stale healed under seat-repair + 2
  lobotomized healed here = 24/24 audit-listed seats resolved).
