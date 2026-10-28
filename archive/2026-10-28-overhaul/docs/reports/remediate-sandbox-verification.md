# remediate-sandbox verification (Wave 2, audit #66 M4–M5) — independent drift-guard audit

- Stage: remediate-sandbox | Worktree: `.lane/trees/remediate-sandbox` | Branch: `remediate/audit-66-p0-p1-sandbox`
- Spec: `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md` (M4, M5 + F1–F3, F7–F9, Gotchas 1–5, 8)
- Implementation report: `docs/reports/remediate-sandbox-implementation.md`
- QA report: `docs/reports/remediate-sandbox-qa.md` (verdict PASS, 1 gap S2a)
- Red-proofs: `docs/evidence/remediate-sandbox/red-proofs.log`
- Auditor method: re-ran every acceptance command in-worktree; did not modify source (`git status --short` clean at close).

## M4 — sandbox every execution-capable seat: PASS

- `scripts/seat-sandbox.sh` present, mode 755, executable. bwrap core byte-matches the spec's verified block: `--die-with-parent --new-session --unshare-pid/ipc/uts/net --ro-bind / / --dev /dev --proc /proc`, scratch bind + `TMPDIR`, `"${binds[@]}" "${mask[@]}" --chdir "$cwd" /bin/bash -c "$cmd"`, scratch default `/var/tmp` (Gotcha 1 respected), usage guard exit 126, `set -euo pipefail`. Only addition is the documented M4 `sandbox.env` bootstrap preamble (deviation recorded in NOTES).
- `shellPath` emitted absolute (`str(Path(__file__).resolve().parent / "seat-sandbox.sh")`, verified absolute + exists +x at runtime); all 51 committed `runtime/pi-settings.json` leaves end in `scripts/seat-sandbox.sh` (spot-checked 10 + V12 per-seat assert).
- `HERETEK_SANDBOX_WRITE` mechanism is real: `build_seat_files` unconditionally emits `sandbox.env` (bind-normalized `path_write` via `_sandbox_bind_roots` + secrets dir); `render-seat.py --out` writes every `files[]` entry to the seat agent dir; the wrapper sources `$PI_CODING_AGENT_DIR/sandbox.env`. Unit test pins `tests/chaos:docs/qa` for sabotage-qa-tester. `sandbox.env` correctly absent from regen `rigs/` reference leaves (live agent dirs are the delivery path; wrapper fail-closes to whole-tree-read-only when roots unset).
- All 18 `builtin:locked` seats hold zero runner/interpreter verbs (fleet-wide sweep incl. `python|pytest|npm|npx|yarn|cargo|rustc|go|ruby|perl|garak|pyrit|promptfoo|clippy|stryker|mutmut|jest|mocha` — no hits). Spot-checks: sabotage-qa-tester (11 allows), ai-red-teamer (11), static-analysis-lead (13, semgrep/ruff only) — clean.
- dependency-patcher: zero `commit`/`checkout` grants (legitimately keeps its `npm/pytest/cargo/go test` verbs as a `builtin:standard` seat).
- `generate-rigs.py` twice: both runs exit 0 and converge to the same fixed point; only delta is the known-accepted `resolvedCommit` re-lag (16 registry files × 1 line). Tree restored via `git checkout -- registry/`; status clean.
- F2 corpus independently re-run under the committed wrapper (bwrap 0.13.1): in-scope write rc=0; `root.txt` rc=1 Read-only; secret-store key `No such file` rc=1; bad usage rc=126. (git probe skipped only because the scratch dir is not a repo; confinement + masking confirmed.)

## M5 — git-diff bypass + identity forgery: PASS

- Deny tuples: renderer emitter and `verify-rigs.sh:588` mirror each hold 31 entries, ordered identical (15 pre-existing + 14 M5 git-diff denies + 2 env denies). All 14 spec denies (`-u/-U/--unified/--cc/-c/-m/-W/--function-context/--word-diff/--color-words/--binary/--raw` incl. tab variants) present in BOTH.
- `:1153–1160` asserts extended to all 16 new denies (line 1158 loop); unit deny tuple in `test_render_seat.py` likewise extended.
- `send-authenticated.sh`: refuses (exit 2, never unsets-and-proceeds — the spec-allowed variant) when `OPENRIG_SESSION_NAME` is set (re-run: rc=2). Receipt fail-closed matrix re-run via PATH-shadowed stub `rig`: missing qitemId/state rc=4, failed-state rc=5, unpersisted rc=6, createWarning rc=7, pending/in-progress+persisted rc=0. `--source exec-director` rc=2, `--source blue-appsec@rig` rc=2, `--source operator --dry-run` rc=0.
- `gate-role.sh`: M5 probes present (`-u`, `--cc`, `env OPENRIG_SESSION_NAME=x rig whoami` expect-deny) with canary seed (:32–40) and anti-overblock allow probes untouched. Re-run: sabotage-qa-tester exit 0; go-backend-eng M5 probes all `ok`.
- `./scripts/verify-rigs.sh --check-only`: `SUMMARY: 28 checks passed, 0 failed.` `make test`: `Ran 210 tests ... OK`.

## F9 residual: honest, spec-consistent — NOT a finding

- Re-ran live: bare leading `OPENRIG_SESSION_NAME=x rig whoami` EXECUTES (rc=0, daemon reached) — pps strips the assignment before matching, exactly as F9 states. `env OPENRIG_SESSION_NAME=x rig whoami` DENIES via `*OPENRIG_SESSION_NAME=*`. The committed probe uses the env form; the leading form is closed at the `send-authenticated.sh` layer and documented in NOTES:236-239 + implementation report. F9 declares no policy-rule fix exists; the closure + NOTES record is the spec-consistent mitigation. Upstream per-seat identity tokens remain the M10-track follow-up.

## QA advisory S2a (mirror-tuple removal stays green): legitimate M10 follow-up, NOT a merge-blocker

- Confirmed: no in-repo assert compares the renderer emitter tuple with the `:588` mirror, so mirror-only weakening is silent. But the dangerous direction is guarded twice over: renderer weakening goes RED via `:1158` asserts + unit tests (S2b: 27 passed, 2 failed), and leaf tampering goes RED via the mirror-vs-leaves and subset gates. During S2a the committed leaves retained all denies — real protection intact, only verifier coverage narrowed. The `:588` check is not vacuous (it enforces 31 denies × 51 seats against leaves). Recommendation stands as M10 follow-up: assert the two tuples identical (or derive one from the other). Also noted: `generate-rigs.py:493` charter prose predates M5 denies (already in NOTES, M10).

## Hygiene: PASS

- No stubs/swallowed errors: `TODO|FIXME|TBD|PLACEHOLDER` absent from `seat-sandbox.sh`/`send-authenticated.sh`; no empty `except: pass`; the sole `|| true` (gate-role.sh:47 grep pipe) predates this stage and preserves FAIL accounting.
- No hand-edits to `specs/|rigs/|rosters/|registry/`: M4/M5 commits touch only `fleet/`, `scripts/`, `tests/`, `docs/NOTES.md` plus regen leaves. `yaml.safe_dump` lives only in `write_yaml` (generated leaves); `fleet.yaml` untouched by dump (no writer references it). V1–V11 hunks untouched (verify diff: only `:588`, `:1155`, V12 blocks).
- Commit discipline: one commit per milestone (M4 `2cad3c2`, M5 `4eb9c67`), stale canary test in its own commit `04b1399` with NOTES reason (canary+exactly-5-roles bound verified exact against `a33f3bb`), all with both attribution trailers. QA/evidence commits separate. `git status --short` clean.
- Red-proofs: S1/S2b/S3/S4/S5/S6 each show a recorded RED failure signature reverting to GREEN (non-vacuous); S2a honestly recorded as STAYS GREEN with gap classification; no source modified by QA.

VERDICT: PASS
