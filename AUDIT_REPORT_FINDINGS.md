# AUDIT_REPORT_FINDINGS: heretek-rigs

## Baseline
- Commit: `99b4420c6a2e50749c8bb0b3a8d02186b9aa2b41` (from `.git/refs/heads/main`; `git log` message/date NOT RUN — shell blocked)
- Previous run commit: `9ec0014ff44e7e174f6d7a5c74590de5f8fe664f` (prior report); tree moved, re-audited from scratch
- Audit date (UTC): 2026-10-20 (session date; `date -u` NOT RUN — shell blocked)
- Tool versions: UNKNOWN — shell blocked (`permission.rejected` on every shell call for controller and all subagents; python3/node/npm/git/jq/rg/rig/pi/docker versions not runnable)
- Dirty files: UNKNOWN (`git status --porcelain` not runnable); no worktree copy made (worktree creation needs shell)
- Scratch space: NOT CREATED (`mktemp`/worktree blocked); subagent raw notes are in-session only (no `$AUDIT_TMP/{alpha,beta,gamma}.md` files)
- Host capabilities: file-content (read-only) audit only via Read/Glob/Grep + 3 subagents (Alpha/Beta/Gamma) + 3 cross-examiners; every live check (`rig spec validate` / `bundle check` / `agent validate` / `preflight` / `expand` / `add` / daemon up-down, `pi` seat render, `find -type l`, `jsonschema` validation, JCS/`configurationId`/`packageDigest` recompute, `render-seat.py` refusal matrix, `seed-rig.py` / `bootstrap-pi-seats.sh` in isolated `OPENRIG_HOME`, `make guard-profiles` matrix, `docker compose config`, all 12 sabotage runs, `generate-rigs.py --check-idempotent`, `verify-rigs.sh --check-only`, `audit_loop.py --self-test`, network/registry probes) NOT RUN
- Per section 0.5 + Cardinal Rule: no claim is VERIFIED without execution (ceiling is PARTIAL for static-consistent)
- Formation executed: Alpha (claims [A]) + Beta (claims [B]) + Gamma (claims [G]) ran concurrently with no cross-reading; cross-examination (Alpha's→Beta-challenger, Beta's→Gamma-challenger, Gamma's→Alpha-challenger) completed; synthesis by controller with on-disk re-reads of `schemas/rigspec-keys.pinned.json:12`, `scripts/render-seat.py:398-419`, `specs/agents/languages/go-backend-eng/runtime/policy-enforcement.json:60-63`, `specs/agents/_shared/skills/executing-plans/SKILL.md:50`, `fleet/fleet.yaml:3361-3367`

## Verdict
heretek-rigs at HEAD `99b4420` remains the 51-role / 8-rig OpenRig monorepo described in the prompt, and its static shapes (fleet partition 6+11+4+6+11+6+7, schema keys/versions, permission first/last bounds, sidecar pins, exact-set networks, model/runtime pins) are internally consistent on disk. The two prior-report P3 residuals are STILL OPEN on static re-verification and cross-examination could not overturn them: the `../using-superpowers/references/` prose pointer still dangles with a staged-but-unregenerated fleet binding (HR-6.1), and the `"*\t-p*"` tab deny lives in the renderer + verifier but in zero of the checked-in permission artifacts, so the tree is stale relative to its own fail-closed gate (HR-5.5). No new P0/P1/P2 was proven; a proposed new P1 for each leg was refuted/downgraded by challengers to the same two P3s (duplicate + fail-closed-gate-already-red reasoning). No live proof was possible (rig/pi/docker/python/network all blocked). The single most important fix is to run `python3 scripts/generate-rigs.py` on a networked shell host (materializing both the tab deny and the using-superpowers sibling), then re-run the section-4 live recipes plus the 12 sabotage targets with upstream attestation (tarball bytes, skill tree hashes, matcher semantics), which is the only path to `STATUS: NO_FINDINGS`.

## Prioritized Defect Matrix
| ID | Priority | Claim | Location | Summary |
|----|----------|-------|----------|---------|
| HR-6.1-using-superpowers-prose-ref | P3 | 6.1 | `specs/agents/_shared/skills/executing-plans/SKILL.md:50` + `fleet/fleet.yaml:3366-3367` | dangling `../using-superpowers/references/` prose ref; staged fleet binding without lock/disk/regen; doc-dangles while fail-closed gate now red |
| HR-5.5-tab-p-suffix-gap | P3 | 5.5 / 5.3 | `specs/agents/languages/go-backend-eng/runtime/policy-enforcement.json:60-63` + `scripts/render-seat.py:402-419` + `scripts/verify-rigs.sh:587-603` + `scripts/gate-role.sh:69-76` | `"*\t-p*"` in renderer+verifier but 0/102 artifacts carry it (14 vs 15 denies); tab-separated `-p` un-denied on disk; stale tree fails own gate |

## Findings
### HR-6.1-using-superpowers-prose-ref: dangling using-superpowers prose reference + staged-but-unregenerated binding
- **Priority:** P3
- **Claim:** 6.1 (63/64 vendored skills full-fidelity; every skill ref resolves)
- **Location:** `specs/agents/_shared/skills/executing-plans/SKILL.md:50`; `fleet/fleet.yaml:3366-3367`
- **Proof:** read-only (shell blocked). `grep using-superpowers specs/agents/_shared/skills/executing-plans/SKILL.md` → line 50 `` `../using-superpowers/references/`). Never fabricate a dispatch; run ``; `glob specs/agents/_shared/skills/using-superpowers*` → No files found; `grep using-superpowers fleet/skills-lock.json` → zero hits; `grep using-superpowers fleet/fleet.yaml` → lines 3361-3362 (comments) + 3366 (`- id: using-superpowers`, live list content under `system-architect` `skills.shared`); `specs/agents/_shared/agent.yaml` + all `rigs/*/agents/_shared/agent.yaml` → 63 ids each, zero `using-superpowers`; live `verify-rigs.sh --check-only` NOT RUN
- **Raw output:** `` `../using-superpowers/references/`). Never fabricate a dispatch; run `` (line 50, verbatim); `fleet.yaml:3366-3367` verbatim: `        - id: using-superpowers` / `          source: superpowers`; gate `verify-rigs.sh:357-385` is an explicit HR-6.1 fail-closed gate (fence-strip + `../([a-z0-9-]+)/` match, `fail()` at :385) citing exactly this case
- **Why it matters:** a reader/seat following the executing-plans doc hits a nonexistent sibling path; fleet (declared source of truth) now promises 64 shared ids while lock/disk/generated bindings deliver 63, so source and tree disagree until regen.
- **Remediation:** on a networked shell host vendor `obra/superpowers@bb92a77:skills/using-superpowers/` (+ lock entry; `_shared/agent.yaml` binding follows from `generate-rigs.py:552-605` union), then `python3 scripts/generate-rigs.py` (expect `system-architect/agent.yaml` `uses.skills` + lock + disk to gain the 64th entry); do not hand-edit generated leaves
- **Verify the fix:** `grep -rn "using-superpowers" specs/agents/_shared/skills/ fleet/` resolves to existing dirs/lock entries; `./scripts/verify-rigs.sh --check-only` → 0
- **Cross-examination:** Gamma-challenger (vs Beta) CONFIRMED the dangle (prose not fenced: fences are the ```dot graph :68-106 and example :325-373; :50 survives `re.sub` fence-strip) and disk/lock absence, but corrected the narrative: the sibling gate is now fail-closed (suite red by inspection, not silent green) and the fleet binding is live YAML not comment-only; Beta's proposed separate P1 `HR-6.1-using-superpowers-dangling-binding` DOWNGRADED to this same P3 regen-lag (fleet 64 vs disk 63 is arithmetically real but already caught by `uses.skills` exact-equality gate :444-455 + doc-ref gate :371-385; upstream `using-superpowers` exists in `obra/superpowers@bb92a77`, so remediation is actionable) — folded here, no new ID.

### HR-5.5-tab-p-suffix-gap: tab-separated -p deny in renderer+verifier but absent from all checked-in artifacts (stale generated tree)
- **Priority:** P3
- **Claim:** 5.5 (bash terminal denies fail-closed) / 5.3 (read-deny layer)
- **Location:** `specs/agents/languages/go-backend-eng/runtime/policy-enforcement.json:60-63` (representative of all 102 files); `scripts/render-seat.py:402-419`; `scripts/verify-rigs.sh:587-603`; `scripts/gate-role.sh:69-76`
- **Proof:** read-only. Sampled bash maps show 14 denies (`"* -p*": "deny",` immediately followed by `"*--patch*": "deny",`); `grep -rn $'\t' specs/agents --include='*.json'` pattern → zero TAB denies (controller + Gamma re-read; `grep t-p` hits only `asset-pipeline` strings); `render-seat.py:413-414` verbatim `"* -p*",` / `"*\t-p*",` (15-tuple :402-418); `verify-rigs.sh:587-590` requires all 15 incl `"*\t-p*"` with terminality check :597-603; `generate-rigs.py:629-644` calls `build_seat_files` + order-preserving `write_json` (:195-197, no `sort_keys`), so regen would emit it; live matcher probes + `verify-rigs.sh --check-only` NOT RUN
- **Raw output:** `"* -p*": "deny",` then `"*--patch*": "deny",` (no `"*\t-p*"` line between; `go-backend-eng` :60-61 verbatim) vs renderer `scripts/render-seat.py:414` ` "*\t-p*",` and verifier `scripts/verify-rigs.sh:587` `_TERMINAL_BASH_DENIES = (..., "* -p*", "*\t-p*", "*--patch*", ...)`
- **Why it matters:** under the repo's own last-match-wins substring-glob model, `git log --oneline<TAB>-p -- fleet/fleet.yaml` matches the `git log --oneline*` allow but no deny (tab ≠ space), leaking tracked-content diffs past the `fleet/*` read-deny; secrets live untracked (`$HERETEK_SECRETS`, `*.env`/`*id_rsa*` direct-read denies hold), so blast radius is tracked content only, hence P3.
- **Remediation:** on a networked shell host: `python3 scripts/generate-rigs.py` (emits the TAB deny into all 102 permission files via the already-fixed renderer; expect only those files changed) then `./scripts/verify-rigs.sh --check-only` → 0 and `bash scripts/gate-role.sh threat-modeler` → tab/`-p`/`--patch`/`--full-diff`/`--textconv` all deny with path-scoped allows still allow; optionally tighten gate to assert no allow follows the terminal block (already present :597-603) and keep TAB probe :74
- **Verify the fix:** repo-wide TAB-deny present in all 102 files; `./scripts/verify-rigs.sh --check-only` exits 0
- **Cross-examination:** Alpha-challenger (vs Gamma) CONFIRMED all three legs (renderer emits TAB :413-414 with correct `json.dumps` `\t`→TAB chain; verifier requires it under `<<'PY'` heredoc; 14-vs-15 on disk; no covering TAB deny; `generate-rigs.py` regen would fix; prior legs 2/4-probe and sortedness-vs-terminality already fixed in script :69-76/:597-603) but REFUTED P1: duplicate of this same P3 ID (not a new finding), no execution per Cardinal Rule (matcher whitespace normalization untested; `verify-rigs.sh` red-run and hostile corpus NOT RUN), impact capped at tracked content — folded here as stale-regen fact, no new P1 (`HR-5.5-tab-deny-not-materialized` rejected as duplicate).

## Claim Ledger
| Claim | Status | Evidence (command or finding ID) |
|-------|--------|----------------------------------|
| 1.1 | PARTIAL | static: 51 role keys + 51 `specs/agents/*/*/agent.yaml` (incl 37/51); Heretek-Crew diff NOT RUN |
| 1.2 | PARTIAL | static: 6+11+4+6+11+6+7=51 member-ID counts, spot exclusivity; full uniqueness matrix NOT RUN |
| 1.3 | PARTIAL | static: 3-seat command pod + 15 pods + 51 members + rig.all-51.yaml + roster; `rig expand` NOT RUN |
| 1.4 | PARTIAL | static: 7-file shape sampled, zero stubs in sampled dirs, `local:../../_shared`→`local:../_shared` sole delta in sampled pair; full byte-drift diff NOT RUN |
| 2.1 | PARTIAL | static keys/version + 64-hex attestation shape FIXED; live `rig spec validate` + tarball-byte attestation NOT RUN |
| 2.2 | PARTIAL | static edge kinds/qualification sampled, DFS gate present; programmatic full-DAG NOT RUN |
| 2.3 | PARTIAL | static: 51x `send_text`, zero `guidance_merge`/`hooks:` in agent.yaml; `rig agent validate` NOT RUN |
| 2.4 | PARTIAL | static zero `guidance_merge` in specs+rigs agent.yaml; live preflight/bundle NOT RUN |
| 2.5 | PARTIAL | static `copytree symlinks=False` + `is_symlink` sweep + `..`/absolute gates; `find -type l` + `rig bundle check` NOT RUN |
| 3.1 | UNVERIFIABLE | presence/shape static only; Draft202012Validator NOT RUN (shell blocked) |
| 3.2 | UNVERIFIABLE | 64-hex shape only; JCS recompute NOT RUN |
| 3.3 | UNVERIFIABLE | joined-string/digest shapes + identity-vectors constants static; disk recompute + replay NOT RUN |
| 4.1 | PARTIAL | static model/runtime pins sampled + all-omp presets; seat census + preflight NOT RUN |
| 4.2 | PARTIAL | static renderer logic (0600, `!cat`, O_NOFOLLOW, uid pin, strict default); live render/bootstrap NOT RUN |
| 4.3 | PARTIAL | static `!cat`/echo-Bearer shapes in key/env/headers only, refusal logic present; live refusal matrix NOT RUN |
| 4.4 | PARTIAL | static: zero `env:` in rigs rig.yaml, only prose/placeholder secret-name hits; full literal scan NOT RUN |
| 5.1 | PARTIAL | static: 16x readonly_charter + sampled `builtin:locked`, zero yolo/open in shipped surface; full 18-seat census + live NOT RUN |
| 5.2 | PARTIAL | static: `*` first / `*..*` last in both maps on samples; hostile corpus NOT RUN |
| 5.3 | PARTIAL | static: secret-denies + deny/timeout present, zero `ask`; live probes NOT RUN; tab residual → HR-5.5-tab-p-suffix-gap (P3) |
| 5.4 | PARTIAL | static: 102/102 mut-denies, read-only AST/LSP allows, no pi-lsp@0.1.7 in shipped surface; live bypass probe NOT RUN |
| 5.5 | PARTIAL | static: bash/mcp bounds present but 14/15 terminal denies on disk (stale regen); escape corpus NOT RUN; → HR-5.5-tab-p-suffix-gap (P3) |
| 6.1 | PARTIAL | static: 63 lock entries + 63 skills + multi-file SDD + 6 SOP skills; upstream fidelity UNVERIFIABLE; → HR-6.1-using-superpowers-prose-ref (P3) |
| 6.2 | PARTIAL | static pins exact, zero r2mcp/aws-mcp/:latest in catalog, read-only flags, liveness labels; registry existence NOT RUN |
| 7.1 | PARTIAL | static 8x 127.0.0.1 + 9 pinned images, zero 0.0.0.0/bare; compose/bind check NOT RUN |
| 7.2 | PARTIAL | static 20-toggle exact set `"0"` + 0.5.0 + :ro; proxy probe NOT RUN |
| 7.3 | PARTIAL | static exact-set networks + ro mounts + guard logic; live matrix NOT RUN |
| 8.1 | UNVERIFIABLE | idempotence NOT RUN (shell blocked); static `--check-idempotent` + sorted()/hash features noted |
| 8.2 | UNVERIFIABLE | live exit NOT RUN; clean-tree currently red by inspection (tab-deny + using-superpowers gates); gate-shape passes statically otherwise |
| 8.3 | UNVERIFIABLE | self-test NOT RUN; static evaluator reads fail-closed (7 vectors) |
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
| HR-6.1-using-superpowers-prose-ref | P3 | STILL OPEN (evolved: fleet binding staged, regen pending; fail-closed gate now present) | `executing-plans/SKILL.md:50` verbatim retained; zero `using-superpowers*` dirs; zero lock hits; `fleet.yaml:3366` live binding without regen; Beta + Gamma-challenger CONFIRMED |
| HR-5.5-tab-p-suffix-gap | P3 | STILL OPEN (morphed to stale-regen; scripts fully remediated, artifacts stale) | on-disk 14/102 denies vs renderer+verifier 15 (`render-seat.py:414`, `verify-rigs.sh:587`); `go-backend-eng:60-61` verbatim; Gamma + Alpha-challenger CONFIRMED fact, P1 duplicate REFUTED |
| HR-2.1-pinned-still-local | P1 | FIXED (shape; hash-byte truth UNVERIFIABLE) | `pinned.json:12` 64-hex `289dc007…267f6` + `refreshed_at`; Alpha + Beta + challengers CONFIRMED shape; byte-truth needs `npm pack && sha256sum` on shell host |
| HR-6.1-missing-subagent-sibling | P2 | FIXED retained (counts/bindings/scripts; upstream fidelity UNVERIFIABLE) | `subagent-driven-development/` multi-file + lock + fleet bindings; challengers CONFIRMED |
| HR-7.3-network-exclusivity-gap | P2 (fixed prior) | FIXED retained | static exact-set networks + ro mounts + guard retained; live matrix NOT RUN |
| HR-5.5-rendered-allow-superset-gap | P2 (fixed prior) | FIXED retained | subset gates present; live injection UNVERIFIABLE |
| HR-5.5-git-patch-read-bypass | P3 | FIXED (artifacts materialized as 14 denies; residual split to HR-5.5-tab-p-suffix-gap) | 14 patch/terminal denies on disk; 3 challengers CONFIRMED on-disk fix; tab residual → HR-5.5-tab-p-suffix-gap |

## Not Audited / Unverifiable
- All live checks NOT RUN (shell `permission.rejected` on controller + all subagents): `rig spec validate` / `bundle check` / `agent validate` / `preflight` / `expand` / `add` / daemon up-down; `pi` seat render; `find -type l`; `jsonschema` validation; JCS/`configurationId`/`packageDigest` recomputes; `render-seat.py` refusal matrix; `seed-rig.py` / `bootstrap-pi-seats.sh` in isolated `OPENRIG_HOME`; `make guard-profiles` matrix; `docker compose config`; all 12 sabotage runs; `generate-rigs.py --check-idempotent`; `verify-rigs.sh --check-only`; `audit_loop.py --self-test`.
- No `$AUDIT_TMP` scratch/worktree created or cleaned (blocked); real-checkout dirtiness unverified via shell — human must confirm `git status --porcelain` shows only this report (+ prompt file if untracked). Commit read from `.git/refs/heads/main` (`99b4420`); commit message/date not re-read (no shell).
- Coverage: all 30 claim IDs have a ledger status (Alpha 10 + Beta 10 + Gamma 10; ceiling PARTIAL without execution). Finding IDs stable (`HR-<claim-id>-<slug>`) for next-run matching.
- Human must provide: networked shell host with `@openrig/cli@0.6.11`, pi 1.3.0, loopback daemon, then run section-4 recipes, the 12 sabotage targets, `python3 scripts/generate-rigs.py` regen (tab deny + using-superpowers), the tab-suffix + `--full-diff`/`--textconv` probes, the upstream `using-superpowers` check, and the `npm pack @openrig/cli@0.6.11` + `obra/superpowers@bb92a77` tree-hash attestations.

## Final Loop Sentinel
STATUS: FINDINGS_DETECTED
