# Fleet-proofs runbook evidence — 2026-10-30 (live host)

Conventions: every command below ran on the fleet host with real outputs.
Bearer-shaped strings: none (secrets verified by stat + `!cat` only).
`Refs` only — no issue is closed by this wave.

## Step 1 — secrets safe-check (REQ-P1) GREEN with hardening

- `stat ~/.config/heretek-rigs/secrets` -> dir `700 john`: OK.
- `github.pat`: was `644` (FINDING) -> `chmod 600` -> re-stat `600`: OK.
- `opencode-go.key`: `600`: OK.
- `render-seat.py --role appsec-engineer --rig defensive-sec-and-red-team
  --pod blue --dry-run` -> rc=0, `auth.json` carries `!cat ...opencode-go.key`
  (reference only); one fail-loud `trivy fs*` warn (gate by design).

## Step 2 — provisioning re-take (REQ-P2) DOCUMENTED + Brew-resolved

- Before: `r2`/`rabin2`/`tshark`/`trivy` MISSING; `go 1.27.3`, `pytest 9.1.1`,
  `cmake 4.3.0`, `bwrap 0.13.1`, `rig 0.7.5 (b57c4da3)` PRESENT.
- `sudo -n` -> password required: unattended apt impossible (recorded).
- Brew (user-approved, no sudo): `trivy 0.76.1`, `radare2 6.2.4`
  (`r2`+`rabin2`), TShark 4.6.9 poured; linuxbrew bin already on PATH.
- Proof: re-render `red-binary-reverse-eng@defensive-sec-and-red-team`
  --dry-run rc=0, B1-B3 warns GONE (only `r2mcp` git-artifact warn remains).
- Matrix `docs/74-PROVISIONING-MATRIX.md`: 2026-10-30 re-take + Brew
  resolution recorded. Remaining follow-ups: `r2mcp` clone, `markdownlint`,
  6 npm artifacts (renders stay `enabled:false` by design).

## Step 3 — #91 in-seat builds (REQ-P3a) PARTIAL-GREEN

- pytest via `ml-vector-rag-spec`: `WORKDIR=tests/rag, RC=0, TAIL=1 passed`
  -> GREEN.
- cmake via `systems-cpp-lowlevel-eng`: `WORKDIR=src/probe91cmake, RC=0`,
  configure wrote build files -> GREEN. (Workspace: seat's saved cwd under
  an asset-manager checkout; `src/*` policy-allowed. Probe dir left in
  place, disclosed.)
- go via `build-go-backend-eng`: round 1 `go -C ...` denied (flag form not
  allow-listed — correct fail-closed); round 2 bare `go mod init`/`go build`
  ALLOWED by policy (no denial) but RC=1: workspace-root `go.mod` EROFS;
  round 3 `write`-tool `go.mod` WROTE=yes, `go build` RC=1: GOCACHE
  (`~/.cache/go-build`) read-only -> BIN=no. Policy half PROVEN (bare forms
  pass); execution BLOCKED by sandbox-mount granularity vs file-level allows.
  Follow-up feeds #12 D5-D7 (committer workspaces + GOCACHE binds).

## Step 4 — #12 D1–D4 engine compile: FOLLOW-UP (not attempted)

- No engine compile + ELAPSED clocking run (needs a tasked engine seat on a
  capable runner = #18 track). Steps 3's pytest/cmake/go attempts are the
  available execution evidence; D1–D4 proper stays open with this note.

## Step 5 — #96 refresh-policy-only (REQ-P3b) FULL LOOP GREEN

- Baseline live config sha256 `17adae9a...`.
- Test delta (worktree `fleet/fleet.yaml`, appsec `bash_deny` +=
  `probe96-deny-me*`, one line, reverted after): --refresh-policy-only
  (member fragment, --rig/--pod) rc=0 -> live config `f560c8bb...`,
  `grep -c probe96` = 1. NO relaunch.
- Running seat `probe96-deny-me` -> `Denied by policy: 'bash'
  (rule 'probe96-...` (verbatim, matchedPattern quoted).
- Revert (source git-clean) + refresh rc=0 -> probe count 0 + live config
  SEMANTIC-EQUAL to pristine render under BOTH rig bindings
  (defensive-sec-and-red-team AND heretek-omni-fleet). Baseline hash differs
  only by key order (full-seed vs member-refresh serialization; no volatile
  fields present — scanned).

## Step 6 — live loops (REQ-P3c)

- #9 mechanism on fleet host: `tests.test_send_identity` green here (part of
  124-test run below) + live mint/verify round-trips 4/4 (fresh->attested,
  replay->rejected, wrong-scope->not-attested, tamper->unverified), dummy
  secrets, `docs/evidence/fleet-proofs-2026-10-30/loop-mechanisms.log`.
  Daemon half still open: all live `rig send`s arrived with
  no-sender-identity advisories (recorded) -> #127 (expected).
- #15 mechanism on fleet host: `tests.test_auth_envelope` +
  `tests.test_check_envelope` green here + live round-trips 4/4 (match->
  authorized, replay/wrong-diff/expired->refused). Combined corpus run:
  `Ran 124 tests ... OK` on this host.
- #77 detect on live data (read-only): `is_awaiting_gate_prose`/
  `is_idle_park_prose` positive controls fire; scan over 27 live summaries:
  0 hits (no false positives on mission language; triggers live in tracker
  cells/notes per design). Full diffs stay fixture-proven (cited); no live
  rows touched. Recovery half (synthetic parent+gate lifecycle) NOT run —
  follow-up (needs mission-row orchestration design).
- #81 live loop: synthetic row qitem-...-85fd6988415ae82a -> first-nudge
  claim in 69s (claimedAt==tsUpdated, lastNudgeResult=claimed); claimer hit
  fleet-wide stale-context 400s on action (see infra findings); successor
  occupant (fresh launch) ran `rig whoami` RC=0 + receipt. No park observed
  at any point (eager attempts, never idle-with-obligation). Round 2 row
  qitem-...-e8bcb2a23c2aa345 to healthy seat for clean one-turn observation.
- #81 round 2 CLEAN: row qitem-...-e8bcb2a23c2aa345 claimed in 12s
  (created 01:09:21, claimedAt 01:09:33), `rig whoami` RC=0, receipt
  CLAIMED2 with WHO line observed. Claim->action->receipt contiguous on a
  healthy seat: the one-turn rule holds live. #81 LIVE PROOF GREEN.

## Step 7 — #107 MCP half (REQ-P3d) MECHANISM GREEN

- V23+V24 green inside host 39/0 runs; M2 rotation runbook pre-exists.
- Live issue+revoke cycle on this daemon for blue-appsec-engineer
  (HERETEK_SEAT_GRANT_OPT_IN=1): minted (0600 token file, listed scoped
  seat+rig, roots none) -> `revoke` ("next request is refused") -> token
  file removed -> store empty ("every HTTP request is refused").
  Zero residue. Bearer-200 NOT attempted: grant HTTP service down
  (127.0.0.1:7437 refused; M0 scratch semantics cited).
- Queue half still -> Wave 4. Firecrawl boot NO-GO (no route to
  10.121.15.142:3002). Governance = ticked (gates + issuance + rotation).

## Infra findings (live, recorded)

- F1 stale-rig refusal (#11 live): fresh `rig up rig.all-51.yaml` refused
  ("already exists ... Nothing was created"); restore path
  `rig up heretek-omni-fleet` resumed 51/51 to run+idle. Chose restore over
  archive (preserves queued WORK).
- F2 fleet-wide stale resume rot: every resumed seat 400s
  (`encrypted_content was not issued to this caller`) on first model call;
  `rig seat launch --fresh --stop` fixes (proven on 5 seats). Fresh launches
  audited with reasons. Affects ANY fleet restart — operational note.
- F3 sender-identity advisories on every live `rig send` (daemon gap,
  expected -> #127).
