# Handoff — next session (2026-10-28, post-PR #132 merge on main)

> Superseded 2026-10-26 handoff archived in git history (`2590a87`..`83cbf86`).
> This document reflects the authoritative state of `main` after merging PR #120 through PR #132 (including wave 9 = PR #128, wave 4 = PR #131, and wave 81 = PR #132).

---

## 1. Live State & Environment

- **Repository**: `Heretek-AI/heretek-rigs` (local checkout at `heretek-rig-workspace/heretek-rigs`)
- **Branch**: `main` @ `9e7e14b` (Merge PR #132). Working directory clean at time of writing.
- **Core Stack**:
  - `@openrig/cli@0.7.4` (`6d9e8e27`, bumped from 0.7.2 in PR #122)
  - Pi `1.4.0` (`@earendil-works/pi-coding-agent`)
  - `@gotgenes/pi-permission-system@41.0.0`
  - Model: `opencode-go/muse-spark-1.3-contributor:high` via `https://opencode.ai/inference/go/v1`
- **Verification Baseline**:
  - `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 38 checks passed, 0 failed** (V1–V29 gates green: V22 bare-queue deny, V23 seat grants, V24 rotation runbook, V25–V27 sandbox/hermetic/docker, V28 send attestation, V29 mission gates, V30 seat idle-park).
  - `make test` → **599 unit tests passed, 0 failed** across 24 suites (`unittest discover`; was 562 across 24 at PR #131).
  - `python3 scripts/audit_loop.py --self-test` → **`SELF-TEST PASSED`**.
  - `python3 scripts/generate-rigs.py --check-idempotent` → **byte-identical**.
  - `openspec/`: 9 canonical specs (`identity`, `closeout`, `bump`, `p0`, `contracts`, `archive`, `send-identity`, `mission-gates`, `seat-idle`); active `openspec/changes/` holds only the archive container; 9 waves archived with history under `openspec/changes/archive/`.

---

## 2. Merged Landings Since Last Handoff

### PR #120 (`feat/102-closeout`, Closes #102)
- **HR-F18**: per-seat `bash_deny` triple (`rig queue list`, bare `rig queue create`, `rig send`) ×51 + appended FAIL-ONLY V22; AGENTS.md bare-deny gate.
- **HR-2.5**: `rig spec validate` declared canonical for `rig.all-51.yaml`; bundle-8-intentional documented.
- **Claim 6.1 follow-through**: `writing-skills` dangling ref fixed via vendor/patch + regen; **DAG**: local-only evidence note (no upstream filing).

### PR #121 (`feat/107-identity`, Refs #107)
- **M0 live spike** (isolated scratch env, `rig` 0.7.2): Bearer 200 / bad-token 401 / revoked 401 / `rig_whoami` grant-vs-declared / client-spoof ignored; queue half rc=0 daemon-blocked.
- **M1**: seed-time per-seat grants (`issue_seat_grant`, 0600 secrets store, `!cat` Bearer render, `--seat --rig` scope), `rig-mcp-http` catalog entry (opt-in, stdio unchanged); V23 gate; 15→25 corpus tests across reworks.
- **M2**: revoke + re-add rotation runbook, executed live.
- **M3**: queue-half upstream-blocked note (no code, no filing — unauthorized).
- **Reworks 1–3 + cycle 4**: F1–F5 review findings (grant gating, metadata check, safe store, rig scope, runbook), CodeQL log redaction (choke-point `_redact_for_log`), runbook rig scope + spec opt-in limit + R3 same-rig refutation (impersonation impossible), V24 runbook-step gate.

### PR #122 (`overhaul-bump`, Refs only)
- Host toolchain `@openrig/cli@0.7.4`; ledger `docs/sprints/CLI-0.7.4-BUMP.md` (tarball sha256 `d11dd8a6…` re-verified from published npm by two agents); 8 true-pin files; zero generator-input changes.
- **Rework 1**: idempotence HOLD-with-deferral (Wave B owns 0.7.4-vendor regen), runnable T2 (`&&`), fail-closed V18 `rig --version` gate.

### PR #123 (`feat/overhaul-a`, 2 reworks)
- **M0**: fake-rig exfiltration + forged `--source` both LEAK rc=0 pre-fix (verbatim evidence).
- **M1**: re-derived hardened `rig` relay (fd-passing `O_NOFOLLOW` + `fstat` re-check + `/dev/fd/N` argv rewrite; TOCTOU race proven won pre-fix); `TestRigRelayEnforcement` + TOCTOU class, bwrap-independent; V25.
- **M2**: `filter=` feature-detect guard, hermetic charter fallback + snapshot/restore with skills-lock verification; V26.
- **M3**: `bubblewrap` in Dockerfile + verify step, workflow duplicate-`container:` + unclosed-`if` fix; UniqueKey YAML proof; V27.
- **Rework 1**: tar member-type gate, scratch-root exclusion (`/`, `/tmp`, `/var/tmp`), hermetic notice, recursive fixture. **Rework 2**: mkstemp probes, sys.executable shebang.

### PR #124 (`feat/overhaul-b`)
- **M4**: `codex_permissions` (upstream MEMBER_KEYS exact match), vendored `run-record.v1.schema.json` (byte-identical, sha `b3c7ac64…`), 6 openrig-core skill files synced via generator + clean regen.
- **M5**: `make test` → `unittest discover` (21 suites); canary reworked (triple-normalized bound + fixture fallback → GREEN, closing the pre-existing RED); V19 canonical total 35 (old `passes+1` triplication reproduced then removed); V12 `HERETEK_ALLOW_NO_BWRAP=1` note-mode.

### PR #125 (`feat/overhaul-c`)
- **M6**: 138 stale paths → `archive/2026-10-28-overhaul/` via `git mv` (R100, history preserved); live 102/107/overhaul artifacts spared; HR-8.4 list + docs maps + `.gitignore` updated.
- **M7**: fresh `docs/IMPLEMENTATION_PROMPT.md` (reconciled plan, current gates — not the stale upload); `audit_loop.py` repointed with fail-closed archive-path guard.
- **M8**: clean regen (provenance-only), idempotence + verify + `make test` + topology all green.

### PR #126 (`feat/archive-waves`, 1 rework)
- 36 task boxes checked; 6 changes archived with canonical `openspec/specs/` (19 requirements; `openspec list --specs` green).
- **Rework 1**: runnable acceptance compounds, **0.7.4 bump ledger restored to live path** (had been swept into the archive; it is live-required), grant-mapping + V18 citation accuracy, fixed-digest contract test (`b3c7ac64…`), at-most-one-container language.

### Wave 9 (`feat/09-send-identity`, Refs #9 — merged as PR #128)
- Post-merge reworks 1–3 (all `VERDICT: PASS`): F1–F10 review fixes incl. real sender-check hole (F5) now bound to `expected_sender`; 5 CodeQL findings (chmod masks, log redaction); rotation/reuse/gate-alignment threads. Final: 532 tests, corpus 27.
- **S0**: isolated-scratch spike proving forged `--source`/env sender accepted pre-fix (`docs/evidence/09-send-identity-spoof.md`, verbatim, redacted).
- **S1**: grant-bound sender attestation (`scripts/send_identity.py`, HMAC-SHA256 mint/verify → `attested`/`unverified`/`rejected`, `!cat` render, 0600 stores); `tests/test_send_identity.py` 25 tests covering all four forgery classes; S1a–S1d red-proofs in `docs/evidence/09-send-identity/red-proofs.log`.
- **S2**: appended **V28** gate (new block only; V19 freeze 35→36 + live-count docs); FAIL-ONLY pre-fix recorded (35 passed, 4 failed with module removed); `make test` 530 OK.
- **S3**: rotation runbook executed live in scratch (`docs/evidence/09-send-identity-rotation.md`: `--seat` ×7, `--rig` ×8, 0 rig-less); triad complete with `VERDICT: PASS` (`docs/reports/09-send-identity-verification.md`); change archived, `send-identity` promoted (4 requirements).
- **Out of scope (kept)**: daemon edits, upstream filing (#127 still tracks the gap, no authorization granted), fleet-host live proofs. Issue #9 stays open.

### Wave 4 (`feat/77-mission-gates`, Refs #77 — merged as PR #131, 2 reworks)
- **S0**: B2-pattern fixtures proving pre-fix silence (gateless parent unflagged, dismissal-without-change allowed; `docs/evidence/77-mission-gates-prefix.md`).
- **S1**: charter closure-ownership rule via `fleet/skill-patches/mission-slice-sop.yaml` + clean regen (9 leaves +1) + new `stalled-awaiting-gate` diff class in `reconcile_model.py` (propose-only; live gate exempts).
- **S2**: sweep recovery non-dismissible without row state change (fail-closed refusal, never `done`) + appended **V29** (V19 freeze 36→37); `make test` 558 OK.
- **S3**: runbook with `--gate` creation flow exercised on fixtures; triad complete with `VERDICT: PASS` (`docs/reports/77-mission-gates-verification.md`); change archived, `mission-gates` promoted (4 requirements).
- **Delegated decisions (user)**: scope = 3 checkboxes; NO bot auto-closure ever (safety, not compat); fixtures-only acceptance. Issue #77 stays open until a live mission proves the loop.

### Wave 81 (`feat/81-seat-idle`, Refs #81 — merged as PR #132, 1 rework)
- **S0**: #81-pattern fixtures (claim-then-park with open obligation, park-to-wake spread, operator-labeled daemon handoff) proving pre-fix silence (`docs/evidence/81-seat-idle-prefix.md`, incl. dummy daemon-origin invocation result).
- **S1**: charter claim+first-action-is-one-turn rule via `fleet/skill-patches/queue-handoff.yaml` + clean regen (9 leaves) + new `stalled-idle-park` diff class with report-only park-to-wake attribution + daemon source validation (`daemon:stuck-sweep`, wave-9 genuine-operator handling unchanged).
- **S2**: idle-park recovery non-dismissible without row state change + non-spoofable daemon source + appended **V30** (V19 freeze 37→38); `make test` 595 OK at merge.
- **S3**: triage runbook exercised on fixtures; triad complete with `VERDICT: PASS` (`docs/reports/81-seat-idle-verification.md`); change archived, `seat-idle` promoted (4 requirements).
- **Rework 1**: F1–F5 PR review findings (daemon-invocation evidence pin, wake_ts release-gate, review-only render, mixed-note work eligibility, corrected wake arithmetic) + 3 anti-vacuity pinning tests; `VERDICT: PASS` re-issued, 599 tests. Stale `wake +53s` prose in `81-seat-idle-implementation.md:18` knowingly left (frozen record, disclosed in merge report).
- **Delegated decisions (user)**: scope = the issue's 3 checkboxes; fixtures-only + propose-only; never `Closes #81`. Issue #81 stays open until a live fleet proves the loop.

---

## 3. Current Issue Triage (15 Open Issues: 14 old + #127 new)

| Issue | Priority | Title / Scope | State & Next Steps |
|---|---|---|---|
| **#127** | P2 | Queue/send identity is daemon-side (NEW, opened 2026-10-28) | Tracks the upstream gap with M0/R3 evidence. **Needs principal authorization to file upstream.** |
| **#107** | P2 | Remediation follow-up bundle | **MCP half DONE** (#121). Remaining: firecrawl standalone boot on networked host; governance boxes; queue half → #127. |
| **#91** | P2 | Scoped build/test path args | **Code done** (carried through 0.7.4 + canary rework unchanged). **Pending**: live proof on fleet host. Status comment left 2026-10-28. |
| **#12** | P1 | No seat can execute builds | **Code blockers cleared**; gates green on main. **Pending**: D1–D4 in-seat proof, D5–D7 committer path. Status comment left. |
| **#74** | P1 | Granted tools not provisioned | Gate done (V16 + render warning). **Pending**: host-side provisioning or matrix doc update. |
| **#66** | Umbrella | Tracking: Oct 23–24 adversarial audit | Rollup comment left (#120–#126). Stays open until P1/P2 items close. |
| **#77** | P2 | Mission parent rows stuck 'standing by for gate' | **Merged as PR #131** (wave 4, `VERDICT: PASS`, Refs #77). **Pending**: live-mission proof only. |
| **#78** | P2 | Seats pinned to one workspace | Untouched. Architectural. |
| **#80** | P3 | `rig snapshot list <name>` prints `[object Object]` | Untouched (upstream CLI bug, local mitigation in place). |
| **#81** | P2 | Seats park idle right after claiming | **Merged as PR #132** (wave 81, `VERDICT: PASS` re-issued after rework-1, Refs #81). **Pending**: live-fleet proof only. |
| **#9** | P2 | Operator `rig send` carries no sender identity | **Merged as PR #128** (wave 9, `VERDICT: PASS`, Refs #9). **Pending**: fleet-host live proof only. |
| **#11** | P2 | `rig launch` refuses running nodes | Repo-side replaced by #96 live refresh (shipped PR #119); full restart tracked upstream. |
| **#15** | P2 | Authorization loop lags seat fix cycles | Untouched (investigation). |
| **#16** | P2 | Parallel slice execution | Untouched (investigation). |
| **#17** | P2 | Fleet utilization and slice queue patterns | Untouched (telemetry). |
| **#18** | P2 | GPU-capable runner for godot/bevy testing | Untouched (infrastructure). |
| **#102** | — | Audit P3 bundle | **CLOSED** by #120 (2026-10-27). |

---

## 4. Priority Roadmap

### Priority 1: Next issue wave (needs principal pick + spec)
- Wave 9 landed as PR #128. Wave 4 landed as PR #131 (reworks 1–2, both `VERDICT: PASS`). Wave 81 landed as PR #132 (rework-1, `VERDICT: PASS` re-issued). #77, #9 and #81 are merged; remaining work is live-mission/fleet-host proof.
- Recommended next: a fleet-host proof batch (#91 live, #12 D1–D4) if operating on the live host, or pick a fresh issue.
- Every wave needs an approved `openspec/changes/<id>/` spec first (`/grill-spec`), then the standard triad.

### Priority 2: Fleet Host Proofs (when operating on live host)
- **#96 live**: `--refresh-policy-only` on a running seat with a tightened rule.
- **#91 live**: `pytest tests/rag`, `go build ./...`, `cmake -S . -B build` in-seat.
- **#12 D1–D4**: engine compile + ELAPSED clocking in-seat.
- **#74**: install missing MCP packages + `r2`/`rabin2`/`tshark`, or update matrix docs.

### Priority 3: Upstream (authorization-gated)
- File the queue-attestation issue against `mvschwarz/openrig` (tracked in #127). **Do not file without explicit principal approval.**
- #80 snapshot-by-name, #11 full restart: upstream-tracked, local mitigations in place.

---

## 5. Standard Operating Discipline

> [!IMPORTANT]
> **The One Rule**: Never hand-edit `specs/`, `rigs/`, `rosters/`, or `registry/`.
> Edit `fleet/fleet.yaml`, `fleet/mcp-servers.yaml`, `fleet/skill-patches/`, or `scripts/`, then regenerate:
> ```bash
> python3 ./scripts/generate-rigs.py
> ./scripts/verify-rigs.sh --check-only     # Expect: 38 checks passed, 0 failed
> python3 ./scripts/audit_loop.py --self-test
> ```

- **Git Discipline**:
  - Always branch from `main` (`fix/...`, `feat/...`, `chore/...`, `docs/...`).
  - Never push directly to `main`. Never `--force`.
  - One closing keyword per issue (`Closes #X, closes #Y`). Use `Refs #Z` for issues that stay open.
  - Generator changes: source commit → clean regen → leaves chore commit. Never hand-resolve generated leaves (take `main`'s generator, keep the catalog edit, re-run).
  - Provenance re-lag (1+ commits) is known/accepted; do NOT "fix" registry files.
  - `verify-rigs.sh` gates are audit-baselined (V1–V29): append new blocks, never renumber/reword.
  - `openspec archive <id>` requires parser-valid specs (`### Requirement:` + `#### Scenario:`) and completed task boxes; pre-create the canonical spec shell if the capability is new.
- **Secrets Rule**:
  - Keys live strictly in `~/.config/heretek-rigs/secrets/` (0700/0600). Never print, log, or commit secret values. Dummy keys in scratch/tests only. Bearer-shaped strings in evidence must be redacted (`or…XX`) or dummy.
  - Shell pro tip: quote `gh` bodies via heredoc files — backticks in `-m`/`--body` get eaten by bash.
