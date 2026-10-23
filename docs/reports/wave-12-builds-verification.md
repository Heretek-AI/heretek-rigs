# Wave-12 builds — independent adversarial verification (NOT committed)

- **Stage:** wave-12-builds (issues #12 + #9 + #11, canary scope ONLY)
- **Auditor:** Independent Drift Guard subagent (read-only; this report is the only file written, uncommitted)
- **HEAD audited:** `bf890cf` (branch `feat/12-build-capability`); `git status --short` CLEAN at audit time
- **Binding:** `openspec/changes/issue-12-build-capability/specs/build-capability/spec.md` (REQ-BC1..BC7),
  `tasks.md`, `docs/reports/wave-12-builds-implementation.md`,
  `docs/evidence/wave-12-builds/red-proofs.log`
- **Method:** every headline gate re-run by the auditor at `bf890cf`; matcher and verifier
  probed with hostile inputs beyond the shipped suites; all sabotage/mutation work in scratch
  (`/tmp`, since removed); no worktree file touched.

## Re-run results (auditor-executed, exit codes observed)

| Gate | Command | Result |
|---|---|---|
| Envelope suite | `python3 -m unittest tests/test_check_envelope.py` | 36/36 OK, exit 0 |
| Canary suite | `python3 -m unittest tests/test_build_canary.py` | 11/11 OK, exit 0 (~28s) |
| Baseline gates | `./scripts/verify-rigs.sh --check-only` | 27 passed, 0 failed, exit 0 |
| Role gate | `bash scripts/gate-role.sh engine-systems-eng` | 40 ok, 0 FAIL, exit 0 |

(Note: `verify-rigs.sh` reports 27 checks vs AGENTS.md's baselined 26 — the delta is additive
alongside per convention; no baselined check renumbered/reworded. Tracked `Makefile`/`scripts/`
(except the two NEW files) are byte-identical to `main`: `git diff main --stat -- tests/ Makefile scripts/`
shows only the 3 new files, 0 modifications.)

## (a) SCOPE — PASS

- `git diff main -- fleet/fleet.yaml` is exactly one line: `+      - date +%s*` under
  `engine-systems-eng.bash_allow`. No other catalog +/- lines.
- Every regenerated permission leaf sampled carries only that delta:
  `specs/.../engine-systems-eng/runtime/pi-permission-config.json`,
  both rig copies' `pi-permission-config.json` + `policy-enforcement.json` — each `+      "date +%s*": "allow",`
  only. `git diff main -- '*pi-permission-config.json' '*policy-enforcement.json' | grep -E "^[+-]" |
  grep -v "^[+-][+-]" | grep -v "date +%s"` → empty (zero non-date churn).
- `role.md` leaves: only the verification-commands line gains `, \`date +%s*\`` (mechanical regen).
- `bundle.yaml` diffs: integrity-hash churn only. `registry/` diffs: `resolvedCommit` re-lag
  (`8f6bbca`→`a33f3bb`, the known accepted pre-merge-HEAD pin per AGENTS.md — NOT flagged) +
  `packageDigest`/`bodyDigest` churn only; `registry/views/*/behaviour.json` diffs filtered for
  non-provenance lines → empty.
- No hand-edits of generated trees: all leaf changes are consistent with generator output for a
  one-line catalog delta (no content a regen could not produce). No commit, no push by the wave
  beyond the branch itself; auditor committed nothing.

## (b) SPEC DRIFT — PASS (every REQ honestly met or honestly staged)

- **REQ-BC1:** static legs hold — `bash_allow` contains `./build.sh*`? No: authoring seat correctly
  lacks it; `cmake*`/`ninja*`/`ctest*` present as before. D1–D4 log proof honestly STAGED (no build
  claimed). The three sabotage replays re-probed by the auditor on a fresh mock render: DENY all.
- **REQ-BC2:** grant→artifact pairing honest — `date +%s*` is the D4 ELAPSED clock read, nothing more.
- **REQ-BC3:** holds — `engine-systems-eng.bash_allow` has no `cmake --preset`, no compiler invocation
  (only `clang --version*` probe), no `./build.sh*`. (`build.sh` under `path_write` is pre-existing
  write scope, not execution, and unchanged.)
- **REQ-BC4:** verifier + 36 binary fail-closed tests shipped (one per required field incl. all 3 audit
  links); wrapper untouched and its receipt-parsing coverage still green. Live round-trip legs are
  claimed MEASURED in the implementation report and independently re-proofed in `red-proofs.log`
  (receipt `qitem-20261023201301-…` → `done`); auditor re-ran all disk gates but did not inject live
  fleet traffic — accepted as QA-evidenced, not auditor-replicated.
- **REQ-BC5:** no raw-`rig-send` authority change anywhere in the diff. Holds.
- **REQ-BC6:** option (a) only, honestly — `grep -c "git add" fleet/fleet.yaml` → 0 (auditor re-ran);
  `git-drift-coord` still `builtin:locked`, no stage/commit verbs. D5–D7 STAGED, stated plainly.
- **REQ-BC7:** canary-only refresh per report; no fleet-wide mutation in the diff (see (f)).

## (c) OVERREACH (`date +%s*` prefix semantics) — PASS, proven by probe not assumed

Auditor-rendered canary policy (mock harness, `gate-run.sh`), STRICT `Denied by policy` classification:

| Input | Result | Required |
|---|---|---|
| `date +%s; id` | DENY | DENY ✓ |
| `date +%s > /tmp/audit12-pwned` | DENY | DENY ✓ |
| `date --help` | DENY | DENY ✓ (grant is `date +%s*`, not `date*`) |
| `date +%s \| tee /tmp/…`, `$(id)`, backtick, `&&`, `\|\|`, embedded newline, `;echo` | DENY (suite + auditor) | DENY ✓ |
| `date +%s -f /etc/passwd`, `--file=…`, `-r /etc/passwd` | DENY (path rule — defense in depth holds) | DENY ✓ |
| `DATE +%s`, `env date +%s` | DENY | — |
| `date +%s --help` | ALLOW — prints help text only, no execution primitive | benign, noted |
| `" date +%s"` (leading space), `TZ=UTC date +%s` | ALLOW — same `date` binary, no metachars, no added capability | benign, noted |
| `date +%s -d @…`, `-u` | ALLOW — pure clock math | benign, noted |

The terminal-metachar deny fires on every chaining/write-escape shape tried; the residual ALLOW surface
is the `date` binary itself with inert flags. No unintended capability opened.

## (d) ENVELOPE VERIFIER SOUNDNESS — PASS (allowlist, expiry, self-verification hold)

Auditor-probed `scripts/check-envelope.py` beyond the suite (reference `--at "2026-10-23 19:00Z"`):

- **Allowlist:** `commit` (lowercase), `COMMIT --amend`, `PUSH feat/x --force`, `PUSH -d feat/x`,
  `FILE-QUEUE-ITEM ops-log extra`, bare `PUSH`/`FILE-QUEUE-ITEM`, `REBASE`, `SEED` → all REFUSE (exit 1).
  `PUSH feat/wave-12-canary` (exact branch) → ACCEPT, as designed.
- **Expiry edges:** deadline == now → REFUSE (`<=` boundary fail-closed ✓); `Expires` (capital) without
  parseable stamp → REFUSE ✓; impossible date (`2026-02-30`) → REFUSE ✓; `never`/`open-ended` → REFUSE ✓;
  deadline + `--consumed` → ACCEPT (deadline semantics unaffected ✓); single-slice + `--consumed` →
  REFUSE/VOID ✓; `--revoked` → VOID ✓.
- **Self-verification:** `BY WHOM: TPM countersigned engine-systems-eng` → REFUSE (substring match, safe
  direction) ✓.
- **Plumbing:** unreadable file → REFUSE exit 1; missing `--envelope` → exit 2; unknown top-level section
  (`Extra grants:` at column 0) → REFUSE ✓.
- **Advisory notes (NOT findings — author-is-trusted model, actions are the sole authority source and
  are strictly allowlisted, so none of these grant anything):**
  1. A duplicated second `Expiry: never` section is ignored (first-wins) → ACCEPT. Consider refusing on
     duplicate known sections.
  2. An *indented* unknown header (`  Extra grants: …`) is absorbed inertly into the preceding body
     rather than refused. Inert in all sections (in `actions` it would still hit the allowlist).
  3. Audit links are keyword-checked (`envelope`/`verif`/`execution|commit`) without `qitem`-ID shape
     validation — a keyword-only audit paragraph ACCEPTs. Consider per-link ID-shape checks.

## (e) VACUOUS TESTS — PASS (non-vacuity demonstrated, not assumed)

- `test_clock_read_grant_present`: auditor replicated the assertion against a scratch copy with the grant
  removed → FAILS-as-designed (non-vacuous).
- `test_canary_scope_only`: auditor replicated the logic with `date +%s*` added to `cpp-lowlevel-eng`
  in a scratch copy → `changed=['cpp-lowlevel-eng']`, FAILS-as-designed (non-vacuous).
- Envelope RED: `red-proofs.log` records 34 pre-implementation failures on the missing script; auditor's
  hostile inputs above all produce REFUSE, so every `assertEqual(returncode, 1)` refusal test is load-bearing.
- `test_deny_cases_rejected` re-ran green standalone in the suite run above (10 DENY subtests, STRICT).

## (f) ROLLOUT CREEP (#9/#11 fleet-wide) — PASS

`git diff main --name-only` filtered against `engine-systems-eng|bundle.yaml|registry/|fleet/fleet.yaml|
check-envelope|test_build_canary|test_check_envelope|red-proofs|wave-12-builds-implementation` →
empty. No other role's grants touched; no `Makefile`/`verify-rigs.sh`/`gate-*.sh` edits; no fleet-wide
#9/#11 rollout smuggled in. New suites run via `python3 -m unittest`, correctly NOT yet wired into
`make test` (stated as follow-up in the implementation report §8 — honest, not creep).

## (g) SECRETS / STUBS — PASS

- `grep -rnE "TODO|FIXME|XXX|\|\| true|except.*: *pass"` on the 3 new files → clean (exit 1, no hits).
- Credential-shaped grep on the wave diff → only dummy/mock values (`write_text("dummy")`,
  `"apiKey": "mock"`, `--allow-missing-secrets`) and the English words "seat token"; no real keys,
  no `~/.config/heretek-rigs/secrets` reads. `git status --short` CLEAN (auditor wrote only this report,
  uncommitted; scratch removed).

## Summary

Scope is exactly the canary single-grant delta; every REQ-BC1..BC7 leg is either statically proven
above or honestly marked STAGED with its deferral reason; the prefix matcher denies every hostile
shape with a real tooth; the envelope allowlist/expiry/self-verification checks hold; tests are
non-vacuous; no rollout creep; no secrets or stubs. Three envelope hardening notes are advisory only.

VERDICT: PASS
