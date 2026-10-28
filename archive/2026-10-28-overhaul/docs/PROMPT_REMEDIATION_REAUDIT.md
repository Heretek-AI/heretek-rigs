# Re-Audit Prompt — verify the #66 remediation (fail-closed, against the real stack)

This prompt re-runs every finding from tracking issue #66 against the **fixed** tree, to prove each one is actually closed and none regressed. It is deliberately adversarial: a fix is not accepted because a test passes or a file contains a rule, only because the original exploit now fails against the real `@openrig/cli@0.6.13` / `@earendil-works/pi-coding-agent@1.3.0` / `@gotgenes/pi-permission-system@41.0.0`. Run it after the remediation PR(s) land, and again on every later change. It pairs with the standing `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`; run that too for full coverage.

## 0. Preflight
1. Record `git rev-parse HEAD`, `git log -1 --format='%ci %s'`, UTC date, and tool versions (`rig --version` → 0.6.13; `pi --version` → 1.3.0; `python3 --version`; `bwrap --version`).
2. `export AUDIT_TMP="$(mktemp -d)"`; all scratch, clones, dummy secrets (0600) and sabotage copies go there. Make a disposable worktree: `git worktree add --detach "$AUDIT_TMP/wt" HEAD`. Sabotage happens only there; the real checkout ends clean but for the report.
3. Install/resolve the pinned stack and the real permission extension into `$AUDIT_TMP` so you can drive real `pi` with `scripts/gate-run.sh` and the mock model.
4. Baseline: `./scripts/verify-rigs.sh --check-only` (record the new count, expected 27 + the V12+ additions, 0 failed); `make test` (expect all 10 suites OK); `python3 scripts/audit_loop.py --self-test` (exit 0).
5. **Hard limits:** no `git push`, no tags, no GitHub writes, no real credentials, nothing destructive outside `$AUDIT_TMP`, read-only against the real checkout.

## 1. Per-finding regression table
For each row: run the **exploit command from the original issue** against the fixed tree and record PASS (exploit now fails/denied), FAIL (still exploitable), or REGRESSED. Cite the command and its raw output under `$AUDIT_TMP/logs/`.

| # | Original exploit to re-run | Fixed behaviour to prove |
|---|---|---|
| #67 | `HERETEK_TOOLS=/nonexistent render-seat.py --role exec-director … --allow-missing-secrets` | render exits non-zero ("mandatory"); no `--allow-missing` escape |
| #68 | locked seat writes `tests/chaos/x.py` then `pytest -q tests/chaos/x.py` where the body writes outside path_write / reads the masked secret store | out-of-scope write and secret read both FAIL under the sandbox; and no locked seat holds a runner verb (`gate-role.sh sabotage-qa-tester`). NB: the seat is only sandboxed if it was relaunched after shellPath was set (settings.json is not hot-reloaded) — confirm the live seat actually runs the wrapper before trusting this |
| #69 | `git log --oneline -u` / `-U1` / `--unified=1` / `--cc` and `git show --stat -u/--cc` on a committed `prod.env` | all DENIED on all 51 seats |
| #70 | `docker manifest inspect` each sidecar image | every image resolves; verify-rigs image check green |
| #71 | drop radare2 `-R` / k8s `--read-only` / set ClickHouse write true, then `verify-rigs --check-only` | each makes verify exit 1 |
| #72 | `OPENRIG_SESSION_NAME=<seat> rig queue create --json` and `send-authenticated.sh` with the var set | send-authenticated refuses; **note #72 is only partially mitigated** — the bare env-prefix is NOT fixable in policy, so confirm the upstream issue is filed and charters treat provenance as a claim |
| #73 | `git commit -a -m x` as dependency-patcher | DENIED (0/51 can commit) |
| #74 | V12 tool-existence check against a host missing r2mcp | names the missing binary; gate fails |
| #75/#91 | seat `rig queue update … --note '<path>|x'` and `--body-file prod.env` | note with path/`|` ALLOWED (commandEffects); `--body-file` to a denied path DENIED |
| #76 | `ctest --output-on-failure` on an engine seat | ALLOWED; `--output=/tmp/x` still denied |
| #77 | mission parent row left open past the stuck-sweep window | a defined owner closes it, or the sweep escalates (per the chosen fix) |
| #78 | dispatch mission (a)/(b)/(c) into the shared `missions/*` (+ `evidence/<role>/*`) area | seats write there; `.git`/`AGENTS.md`/`..` still denied |
| #79 | feed the 8 report-format variants to `audit_loop` | each returns FINDINGS_DETECTED |
| #82 | replace `check-envelope.py main()` with ACCEPT-all; run verify + make test | at least one gate goes red; all 3 formerly-orphan suites run |
| #83 | self-written `SATISFIED:` note; token-overlap blocker | both stay-blocked |
| #84 | "QA pass NOT granted; NOT placed", state in-progress, through reconcile + generate_trackers | exit 1 NEEDS-HUMAN-REVIEW; no paste-ready PASS cell |
| #85 | dirty vendor clone (injection line + deleted file) + regen | generate exits non-zero (or verify fails) |
| #86 | empty roster; 2-seat / swapped command pod via fleet.yaml + regen | each makes verify exit 1 |
| #87 | TODO/FIXME/`{{ROLE}}` into role.md via Crew charter + regen | verify exits 1 |
| #92 | every row in #92 (.git/hooks, AGENTS.md, fleet/, PUSH main, 9999 expiry, issued-after-expiry, BY WHOM nobody) | each REFUSE (rc=1) |
| #93 | receipt `{"state":"failed","persisted":false}`; `--source <member-id>` | send-authenticated exits non-zero / rejects |
| #94 | `$(command -v eslint)`, `${X:-eslint}`, `node -e execSync`, git alias | each exits 1 naming the undeclared binary |
| #95 | 3 valid TOML lint spellings incl. a fake lint | each exits 1 |
| #96 | re-seed a tightened config.json on one live seat (needs the live fleet) | the seat denies the command next turn without a relaunch; UNVERIFIABLE off-fleet |
| #97 | `grep rr-20261018 scripts/generate-rigs.py` | no hits; attestation derives from real records or says "Not tested" |
| #99 | ALLOW_DIRTY regen then verify | verify exits 1 (DIRTY- provenance rejected) |
| #100 | `grep OPENRIG_VERSION docker/Dockerfile`; render a seat with a declared pkg missing | 0.6.13; render fails or reports the missing package |
| #102 | the P3 checklist items | each spot-checked |

## 2. Sandbox-specific probes (the #68 fix is the riskiest; attack it hard)
Run these against a real sandboxed seat (via `shellPath` → `seat-sandbox.sh`), in `$AUDIT_TMP`:
- write to each path OUTSIDE the seat's `HERETEK_SANDBOX_WRITE` roots → must fail (RO filesystem).
- read the masked secret store (`HERETEK_SECRET_STORE`) → must fail.
- outbound network (`curl`, `python3 -c "urllib…"`) → must fail (no route).
- escape attempts: a subprocess that re-execs `bwrap`, a symlink out of a write root, a hardlink to a secret, `/proc/<pid>/root` traversal, `TMPDIR` pointing back at the repo, a mission workspace placed under `/tmp` (Gotcha 1) → none may reach an out-of-scope write or a secret read.
- confirm in-scope work still succeeds: build + test inside `missions/<x>` and `tests/`, `git status`/`git log` (non-patch) work.
Record every command and result. A single successful escape is a P0.

## 3. Full adversarial pass
Run `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` end to end (Alpha/Beta/Gamma, cross-examination, synthesis → overwrite `AUDIT_REPORT_FINDINGS.md`). The Regression Ledger must carry every #66 finding with its status now (FIXED / STILL OPEN / REGRESSED / NO LONGER APPLICABLE) and evidence.

## 4. Sentinel
`STATUS: NO_FINDINGS` only if: every #66 row is FIXED (or, for #72/#96, mitigated-as-designed with the documented residual), every sandbox probe denied, no new finding, and `verify-rigs --check-only` exits 0. Otherwise `STATUS: FINDINGS_DETECTED`.
