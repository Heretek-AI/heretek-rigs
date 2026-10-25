# AGENTS.md — heretek-rigs operator guide (for agents working in this repo)

51 specialist seats across 8 OpenRig v0.2 bundles, generated deterministically.
Stack: `@openrig/cli@0.6.13` (`rig`), Pi 1.3.0 (`pi`), `@gotgenes/pi-permission-system@41.0.0`,
`opencode-go/muse-spark-1.3-contributor:high` via `https://opencode.ai/inference/go/v1`.

## The one rule

**Never hand-edit `specs/`, `rigs/`, `rosters/`, or `registry/`.**
Edit `fleet/fleet.yaml`, `fleet/mcp-servers.yaml`, or `scripts/`, then regenerate:

```bash
python3 ./scripts/generate-rigs.py        # no blocking dirt only: sanctioned session strays ignored (issue #43 allowlist), tracked/non-allowlisted dirt refuses (by design)
HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py   # dev iterations only
./scripts/verify-rigs.sh --check-only     # expect: 35 checks passed, 0 failed
python3 ./scripts/audit_loop.py --self-test
```

Use `yaml.safe_dump` NEVER on `fleet/fleet.yaml` — it strips comments. Surgical text edits only.

## Daily workflows

| Task | Command |
|---|---|
| Verify tree | `make verify` (or script directly) |
| Seat render dry-run | `HERETEK_SECRETS=~/.config/heretek-rigs/secrets python3 scripts/render-seat.py --role <id> --rig <id> --pod <id> --dry-run` |
| Seed then launch | `python3 scripts/seed-rig.py rigs/<rig>/rig.yaml [--allow-missing-secrets]` → `(cd rigs/<rig> && rig up rig.yaml --cwd <workspace> --yes)` |
| Talk to a seat | `rig send '<pod>-<member>@<rig>' "<message>"` / `rig capture` / `rig transcript --tail N` |
| Queue work | `rig queue create --json --verify --destination <session> --body-file <file>` / `rig queue list --json [--destination S] [-a]` (copy qitem IDs only from `--json` output — never retype; bare queue output mixes JSON with a human trailer/advisory and MUST NOT be parsed; bare create output is advisory, not proof of persistence) |
| Tracker proposals | `make reconcile TRACKER=… [OUT=…]` / `make generate-tracker TRACKER=… OUT=…` — propose-only: NEVER auto-edit trackers or write queue state; `--out` MUST be a fresh non-tracker path (refuse `*dispatch-tracker.md`, `sprints/` locations, existing files; `O_EXCL` create) — violations fail closed (exit 2). |
| Permission gate (mock) | `bash scripts/gate-role.sh <role>` (also: `make gate ROLE=`) |
| Wiring gates + graphs | `make topology OUT=/tmp/topo` |
| Live-seat audit | `make audit-sessions WORKSPACE=/path/to/seat-workspace` |
| TUI / tiles | `rig tui` / `rig terminal open <rig> --window` / `tmux attach -t <session>` |

Seeding is strict by default: missing `github.pat` etc. fails closed. Degraded mode
(`--allow-missing-secrets`) renders those servers `"enabled": false`. Unseeded seats have
NO permission config — always seed before `up`/`expand`/`add`.

## Git conventions (enforced by review, not hooks)

- One branch per change (`fix/…`, `feat/…`, `docs/…`, `remediate/…`), PR before merge to `main`. Never push straight to `main`.
- Never `--force` (a force-push guardrail has bitten before); if a branch goes stale, open a fresh branch name instead.
- Merge-conflict rule for generated files: take `main`'s generator, keep the branch's catalog edit, **re-run `generate-rigs.py`** — never hand-resolve generated leaves.
- Committed provenance (`resolvedCommit`) pins the pre-merge HEAD and re-lags one commit per merge. Known, accepted; `packageDigest`s stay self-consistent. Do NOT "fix" it by hand-editing registry files.
- `verify-rigs.sh`'s 35 checks are audit-baselined: add new gates alongside (new script or new block), don't renumber/reword existing checks casually.
- Leave untracked strays alone unless asked: `docs/evidence/`, `docs/reports/`, `.agents/`, `.claude/`, root `skills-lock.json`, `PROMPT_REVIEW.md` — prior sessions' artifacts, not yours to delete.

## Secrets (hard rules)

- Real key lives ONLY at `~/.config/heretek-rigs/secrets/` (0700 dir, 0600 files). Never print, copy, or commit it. Verify without reading: `stat -c '%a %U'`, `render-seat.py --dry-run` (shows `!cat …` reference only).
- No real credentials in commands, files, reports, or audit output. Audit findings redact secret-shaped strings.
- Dummy keys for all harness/matrix tests (`/tmp` scratch, 0600).

## Live environment notes

- Daemon: `rig daemon start --no-kernel` (loopback). `rig agent validate` / `preflight` need it; `spec validate` / `bundle check` don't.
- `rig up` from inside `rigs/<rig>/` writes OpenRig-managed `AGENTS.md` into the **cwd** (workspace if `--cwd` given, else the bundle dir — the latter breaks digest gates; prefer a dedicated workspace dir).
- `rig ps --nodes` needs `--rig <name>` (or `-A`) outside a managed session.
- `pgrep -f pi-runner` matches your own grep command — exclude it before concluding processes linger.
- Shell tooling here intermittently rejects commands (`permission.rejected`, `ln -s`, `--force*` flags): split commands, retry once, reroute (python `os.symlink`, fresh branch names).

## Docs map

- `README.md` — entry point + verified quickstart. `docs/USER_GUIDE.md` — operator manual (§11 Docker).
- `docs/TECHNICAL_DOCUMENTATION.md` — architecture reference (authoritative over older briefs).
- `docs/OPENRIG_MUSE_GO_ARCHITECTURE.md`, `docs/OSINT_ECOSYSTEM_REPORT.md` — planning snapshots.
- `docs/PROMPT_REVIEW_ARGON.md`, `docs/PROMPT_REVIEW_WEB.md` — prompt-pass decision record.
- `AUDIT_REPORT_FINDINGS.md`, `REMEDIATION_LOG.md` — audit trail (append, don't rewrite history).
- `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`, `PROMPT_FLEET_AUDIT_REMEDIATION.md` — audit/remediation protocols.
