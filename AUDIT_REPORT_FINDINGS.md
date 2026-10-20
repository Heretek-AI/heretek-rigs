# AUDIT_REPORT_FINDINGS: heretek-rigs

## Baseline
- Commit: `9e805ade8de9f54540ca6ca2174b955a0a629607` (from `.git/refs/heads/main`; `git log` message/date NOT RUN — shell blocked)
- Previous run commit: `99b4420c6a2e50749c8bb0b3a8d02186b9aa2b41` (prior report); tree moved (`9e805ad`), re-audited from scratch
- Audit date (UTC): 2026-10-20 (session date; `date -u` NOT RUN — shell blocked)
- Tool versions: UNKNOWN — shell blocked (`permission.rejected` on every shell call for controller and all subagents; python3/node/npm/git/jq/rg/rig/pi/docker versions not runnable)
- Dirty files: UNKNOWN (`git status --porcelain` not runnable); no worktree copy made (worktree creation needs shell)
- Scratch space: NOT CREATED (`mktemp`/worktree blocked); subagent raw notes are in-session only (no `$AUDIT_TMP/{alpha,beta,gamma}.md` files)
- Host capabilities: file-content (read-only) audit only via Read/Glob/Grep + 3 subagents (Alpha/Beta/Gamma) + 3 cross-examiners; every live check (`rig spec validate` / `bundle check` / `agent validate` / `preflight` / `expand` / `add` / daemon up-down, `pi` seat render, `find -type l`, `jsonschema` validation, JCS/`configurationId`/`packageDigest` recompute, `render-seat.py` refusal matrix, `seed-rig.py` / `bootstrap-pi-seats.sh` in isolated `OPENRIG_HOME`, `make guard-profiles` matrix, `docker compose config`, all 12 sabotage runs, `generate-rigs.py --check-idempotent`, `verify-rigs.sh --check-only`, `audit_loop.py --self-test`, network/registry probes) NOT RUN
- Per section 0.5 + Cardinal Rule: no claim is VERIFIED without execution (ceiling is PARTIAL for static-consistent)
- Formation executed: Alpha (claims [A]) + Beta (claims [B]) + Gamma (claims [G]) ran concurrently with no cross-reading; cross-examination (Alpha→Beta-challenger, Beta→Gamma-challenger, Gamma→Alpha-challenger) completed; synthesis by controller with on-disk re-reads of `specs/agents/languages/go-backend-eng/runtime/policy-enforcement.json:60-64`, `specs/agents/_shared/skills/executing-plans/SKILL.md:50`, `specs/agents/_shared/agent.yaml:120-121`, `specs/agents/_shared/skills/using-superpowers/{SKILL.md,LICENSE,references/}`, `fleet/fleet.yaml:25-28`

## Verdict
heretek-rigs at HEAD `9e805ad` remains the 51-role / 8-rig OpenRig monorepo described in the prompt, and its static shapes (fleet partition 6+11+4+6+11+6+7, schema keys/versions, permission first/last bounds, sidecar pins, exact-set networks, model/runtime pins) are internally consistent on disk. Both prior-report P3 residuals are FIXED on static re-verification and all three cross-examiners confirmed the fix: `using-superpowers` is now vendored with lock entry plus specs/8-rigs/fleet/roster/bundle bindings so the `executing-plans/SKILL.md:50` pointer resolves, and `"*\t-p*"` is now materialized in the sampled `policy-enforcement.json` (15-deny terminal block) with 100+ escaped-sequence hits across both artifact kinds plus renderer/verifier/gate consistency. No new P0/P1/P2/P3 was proven on static attack. No live proof was possible (rig/pi/docker/python/network all blocked), so per the prompt's NO_FINDINGS gate (zero findings + every verifiable claim VERIFIED + all sabotage caught + verifier exit 0) the sentinel must stay FINDINGS_DETECTED. The single most important next step is to re-run on a networked shell host: `python3 scripts/generate-rigs.py --check-idempotent`, the section-4 live recipes, the 12 sabotage targets, and the upstream `obra/superpowers@bb92a77` tree-hash + `npm pack @openrig/cli@0.6.11` attestations — the only path to `STATUS: NO_FINDINGS`.

## Prioritized Defect Matrix
| ID | Priority | Claim | Location | Summary |
|----|----------|-------|----------|---------|
| _none — no open findings this run_ | — | — | — | — |

## Findings
No open findings this run. Both prior-run findings were re-verified from scratch and found FIXED on disk (static basis); see Regression Ledger. Live confirmation (verifier exit 0, matcher corpus, upstream hashes) is still owed on a shell-capable host.

## Claim Ledger
| Claim | Status | Evidence (command or finding ID) |
|-------|--------|----------------------------------|
| 1.1 | PARTIAL | static: `fleet.yaml:25-28` counts 51/8/15 + 51 role entries + 51 `specs/agents/*/*/agent.yaml` (incl 37/51); Heretek-Crew diff NOT RUN |
| 1.2 | PARTIAL | static: 6+11+4+6+11+6+7=51 member counts sampled per rig; full uniqueness matrix NOT RUN |
| 1.3 | PARTIAL | static: 3-seat command pod + 15 pods + 51 members + rig.all-51.yaml + roster; `rig expand`/`add` NOT RUN |
| 1.4 | PARTIAL | static: 7-file shape sampled, zero stubs sampled, `local:../../_shared`→`local:../_shared` sole delta in sampled pair; full byte-drift diff NOT RUN |
| 2.1 | PARTIAL | static keys/version + pinned-keys attestation shape; live `rig spec validate` + tarball-byte attestation NOT RUN |
| 2.2 | PARTIAL | static edge kinds/qualification sampled, DFS gate present; programmatic full-DAG + bundle check NOT RUN |
| 2.3 | PARTIAL | static: 51x `send_text`, zero `guidance_merge`/`hooks:` in agent.yaml; `rig agent validate` NOT RUN |
| 2.4 | PARTIAL | static zero `guidance_merge` in specs+rigs agent.yaml; live preflight/bundle NOT RUN |
| 2.5 | PARTIAL | static `copytree symlinks=False` + `is_symlink` sweep + escape gates; `find -type l` + `rig bundle check` NOT RUN |
| 3.1 | UNVERIFIABLE | presence/shape static only; Draft202012Validator NOT RUN (shell blocked) |
| 3.2 | UNVERIFIABLE | 64-hex shape only; JCS recompute NOT RUN |
| 3.3 | UNVERIFIABLE | joined-string/digest shapes + identity-vectors constants static; disk recompute + replay NOT RUN |
| 4.1 | PARTIAL | static model/runtime pins sampled + all-omp presets; seat census + preflight NOT RUN |
| 4.2 | PARTIAL | static renderer logic (0600, `!cat`, O_NOFOLLOW, uid pin, strict default); live render/bootstrap NOT RUN |
| 4.3 | PARTIAL | static `!cat`/echo-Bearer shapes in key/env/headers only, refusal logic present; live refusal matrix NOT RUN |
| 4.4 | PARTIAL | static: zero `env:` in sampled rigs rig.yaml, zero yolo/open; full literal-secret scan NOT RUN |
| 5.1 | PARTIAL | static: READONLY_16/LOCKED_18 gates + sampled `builtin:locked`, zero yolo/open; full 18-seat census + live NOT RUN |
| 5.2 | PARTIAL | static: `*` first / `*..*` last in both maps on samples; hostile corpus NOT RUN |
| 5.3 | PARTIAL | static: secret-denies + deny/timeout present, zero `ask`; live probes NOT RUN; prior tab residual FIXED (see Regression Ledger) |
| 5.4 | PARTIAL | static: mut-denies present, read-only AST/LSP allows scoped, no pi-lsp@0.1.7 pins; live bypass probe NOT RUN |
| 5.5 | PARTIAL | static: 15/15 terminal denies incl `"*\t-p*"` on samples + 100+ escaped hits, mcp fail-closed; escape corpus NOT RUN; prior gap FIXED (see Regression Ledger) |
| 6.1 | PARTIAL | static: 64 lock entries + 64 skill dirs + SDD multi-file + 6 SOP skills + using-superpowers vendored/bound; upstream fidelity UNVERIFIABLE; prior dangle FIXED (see Regression Ledger) |
| 6.2 | PARTIAL | static pins exact, zero r2mcp/aws-mcp/:latest active, read-only flags, liveness labels; registry existence NOT RUN |
| 7.1 | PARTIAL | static 8x 127.0.0.1 + pinned images, zero 0.0.0.0/bare; compose/bind check NOT RUN |
| 7.2 | PARTIAL | static 20-toggle exact set `"0"` + 0.5.0 + :ro; proxy probe NOT RUN |
| 7.3 | PARTIAL | static exact-set networks + ro mounts + guard logic; live matrix NOT RUN |
| 8.1 | UNVERIFIABLE | idempotence NOT RUN (shell blocked); static determinism features noted |
| 8.2 | UNVERIFIABLE | live exit NOT RUN; gate-shape passes statically |
| 8.3 | UNVERIFIABLE | self-test NOT RUN; static evaluator reads fail-closed |
| 8.4 | PARTIAL | all 8 deliverables present non-empty; full placeholder sweep NOT RUN |

## Sabotage Results
| Invariant | One-line sabotage (file:line, before -> after) | Suite result | Caught? |
|-----------|------------------------------------------------|--------------|---------|
| 1.1 rm static-analysis-lead | `specs/agents/qa/static-analysis-lead/agent.yaml` present -> removed | NOT RUN (shell blocked, no worktree) | UNVERIFIABLE (static: role-count gate exists) |
| 2.1 unknown_key | `rigs/executive-and-architecture/rig.yaml` clean -> `unknown_key: true` | NOT RUN | UNVERIFIABLE (static: unknown-keys fail gates) |
| 2.2 cycle edge | DAG -> add `delegates_to product-director->exec-director` | NOT RUN | UNVERIFIABLE (static: adjacency+DFS fail gates) |
| 2.4 guidance_merge | `send_text` -> `guidance_merge` (exec-director agent.yaml) | NOT RUN | UNVERIFIABLE (static: specs+vendored guidance_merge gates) |
| 2.5 symlink | clean -> `agents/link.md` symlink | NOT RUN | UNVERIFIABLE (static: is_symlink sweep) |
| 3.2 bodyDigest flip | `registry/status.json` digest -> flipped hex char | NOT RUN | UNVERIFIABLE (static: digest-equality gate) |
| 4.3 sk-live | `runtime/mcp.json` `!cat /...` -> `sk-live-123456` | NOT RUN | UNVERIFIABLE (static: literal-secret regex gate) |
| 5.1 yolo | `builtin:locked` -> `builtin:yolo` | NOT RUN | UNVERIFIABLE (static: policy gates, LOCKED_18_ROLES) |
| 5.2 remove *..* | `policy-enforcement.json` `*..*:deny` -> removed | NOT RUN | UNVERIFIABLE (static: bounds/order gates) |
| 5.4 code_rewrite allow | `code_rewrite:deny` -> `allow` | NOT RUN | UNVERIFIABLE (static: mut-deny gate) |
| 7.1 0.0.0.0 | `127.0.0.1:8888:8080` -> `0.0.0.0:8888:8080` | NOT RUN | UNVERIFIABLE (static: loopback-bind gate) |
| 7.2 POST:1 | `POST: "0"` -> `POST: "1"` | NOT RUN | UNVERIFIABLE (static: 20-toggle exact-set gate) |

## Regression Ledger
| Previous finding ID | Previous priority | Status now: FIXED / STILL OPEN / REGRESSED / NO LONGER APPLICABLE | Evidence |
|-----|-------------------|--------|----------|
| HR-6.1-using-superpowers-prose-ref | P3 | FIXED (static; live gate + upstream hash still owed) | `using-superpowers/` vendored (`SKILL.md`+`LICENSE`+`references/` 7 files); `fleet/skills-lock.json` 64th entry; `specs/agents/_shared/agent.yaml:120-121` + 8/8 rigs copies bound; `fleet.yaml` live binding; `executing-plans/SKILL.md:50` resolves; Alpha+Beta+Gamma + 2 challengers CONFIRMED static |
| HR-5.5-tab-p-suffix-gap | P3 | FIXED (static; live matcher + verifier exit still owed) | `go-backend-eng/policy-enforcement.json:60-64` 15 denies with `"*\t-p*": "deny"` at :61 (twin `pi-permission-config.json:52`); 100+ escaped `*\t-p*` hits across both artifact kinds; `render-seat.py:414` + `verify-rigs.sh:587` + `gate-role.sh:73-74` consistent; Alpha+Gamma + 2 challengers CONFIRMED static; old-report literal-TAB grep reading corrected (JSON stores `\t` escape, not TAB byte) |

## Not Audited / Unverifiable
- All live checks NOT RUN (shell `permission.rejected` on controller + all subagents): `rig spec validate` / `bundle check` / `agent validate` / `preflight` / `expand` / `add` / daemon up-down; `pi` seat render; `find -type l`; `jsonschema` validation; JCS/`configurationId`/`packageDigest` recomputes; `render-seat.py` refusal matrix; `seed-rig.py` / `bootstrap-pi-seats.sh` in isolated `OPENRIG_HOME`; `make guard-profiles` matrix; `docker compose config`; all 12 sabotage runs; `generate-rigs.py --check-idempotent`; `verify-rigs.sh --check-only`; `audit_loop.py --self-test`.
- No `$AUDIT_TMP` scratch/worktree created or cleaned (blocked); real-checkout dirtiness unverified via shell — human must confirm `git status --porcelain` shows only this report (+ prompt file if untracked). Commit read from `.git/refs/heads/main` (`9e805ad`); commit message/date not re-read (no shell).
- Coverage: all 30 claim IDs have a ledger status (Alpha 10 + Beta 10 + Gamma 10; ceiling PARTIAL without execution). Finding IDs stable (`HR-<claim-id>-<slug>`) for next-run matching.
- Human must provide: networked shell host with `@openrig/cli@0.6.11`, pi 1.3.0, loopback daemon, then run section-4 recipes, the 12 sabotage targets, `verify-rigs.sh --check-only` → 0, `audit_loop.py --self-test`, and the `npm pack @openrig/cli@0.6.11` + `obra/superpowers@bb92a77:skills/using-superpowers` tree-hash attestations to reach NO_FINDINGS.

## Final Loop Sentinel
STATUS: FINDINGS_DETECTED
