# Phase A recon — fleet-proofs 2026-10-30 (redacted)

All commands ran on the fleet host. No secret values appear below (stat +
`!cat`-only dry-run). Bearer-shaped strings: none observed.

## Step 1 safe-check — GREEN (with one hardening)

- `stat ~/.config/heretek-rigs/secrets`: dir `700 john` — OK.
- `github.pat`: was `644` (FINDING) → `chmod 600` → re-stat `600 john` — OK.
- `opencode-go.key`: `600 john` — OK.
- `HERETEK_SECRETS=~/.config/heretek-rigs/secrets python3 scripts/render-seat.py
  --role appsec-engineer --rig defensive-sec-and-red-team --pod blue --dry-run`
  → rc=0. `auth.json` carries `"key": "!cat
  /home/john/.config/heretek-rigs/secrets/opencode-go.key"` (reference only).
  Side observation: stderr warns `bash grant 'trivy fs*' missing tool
  artifact: trivy` (fail-loud per gate design, not silent).

## Step 2 provisioning re-take — DOCUMENTED

- `r2` / `rabin2` / `tshark` / `trivy`: MISSING (`command -v` rc=1).
- `go 1.27.3`, `pytest 9.1.1`, `cmake 4.3.0`, `bwrap 0.13.1`,
  `rig 0.7.5 (b57c4da3)`: PRESENT.
- `sudo -n true` → password required: unattended installs impossible.
  Installs recorded as named follow-ups in `docs/74-PROVISIONING-MATRIX.md`.
- Matrix addendum 2026-10-30 written (deltas + secrets finding).

## Live recon (read-only) — daemon + seats + firecrawl

- Daemon was DOWN on arrival (`rig ps`: "Daemon not running").
  Started loopback for recon: `rig daemon start --no-kernel` → port 7433
  (pid 92297). LEFT RUNNING for Phase B; disclose at handoff.
- `rig ps --nodes -A`: 102 node rows (`heretek-omni-fleet` + `kernel`).
  EVERY seat: `last observed UNKNOWN (seat-not-running)`. Queued WORK
  exists on some rows (ts-node-fullstack 7, data-pipeline 2, design 2–3,
  tpm-scrum-lead 2) — records, not running agents.
- Firecrawl `10.121.15.142:3002`: NO ROUTE TO HOST (TCP check rc=1).

## Per-step GO / NO-GO for Phase B

| Step | Verdict | Reason |
|---|---|---|
| 3 (#91 in-seat builds) | NO-GO until a seat runs | No running seats; host-shell run is NOT "in-seat" |
| 4 (#12 D1–D4) | NO-GO until a seat runs | Same; D5–D7 already follow-up |
| 5 (#96 refresh) | NO-GO until a seat runs | `--refresh-policy-only` targets a running seat |
| 6 (live loops #77/#81/#9/#15) | NO-GO until a seat runs | Loops need live claim/action/send traffic |
| 7 (#107 MCP half) | PARTIAL-GO | Governance boxes from repo state: GO; firecrawl boot: NO-GO (no route) |
| Installs (r2/tshark/trivy) | Follow-up | Needs tty sudo / third-party repo |

## Standing questions for the user (Phase B gate)

1. Launch seats for proofs? (single seat vs wider; token spend + side effects)
2. Approve tty-sudo installs (tshark, radare2, trivy repo) now or defer?
3. Leave daemon running (current) or tidy-stop until Phase B?
