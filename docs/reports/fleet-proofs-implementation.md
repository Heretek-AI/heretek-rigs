# Fleet-proofs implementation — Phase A (2026-10-30)

> Execution note: the `subagent` tool was policy-denied this session
> (retried once), so Phase A was executed directly by the coordinator with
> read-only live ops + worktree-confined file writes. No code or tests
> touched; live mutations limited to: daemon start (loopback, disclosed),
> `chmod 600` hardening (safe direction). No seats launched, no queue
> writes, no installs attempted.

## What ran (real outputs)

- `stat` secrets: dir `700`; `opencode-go.key` `600`; `github.pat` was
  `644` → hardened to `600`, re-verified. Strict-mode compliant after fix.
- `render-seat.py --dry-run` (blue-appsec-engineer@defensive-sec-and-red-team):
  rc=0, `!cat` refs only; one fail-loud `trivy` warn (gate working as designed).
- Tool presence: `r2`/`rabin2`/`tshark`/`trivy` MISSING; `go 1.27.3`,
  `pytest 9.1.1`, `cmake 4.3.0`, `bwrap 0.13.1`, `rig 0.7.5 (b57c4da3)` PRESENT.
- `sudo -n true` → password required: no unattended installs.
- Daemon: was down; `rig daemon start --no-kernel` → port 7433, left running.
- `rig ps --nodes -A`: 102 rows, ALL `seat-not-running` (some with queued WORK).
- Firecrawl `10.121.15.142:3002`: no route to host.

## Files written (worktree only)

- `openspec/changes/2026-10-29-fleet-proofs/` (proposal, specs/fleet-proofs,
  design, tasks — Phase A boxes checked, Phase B unchecked)
- `docs/74-PROVISIONING-MATRIX.md` (2026-10-30 re-take addendum)
- `docs/evidence/fleet-proofs-2026-10-30/phase-a-recon.md` (redacted recon +
  GO/NO-GO table + user questions)
- This report.

## Validation

- `./scripts/verify-rigs.sh --check-only` → 39/0 (run at commit time below).
- `openspec validate 2026-10-29-fleet-proofs` → must be rc=0 (run below).
- `make test`: SKIPPED — no code/tests touched (spec+docs+evidence only);
  634/0 baseline stands from the Wave-1 merge validation.
- `python3 scripts/audit_loop.py --self-test` + `--check-idempotent` at commit.

## Skips / deferrals

- Runbook steps 3–7: NO-GO per recon (no running seats; firecrawl unroutable)
  — gated on user approval, NOT attempted.
- Installs: named follow-ups (sudo needs tty).
- `HANDOFF.md` sync: still pending (pre-existing).

## Phase B — live execution (2026-10-30, same session, no subagents available)

Triad roles performed explicitly by the coordinator and LABELED as
self-issued (subagent tool policy-denied, retried). Evidence-first; every
claim below has a cited artifact.

### Live operations log

- Daemon was down on arrival; `rig daemon start --no-kernel` (port 7433,
  pid 92297), left running per user approval (Q3).
- Fresh `rig up rig.all-51.yaml` REFUSED (stale existing rig
  `01M5GWFPKVNQEXQVSAGQ2ANJBE`, tmux socket gone, "Nothing was created") —
  #11 refusal class live. Restored via `rig up heretek-omni-fleet`
  (non-destructive; archive would drop queued WORK): 51/51 run+idle.
- Brew (user: try Brew first): trivy 0.76.1, radare2 6.2.4, TShark 4.6.9.
- Fresh seat launches (`--fresh --stop`, audited reasons): rag, go, cpp,
  appsec, threat-modeler — all `ok:true`. Reason: fleet-wide stale resume
  rot (every resumed seat 400s `encrypted_content was not issued to this
  caller` on first model call; fresh launch fixes; PING-OK proven).
- Seed strict-clean for all 51 (fail-loud warns only).

### Step verdicts (evidence: docs/evidence/fleet-proofs-2026-10-30/runbook.md)

- Step 1 GREEN (+github.pat 644->600 hardening). Step 2 DOCUMENTED +
  Brew-resolved. Step 3: pytest RC=0, cmake RC=0, go policy-pass +
  exec-BLOCKED (GOCACHE ro; follow-up -> #12 D5-D7). Step 4 FOLLOW-UP
  (D1-D4 need engine seat + runner). Step 5 FULL LOOP GREEN (hashes
  17adae9a->f560c8bb->restored SEMANTIC-EQUAL x2 bindings; live denial by
  new rule; source reverted git-clean). Step 6: #9 8/8 + 124-test host
  run (daemon advisories persist -> #127); #15 same pattern; #77
  detect-scan (pos-controls fire, 27 live summaries 0 hits) + fixtures,
  recovery follow-up; #81 GREEN (69s claim + 12s claim, RC=0 actions,
  no park ever). Step 7 MECHANISM GREEN (live issue/revoke/cleanup,
  zero residue; V23/V24 in 39/0; firecrawl NO-GO no-route).
- Probe dirs left in seat workspaces (policy-compliant use), disclosed.
  /tmp scratch (fp81 bodies, proof-loops.py, liveq.json) noted, not committed.

### Self-QA (explicit role)

- Compound: 39/0, validate rc=0, self-test PASSED, idempotent rc=0
  (side-effect reverted); make test SKIPPED (no code/tests touched).
- Bearer-shape scan over all new files: 0 hits. `Closes` token: removed
  from proposal (was negation-without-number; reworded anyway).
- fleet.yaml git-clean (delta reverted). Secrets dir: exactly 2 keys.
- Sabotage (in-tree, byte-identical restore): REQ-P1 `#### Scenario:`
  block removed (5 lines) -> `openspec validate` emits missing-Scenario
  ERROR (RED); `git checkout --` restores sha256
  0e9dccabab64799e70189837c8616563a00255b42a5af51c0a643c65072b7ed8
  (identical to pre-sabotage) -> validates (GREEN).

### Self-audit verdict (explicit role)

- Minimality: diff limited to spec package + matrix addendum + evidence +
  reports. One Rule holds (specs/rigs/rosters/registry/fleet untouched —
  fleet.yaml edited then byte-reverted, git-clean). archive/ untouched.
  Zero V-gate/script/test changes. No upstream filing. Refs-only.
- Secrets: stat + `!cat` only; 400/queue/transcript evidence contains no
  secret material (scanned). Daemon sends arrived unattested (recorded,
  expected -> #127, NOT silently absorbed).
- Skips: make test (reason above); synthetic #77 parent+gate lifecycle
  (follow-up); D1-D4 (follow-up); installs beyond Brew (follow-ups).

VERDICT: PASS (self-issued — subagent triad unavailable this session;
recommend independent drift-guard re-audit when tool policy allows)
