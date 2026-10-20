# #12 Build Closeout Criteria — "No seat can execute builds"

**Slice:** A3 (self-improvement program, Workstream A).
**Branch:** `feat/self-build-closeout`. **Status:** CRITERIA-ONLY + documented refusal on catalog delta (Part 2 outcome b).
**Fleet state at writing:** DOWN (per program plan §status). All live proof is DEFERRED — see §6.

## 1. Background (what #12 reported)

Verified live seat denials: the engine seat could not `cmake`-configure, `clang++`-compile,
run `./build.sh`, read the clock, or stage/commit. A fleet-wide permission matrix showed only
`cpp-lowlevel-eng` as build-capable — and even that seat could not execute `./build.sh`.
The issue stays open until green build proof exists.

## 2. ALREADY MERGED (do not re-litigate)

| PR | Grant (in `fleet/fleet.yaml`, regenerated + verified) | Effect |
|---|---|---|
| #10 `feat/s02-engine-repo-root-scope` | `engine-systems-eng.path_write` += `build.sh`, `CMakePresets.json`, `CMakeLists.txt` (src stays under `src/engine/*`, no `src/*` widening) | S02 skeleton authorship has a valid seat |
| #13 `feat/s02-build-runner-scope` | `cpp-lowlevel-eng.bash_allow` += `./build.sh*` (on top of existing `cmake*` / `ninja*` / `ctest*`; interpreter-prefix ban untouched; `path_write` unchanged) | One designated seat can drive configure+build+smoke via the one-command build |

Both landed via PR → human merge with Triad (programmer + QA PASS + drift-guard PASS) and
`verify-rigs.sh` 22/0. They are the exec/build halves of #12.

## 3. REMAINING GAPS (why #12 is still open)

### Gap 1 — Committer path (no seat can stage/commit engine output)
- `git-drift-coord` (the nominal committer / drift coordinator, `builtin:locked`,
  member of the `READONLY_16_ROLES` set enforced by `verify-rigs.sh`) holds read-only git
  verbs ONLY: `git branch*`, `git merge-base*`, `git status*`, `git diff --stat*`,
  `git diff --name-only*`, `git log --oneline*`, `git show --stat*`. No staging, no commit.
- Fleet-wide grep (2026-10-20): **no role declares any `git add*` verb** — staging is
  impossible for every seat. `dependency-patcher` holds broad `git checkout*` + `git commit*`,
  but without `git add` that commit grant can only commit already-staged content (the empty
  set in a seat workspace) — a dead grant for this purpose, and its unscoped form is not a
  pattern to copy.
- So: build output cannot be staged or committed by any seat. Gap is real and blocking.

### Gap 2 — In-seat end-to-end proof
No green build has ever been observed from inside a relaunched seat (fleet DOWN). Merged
scopes are verified statically (regen + 22/0 + gate-role mocks), not behaviorally.

## 4. Done checklist (ALL boxes required before #12 closes)

| # | Check | Seat / actor | Command / evidence | Verified by |
|---|---|---|---|---|
| D1 | Configure succeeds in-seat | `cpp-lowlevel-eng` (build rig workspace) | `./build.sh` (or `cmake --preset …`) exits 0; **build log captured, exit 0 shown** | QA seat + log attached to #12 |
| D2 | Full test suite green in-seat | `cpp-lowlevel-eng` | `ctest` log showing **all tests passed (13/13-style: N/N, zero failures)** | QA seat + log attached to #12 |
| D3 | Tree identity recorded | operator | `git rev-parse HEAD` **tree SHA** of the built checkout, recorded alongside logs | TPM / operator |
| D4 | Elapsed-time proof | `cpp-lowlevel-eng` | **ELAPSED** wall-clock for configure+build+test captured from the seat transcript (no "works" without timing) | QA seat |
| D5 | Committer path exercised | designated committer (post-A2 envelope; today: NONE — Gap 1) | `git add <scoped paths>` + `git commit` on a branch succeed in-seat; **push-to-main never required, never granted** | drift-guard / red-team seat |
| D6 | Human merge | human operator | PR merged to `main` (Constitution §2: permission/behavior changes land via PR → human merge → re-seed → relaunch; never self-applied live) | merge record |
| D7 | Post-merge green re-proof | relaunched seat | D1–D4 re-run after re-seed/relaunch (running sessions enforce old policy — that staleness is a safety property, #11 lesson) | QA seat |

#12 closes when D1–D7 are all evidenced on the issue. D1–D4 are unblocked by #10/#13 once the
fleet relaunches. D5 is blocked on Gap 1 + the A2 envelope design (commit authority lives in
A2's pre-authorization envelopes, sibling work — this slice does not pre-empt it).

## 5. Part 2 decision record — OUTCOME (b): documented refusal, no catalog edit

**Proposed minimal grant (REJECTED):** scoped `git add`/`git commit` verbs for `git-drift-coord`
on engine paths.

**Exact reasons (each independently sufficient under fail-closed rules):**

1. **The commit half cannot be scoped.** `bash_allow` entries are trailing-`*` prefix matches
   (see `verify-rigs.sh` HR-5.5 comments: "prefix-glob matcher semantics", "trailing-* prefix
   allows"). `git commit -m … [paths…]` carries its paths *after* flags, so any `git commit*`
   allow matches `git commit -a`, `--amend`, and arbitrary paths. A "narrowly-scoped commit
   verb" is inexpressible in this permission system — the grant would be broad by construction.
2. **Identity config needs its own surface.** A seat commit requires `user.name`/`user.email`;
   the `git -c … commit …` form does not match a `git commit*` prefix (needs a separate
   `git -c*` allow = git-config surface widening), and repo-local config lives under `.git/`,
   which is deny-guarded fleet-wide. The "minimal" grant drags in a second widening.
3. **Wrong role.** `git-drift-coord` is `builtin:locked` and in the verify-enforced
   `READONLY_16_ROLES` set (charter = drift *coordination*, observe/report). Making a locked
   read-only coordinator into a committer contradicts its charter semantics even though the
   current gate only checks `path_write` for that set — gates pin floors, not intent.
4. **A2 owns commit authority.** Standing commit authority is A2's pre-authorization-envelope
   mechanism (sibling branch; conflict-avoidance binding). A standing `git add`/`git commit`
   grant here would pre-empt that design and create a merge-time collision.

Per the task's conflict rule ("if the required grant is anything broader than that, do NOT
implement"), no `fleet/fleet.yaml` edit was made. A future committer grant must, at minimum:
(a) be designed against prefix-matcher reality (allowlist the exact argv forms, not paths);
(b) resolve seat git identity without opening git-config surface; (c) land on a non-locked,
non-readonly role or come with a charter change + red-team review; (d) align with the A2
envelope model. That is a design task, not a one-line delta.

## 6. Live-proof deferral (explicit)

Fleet is DOWN. D1–D5 cannot be executed from this worktree. No mock, no `echo passed`, no
gate-role transcript is accepted as build proof. After human approval + relaunch, D1–D4 run
first (they need only #10/#13, already merged); D5 waits on the Gap-1 design above. Evidence
lands on issue #12 as logs (build log exit 0, CTest N/N, tree SHA, ELAPSED), not claims.

## 7. Self-audit notes (this slice)

- No `fleet/fleet.yaml` change; no regen run required (nothing to regenerate).
- No hand-edits to generated leaves (`specs/`, `rigs/`, `rosters/`, `registry/` untouched).
- No files from sibling slices touched (`docs/USER_GUIDE.md`, `PRE-AUTH-ENVELOPES.md`,
  `SEAT-REFRESH-RUNBOOK.md` — untouched by design).
- No secrets, no machine paths. Nothing committed, nothing pushed.
- `verify-rigs.sh --check-only` re-run from this worktree post-change: **22/0** (see summary).
