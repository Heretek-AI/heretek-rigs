# 107-identity M0–M3 Independent Drift-Guard Verification

Stage: 107-identity M0–M3. Worktree: `.lane/trees/107-identity` (branch `feat/107-identity`).
Commits audited: `1c5ac57` spec+M0, `47e71aa` feat, `22f2946` chore regen, `3d1edb1` test evidence. Tree status at audit: clean (`git status --short` empty).
Auditor method: read every listed file from disk; diffed `51d7df1..HEAD`; re-ran all three gates live. No code fixed, nothing committed.

## 1. Spec & architecture audit (source of truth)

Read from disk:
- `openspec/changes/107-identity/proposal.md` — scope: M0 spike first, M1 MCP-bearer via seed `!cat`, M2 revoke+re-add, M3 queue disposition, no upstream filing without principal.
- `openspec/changes/107-identity/specs/identity/spec.md` — REQ-I0/I1/I2/I3/G1 (35 lines, quoted in findings below).
- `openspec/changes/107-identity/design.md` — M0-gates-M1 order, verified upstream facts for `rig` 0.7.2 (`8b180689`), fail-closed modes (never touch real `$OPENRIG_HOME`).
- `openspec/changes/107-identity/tasks.md` — T0/M0/M1/M2/M3/T2/T3 with acceptance commands.
- `docs/reports/107-identity-implementation.md`, `docs/evidence/107-identity-m0.md` (419 lines), `docs/evidence/107-identity-rotation.md` (214 lines), `docs/evidence/107-identity-queue.md` (85 lines), `docs/evidence/107-identity/red-proofs.log` (S1–S8), `docs/evidence/107-identity/qa-run.log`.

`git diff --name-only 51d7df1..HEAD` (31 files): 6 openspec files, 3 M0/M2/M3 evidence files, 2 T2 evidence files, 1 implementation report, `fleet/mcp-servers.yaml`, `scripts/render-seat.py`, `scripts/seed-rig.py`, `scripts/verify-rigs.sh`, `tests/test_identity_m1.py`, 16 registry files (provenance-stamp-only `resolvedCommit` lines). `git diff 51d7df1..HEAD -- specs/ rigs/ rosters/` is EMPTY — no hand-edits to generated leaves (REQ-G1 generator rule holds; registry delta is `resolvedCommit` re-stamp from the chore regen, zero `DIRTY-` stamps: `grep -c DIRTY` over the registry diff = 0).

### REQ-I0 — M0 spike gates M1, no queue code
PASS. `docs/evidence/107-identity-m0.md` §1–§7 records verbatim: `token add` hash-only/600 (§1), scratch daemon+serve (§2), valid-Bearer 200 (§3), bad-token 401 + no-token 401 with distinct messages (§4), revoke → re-present 401 (§5), `rig_whoami` grant-seat vs declared-seat + client-spoof ignored (§6, probes 4b/4c/4d), queue-half bare-leading and `env`-prefixed both `rc=0` served with zero challenge (§7, probes 5b/5c). §9 WINNER explicitly follows the MCP-bearer path and forbids repo-side queue grants; M1/M2/M3 evidence all cite it. `design.md` needed no fix. No queue-identity code exists (see REQ-I3).

### REQ-I1 — per-seat grants, `!cat` reuse, no third substitution form, scope
PASS.
- Catalog (`fleet/mcp-servers.yaml` +9): `rig-mcp-http`, `transport: http`, `url_template: http://127.0.0.1:7437/mcp`, `seat_grant: true`, no static `env`/`headers`, `exposure: deferred`. Zero fleet roles bind it (opt-in; `test_grant_server_catalog_shape_and_opt_in_default` asserts `bound == []`; stdio unchanged).
- Render (`scripts/render-seat.py` +33/-1): `SEAT_GRANT_FLAG`, `seat_grant_token_filename(session)` → `mcp-http-<session>.key` (`.key` suffix reuses frozen `*.key` deny); dynamic file joins existing required/missing/degraded machinery; when present wires exactly `{"Authorization": "!echo Bearer $(cat <secrets>/<file>)"}` — the existing header form, never a third substitution form (only `subst()` + this one header injection in the file).
- Seed (`scripts/seed-rig.py` +189): `parse_issued_token` (exact `Token for <name>,` + token-shaped line else None), `_list_grant_names`, `_revoke_grant`, `issue_seat_grant` (fresh add → 0600 store; reuse when grant+file agree; revoke+re-add heal when file missing/symlinked; add-parse/write failure revokes minted grant and dies with rc=2 — never a dead grant; `--allow-missing-secrets` degrades loudly), wired into `main()` before each seat's render, skipped for `--dry-run` / `--refresh-policy-only`. Token-add call is seat-only: `token add <session> --seat <session>` — no `--rig/--root/--workspace/--owner` flags (M0-proven scope; only other `--rig` mentions are pre-existing fragment-arg plumbing).
- Deny matrix: M0 §4/§5 (bad/revoked 401) + M2 §2 step E (new 200 / old 401 / none 401) + T2 S6 live scratch matrix (valid 200; tampered/unknown-foreign/missing 401 with exact `{"error":"unauthenticated",...}` body for the cross-home case) + 15 corpus tests. Spec scenario text says `out_of_scope`; the 0.7.2 adapter's actual refusal is `401 unauthenticated` — the evidence records the real wire behavior verbatim rather than inventing an `out_of_scope` string, which is the honest mapping (cross-seat/foreign grant denied all the same).

### REQ-I2 — rotation live evidence
PASS. `docs/evidence/107-identity-rotation.md` §1 runbook + §2 executed-live scratch proof (`OPENRIG_HOME=/tmp/107-rotate-...`, daemon `:18433`, serve `:18437`): add rc=0 → pre-rotation 200 → revoke rc=0 → same-token 401 (verbatim body with `WWW-Authenticate: Bearer realm="openrig"`, `curl rc=0` so the 401 is a green transport) → re-add rc=0 (new 47-char bearer `DIFFERENT`) → new 200 / old 401 / none 401; `token list --json` confirms single grant; §3 cleanup (listeners gone, `~/.openrig/daemon.json` byte-identical). No expiry flags involved (0.7.2 offers none — matches design).

### REQ-I3 — queue note only, no upstream filing
PASS. `docs/evidence/107-identity-queue.md` is NOTE ONLY citing M0 §7 exact outputs; `git diff 51d7df1..HEAD --name-only | grep -i queue` → ONLY that note; `grep -rn "token add|token revoke|seat_grant" scripts/seed-rig.py scripts/render-seat.py | grep -i queue` → EMPTY (rc=1); render-seat queue mentions are pre-existing frozen terminal bash denies (V22) and `rig queue --note/--body-file` argv descriptors, unchanged. No upstream issue/PR filed (all three docs state filing needs principal authorization, not granted; no filing reference appears anywhere).

### REQ-G1 — append-only, generator rule, safe_load, specs untouched
PASS. V23 block is appended alongside (+50 lines, FAIL-ONLY, no `ok()`); V1–V22 headers all present unrenamed (`== V1,V2,V4,V6–V23` plus combined `V2&V3`,`V4&V5` baselines); SUMMARY frozen at 35 (live run: `SUMMARY: 35 checks passed, 0 failed`); `specs/ rigs/ rosters/` diff empty; registry diff is provenance-stamp-only; all YAML parsing in touched code paths uses `yaml.safe_load` (zero `yaml.load`/`safe_dump` in `seed-rig.py`/`render-seat.py`/V23 block).

## 2. Stub hunt (changed scripts/tests)
- `TODO/FIXME/STUB/XXX`: zero hits in `scripts/seed-rig.py`, `scripts/render-seat.py`, `tests/test_identity_m1.py`, `fleet/mcp-servers.yaml` (`grep` rc=1). The only `TODO|FIXME` hits in `verify-rigs.sh` are its own pre-existing placeholder-detector regexes + comments, not new code.
- Swallowed errors / vacuous passes: none. `|| true` zero hits (rc=1); `except.*pass / except:$ / skipTest / @unittest.skip` zero hits (rc=1); every `except (OSError, ...)` returns `None`/`False`/loud `_fail`; corpus has 15 real assertions, no skips.
- `semgrep_scan`/full `anti-stub-scanner` tool not installed in this seat; manual grep + V23 non-vacuous floor (`Ran >= 15`) + T2 S1–S5 sabotage trips substitute (all RED on sabotage, GREEN on restore — see §4).
- No unreferenced modules: `seat_grant_token_filename` consumed by `seed-rig.py` + V23 gate + corpus; `issue_seat_grant` wired into `main()`; `SEAT_GRANT_FLAG` consumed at render; `rig-mcp-http` consumed by V23 + corpus + render path.
- `.meta`/GUID: N/A (non-Unity repo). `.scratch/vendor` symlink → `/home/john/.../.scratch/vendor`, gitignored via `.gitignore:1:.scratch/` — correctly uncommitted/ignored.

## 3. Secrets
PASS. Evidence logs redact live bearers to first/last-2 (`or...Gc`, `or...Tk`, `or...VE`) + `len=47` + `tokenSha256`; the only 40+-char strings in evidence are two 64-hex `tokenSha256` hashes (hash-only storage proofs, not credentials) and long test-method names. Corpus fake tokens (`fakegrantsessiontoken%06d`) are dummy, in `/tmp` 0700 scratch with 0600 files. Real tokens lived only in `/tmp` scratch + tool output per reports. No secret-shaped material committed.

## 4. Red-proof audit (`docs/evidence/107-identity/red-proofs.log`, `qa-run.log`)
PASS — 8 sabotages, every one non-vacuous with exact RED signatures and clean restores:
- S1 transport→stdio: `--check-only` exit 1, `[FAIL] V23 ... must use transport http` + cascading corpus failure → restore → exit 0.
- S2 `.key`→`.tok`: corpus exit 1 (`2 failed, 13 passed`, both filename/strict tests) → restore → 15 passed.
- S3 header→`X-Bogus-Auth`: corpus `1 failed, 14 passed` + gate `SUMMARY: 35 passed, 1 failed` → restore → green.
- S4 parser→`return None`: corpus `4 failed, 11 passed` (fresh/heal/idempotence unparseable-path) → restore → green.
- S5 generated-leaf hand-edit probe: gate `SUMMARY: 35 passed, 2 failed` with V21 drift lines → restore; positive controls: `git diff 51d7df1..HEAD --name-only -- specs/ rigs/ rosters/` EMPTY, V-headers unrenamed, SUMMARY 35.
- S6 live deny matrix (scratch `OPENRIG_HOME`, daemon `:19433`): valid 200 vs tampered/missing/unknown/foreign-home 401s on the same server; real `daemon.json` sha256 identical before/after.
- S7 live revoke→401 + rotation matrix: same-token 200→401 flip on next request, re-add `DIFFERENT`, new 200 / old 401.
- S8 queue detector: positive control (only queue.md note; no queue token logic) + injected `_QUEUE_GRANT_SENTINEL` trips the grep detector → restore.
`git status --short` at audit is clean (evidence files committed in `3d1edb1`; no sabotage residue). `qa-run.log` baseline + final both green (15 passed, `SELF-TEST PASSED`, `SUMMARY: 35 checks passed, 0 failed`, `QA verdict: PASS`).

## 5. Re-run (this audit, real output)
- `bash scripts/verify-rigs.sh --check-only` → exit 0, `V23/107-identity M1 green: seat-grant catalog shape + filename helper + 15 corpus tests pass (FAIL-ONLY, SUMMARY frozen)`, `SUMMARY: 35 checks passed, 0 failed.` (Note: must run under `bash`; `python3 scripts/verify-rigs.sh` fails with `SyntaxError` — expected, it is a bash/python polyglot.)
- `python3 -m pytest tests/test_identity_m1.py -q` → exit 0, `15 passed in 1.25s`.
- `python3 scripts/audit_loop.py --self-test` → exit 0, `SELF-TEST PASSED: audit_loop.py is ready for autonomous OpenCode execution.`
- `make verify` → exit 0: same 35/0 SUMMARY plus `LIVE-HEALTH SKIP` (6 `[SKIP] ... Daemon not running` — the normal no-daemon data-source skips, also recorded in `qa-run.log`).
- Failed/skipped commands: none failed; live-health `[SKIP]×6` are by-design without a daemon (not failures).

## Findings
None. All deliverables present, all gates green, no stubs, no secrets, provenance clean, red-proofs non-vacuous.

VERDICT: PASS
