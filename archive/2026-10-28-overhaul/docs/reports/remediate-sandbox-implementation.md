# remediate-sandbox implementation report (Wave 2, audit #66 M4–M5)

- Stage id: remediate-sandbox (Wave 2 of audit #66 remediation)
- Branch: remediate/audit-66-p0-p1-sandbox
- Worktree: /home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/remediate-sandbox
- Spec: docs/REMEDIATION_IMPLEMENTATION_PROMPT.md (M4, M5 + Verified facts F1, F2, F3, F7, F8, F9, Target layout, Gotchas 1–5, 8)
- Prior state (Wave 1): 28 checks, 10 suites, bwrap 0.13.1 (docs/NOTES.md #66 M0–M3)

## Deliverables

- M4: scripts/seat-sandbox.sh (new, +x); settings.json shellPath + per-seat sandbox.env (render-seat.py); runner-verb strips on 4 locked seats + dependency-patcher commit strip (fleet.yaml) + top-level `sandbox:` write-roots schema; V12 extended (shellPath/sandbox.env/bwrap/per-seat shellPath); +2 renderer unit tests; canary-scope test adaptation (own commit).
- M5: 16 new terminal bash denies (renderer + verify mirror + renderer asserts + unit tuple); send-authenticated.sh fail-closed (env refusal, receipt state/persisted/createWarning, fleet member-id source rejection); gate-role.sh +3 deny probes.

## Files changed

| File | Change |
|---|---|
| scripts/seat-sandbox.sh (new) | F2-verified bwrap core + PI_CODING_AGENT_DIR sandbox.env bootstrap (M4 deviation, evidence in NOTES) |
| scripts/render-seat.py | M4 shellPath + sandbox.env + _sandbox_bind_roots; M5 16 terminal denies |
| fleet/fleet.yaml | M4 verb strips + sandbox schema block |
| scripts/verify-rigs.sh | V12a2 sandbox asserts + per-seat shellPath; :588 mirror + :1153-1160 asserts (M5) |
| scripts/send-authenticated.sh | M5 env refusal + receipt fail-closed + fleet source rejection |
| scripts/gate-role.sh | M5 -u/--cc/env-probes |
| tests/test_render_seat.py | M4 +2 tests; M5 deny tuple extended (11 tests total) |
| tests/test_build_canary.py | canary scope bound adapted to M4 roles (own commit) |
| docs/NOTES.md | M4 + M5 sections appended |
| rigs/ specs/ registry/ rosters/ | regenerated leaves (shellPath, verb strips, new denies) |

Commits (explicit git add, attribution trailers present):
- 2cad3c2 remediate(#66): M4 sandbox every execution-capable seat (226 files)
- 04b1399 remediate(#66): adapt canary scope bound to M4 remediation roles (1 file)
- 4eb9c67 remediate(#66): M5 git-diff bypass and identity forgery hardening (337 files)

## Acceptance outputs (all run 2026-10-24 in-worktree)

1. `bash scripts/gate-role.sh sabotage-qa-tester` → exit 0; rendered bash allows 11, zero runner-ish (`test|stryker|mutant|mutmut|pytest|cargo|garak|pyrit|promptfoo|npx|clippy`).
2. F2 corpus (bwrap 0.13.1, HERETEK_* unset, PI_CODING_AGENT_DIR=<rendered seat>): `tests/chaos/t.txt` rc=0; `root.txt` rc=1 Read-only; secret-store key `No such file` rc=1; curl rc=7 blocked; git works rc=0; bad usage rc=126.
3. `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py` twice → byte-identical diff (cmp clean), exit 0 both.
4. `bash scripts/gate-role.sh go-backend-eng` → exit 0, 43 ok / 0 FAIL (M5 probes included).
5. `OPENRIG_SESSION_NAME=... bash scripts/send-authenticated.sh ...` → `error: refusing ...`, rc=2.
6. Stub-rig receipt matrix: `{"state":"failed","persisted":false}` → rc=4; +qitemId → rc=5; createWarning → rc=7; persisted false → rc=6; pending/in-progress true → rc=0 `created ...`.
7. `--source exec-director` → rc=2; `--source blue-appsec@rig` → rc=2; `--source operator --dry-run` → rc=0.
8. `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 28 checks passed, 0 failed.` (exit 0).
9. `make test` → `Ran 210 tests ... OK` (exit 0).

F9 residual (evidence, not a failure): bare leading `OPENRIG_SESSION_NAME=x rig whoami` EXECUTES (rc=0) — pps strips the assignment before matching, so no policy deny can catch it. `env OPENRIG_SESSION_NAME=x rig whoami` DENIES. Committed probe uses the env form; leading form closed at script layer.

## Env-mechanism decision (M4)

render-seat.py writes `sandbox.env` into the seat agent dir; seat-sandbox.sh loads it via `$PI_CODING_AGENT_DIR/sandbox.env`. Rejected: daemon env and rig `env:` — both die at the deny-by-default pi-runner child env (`buildPiChildEnv` allowlist; rig-spec "Where the declared names reach, by runtime"). Evidence + deviation note in docs/NOTES.md.

## Rollout split

- NOT no-bounce (needs per-seat relaunch or RPC reload): settings.json `shellPath` (F1 — pi reads settings at startup only). The sandbox itself.
- Canary-then-fleet WITHOUT bounce (permission config.json hot-reloads on mtime): M5 git-diff terminal denies, M4 locked-seat verb removal, dependency-patcher commit strip, MCP flags.

## Draft PR text

```
## Remediation: audit #66 sandbox wave (M4–M5)

Fixes: #68 #69 #72 #73 #93 (partial: #72 policy layer per F9)

| Issue | Fix | Verify command | Result |
|---|---|---|---|
| #68 | strip runner verbs from 4 locked seats; seat-sandbox.sh jail + shellPath + sandbox.env | `bash scripts/gate-role.sh sabotage-qa-tester`; F2 corpus under `scripts/seat-sandbox.sh` | PASS (exit 0, zero runner verbs; in-scope rc=0, root.txt ro rc=1, store masked, curl blocked) |
| #69 | 14 git-diff read denies (-u/-U/--unified/--cc/-c/-m/-W/--function-context/--word-diff/--color-words/--binary/--raw) | `bash scripts/gate-role.sh go-backend-eng` | PASS (43/0, exit 0) |
| #72/#93 | send-authenticated.sh env refusal + receipt fail-closed + fleet source rejection; policy-layer `*OPENRIG_SESSION_NAME=*` deny (env form only, F9) | env-set run (rc=2); stub-rig fake matrix (rc=4/5/6/7); fleet-id sources (rc=2) | PASS |
| #73 | strip dependency-patcher git checkout/commit | fleet grep (0 hits); regen + verify | PASS |

Gates: verify-rigs 28/0, make test OK (210 tests, 10 suites), generate-rigs clean ×2 (idempotent cmp).
Rollout: sandbox (shellPath) needs relaunch/RPC reload — NOT no-bounce. Permission config.json changes (git-diff denies, locked-seat verb removal) can go canary-then-fleet without bounce.

Not done / follow-up: #72 leading-`VAR=x` form remains policy-allowed per F9 (upstream per-seat identity tokens); generate-rigs.py:493 charter denial text predates M5 denies (M10); bwrap required on every host (V12 hard-fails otherwise).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014wevSWHET5eqHNVNTYZnx9
```

## Self-audit notes (unfinished / stated plainly)

- M4 is complete; the canary test adaptation was split into its own commit per the stale-test rule (not counted as a 4th milestone).
- `git status` clean except implementation commits; `.scratch/vendor` is an ignored symlink to the main checkout (setup note in NOTES for fresh worktrees).
- HR-4.4 fleet scan tripped twice during M4 (once by design content, once by my own meta-comment) — both reworded, scan green; recorded in NOTES.
- Bash-quoting bug in send-authenticated.sh receipt parser (nested single quotes in `python3 -c '...'`) caught by stub-rig test before commit — fixed, recorded in NOTES.
- generate-rigs.py:493 charter denial-classification prose not updated for M5 denies — deferred to M10/PR, recorded in NOTES.
- No QA dispatch performed; tree holds implementation commits only (report + NOTES, no evidence files).
- Stopping point: M4–M5 complete; M6+ owned by later waves.
