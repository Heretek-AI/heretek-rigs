# Heretek-Rigs Verification & Discovery Log

## M0 — Repo scaffold
- `.gitignore` created.

## M1 — Toolchain / vendor clones — BLOCKED
- Toolchain/vendor clones BLOCKED: shell `permission.rejected`.
- External paths `/home/john/Projects/Heretek-Crew` and `/home/john/Projects/openrig-workspace/...` `permission.rejected`.
- Cannot run `node` / `rig` / `pi` / `uv`.
- Cannot run `git log`.
- Exact blocker error verbatim: `permission.rejected`.
- Same error survived >3 attempts -> stop per rule 5.

## M2 — Secrets — BLOCKED
- `.env.example` write BLOCKED with exact error verbatim: `Permission denied: edit` (policy blocks `.env*` files).

## M3 — Files created via file tools only
- `policies`, `mock-openai.mjs`, `gate-run.sh`, `render-seat.py`, `seed-rig.py`, `bootstrap-pi-seats.sh`, `test_render_seat.py`, `generate-rigs.py`, `gate-role.sh`, `verify-rigs.sh`, `Makefile` created verbatim from `PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md` via file tools only.

## M4 — Schemas / sidecars — MISSING (copy source blocked)
- `schemas/*.v1.schema.json` MISSING (needs `/home/john/Projects/openrig-workspace/openrig/docs/reference/schemas/` copy, blocked).
- `docker-compose.sidecars.yml` MISSING (needs `/home/john/Projects/Heretek-Crew/docker-compose.sidecars.yml` copy, blocked).
- Blocker: external-path read `permission.rejected`.

## M5 — Generation — NOT generated (needs shell + pins)
- `specs/`, `rigs/`, `rosters/`, `registry/`, `fleet/skills-lock.json` NOT generated.
- Needs `python3 scripts/generate-rigs.py` + pinned `Heretek-Crew@5ffb1fc`.
- Vendor clones `obra_superpowers@bb92a77`, `trailofbits_skills@5c99c03`, `getsentry_skills@f57ada2`, `anthropics_skills@dbd4588`, `vercel-labs_agent-skills@063bee9`, `openrig-core` skills — all blocked by no-shell + no-external-read.
- Same error survived >3 attempts -> stop per rule 5.

## M6 — Verification — NOT executed (shell blocked)
- `verify-rigs.sh`, unit tests, `audit_loop` self-test NOT executed (shell blocked).
- Exact blocker error verbatim: `permission.rejected`.
- Same error survived >3 attempts -> stop per rule 5.

## 2026-10-19 — Remediation pass (file-tool-only; shell still blocked)
- `default.shell` probe (`pwd; python3 --version; ...`) → `{"type":"permission.rejected",...}`. No commands executed.
- `.env.example` write → `Permission denied: edit` (policy blocks `.env*`; M2 blocker persists).
- External read `/home/john/Projects/Heretek-Crew/docker-compose.sidecars.yml` → `permission.rejected` (M4 blocker persists).
- Applied fail-closed source fixes (see `REMEDIATION_LOG.md`): 11-guard `path_write` in `render-seat.py` + verifier ordering, 7th file `pi-permission-config.json` in `generate-rigs.py`, lifecycle/`hooks` checks, `--output` reject, secret-shape allowlist + fleet scan, 8-key proxy + pin/`:ro` + network isolation, evaluator `IGNORECASE` + fence-strip + 3 extra self-test vectors, audit-prompt baseUrl/recipe/claim corrections, `gate-role.sh` `docs/AGENTS.md` + `--output` probes.
- Created `docker-compose.sidecars.yml` baseline (loopback, pinned, GET-only proxy) and 6 `schemas/*.v1.schema.json` baselines matching generator shapes; originals still need vendoring from blocked checkouts.
- Generation + verification STILL REQUIRE shell host:
  `python3 scripts/generate-rigs.py && ./scripts/verify-rigs.sh --check-only && ./scripts/bootstrap-pi-seats.sh --all --dry-run && python3 ./scripts/audit_loop.py --self-test` (all must exit 0; second generate must be diff-clean).

## 2026-10-19 — Remediation pass per PROMPT_FLEET_AUDIT_REMEDIATION.md (file-tool-only)
- `default.shell` probe (`pwd; git rev-parse --show-toplevel; ls`) → `{"type":"permission.rejected","message":"This non-interactive run cannot ask the user for permission..."}` (1 attempt, no retries).
- External reads `/home/john/Projects/Heretek-Crew`, `/home/john/Projects/openrig-workspace/openrig` → `permission.rejected` (M4/M5 blockers persist).
- `python3 scripts/generate-rigs.py`, `./scripts/verify-rigs.sh --check-only`, `./scripts/bootstrap-pi-seats.sh --all --dry-run`, `python3 ./scripts/audit_loop.py --self-test` → NOT RUN (same blocker). Second-run idempotency UNTESTABLE.
- Fail-closed verifier hardening applied (see `REMEDIATION_LOG.md` 2026-10-19 entry): `rig.yaml` reserved/secret-name scan (HR-4.4), per-seat `mcp["*"]:deny` + bound-server-only assert (HR-5.5), `Makefile` guard-profiles coverage (HR-7.3), 8-deliverable placeholder scan (HR-8.4). No check weakened; 18× `builtin:locked`, `*..*` deny-last, triple-deny, `!cat` templates, loopback/pinned sidecars preserved.
- P0 generation findings STILL OPEN (blocked here); shell host must run gate until green, then `scripts/audit_loop.py` spawns next triad audit.

## 2026-10-19 — Remediation pass per PROMPT_FLEET_AUDIT_REMEDIATION.md (file-tool-only)
- `default.shell` probes (`pwd; ls -la` then `python3 ./scripts/generate-rigs.py && ./scripts/verify-rigs.sh --check-only`) → each `{"type":"permission.rejected","message":"This non-interactive run cannot ask the user for permission..."}` (2 attempts, 0 blind retries; stop per hard rule 4).
- `python3 scripts/generate-rigs.py`, `./scripts/verify-rigs.sh --check-only`, `./scripts/bootstrap-pi-seats.sh --all --dry-run`, `python3 ./scripts/audit_loop.py --self-test` → NOT RUN (same blocker). Second-run idempotency UNTESTABLE.
- Fail-closed hardening applied (see `REMEDIATION_LOG.md` latest entry): generator float + ASCII-only JCS die (HR-3.2), verifier ASCII-only assert + `SYNTHETIC-` warn/`CI=true` forbid (HR-3.2/HR-3.3), seed passthrough + idempotency wiring + guard-message asserts (HR-4.2/HR-8.1/HR-7.3). No check weakened; 20× `builtin:locked`, `*..*` deny-last, triple-deny, `!cat` templates, loopback/pinned sidecars preserved.
- P0 generation findings STILL OPEN (blocked here); shell host must run gate until green, then `scripts/audit_loop.py` spawns next triad audit.

## 2026-10-19 — Remediation pass per PROMPT_FLEET_AUDIT_REMEDIATION.md (file-tool-only, current-findings sweep)
- `default.shell` probe (`pwd; git rev-parse --show-toplevel; ls`) → `{"type":"permission.rejected","message":"This non-interactive run cannot ask the user for permission, so the request was rejected. Continue without this action."}` (1 attempt, 0 blind retries; stop per hard rule 4 well before 3).
- `python3 scripts/generate-rigs.py`, `./scripts/verify-rigs.sh --check-only`, `./scripts/bootstrap-pi-seats.sh --all --dry-run`, `python3 ./scripts/audit_loop.py --self-test` → NOT RUN (same blocker). Second-run idempotency UNTESTABLE.
- Reproduction via file tools: `Glob specs|rigs|registry|rosters|**/skills-lock*` → all `No files found`; `.scratch/` holds only `audit-loop-logs/`; `fleet.yaml` 20× `builtin:locked`, 15 pods + 51 member_fragments explicit; `identity-vectors.json` + 6/6 schemas present; all generator/verifier/renderer/gate hardenings re-verified present by `Read`/`Grep` (see `REMEDIATION_LOG.md` latest entry). `generate-rigs.py:939 guidance_merge` confirmed as legitimate `toldFiles` culture delivery, not an `agent.yaml` startup file.
- No code change this pass (source already hardened; no `Caught? = No` sabotage to trigger hard rule 2). No check weakened; 20× `builtin:locked`, `*..*` deny-last, triple-deny, `!cat` templates, loopback/pinned sidecars preserved.
- P0 generation findings STILL OPEN (blocked here); shell host must run gate until green, then `scripts/audit_loop.py` spawns next triad audit.

## 2026-10-19 — Remediation pass per PROMPT_FLEET_AUDIT_REMEDIATION.md (current-findings sweep, 4 source hardenings)
- `default.shell` probes (`pwd` probe + `python3 scripts/generate-rigs.py` probe + gate batch `verify-rigs.sh --check-only && bootstrap-pi-seats.sh --all --dry-run && audit_loop.py --self-test`) → each `{"type":"permission.rejected","message":"This non-interactive run cannot ask the user for permission, so the request was rejected. Continue without this action."}` (3 attempts, 0 blind retries; stop per hard rule 4 at threshold, no blind retries).
- `python3 scripts/generate-rigs.py`, `./scripts/verify-rigs.sh --check-only`, `./scripts/bootstrap-pi-seats.sh --all --dry-run`, `python3 ./scripts/audit_loop.py --self-test` → NOT RUN (same blocker). Second-run idempotency UNTESTABLE.
- Fail-closed source hardenings applied (see `REMEDIATION_LOG.md` latest entry): `docs/OPENRIG_MUSE_GO_ARCHITECTURE.md` JCS doc fix (HR-3.2), verifier `SYNTHETIC-` ack-gated fail unless `HERETEK_ALLOW_SYNTHETIC=1` (HR-3.3), `gate-role.sh` +8 deny probes for `.git/hooks`/`.pi`/`.agents`/`*/secrets/*`/`*.url`/`*.user`/read-`..`/`code_rewrite` (HR-5.2), compose HR-7.3 coexistence matrix + verifier `sidecars-up -> guard-profiles` wiring assert. No check weakened; 20× `builtin:locked`, `*..*` deny-last, triple-deny, `!cat` templates, loopback/pinned sidecars preserved.
- P0 generation findings STILL OPEN (blocked here); shell host must run `python3 scripts/generate-rigs.py && ./scripts/verify-rigs.sh --check-only && ./scripts/bootstrap-pi-seats.sh --all --dry-run && python3 ./scripts/audit_loop.py --self-test` until green, then `scripts/audit_loop.py` spawns next triad audit.

## 2026-10-19 — Remediation pass per PROMPT_FLEET_AUDIT_REMEDIATION.md (current-findings sweep, verify-only)
- `default.shell` probes (`pwd; git rev-parse --show-toplevel; ls -la`, then `python3 scripts/generate-rigs.py && ./scripts/verify-rigs.sh --check-only` gate) → each `{"type":"permission.rejected","message":"This non-interactive run cannot ask the user for permission, so the request was rejected. Continue without this action."}` (2 attempts, 0 blind retries; stop per hard rule 4 well before 3).
- `python3 scripts/generate-rigs.py`, `./scripts/verify-rigs.sh --check-only`, `./scripts/bootstrap-pi-seats.sh --all --dry-run`, `python3 ./scripts/audit_loop.py --self-test` → NOT RUN (same blocker). Second-run idempotency UNTESTABLE.
- Reproduction via file tools: `Glob specs|rigs|registry|rosters|**/skills-lock*` → all `No files found`; `fleet.yaml` 20× `builtin:locked`, zero `yolo/open/guidance_merge/0.0.0.0/:latest`, zero reserved-name literals; `identity-vectors.json` + 6/6 schemas present; doc `jcs_canonicalize()` citation + `gate-role.sh:59-75` extended corpus + all generator/verifier/renderer hardenings re-verified present by `Read`/`Grep` (see `REMEDIATION_LOG.md` latest entry). Sabotage table: 12× `NOT RUN`, zero `Caught? = No` → hard rule 2 not triggered.
- No code change this pass (source already hardened; P0s are generation-blocked, P1-P3 execution halves need shell/Docker/network/`pi`). No check weakened; 20× `builtin:locked`, `*..*` deny-last, triple-deny, `!cat` templates, loopback/pinned sidecars preserved.
- P0 generation findings STILL OPEN (blocked here); shell host must run the gate until green, then `scripts/audit_loop.py` spawns next triad audit.

## 2026-10-19 — Remediation pass per PROMPT_FLEET_AUDIT_REMEDIATION.md (current-findings sweep, verify-only)
- `default.shell` probes (`pwd; git rev-parse --show-toplevel; ls -la; python3 --version`, then `python3 ./scripts/generate-rigs.py && ./scripts/verify-rigs.sh --check-only` gate batch) → each `{"type":"permission.rejected","message":"This non-interactive run cannot ask the user for permission, so the request was rejected. Continue without this action."}` (2 attempts, 0 blind retries; stop per hard rule 4 well before 3).
- `python3 scripts/generate-rigs.py`, `./scripts/verify-rigs.sh --check-only`, `./scripts/bootstrap-pi-seats.sh --all --dry-run`, `python3 ./scripts/audit_loop.py --self-test` → NOT RUN (same blocker). Second-run idempotency UNTESTABLE.
- Reproduction via file tools: `Glob specs|rigs|registry|rosters|**/skills-lock*` → all `No files found`; `.scratch/` holds only `audit-loop-logs/`; 6/6 schemas present; `identity-vectors.json:1-31` present; `.gitignore:1-8` ignores only deps (absence is real HEAD-state defect); `fleet.yaml` 20× `builtin:locked`, zero `yolo/open/guidance_merge`, zero active `0.0.0.0`/`:latest`; `--output` die-guards + triple-deny + `*..*` deny-last + 18-toggle proxy + idempotent wiring + evaluator hardening all re-verified present by `Read`/`Grep` (see `REMEDIATION_LOG.md` latest entry). Sabotage table: 12× `NOT RUN`/`UNVERIFIABLE`, zero `Caught? = No` → hard rule 2 not triggered.
- No code change this pass (source already hardened; P0s are generation-blocked, P1-P3 execution halves need shell/Docker/network/`pi`). No check weakened; 20× `builtin:locked`, `*..*` deny-last, triple-deny, `!cat` templates, loopback/pinned sidecars preserved.
- P0 generation findings STILL OPEN (blocked here); shell host must run the gate until green, then `scripts/audit_loop.py` spawns next triad audit.

## 2026-10-19 — Remediation pass per PROMPT_FLEET_AUDIT_REMEDIATION.md (486-line findings sweep, verify-only)
- `default.shell` probes (`pwd; git rev-parse --show-toplevel`, then `python3 ./scripts/generate-rigs.py`, then `echo blocked`) → each `{"type":"permission.rejected","message":"This non-interactive run cannot ask the user for permission, so the request was rejected. Continue without this action."}` (3 attempts, 0 blind retries; stop per hard rule 4).
- `python3 scripts/generate-rigs.py`, `./scripts/verify-rigs.sh --check-only`, `./scripts/bootstrap-pi-seats.sh --all --dry-run`, `python3 ./scripts/audit_loop.py --self-test` → NOT RUN (same blocker). Second-run idempotency UNTESTABLE.
- Reproduction via file tools: `Glob specs|rigs/**/*` → `No files found`; `Grep builtin:locked fleet/` → 20 hits; `Grep *..*|code_rewrite|guidance_merge|builtin:yolo|0.0.0.0|:latest` → no active violations; all generator/verifier/renderer hardenings re-verified present (see `REMEDIATION_LOG.md` latest entry). Sabotage table: 12× `NOT RUN`, zero `Caught? = No` → hard rule 2 not triggered.
- No code change this pass (source hardened; P0s generation-blocked, P1-P3 execution halves need shell/Docker/network/`pi`). No check weakened.
- P0 generation findings STILL OPEN (blocked here); shell host must run gate until green, then `scripts/audit_loop.py` spawns next triad audit.
