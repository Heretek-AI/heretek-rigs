# Handoff — next session (2026-10-30, Wave 1 merged + Wave 2 PR #136 open)

> Supersedes the 2026-10-29 handoff retained verbatim below (post-#133 state).
> New session with working subagent permissions: START HERE. This top section
> is the current truth; the retained section is history (PR #120–#133 detail).
> Plan file (agreed Q1–Q14, 5 waves): `/home/john/.opencode/plan/2026-10-29-five-wave-remediation-plan.md`.

---

## 0. Where things live (read this first)

- **Local `main`**: `4939e94` (Merge PR #135). Clean, synced with `origin/main`.
- **PR #136 OPEN** (`feat/fleet-proofs` → `main`): Wave 2, commits `c5cd2dd`
  (Phase A) + `4886ac7` (Phase B). CI was pending at handoff time.
  Worktree (kept): `.lane/trees/fleet-proofs` (branch `feat/fleet-proofs`).
  THIS FILE's new section lives in that branch until #136 merges.
- **Prior bookmark**: `docs/handoff-post-133` (`c1da1fb`, post-#133 HANDOFF
  sync, never pushed — superseded by this file, safe to delete after #136).
- **Spec discipline reminder**: `openspec/changes/` holds only `archive/`
  on main; Wave 2's active package is on the PR branch
  (`openspec/changes/2026-10-29-fleet-proofs/` → archive on merge).

## 1. Live State & Environment (2026-10-30)

- **Stack**: `@openrig/cli@0.7.5` (`rig 0.7.5 b57c4da3`, ledger
  `docs/sprints/CLI-0.7.5-BUMP.md`), Pi 1.4.0, pps 41.0.0.
- **Gates on merged main**: `verify-rigs.sh` 39/0, `make test` 634 OK,
  `audit_loop --self-test` PASSED, `--check-idempotent` byte-identical.
  Re-validated post-merge in a scratch worktree (since removed).
- **Fleet host (THIS machine, live)**: daemon UP loopback (port 7433,
  started by coordinator — was down on arrival); `heretek-omni-fleet`
  restored (fresh `rig up` refused on stale rig — #11 class live), 51/51
  `run`+`idle`. Fresh seat launches (audited): rag, go, cpp, appsec,
  threat-modeler. Secrets dir `700`, both keys `600` (github.pat was
  `644` → hardened this session). Brew: trivy 0.76.1, radare2 6.2.4,
  TShark 4.6.9 (linuxbrew bin on PATH). Firecrawl `10.121.15.142:3002`
  unreachable (no route). `sudo -n` needs password (no unattended apt).
- **Tooling caveat**: the `subagent` tool was policy-denied for this ENTIRE
  session (retried). ALL Wave 2 work below was executed directly by the
  coordinator with worktree-confined writes + read-only-first live ops.
  Triad verdicts are explicitly SELF-ISSUED — the re-review must be a real
  independent triad (`agency-programmer` / `agency-qa` / `agency-drift-guard`).

## 2. What happened since the retained handoff

### Wave 1 → PR #135 MERGED (`4939e94`)

- `2026-10-29-bump-075`: 0.7.4→0.7.5 ledger (two-fetch sha `22d67c2c…`,
  8 true-pins, zero generator changes), AGENTS.md 2+/1−.
- Reworks 1–5 (coordinator): local-paths hook ×2, review F1–F4
  (QA-wording, USER_GUIDE migration-126 warning, REQ-BUMP1/2 SUPERSEDED,
  stale F4 skipped), CI `referencing` dep + `jsonschema>=4.18` floor
  (proven: 4.17.3 rejects, 4.18.6 accepts), bwrap-before-verify reorder,
  lowercase ghcr name. Each with QA red-proofs + `VERDICT: PASS` re-issued.
- Rework-6 (Gemini): docker build context (`.git`+evidence) + CHROME_PATH
  `-x` under QEMU arm64, with QA + `VERDICT: PASS`. All PR checks green
  at merge (Host gate, Build slim/full, CodeQL, SonarCloud, wiring).
- `openspec archive` applied (bump spec promoted); worktrees pruned.

### Wave 2 → PR #136 OPEN (needs independent re-review)

- `2026-10-29-fleet-proofs`: Phase A (spec package + safe-check +
  provisioning re-take + read-only recon, committed `c5cd2dd`) + Phase B
  live execution (committed `4886ac7`). Evidence:
  `docs/evidence/fleet-proofs-2026-10-30/` (runbook.md, phase-a-recon.md,
  loop-mechanisms.log, predicate-scan.log). Reports: `docs/reports/`
  (`fleet-proofs-implementation.md` incl. Phase A+B sections + self-QA and
  self-audit appendices with the self-issued VERDICT). Wave-1 QA material
  lives separately in `docs/reports/bump-075-qa.md` (untouched by Wave 2).
- Per-step verdicts: S1 GREEN (+hardening) · S2 documented+Brew-resolved ·
  S3 pytest RC=0 + cmake RC=0 + go policy-pass/exec-BLOCKED (GOCACHE ro;
  follow-up → #12 D5-D7) · S4 FOLLOW-UP (D1–D4 need engine seat+runner) ·
  S5 #96 FULL LOOP GREEN (hashes, refresh ×2, live denial, revert,
  restoration SEMANTIC-EQUAL ×2 bindings) · S6 #9/#15 8/8 live + 124-test
  host run, #77 detect-scan + fixtures (recovery follow-up), #81 GREEN
  (69s + 12s claims, RC=0 actions, no park) · S7 #107 live
  issue/revoke/cleanup, zero residue.
- Live findings to preserve: (F1) stale-rig launch refusal (#11 live);
  (F2) fleet-wide stale-resume 400 rot + fresh-launch remedy (affects ANY
  fleet restart); (F3) every `rig send` arrived with no-sender-identity
  advisory (daemon gap → #127, expected).
- Compound on branch: 39/0, `openspec validate` rc=0, self-test PASSED,
  idempotent rc=0 (side-effect reverted); `make test` skipped with reason
  (no code/tests touched). Self-QA red-proofs: spec sabotage RED→
  sha-identical GREEN, bearer-scan 0 hits, `Closes` removed, fleet.yaml
  git-clean, secrets dir 2 keys.
- **Re-review checklist for the new session**: (1) re-run every cited
  live claim that can be re-verified read-only (hashes, configs, row
  states, transcripts); (2) judge the self-issued VERDICT honestly —
  downgrade to FAIL with numbered findings if anything is overclaimed
  (prime suspects: go-step framing, #77-recovery absence, D1–D4 absence);
  (3) confirm scope discipline (no V-gate/script/test diffs, archive/
  untouched, Refs-only, secrets hygiene); (4) on PASS: merge #136,
  `openspec archive 2026-10-29-fleet-proofs`, sync THIS file to main,
  prune `.lane/trees/fleet-proofs`.

## 3. Issue triage deltas (vs retained section below)

| Issue | Delta this session |
|---|---|
| #91 | PARTIAL→ live: pytest RC=0 in-seat; cmake RC=0 in-seat; go policy-pass, exec-blocked (GOCACHE) |
| #12 | Code blockers cleared (prior); live: seats CAN execute allowed builds; D1–D4 + committer path still open |
| #74 | Gate + matrix re-take 2026-10-30; B1–B3 + trivy PRESENT via Brew; r2mcp/npm artifacts/markdownlint still follow-ups |
| #77 | Live detect-scan (predicates fire, 27 summaries clean) + fixtures; recovery lifecycle follow-up |
| #81 | LIVE GREEN (synthetic rows, 69s + 12s claims, RC=0 actions, no park) |
| #9 | Mechanism green on host (4/4 round-trips + corpus); daemon sends unattested (→ #127, expected) |
| #15 | Mechanism green on host (4/4 incl. expiry/replay + corpus) |
| #107 | MCP mechanism green live (issue/revoke/cleanup); queue half → Wave 4; firecrawl NO-GO |
| #11/#96 | #96 full loop GREEN live; #11 refusal class observed live (stale-rig) + upstream #2200 still open |
| #134 (F4) | Untouched (Wave 5: amendment-first) |
| #16/#17/#18/#78 | Untouched (Wave 3: fresh-slices spec) |
| #127/#80 | Untouched (Wave 4: upstream-filing, auth-gated) |
| #66/#102 | Unchanged (meta/closed) |

## 4. Roadmap (immediate)

1. **Re-review PR #136** with proper subagents (checklist §2) — do NOT
   merge on the self-issued verdict alone.
2. Address findings (bounded rework on `feat/fleet-proofs`), merge, archive
   the change, sync this handoff to `main`, prune the worktree.
3. Wave 3 (`2026-10-29-fresh-slices`, #16+#17+#18): `/grill-spec` → triad.
4. Wave 4 (upstream-filing, needs principal filing approval) + Wave 5
   (F4 amendment-first). Live follow-ups (D1–D4, #77 recovery, tty installs)
   ride future waves, not hotfixes.
5. Housekeeping whenever convenient: stop the loopback daemon if no live
   work is active; remove `/tmp/opencode/{fp81-body.md,fp81b-body.md,
   proof-loops.py,liveq.json}` scratch; seat-workspace probe dirs
   (`src/probe91cmake`, `pkg/probe91go`, `go.mod`, `test_probe91.py`) are
   policy-compliant seat work — remove only via the seats or leave;
   delete bookmark `docs/handoff-post-133` once this file is on main.

## 5. Standing cautions (unchanged from prior discipline)

One Rule · append-only V-gates · Refs-never-Closes for live waves ·
dummy keys + redacted logs only · propose-only trackers/queue (synthetic
proof rows in §2 were the runbook-authorized exception, labeled
FLEET-PROOFS-*) · never push straight to `main` · never `--force`.

---

## Retained handoff (2026-10-29, post-#133) — history, verbatim below

# Handoff — next session (2026-10-29, post-PR #133 merge on main)

> Superseded 2026-10-26 handoff archived in git history (`2590a87`..`83cbf86`).
> This document reflects the authoritative state of `main` after merging PR #120 through PR #133 (including wave 9 = PR #128, wave 4 = PR #131, wave 81 = PR #132, and wave 15 = PR #133).

---

## 1. Live State & Environment

- **Repository**: `Heretek-AI/heretek-rigs` (local checkout at `heretek-rig-workspace/heretek-rigs`)
- **Branch**: `main` @ `a64b437` (Merge PR #133). Working directory clean at time of writing.
- **Core Stack**:
  - `@openrig/cli@0.7.4` (`6d9e8e27`, bumped from 0.7.2 in PR #122)
  - Pi `1.4.0` (`@earendil-works/pi-coding-agent`)
  - `@gotgenes/pi-permission-system@41.0.0`
  - Model: `opencode-go/muse-spark-1.3-contributor:high` via `https://opencode.ai/inference/go/v1`
- **Verification Baseline**:
  - `./scripts/verify-rigs.sh --check-only` → **SUMMARY: 39 checks passed, 0 failed** (V1–V29 gates green: V22 bare-queue deny, V23 seat grants, V24 rotation runbook, V25–V27 sandbox/hermetic/docker, V28 send attestation, V29 mission gates, V30 seat idle-park, V31 pre-auth envelopes).
  - `make test` → **634 unit tests passed, 0 failed** across 24 suites (`unittest discover`; was 599 across 24 at PR #132).
  - `python3 scripts/audit_loop.py --self-test` → **`SELF-TEST PASSED`**.
  - `python3 scripts/generate-rigs.py --check-idempotent` → **byte-identical**.
  - `openspec/`: 10 canonical specs (`identity`, `closeout`, `bump`, `p0`, `contracts`, `archive`, `send-identity`, `mission-gates`, `seat-idle`, `auth-envelope`); active `openspec/changes/` holds only the archive container; 10 waves archived with history under `openspec/changes/archive/`.

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

### Wave 15 (`feat/15-auth-envelope`, Refs #15 — merged as PR #133, 1 rework)
- **S0**: #15-pattern fixtures (authorized premise vs live drifted diff, premise-age spread, no-envelope baseline) proving pre-fix silence (`docs/evidence/15-auth-envelope-prefix.md`).
- **S1**: premise-drift classifier (`stalled_premise_drift_diff`, propose-only, clean premises quiet) with report-only premise-age attribution, inputs for #17.
- **S2**: new `scripts/auth_envelope.py` (HMAC mint/validate: diff-hash + scope paths + mandatory expiry + single-use nonce; drift/scope-breach/expiry/replay refused fail-closed, redacted log; no executor, no commit surface) + non-dismissible recovery + appended **V31** (V19 freeze 38→39); `make test` 628 OK at merge.
- **Pre-commit fix**: gitleaks flagged hex dummy diff-hash fixtures; replaced with low-entropy hex dummies the premise grammar accepts (programmer-documented deviation from prescribed `dummy-` tokens).
- **S3**: landing/triage runbook exercised on fixtures; triad complete with `VERDICT: PASS` (`docs/reports/15-auth-envelope-verification.md`); change archived, `auth-envelope` promoted (4 requirements).
- **Rework 1**: F1–F3,F5–F9 PR review fixes (report scope/opening accuracy, HANDOFF expect 38→39, comma rejection, path-shape validation, `..` rejection, newest-to-oldest landing, MAC-tamper pin) with 6 anti-vacuity pins; F4 skipped (no envelope registry in reconciler; contradicts REQ-E2 clean-quiet scenario — needs spec amendment, agreed by QA + drift-guard); `VERDICT: PASS` re-issued, 634 tests.
- **Delegated decisions (user)**: mechanism (a) pre-auth envelopes; never self-executes / never auto-commits (safety invariant); fixtures-only + propose-only; never `Closes #15`. Issue #15 stays open until a live fleet proves authorization keeps pace.

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
| **#15** | P2 | Authorization loop lags seat fix cycles | **Merged as PR #133** (wave 15, `VERDICT: PASS` re-issued after rework-1, Refs #15). **Pending**: live-fleet proof only. |
| **#16** | P2 | Parallel slice execution | Untouched (investigation). |
| **#17** | P2 | Fleet utilization and slice queue patterns | Untouched (telemetry). |
| **#18** | P2 | GPU-capable runner for godot/bevy testing | Untouched (infrastructure). |
| **#102** | — | Audit P3 bundle | **CLOSED** by #120 (2026-10-27). |

---

## 4. Priority Roadmap

### Priority 1: Next issue wave (needs principal pick + spec)
- Wave 9 landed as PR #128. Wave 4 landed as PR #131 (reworks 1–2, both `VERDICT: PASS`). Wave 81 landed as PR #132 (rework-1, `VERDICT: PASS` re-issued). Wave 15 landed as PR #133 (rework-1, `VERDICT: PASS` re-issued). #77, #9, #81 and #15 are merged; remaining work is live-mission/fleet-host proof.
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
> ./scripts/verify-rigs.sh --check-only     # Expect: 39 checks passed, 0 failed
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
