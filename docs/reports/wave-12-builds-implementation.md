# Wave-12 builds — implementation report (NOT committed)

- **Stage:** wave-12-builds (issues #12 + #9 + #11, canary scope ONLY)
- **Worktree:** `.lane/trees/wave-12-builds` (branch `feat/12-build-capability`)
- **Binding:** `openspec/changes/issue-12-build-capability/` (proposal/design/
  `specs/build-capability/spec.md` REQ-BC1..BC7 incl. review criteria F6/N1/N2,
  tasks.md) + `docs/reports/spike-12-build-capability.md`.
- **Bounds honored:** catalog grants touch `engine-systems-eng` and NOTHING
  else; no other role's `bash_allow`/`path_write` changed (static pin +
  zero non-date allow churn in baked leaves); no fleet-wide #9/#11 rollout;
  no `Makefile`/`verify-rigs.sh` edits; dummy secrets only (`/tmp`
  scratch); `~/.config/heretek-rigs/secrets` never touched; every re-seed
  used `--allow-missing-secrets` (github.pat absent fleet-wide); no commit,
  no push, no `--force`.
- **Live fleet at wave time:** `heretek-omni-fleet`, 51/51 running, rigId
  `01M5GWFPKVNQEXQVSAGQ2ANJBE`. Canary: `engine-engine-systems-eng@heretek-omni-fleet`.

## 1. Deliverables

| # | Deliverable | Spec anchor |
|---|---|---|
| 1 | 12a canary grant: exact `date +%s` on `engine-systems-eng.bash_allow` (bounded clock read for D4 ELAPSED proof, narrowed from `date +%s*` in rework cycle 1 §8 F3; output-anchored per REQ-BC2; NOT configure/compile/`./build.sh`, so REQ-BC3 holds) | REQ-BC1/BC2/BC3 |
| 2 | `scripts/check-envelope.py` — PRE-AUTH envelope verifier (12b verification path, not a standing grant) | REQ-BC4/BC5 |
| 3 | 12c commit path = envelope-authorized operator COMMIT (REQ-BC6 option a): no standing `git add` grant anywhere, `git-drift-coord` untouched (locked + read-only) | REQ-BC6 |
| 4 | #9/#11 canary validation: full per-node refresh composition executed on the canary only (snapshot → drain check → re-seed → `--plan` → `--stop` launch → confirm → authenticated relay round-trip) | REQ-BC7 |
| 5 | `tests/test_check_envelope.py` (36 tests, N2 binary fail-closed, one per required field) + `tests/test_build_canary.py` (11 tests: catalog pins, canary-scope guard, F6 sabotage-replay mock probes) — ADDED alongside, no baselined gate renumbered or reworded | F6/N1/N2 |

## 2. Files changed

- `fleet/fleet.yaml` — 1 insertion (`      - date +%s` after `clang --version*`
  in `engine-systems-eng.bash_allow`; exact form since rework cycle 1 §8 F3).
  Full diff is that line only.
- `scripts/check-envelope.py` — NEW (executable). Exit 0 `ACCEPT`, 1 `REFUSE
  (<field>)` (operator holds), 2 usage. Validates: envelope id, slice class,
  issued-by, issued-at (`YYYY-MM-DD HH:MMZ`, real calendar date), expiry
  (single-slice XOR explicit UTC deadline; `never`/`open-ended`/`indefinite`
  refused; past deadline refused at `--at`/now; `--consumed` voids
  single-slice; `--revoked` voids all), path scope (≥1 repo-relative entry;
  absolute/`..`/whitespace refused), owning seats (≥1 `[a-z0-9-]+` token),
  actions (each line exactly `COMMIT`, `FILE-QUEUE-ITEM <queue>` or
  `PUSH <branch-ref>` — `REBASE`/`SEED`/bare `PUSH`/flagged `COMMIT`/bare
  `FILE-QUEUE-ITEM` refused), TPM gate (`WHAT`+`BY WHOM`+`ARTIFACTS` present
  and non-empty; verifier naming an owning seat refused), revocation channel
  named (placeholder values refused), audit trail (all 3 links: envelope +
  verification + execution/commit), unknown top-level sections refused.
  Accepts single-line and template-verbatim wrapped header forms.
- `tests/test_check_envelope.py`, `tests/test_build_canary.py` — NEW (see §5).
- Regenerated leaves (via `generate-rigs.py`, never hand-edited):
  `specs/agents/gamedev/engine-systems-eng/` (role.md + 2 permission JSONs),
  both rig copies (`game-dev-and-sim-rig`, `heretek-omni-fleet`) + bundle
  digests, `registry/entries/*` + `registry/status.json` + `registry/views/*`
  (mechanical digest/provenance churn, incl. the known accepted
  `resolvedCommit` re-lag to the wave HEAD).
- This report. NOT committed, per tasking.

## 3. Grants changed, before/after hashes

Canary dry-run render (dummy secrets, post-regen catalog) sha256:

| file | before (spike baseline) | after (this wave) |
|---|---|---|
| `extensions/pi-permission-system/config.json` | `92aea891…7ae5b6` | `f08d04e6d086d59b53c2889f05584256b17b1d97f812d6bd0801043131479488` |
| `mcp.json` | `47853051…f9838` | `478530510b31c3eb4abeaac8a33b81f8f3c207df7f56e076ec3f7ae5b6bf9838` (UNCHANGED) |
| `settings.json` | `781034d9…d3087cf` | `781034d972e657357498c5a4f32c590b0efa9b4953d4fe7661d0cd3087cf046d` (UNCHANGED) |

Only the permission config moved — exactly the one-grant delta. Rendered-allow
audit over every regenerated permission file: zero non-`date` allow churn
(`git diff` on `*pi-permission-config.json`/`*policy-enforcement.json`
filtered for `^[+-]` minus `date` lines → empty).

## 4. Live proof log (canary only)

Pre-mutation snapshot: `01M5N5N7DJ4BA630WQERJBE86R`
(`rig snapshot 01M5GWFPKVNQEXQVSAGQ2ANJBE`, pre-mutation).
Queue pre-check: `rig queue list --destination <canary> --json` → `[]`
(drain-to-zero; nothing HELD, nothing to unpark — same before retry).

Refresh round 1 (seed-key MISS — recorded honestly, see §7 decision 3):
re-seed member fragment with `--rig <ULID>` (wrong state key) → `--plan`
(launchable true, 50/50 siblings `unchanged`, no blockers) → `seat launch
--fresh --stop` → session `01M5N5NXMRDKNDBQ6E5FW617Z6` ready,
`startupPolicyHash 9afdc3f5…` → relay `qitem-20261023200216-9c732ee0d4f55a8c`
(`persisted=True`, later `done`) → seat reported `date +%s` DENIED.
Diagnosis: seed wrote `…@01M5GWFPKVNQEXQVSAGQ2ANJBE` (key nothing reads);
live seat reads `…@heretek-omni-fleet` (stale, 0 date grants). No fleet harm.

Refresh round 2 (correct key): re-seed with `--rig heretek-omni-fleet --pod
engine --allow-missing-secrets` → state dir config contains the grant →
queue still `[]` → `--plan` again (launchable true, 50/50 unchanged, no
blockers) → `seat launch --fresh --stop` → session `01M5N5T6A4CXDX1JYMRMG29V9S`
ready, `startupPolicyHash 482ae6ce…` (differs from round 1 — policy moved) →
relay `qitem-20261023200427-1c2e7b908d09b3ac` (`persisted=True`,
`rig queue show` → `done`; transcript quotes receipt verbatim).

Round-2 seat verdict table (verbatim, each command run separately, no files
created or modified):

| # | Command | Result | Verbatim |
|---|---|---|---|
| 1 | `date +%s` | ALLOWED | `1792785873` |
| 2 | `cmake --preset linux-release` | DENIED | `[pi-permission-system] Denied by policy: 'bash' (rule '*').` |
| 3 | `./build.sh --help` | DENIED | `[pi-permission-system] Denied by policy: 'bash' (rule '*').` |
| 4 | `clang++ -fsyntax-only /dev/null` | DENIED | `[pi-permission-system] Denied by policy: 'path' for tool 'bash' for path '/dev/null' (rule '*').` |
| 5 | `git add src/engine tests/engine` | DENIED | `[pi-permission-system] Denied by policy: 'path' for tool 'bash' for path 'src/engine' (rule '*').` |
| 6 | `git status --short` | ALLOWED | untracked-tree listing, exit 0 |

Post-mutation fleet: `rig ps --rig heretek-omni-fleet` → 51/51 running,
0 need attention. The other 50 seats were never contacted (both `--plan`
non-target lists show no other seat touched; no `send`/relay left the canary).

BC-L3 (REQ-BC4 live leg): TWO authenticated-relay round-trips, both via
`send-authenticated.sh` (never raw `rig send`), both seat-ACKed in transcript
with the `qitemId` quoted and rows closed `done`. BC-L4 (REQ-BC7 incl. N1):
snapshot ID on file pre-mutation ✓, sibling preservation (50/50 unchanged
both rounds) ✓, queue drain-to-zero with nothing to unpark ✓, snapshot-restore
rollback available (ID recorded, never needed) ✓.

D1–D7 outcomes: D1–D4 REMAIN STAGED (no build runnable — correctly not
attempted; the canary grant is clock-only by design, and the designated
runner's build proof belongs to the follow-up wave). D5–D7 REMAIN STAGED
(need the approved C1 design + human merge; 12c here ships option (a) only).
BC-L1: SUPERSEDED in exactly one cell by design (`date +%s` DENIED→ALLOWED);
the other four denials re-MEASURED live (table above). BC-L2/L5: STAGED for
follow-up. No live behavior was claimed beyond the above.

Rollback: NOT executed. Reason: no misbehavior at any step — both relaunches
`ready`, fleet stayed 51/51 with 0 attention, probes matched the designed
delta exactly. Pre-mutation snapshot `01M5N5N7DJ4BA630WQERJBE86R` retained on
file (`rig restore 01M5N5N7DJ4BA630WQERJBE86R --rig 01M5GWFPKVNQEXQVSAGQ2ANJBE`).
Stray-state cleanup: the mis-keyed round-1 state dir
(`…@01M5GWFPKVNQEXQVSAGQ2ANJBE`, created by this wave, read by nothing) was
removed via python `shutil.rmtree` after round 2 proved green (shell `rm -rf`
rejected once by tooling policy — retried via python per AGENTS.md reroute
guidance; only remaining canary keys are the pre-existing `@game-dev-and-sim-rig`
and the live `@heretek-omni-fleet`).

## 5. Verification outputs (exact commands, exit codes)

- `python3 -m unittest tests/test_check_envelope.py` → **36/36 OK** (exit 0).
- `python3 -m unittest tests/test_build_canary.py` → **11/11 OK** in 25.7s
  (exit 0; 9 static pins + ALLOW `date +%s` executes + 10 DENY subtests incl.
  F6 `;`/`|`/`>`/`$()`/backtick replays, bare-`date` narrowness, BC-L1
  remainder — STRICT denial-text classification throughout).
- `bash scripts/gate-role.sh engine-systems-eng` → **40 ok, 0 FAIL** (existing
  baseline unbroken by the grant).
- `./scripts/verify-rigs.sh --check-only` → **27 passed, 0 failed** (exit 0).
- `python3 -m unittest tests/test_render_seat.py tests/test_sweep_typed_blocks.py tests/test_regen_gate.py tests/test_queue_id_discipline.py tests/test_queue_json_discipline.py tests/test_reconcile.py tests/test_generate_trackers.py`
  (the 7 `make test` files) → **125 tests OK** (exit 0).
- `python3 ./scripts/audit_loop.py --self-test` → **SELF-TEST PASSED** (exit 0).
- `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py --vendor-dir
  /home/john/Projects/heretek-rig-workspace/heretek-rigs/.scratch/vendor`
  → success ("wrote 51 specialist AgentSpecs, 68 shared skills, 8 RigBundles…").
  Plain `generate-rigs.py` refuses on the intended tracked dirt by design;
  `--vendor-dir` points at the main checkout's pinned clones read-only
  (this worktree has no `.scratch/`; SHAs verified by the generator itself).
  First attempt without `--vendor-dir` failed closed on the missing pin dir —
  recorded, no state changed.
- RED proof (TDD): pre-implementation runs failed exactly as designed
  (`test_check_envelope` 34 failures on missing script; canary pins failed on
  absent grant; two test-authoring bugs — an `isError`-style over-broad
  compiler assertion and a wrong-field refusal attribution — caught by RED and
  fixed before GREEN).

## 6. Tasks.md disposition

- BC-T1 (matrix pin): covered by `test_build_canary` BC3/`git-add` pins +
  `grep -c "git add" fleet/fleet.yaml` → 0 re-verified.
- BC-T2 (mock probes): `CanaryMockProbes` (11 probes, strict classification).
- BC-T3 (wrapper check): unchanged wrapper; `test_queue_json_discipline.py`
  still green (125-file run above); live `--dry-run` form previously measured.
- BC-T4 (help-text verbs): `seat launch --help` excerpts captured live (§4
  flow used `--fresh --stop --plan --reason --json` exactly as documented).
- BC-T5 (C1 alignment): no C1 delta shipped — 12c via option (a) only;
  BUILD-CLOSEOUT Part-2 refusal stands; decision recorded (§7.1).
- BC-L1: MEASURED with one designed supersession (table §4).
- BC-L2: STAGED (follow-up: D1–D4 from `cpp-lowlevel-eng`, untouched).
- BC-L3: MEASURED (two authenticated round-trips, receipts quoted).
- BC-L4: MEASURED (N1 criteria all recorded §4).
- BC-L5: STAGED (needs C1 + human merge).

## 7. Decisions

1. **Canary grant is clock-only.** The canary bound (grants on
   `engine-systems-eng` only) intersected with binding REQ-BC3 (no
   configure/compile/`./build.sh` for authoring seats) leaves exactly the
   output-anchored clock read for D4 ELAPSED — the hole the spike §8 left
   open and design A1 named (`date*`-shaped grant). Narrowed to `date +%s*`
   (not `date*`), then to exact `date +%s` in rework cycle 1 (§8 F3, mechanism
   proven) so bare `date`/`date --help`/`date +%s -u` stay denied (pinned by test).
   No A2 widening; fleet-wide rollout explicitly not started.
2. **No `Makefile`/`verify-rigs.sh` wiring.** Draft tasks require none; the
   new suites run via `python3 -m unittest tests/test_build_canary.py
   tests/test_check_envelope.py` (recorded here). Follow-up may append them
   to `make test` — surgical, one line.
3. **Round-1 seed-key miss kept in the report.** `seed-rig.py --rig` is the
   state-address rig NAME (`render-seat.py:573
   session = f"{args.pod}-{member_id}@{args.rig}"`), not the daemon ULID the
   spike recipe called `<rig-id>`. The live denial (not a refusal, not fleet
   harm) diagnosed it within the hour; round 2 with `--rig
   heretek-omni-fleet` flipped exactly the designed cell. Lesson for the
   runbook: after any re-seed, `grep` the grant in the STATE dir under the
   session's own key BEFORE `seat launch --stop`.
4. **12c = option (a) only.** No `git add*` delta (still 0 fleet-wide);
   `git-drift-coord` still `builtin:locked` + `READONLY_16_ROLES`; commit
   authority flows through the verified envelope path (§1.2).

## 8. Rework cycle 1 (review findings F1–F7, N1–N2 — 2026-10-23)

Nine verified findings fixed, minimal hunks, no commit. Validation after fix:
`test_check_envelope + test_build_canary` → **60 tests OK** (49 + 11);
7-file `make test` form → **125 OK**; `verify-rigs.sh --check-only` → **27/0**;
`generate-rigs.py` clean (regen leaves carry only the F3 delta).

- **F1 (report ellipsis):** §5 command replaced with the full 7-file form
  (`test_render_seat test_sweep_typed_blocks test_regen_gate test_queue_id_discipline
  test_queue_json_discipline test_reconcile test_generate_trackers`); the exact
  pasted command re-run → 125 OK before writing it in.
- **F2 (expiry XOR):** `check_expiry()` now refuses single-slice + explicit
  deadline combined (named `Expiry` Refusal); neither-only-one refusals preserved.
  Test `test_combined_single_slice_and_deadline_refused` → exit 1 + names expiry.
  RED proof: combined envelope ACCEPT (exit 0) on pre-fix checker, REFUSE on fixed.
- **F3 (narrow `date +%s*` → `date +%s`):** MECHANISM PROVEN FIRST on /tmp renders
  (worktree untouched): wildcard render — bare ALLOW, `-u` ALLOW, `--help` ALLOW,
  `;id` DENY; exact-pattern render — bare ALLOW (`1792787710`), `-u`/`--help`/`;id`
  all DENIED verbatim. Narrowing is real, not theater, so shipped: catalog line
  narrowed, `test_build_canary` pins updated (`date +%s`, +2 narrowness DENY cases
  `-u`/`--help`), regen re-run (6 permission JSONs now `"date +%s": "allow"`;
  role.md verification-commands line updated; canary-only). Live re-probe, canary
  only, bare `date +%s` → `1792787868` exit 0 ALLOWED
  (`qitem-20261023203742-194fbe78a6bb9c27`, done). NOTE: live seat still runs the
  pre-narrowing wildcard render until the next refresh; narrowed behavior is proven
  by the mock suite rendering the current catalog (13 DENY subtests green).
- **F4 (marker anchoring):** `marker_value()` is now line-start anchored (optional
  whitespace + optional `1.`/`(a)` prefix, REQUIRED colon), returns None when absent;
  `check_tpm_gate()` presence checks go through it. Tests: embedded `WHAT` in
  `whatever` mid-record → refused naming WHAT; empty `WHAT:` → refused. Missing-marker
  refusals preserved (existing tests green). RED proof: embedded envelope ACCEPT on
  pre-fix, REFUSE on fixed.
- **F5 (duplicate sections):** `require()` now refuses 2+ same-key sections as
  AMBIGUOUS (named Refusal); missing-section refusal preserved. Test: appended second
  `Permitted operator actions:` with REBASE → exit 1 + `AMBIGUOUS`. RED proof:
  pre-fix ACCEPT (first section wins, REBASE ignored), fixed REFUSE.
- **F6 (path-scope classes):** `check_path_scope()` additionally refuses root aliases
  (`.`, `./`, empty-after-normalize), `~`-prefixed entries, and glob metacharacters
  (`*?[]{}!`); absolute/`..`/whitespace refusals preserved. Five tests added
  (`.`, `./`, `~/evil`, `src/*`, `src/[a-z]`). RED proof: `src/*` ACCEPT pre-fix,
  REFUSE fixed.
- **F7 (PUSH branch validation):** branch must be a plain name — refuses leading
  `+ - / . :`, trailing `/ . .lock`, `..`, any `:`, wildcards/specials
  (`*?[]{}!~^\`), and bare `HEAD`; `PUSH main` + `PUSH feat/wave-12-canary` still
  ACCEPT. Root cause found live: `PUSH :…` lines never reached `check_actions`
  (colon ⇒ unknown-section gate fired first); fixed by keeping action-shaped lines
  inside the actions section as body so `check_actions` rules on them (fail-closed
  either way; no behavior change outside the actions section). Tests: `PUSH +main`,
  `PUSH :main`, `PUSH HEAD:main` → exit 1; `PUSH main` → ACCEPT. RED proof: `PUSH
  +main` ACCEPT pre-fix, REFUSE fixed.
- **N1 (drifting HEAD):** `test_canary_scope_only` compares on-disk catalog vs fixed
  base `a33f3bb` and asserts `changed == [CANARY_ROLE]` exactly (was `HEAD` +
  `assertIn ([], [canary])`). Holds with the F3 narrowing. Verified green.
- **N2 (unknown-section text):** test now also asserts `unknown section` in output
  (checker emits exactly that).

RED-proof method (all in /tmp scratch, worktree files never touched for sabotage):
pre-fix checker extracted via `git show HEAD:scripts/check-envelope.py`; five sabotage
envelopes (F2 combined, F4 embedded, F5 duplicate, F6 glob, F7 `PUSH +main`) → exit 0
pre-fix, exit 1 fixed. Scratch removed afterwards.

## 9. Self-audit notes (unfinished stated plainly)
- New suites are NOT wired into `make test` or `verify-rigs.sh` (decision 2) —
  CI will not run them until the follow-up appends them.
- `git status` at hand-off: 29 tracked modifications (1-line catalog delta +
  28 regen'd leaves) + 4 untracked (`scripts/check-envelope.py`,
  `tests/test_build_canary.py`, `tests/test_check_envelope.py`, this report).
  Nothing else touched; nothing committed.
- Live `rig send operator` from the seat fails (`Session 'operator' not
  found`) — delivery relies on queue closure, as in the spike. Not a defect,
  noted for operator UX.
- The whole fleet (canary included) runs re-seeded `--allow-missing-secrets`
  (degraded MCP servers) — pre-existing fleet condition, unchanged by this wave.
- No secrets, no credential-shaped strings, no stubs/`TODO`s/empty catches in
  the diff. `grep -rn "TODO\|stub\||| true" scripts/check-envelope.py
  tests/test_build_canary.py tests/test_check_envelope.py` → clean (only the
  word "stub" appears in this report's prose, not in code).
