# Verification — wave-40-manifest-closure (issue #40)

Stage: `wave-40-manifest-closure` · Branch: `remediate/40-manifest-closure`
Change: `remediate-40-manifest-closure` · Commits audited: `9eb5171` + `d4a55ef`
Base: `d863df0` · Date: 2026-10-22 (UTC) · Auditor: drift-guard (read-only; nothing committed)

## 1. Diff audit — scope and generated-tree integrity

`git diff d863df0..HEAD --name-only` (8 files, +1699/−1):

- `scripts/manifest-closure.py` (new, 739), `tests/test_manifest_closure.py` (new, 547),
  `fleet/allowed-system-tools.txt` (new, 26) — the lint, its suite, its allowlist.
- `scripts/verify-rigs.sh` (+33/−0), `Makefile` (+4/−1) — stage-time wiring.
- `docs/reports/wave-40-manifest-closure-implementation.md`,
  `docs/reports/qa-wave-40-manifest-closure.md`,
  `docs/evidence/wave-40-manifest-closure/red-proofs.log` — reports/evidence.
- Zero changes under `specs/ rigs/ rosters/ registry/` (empty `git diff` on those paths).

Every file maps to tasks.md T1–T6; no scope creep. `verify-rigs.sh` diff is a pure
33-line V8 append: `grep -cE '^-[^-]'` on that diff = **0** removed/modified lines,
exactly one new `ok()`, no existing check renumbered or reworded. Makefile diff is
+5/−1 where the single modified line is the `.PHONY` token addition — additive,
non-masking (`manifest-closure` is a new target; no existing target touched).
AGENTS.md one-rule and the 23-check audit-baseline hold: V8 append-only pattern confirmed.

Boundary note (observed, resolved, no finding): proposal §Boundaries says "No changes
to `fleet/`", but normative REQ-C3 explicitly blesses
"`fleet/allowed-system-tools.txt` or equivalent". The implementation follows the
spec's explicit example path with a purely additive new file — no generator input
touched, no regen required, no digest impact (`make verify` 24/0 proves it).

## 2. Lint read-through — real parsing, no stubs

Full read of `scripts/manifest-closure.py` (739 lines): quote-aware `&&`/`;`/`|`
segmentation, `shlex` first-token extraction with env-assignment / redirection /
`${{ }}` / `$VAR` skipping, `pnpm|npm|yarn|npx` indirection recursed into every
defining package with visited-set cycle detection + depth cap 32, `cargo <sub>`
→ toolchain cargo, `pnpm dlx`/`npx <pkg>` one-shots always undeclared, `bin`-field
and root-dep resolution, `BIN_ALIASES = {tsc: typescript, playwright: @playwright/test}`,
relative-`extends` following, tsconfig `types` resolution, exit 0/1/2 semantics.
Stub scan: zero `TODO/FIXME/XXX/HACK/NotImplementedError`; zero `|| true` in new
files; zero bare `except:` (the one `except Exception` names and fail-closes
malformed workflow YAML). No `TODO`, no skipped tests, no swallowed errors.

Offline / parse-only verified by inspection: imports are
`argparse json os re shlex subprocess sys pathlib` only — no `urllib/requests/socket`,
no `shutil.which`, no `PATH` consult, no `node_modules` probing (`SKIP_DIRS`
excludes it; "PATH resolution never counts" is load-bearing and tested).
The only `subprocess` use is `git diff --cached` / `git show` for `--staged`.

Alias-table completeness: every binary on the live Wave-2 surface resolves without
the table except the two genuine bin≠package cases it covers (`tsc`, `playwright`);
all others (`eslint prettier vitest vite turbo cargo git node pnpm echo rig`) resolve
by exact dep, `bin` field, builtin rule, or allowlist. No ad-hoc gap that would
false-positive on a legit pin; no entry that could shelter an undeclared devDependency
(all 8 allowlist entries are runner-guaranteed tools, each grounded in the file's
header comment against the live fixed state; `curl`/`docker` correctly absent and
proven to fail).

## 3. Test suite — non-vacuous, fixture-only

`python3 -m unittest tests/test_manifest_closure.py` re-run by auditor: **Ran 17 / OK**.
Spot-read in both directions: omission tests assert `assertNotEqual(returncode, 0)` **plus**
named-binary assertions (`@types/node` + `tsconfig`, `eslint`, `prettier`, `vitest`,
`tsc`); pass-state tests assert exit 0. All fixtures synthetic under `tempfile`
(`write_tree`/`fixed_tree` only) — zero dependence on live mission pins or this
repo's live files, so the suite passes on a machine without the mission repo
(the one exception, `test_checked_in_allowlist_covers_toolchain`, reads only the
checked-in allowlist itself). Both directions discriminate; nothing vacuous.

## 4. Independent red-proof spot-checks (in-memory harness, no disk writes)

Auditor reproduced four QA red-proofs against the shipped code with fresh synthetic
inputs (not QA's fixtures):

- (a1) `types:["node"]` without `@types/node` → exit-1 class naming `@types/node` + tsconfig. RED confirmed.
- (a3) bare `vitest` → `UNDECLARED BINARY 'vitest'` naming script + package. RED confirmed.
- (a4) JSX without `@types/react` → zero findings, exit 0. Matches QA R4 exactly.
- Indirection cycle `a→pnpm b→pnpm a` → `INDIRECTION CYCLE` naming both legs. RED confirmed.
- Read-only CLI probe: missing allowlist → `MISSING ALLOWLIST … refusing to default-allow`, exit 2. Fail-closed confirmed.

## 5. The (a4) determination — contractual, NOT a gap

My own reading of the binding text, done before accepting QA §4:

- REQ-C2 "Each original omission fails named" enumerates **only** undeclared
  `vitest`, undeclared `eslint`/`prettier`, and undeclared `@types/node` with a
  `types: node` entry. `@types/react` omission is deliberately absent.
- REQ-C5: "Ambient-JSX-style failures (instance #2 …) are outside parse-only reach
  and MUST remain covered by the `tsc` typecheck gate — the lint MUST NOT claim to
  catch that class."
- tasks.md T4: "Instance #2 omission is expected to PASS the lint (documented
  limitation) and MUST instead fail the `tsc` typecheck gate — record both outcomes."
- design.md §Instance-2 + proposal §Non-goals say the same, honestly.

The lint passing instance #2 is therefore **contractually required behavior**, and a
stage that caught it would violate its own spec. Demanding otherwise would require
type-resolution, which the proposal non-goals with stated reason (a parse-only lint
has no textual hook: the web tsconfig carries only `types:["vite/client"]`; React 19
JSX breakage surfaces solely through type-resolution, which is tsc's job and is
already gated). QA's covering-gate evidence (no-`@types/react` JSX fixture fails
`tsc --noEmit` with TS7026+TS2875, the issue's TS7016/7026 class) is recorded with
exact error text by two independent runs (implementer + QA); `tsc` is present on this
host. No spec gap; no finding. (If intent had been "lint must catch it", that would be
a spec bug, not an implementation bug — it was not the intent.)

## 6. Commands re-run (auditor, unmodified tree)

- `python3 -m unittest tests/test_manifest_closure.py` → Ran 17 / OK, exit 0.
- `openspec validate remediate-40-manifest-closure` → valid, exit 0.
- `make verify` → `SUMMARY: 24 checks passed, 0 failed`, exit 0 (V8 present; live-health advisories only, same heartbeat WARNs as baseline).
- `git status --short` → clean. Secrets scan over `git diff d863df0..HEAD` →
  only benign substrings (`first_token`, `.PHONY` token, tokenizer prose); zero
  secret-shaped strings, zero credentials.
- Mission repo untouched: by code reasoning — the lint's only inputs are explicit
  PATH args / cwd walk / git-index blobs and it never writes outside stdout; T5 ran
  read-only — plus `git status --short` in this worktree is clean, so the QA
  staged-index probe was fully restored. (Mission-repo shell access is denied from
  this audit seat; the no-write-path conclusion rests on the full code read above.
  No code path in this diff can write outside the repo it runs in.)

## 7. Numbered deviations — all legitimate, none findings-grade

- **24-vs-23**: brief acceptance line says 23/0; tree reports 24/0. tasks.md T3
  ("plus one new named check, all passing") + REQ-C4 mandate the additive gate, so
  24/0 with byte-identical V1–V7 is the correct reading; "23" is the stale
  no-regression baseline (proposal text predates the #43 bump). LEGITIMATE.
- **Report filename**: tasks.md T6 names `remediate-40-…-implementation.md`; file
  lives at the lane-mandated `wave-40-…-implementation.md` with all T6 content
  (files changed, verification outputs). Convention-compliant; content complete. NOTE only.
- **AGENTS.md "expect: 23 checks" staleness**: post-stage truth is 24. Updating it was
  outside the stage's touch-only scope and risks churn with concurrent waves; correctly
  left stale here. Advisory for a follow-up sweep, NOT a finding — no deliverable in
  tasks.md or the spec requires it, and the severity rule reserves FAIL for stubs,
  vacuous checks, failing commands, or missing deliverables.

Auditor advisories (non-blocking, future hardening): `pnpm exec <bin>` and bare-package
tsconfig `extends` resolve conservatively toward the tsc/manager gates (both disclosed
in the implementation report); `$VAR`-head segments are skipped as unknowable offline
(disclosed); a `run:` step opening with a bare shell keyword (`set -e`) would be
flagged — none exists on the live surface (T5 42/0 proves it). None violate any
spec clause on the Wave-2 surface.

Report path: `docs/reports/wave-40-manifest-closure-verification.md` (uncommitted, per order).

VERDICT: PASS
