# AUDIT_REPORT_FINDINGS: heretek-rigs

## Baseline
- Commit: `9ec0014ff44e7e174f6d7a5c74590de5f8fe664f` (from `.git/refs/heads/main`; `git log` message/date NOT RUN — shell blocked)
- Audit date (UTC): 2026-10-19 (user-supplied session date; `date -u` NOT RUN)
- Tool versions: UNKNOWN — shell blocked (`permission.rejected` on every shell call for controller and all subagents; python3/node/npm/git/jq/rg/rig/pi/docker versions not runnable)
- Dirty files: UNKNOWN (`git status --porcelain` not runnable); no worktree copy made (worktree creation needs shell)
- Scratch space: NOT CREATED (`mktemp`/worktree blocked); subagent raw notes are in-session only (no `$AUDIT_TMP/{alpha,beta,gamma}.md` files)
- Host capabilities: file-content (read-only) audit only via Read/Glob/Grep + 3 subagents (Alpha/Beta/Gamma) + 3 cross-examiners; every live check (rig/pi/docker/network/python/jsonschema/digest recompute/sabotage/bootstrap/render-seat/guard-profiles/compose) NOT RUN
- Per section 0.5 + Cardinal Rule: no claim is VERIFIED without execution (ceiling is PARTIAL for static-consistent)
- Formation executed: Alpha (claims [A]), Beta (claims [B]), Gamma (claims [G]) ran concurrently with no cross-reading; cross-examination (Alpha's→Beta, Beta's→Gamma, Gamma's→Alpha) completed; all challenges returned CONFIRMED (one refinement: Alpha's patch-bypass "REMEDIATED" holds for toolchain only, not checked-in artifacts — see HR-5.5-patch)

## Verdict
heretek-rigs at HEAD `9ec0014` is the 51-role / 8-rig OpenRig monorepo described in the prompt, and its static shapes (fleet partition 6+11+4+6+11+6+7, schema keys/versions, permission first/last bounds, sidecar pins, exact-set networks, model/runtime pins) are internally consistent on disk. Three defects stand on static evidence, each re-verified from scratch and cross-examined (all CONFIRMED): the upstream tarball attestation is still a placeholder forcing the verify gate red on a clean tree (HR-2.1, P1, Claim 8.2 BROKEN), the `subagent-driven-development` sibling skill is still absent with dangling fleet bindings and unconditional hard script refs (HR-6.1, P2, Claim 6.1 BROKEN), and allowed `git log/show/diff` prefixes still admit patch output past `path` read-denies in every checked-in artifact even though the renderer+gate+gate-role toolchain fix has landed unmaterialized (HR-5.5-patch, P3). The prior HR-5.5 rendered-allow-superset gap is FIXED in gate (`verify-rigs.sh:577-584` subset checks; live injection UNVERIFIABLE). No live proof was possible (rig/pi/docker/python/network all blocked). The single most important fix is to attest the real `@openrig/cli@0.6.11` tarball SHA-256 into `schemas/rigspec-keys.pinned.json:12` and run `python3 scripts/generate-rigs.py` on a networked shell host (HR-2.1 + HR-5.5-patch regen), which unblocks the green gate, the audit-loop self-test, and any reachable `STATUS: NO_FINDINGS`.

## Prioritized Defect Matrix
| ID | Priority | Claim | Location | Summary |
|----|----------|-------|----------|---------|
| HR-2.1-pinned-still-local | P1 | 2.1 / 8.2 | `schemas/rigspec-keys.pinned.json:12` + `scripts/verify-rigs.sh:183-186` | `tarball_sha256` placeholder forces gate-red on clean tree |
| HR-6.1-missing-subagent-sibling | P2 | 6.1 | `specs/agents/_shared/skills/` (absent dir) + `fleet/fleet.yaml:2860,3359` | sibling absent; dangling seat bindings; hard script refs dangle, Native path intact |
| HR-5.5-git-patch-read-bypass | P3 | 5.3 / 5.5 | `specs/agents/security/threat-modeler/runtime/pi-permission-config.json:15-38` (allows `:24-27`, no patch denies) vs `scripts/render-seat.py:398-414` + `scripts/verify-rigs.sh:556-567` (toolchain fixed, artifacts stale) | `git log/show/diff` prefixes admit `-p` patch output past `fleet/*`+`scripts/*` read-denies on disk |

## Findings
### HR-2.1-pinned-still-local: upstream tarball attestation still placeholder, gate red on clean tree
- **Priority:** P1
- **Claim:** 2.1 (rig validation chain attested to upstream) + 8.2 (`verify-rigs.sh --check-only` exits 0 clean)
- **Location:** `schemas/rigspec-keys.pinned.json:12`; gate `scripts/verify-rigs.sh:183-186`; generator `scripts/generate-rigs.py:384-403` (per Alpha re-read); tgz `schemas/openrig-cli-0.6.11.tgz` absent
- **Proof:** read-only (shell blocked). `pinned.json:10-14` shows `"tarball_sha256": "PENDING_SHELL_HOST_REFRESH", "refreshed_at": null` (controller re-read this run); gate requires `re.fullmatch(r"[0-9a-f]{64}", ...)` else `fail()`; live `./scripts/verify-rigs.sh --check-only; echo $?` NOT RUN (predicted 1). No env/placeholder allowance or skip branch on this path (`CI`/`HERETEK_ALLOW_SYNTHETIC` govern a different SYNTHETIC check)
- **Raw output:** `"tarball_sha256": "PENDING_SHELL_HOST_REFRESH",` (verbatim file content); gate: `fail("schemas/rigspec-keys.pinned.json provenance.upstream_tarball.tarball_sha256 must be the 64-hex SHA-256 of the upstream tarball ...")`
- **Why it matters:** every clean-tree verify exits 1, so Claim 8.2 is false, `audit_loop.py --self-test` fails at its gate step, and the loop can never reach `STATUS: NO_FINDINGS`.
- **Remediation:** on a networked shell host from repo root: `npm pack @openrig/cli@0.6.11 && sha256sum openrig-cli-0.6.11.tgz`, record the 64-hex digest at `pinned.json` `provenance.upstream_tarball.tarball_sha256` (+ `refreshed_at`), optionally place tarball at `schemas/openrig-cli-0.6.11.tgz`, then `python3 scripts/generate-rigs.py`.
- **Verify the fix:** `./scripts/verify-rigs.sh --check-only; echo $?` -> 0; `python3 scripts/audit_loop.py --self-test; echo $?` -> 0
- **Cross-examination:** Beta challenged (re-read pin + gate 183-192 + tgz glob; checked placeholder allowance/env bypass/skip branch — all negative); CONFIRMED, P1 stands (fail-closed, documented "red by design" -> not P0; breaks top-level clean invariant -> not P2).

### HR-6.1-missing-subagent-sibling: vendored subagent-driven-development sibling absent, bindings dangling
- **Priority:** P2
- **Claim:** 6.1 — 63 skills full-fidelity incl. multi-file `subagent-driven-development` sibling required by `writing-plans`/`executing-plans` REQUIRED SUB-SKILL refs
- **Location:** `specs/agents/_shared/skills/` (62 dirs, no `subagent*` — Beta re-listed this run); `fleet/skills-lock.json` (62 entries, `grep subagent` -> No matches); `specs/agents/_shared/agent.yaml:5-129` (62 `resources.skills`); refs `specs/agents/_shared/skills/writing-plans/SKILL.md:59,200-204`, `specs/agents/_shared/skills/executing-plans/SKILL.md:53,60,121,126,236` (+ scripts `executing-plans/scripts/task-start:12,21`, `task-done:10,21` `sdd="$(cd .../../../subagent-driven-development/scripts ...)"` under `set -euo pipefail`); bindings `fleet/fleet.yaml:2860-2861` (product-director), `:3359-3360` (system-architect); verifier expects 63 at `scripts/verify-rigs.sh:251` + sibling gate `:314-356`
- **Proof:** read-only: skills-dir read returns 62 entries; `glob skills/subagent-driven-development/*` -> No files found; `grep subagent skills-lock.json` -> No matches; live `ls|wc -l` + lock-vs-disk reconcile NOT RUN. Nearest candidate `dispatching-parallel-agents/` contains zero `subagent-driven-development|sdd-workspace|task-brief` refs (no alias/proxy)
- **Raw output:** 62 dirs (`address-sanitizer/` ... `yara-rule-authoring/`); `task-start:21`: `sdd="$(cd "$(dirname "$0")/../../subagent-driven-development/scripts" && pwd)"`; `executing-plans/SKILL.md:126`: `` `../subagent-driven-development/scripts/sdd-workspace PLAN_FILE` ``; `:236`: `../subagent-driven-development/scripts/review-package`
- **Why it matters:** two seats bind a skill id with no backing directory/lock entry, and three unconditional procedural script paths (`sdd-workspace` at skill start, `review-package` at final review, `task-start`/`task-done` sdd resolution under `set -euo pipefail` with no `||` guard → immediate exit on missing dir) resolve against a nonexistent dir; plan/execute flow degrades where it touches those scripts. Verifier count+sibling gates go red by design.
- **Remediation:** vendor `obra/superpowers@bb92a77` `skills/subagent-driven-development/` (multi-file incl. `scripts/` + LICENSE) under `specs/agents/_shared/skills/subagent-driven-development/`, add `skills-lock.json` entry + `_shared/agent.yaml` `resources.skills` binding, re-run `python3 scripts/generate-rigs.py`.
- **Verify the fix:** `ls specs/agents/_shared/skills | wc -l` (=63); lock-vs-disk reconcile; `./scripts/verify-rigs.sh --check-only` -> 0
- **Cross-examination:** Gamma challenged (re-read all REQUIRE sites + both scripts + fleet bindings + `verify-rigs.sh:251,314-356`; corrected two non-existent paths cited by Beta — substance unchanged); CONFIRMED. DOWNGRADE P1->P2 SUSTAINED: `writing-plans:59` is disjunctive ("Use SDD (recommended) or executing-plans"), `:200-204` gates SDD-requirement on user choosing the subagent-driven path, and `executing-plans:49-51` documents a working no-subagent Native fallback — seats function via the Native path, so P1/seat-outage refuted. P3 refuted in turn (dangling refs + missing sibling + unconditional script failures exceed cosmetic).

### HR-5.5-git-patch-read-bypass: allowed git log/show/diff prefixes admit patch output past path read-denies (artifacts stale, toolchain fixed)
- **Priority:** P3
- **Claim:** 5.3 / 5.5 (secret/sensitive read-denies vs. role-scoped git allows)
- **Location:** `specs/agents/security/threat-modeler/runtime/pi-permission-config.json:24-27` (allows) vs `:57-58` (denies), bash `:28-37` ends at `"*)*"` with zero patch denies (controller re-read this run; identical in `policy-enforcement.json:30-44`, `exec-director`, `sabotage-qa-tester`); fleet grants `fleet/fleet.yaml:590-593` (+ ~19 roles identical); gate `scripts/verify-rigs.sh:547-567`; renderer `scripts/render-seat.py:387-414`; probes `scripts/gate-role.sh:32-40,69-73`; generator `scripts/generate-rigs.py:629-644`
- **Proof:** read-only. Every checked-in locked seat allows `"git log --oneline*"`, `"git show --stat*"`, `"git diff --stat*"`, `"git diff --name-only*"` (trailing `*` admits flag suffixes). `git log --oneline -p -- fleet/fleet.yaml` matches `"git log --oneline*"`; `-p` matches none of the 10 on-disk terminal denies — while `fleet/*` is `"deny"` in `path`. Toolchain half HAS landed since the prior run: `render-seat.py:398-414` emits `"* -p*","*--patch*","*--full-diff*","*--textconv*"` LAST; `verify-rigs.sh:556-567` mandates all 14 terminal denies + ordering; `gate-role.sh:69-70` probes both patch exfils must-deny (+ `:72` anti-over-block must-allow); `generate-rigs.py:629-644` renders via `build_seat_files` so regen materializes the fix. Consequence: checked-in specs are STALE — clean-tree `--check-only` now fails on missing terminal denies (second red cause alongside HR-2.1).
- **Raw output:** `threat-modeler:24-27` allow prefixes; `path` denies `fleet/*` (`:57`), `scripts/*` (`:58`); on-disk bash ends `"*)*": "deny"` (`:37`); renderer loop `:398-414` + gate tuple `:558` both contain the 4 patch denies
- **Why it matters:** punctures the `fleet/*` + `scripts/*` read-deny layer for locked seats on disk (orchestrator-config disclosure; charter/recon surface). Blast radius capped at tracked content — secrets live untracked in `$HERETEK_SECRETS` (4.3/4.4), and `*.env`/`*id_rsa*` direct-read denies still hold — hence P3, not higher.
- **Remediation (fail-closed):** run `python3 scripts/generate-rigs.py` on a shell host (NOT a hand-edit — materializes renderer patch denies into all 51 specs), then `./scripts/verify-rigs.sh --check-only` + `bash scripts/gate-role.sh threat-modeler` (patch probes must deny, anti-over-block must allow).
- **Verify the fix:** `bash scripts/gate-role.sh threat-modeler` with patch probes → both deny; full `./scripts/verify-rigs.sh --check-only` stays green (needs HR-2.1 attestation too)
- **Cross-examination:** Alpha challenged (re-read `:540-584`, renderer, gate-role canary+probes, all artifact maps, fleet grants, generator); CONFIRMED — STILL OPEN on disk (not FIXED), same ID kept (identical bypass family, residual documented in gate comments), P3 sustained (tracked-only; upgrade to P2 would need secret-bearing tracked content — not in evidence). Alpha's competing "REMEDIATED" verdict REFUTED as fleet-state claim (holds for renderer+gate code only).

## Claim Ledger
| Claim | Status | Evidence (command or finding ID) |
|-------|--------|----------------------------------|
| 1.1 | PARTIAL | static: 51 `member_fragments` + 51 role keys + 51 `specs/agents/*/*/agent.yaml` (incl 37/51); Heretek-Crew diff NOT RUN |
| 1.2 | PARTIAL | static: 6+11+4+6+11+6+7=51, spot exactly-one-rig; full cross-product NOT RUN |
| 1.3 | PARTIAL | static: 3-seat command pod + 15 pods + 51 members + rig.all-51.yaml + roster; `rig expand` NOT RUN |
| 1.4 | PARTIAL | static: 7-file shape, zero stubs (sweeps noted), `local:../../_shared`->`local:../_shared` sole delta (spot-diffed); full byte-drift diff NOT RUN |
| 2.1 | PARTIAL | static keys/version pass; live `rig spec validate` NOT RUN; attestation placeholder -> HR-2.1 (8.2) |
| 2.2 | PARTIAL | static edge kinds/qualification sampled, no cycles in checked subgraph (zero `spawned_by` edges used — legal); programmatic DAG NOT RUN |
| 2.3 | PARTIAL | static: 51x `send_text`, zero `guidance_merge`/`hooks:` in agent.yaml (include-scoped grep), lifecycle pins; `rig agent validate` NOT RUN |
| 2.4 | PARTIAL | static zero `guidance_merge` in specs+rigs agent.yaml (`behaviour.json` `guidance_merge` values are generator-emitted culture/told-files delivery, `generate-rigs.py:1058`, not startup files); live preflight/bundle NOT RUN |
| 2.5 | PARTIAL | static `copytree symlinks=False` + `is_symlink` sweep + `..`/absolute gates present; `find -type l` + `rig bundle check` NOT RUN |
| 3.1 | PARTIAL | static: 8+8+8+1 present, required-fields/consts shape OK; Draft202012Validator NOT RUN |
| 3.2 | PARTIAL | static: 64-hex digest present, pattern-conformant; JCS recompute NOT RUN |
| 3.3 | PARTIAL | static: joined-string IDs sorted (qa sample), triple-agreeing digests; disk recompute + `identity-vectors.json` replay NOT RUN |
| 4.1 | PARTIAL | static model/runtime pins on all sampled seats + member/pod fragments + agent defaults, all-omp presets; seat census + preflight NOT RUN |
| 4.2 | PARTIAL | static renderer logic (0600, `!cat`, O_NOFOLLOW, uid pin, strict default, `--pod`/phantom fail-closed); live render/bootstrap NOT RUN |
| 4.3 | PARTIAL | static `!cat`/echo-Bearer shapes in key/env/headers only (samples), refusal logic present; live refusal matrix NOT RUN |
| 4.4 | PARTIAL | static: zero `env:` in rig.yaml, only `permission_policy` lines match secret-name grep; full-repo literal scan NOT RUN |
| 5.1 | PARTIAL | static: 18x `builtin:locked` + rig defaults, 16x docs/sbom-only, zero yolo/open in shipped surface; live NOT RUN (subset-gap now FIXED in gate, live injection UNVERIFIABLE) |
| 5.2 | PARTIAL | static: `*` first / `*..*` last in both maps on samples; hostile corpus NOT RUN (note: checked-in bash maps lack the 4 patch denies the gate now mandates -> regen pending, see HR-5.5-patch) |
| 5.3 | PARTIAL | static: secret-denies + deny/timeout present, zero `ask`; live probes NOT RUN; patch-bypass -> HR-5.5-git-patch-read-bypass (P3 STILL OPEN, stale artifacts) |
| 5.4 | PARTIAL | static: 3 mut-denies on all samples, read-only AST/LSP allows, no pi-lsp@0.1.7 in shipped surface; live bypass probe NOT RUN |
| 5.5 | PARTIAL | static: bash/mcp bounds + 10 on-disk terminal denies ordered on samples (gate+renderer now mandate 14 incl. patch flags — artifacts stale); escape corpus NOT RUN; -> HR-5.5-git-patch-read-bypass (P3) |
| 6.1 | BROKEN | HR-6.1-missing-subagent-sibling |
| 6.2 | PARTIAL | static pins exact, zero r2mcp/aws-mcp/:latest in catalog (`replaces:` notes only), read-only flags; liveness NOT RUN |
| 7.1 | PARTIAL | static 8x 127.0.0.1 + 9 pinned images, zero 0.0.0.0/bare in shipped surface; compose/bind check NOT RUN |
| 7.2 | PARTIAL | static 20-toggle exact set `"0"` + 0.5.0 + :ro; proxy probe NOT RUN |
| 7.3 | PARTIAL | static exact-set networks + ro mounts + guard logic; live matrix NOT RUN |
| 8.1 | UNVERIFIABLE | idempotence NOT RUN (shell blocked); static sorted()/--check-idempotent features noted |
| 8.2 | BROKEN | HR-2.1 placeholder forces exit 1 on clean tree (plus stale patch-deny artifacts second red cause) |
| 8.3 | UNVERIFIABLE | self-test NOT RUN; static evaluator logic reads fail-closed (7 vectors) |
| 8.4 | PARTIAL | all 8 deliverables present non-empty; full placeholder sweep NOT RUN (adjacent: `LICENSE.md:1` is literally `PLACEHOLDER` — out of claim scope, noted for human) |

## Sabotage Results
| Invariant | One-line sabotage (file:line, before -> after) | Suite result | Caught? |
|-----------|------------------------------------------------|--------------|---------|
| 1.1 rm static-analysis-lead | `specs/agents/qa/static-analysis-lead/agent.yaml` present -> removed | NOT RUN (shell blocked, no worktree) | UNVERIFIABLE (static: role-count gate exists) |
| 2.1 unknown_key | `rigs/executive-and-architecture/rig.yaml` clean -> `unknown_key: true` | NOT RUN | UNVERIFIABLE (static: unknown-keys fail gates) |
| 2.2 cycle edge | DAG -> add `delegates_to product-director->exec-director` | NOT RUN | UNVERIFIABLE (static: adjacency+DFS fail gates) |
| 2.4 guidance_merge | `send_text` -> `guidance_merge` (exec-director agent.yaml) | NOT RUN | UNVERIFIABLE (static: specs+vendored guidance_merge gates) |
| 2.5 symlink | clean -> `agents/link.md` symlink | NOT RUN | UNVERIFIABLE (static: is_symlink sweep) |
| 3.2 bodyDigest flip | `registry/status.json` digest -> flipped hex char | NOT RUN | UNVERIFIABLE (static: digest-equality gate) |
| 4.3 sk-live | `runtime/mcp.json` `!cat /...` -> `sk-live-123456` | NOT RUN | UNVERIFIABLE (static: literal-secret regex gate, `!`-in-args die) |
| 5.1 yolo | `builtin:locked` -> `builtin:yolo` | NOT RUN | UNVERIFIABLE (static: policy gates, LOCKED_18_ROLES) |
| 5.2 remove *..* | `policy-enforcement.json` `*..*:deny` -> removed | NOT RUN | UNVERIFIABLE (static: bounds/order gates) |
| 5.4 code_rewrite allow | `code_rewrite:deny` -> `allow` | NOT RUN | UNVERIFIABLE (static: mut-deny gate) |
| 7.1 0.0.0.0 | `127.0.0.1:8888:8080` -> `0.0.0.0:8888:8080` | NOT RUN | UNVERIFIABLE (static: loopback-bind gate) |
| 7.2 POST:1 | `POST: "0"` -> `POST: "1"` | NOT RUN | UNVERIFIABLE (static: 20-toggle exact-set gate) |

## Regression Ledger
| Previous finding ID | Previous priority | Status now: FIXED / STILL OPEN / REGRESSED / NO LONGER APPLICABLE | Evidence |
|-----|-------------------|--------|----------|
| HR-2.1-pinned-still-local | P1 | STILL OPEN | `pinned.json:12` placeholder + gate `verify-rigs.sh:183-186` unchanged (controller + Alpha + Beta-challenger all re-read this run) |
| HR-6.1-missing-subagent-sibling | P2 (downgraded from P1 on prior cross-exam) | STILL OPEN (P2 sustained: absence confirmed, REQUIRED shown disjunctive, hard script refs unconditional) | 62 skill dirs, no `subagent*`; lock grep no match; dangling bindings `fleet.yaml:2860-2861,3359-3360`; disjunctive REQUIRE `writing-plans:59,200-204` + fallback `executing-plans:49-51`; unconditional refs + `task-start/task-done:21` (Beta + Gamma-challenger re-verified) |
| HR-7.3-network-exclusivity-gap | P2 (fixed) | FIXED retained | static exclusive exact-set networks + ro mounts + guard retained (`docker-compose.sidecars.yml`, `Makefile:46-54`); live matrix NOT RUN |
| HR-5.5-rendered-allow-superset-gap | P2 (new on prior run) | FIXED (in gate; live injection UNVERIFIABLE) | `verify-rigs.sh:568-584` now asserts rendered bash/path_write allows ⊆ fleet-declared sets (surplus fails); `:530-539` mcp bound-set + `:481` rendered↔rendered equality; Alpha + Gamma + both challengers CONFIRMED |
| HR-5.5-git-patch-read-bypass | P3 (new on prior run) | STILL OPEN (toolchain landed, artifacts stale; P3 sustained) | on-disk bash maps still end `"*)*"` with zero patch denies (`threat-modeler:15-38` controller re-read); renderer `render-seat.py:398-414` + gate `:556-567` + probes `gate-role.sh:32-40,69-73` landed but unmaterialized — regen pending (Gamma + Alpha-challenger CONFIRMED) |

## Not Audited / Unverifiable
- All live checks NOT RUN (shell `permission.rejected` on controller + all subagents): `rig spec validate` / `bundle check` / `agent validate` / `preflight` / `expand` / `add` / daemon up-down; `pi` seat render; `find -type l`; `jsonschema` validation; JCS/`configurationId`/`packageDigest` recomputes; `render-seat.py` refusal matrix; `seed-rig.py` / `bootstrap-pi-seats.sh` in isolated `OPENRIG_HOME`; `make guard-profiles` matrix; `docker compose config`; all 12 sabotage runs; `generate-rigs.py --check-idempotent`; `verify-rigs.sh --check-only`; `audit_loop.py --self-test`.
- No `$AUDIT_TMP` scratch/worktree created or cleaned (blocked); real-checkout dirtiness unverified via shell — human must confirm `git status --porcelain` shows only this report (+ prompt file if untracked). Commit read from `.git/refs/heads/main` (`9ec0014`); commit message/date not re-read (no shell).
- Coverage: all 30 claim IDs have a ledger status (Alpha 10 + Beta 10 + Gamma 10; ceiling PARTIAL without execution). Finding IDs stable (`HR-<claim-id>-<slug>`) for next-run matching.
- Human must provide: networked shell host with `@openrig/cli@0.6.11`, pi 1.3.0, loopback daemon, then re-run section-4 recipes, the 12 sabotage targets, the superset-injection probe, and the `gate-role.sh threat-modeler` patch probes; first actions are the HR-2.1 tarball attestation + `python3 scripts/generate-rigs.py` regen (materializes patch denies + any skill vendoring).

## Final Loop Sentinel
STATUS: FINDINGS_DETECTED
