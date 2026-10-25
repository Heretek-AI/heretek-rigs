# Stage report: checker-batch-d T1 (implement)

- Stage/wave id: checker-batch-d (T1 implement only; QA T2 + drift-guard T3 follow)
- Branch: feat/checker-batch-d (worktree `.lane/trees/checker-batch-d`, base b9008b4)
- Date (UTC): 2026-10-25
- Acceptance command: `make verify` — rc=0, `SUMMARY: 35 checks passed, 0 failed`
  (verify-rigs.sh) + live-health advisory SKIPs (no daemon, by design).
  Trust-live-SUMMARY: baseline run said 32; +V17/V18/V19 = 35; docs state 35.

## Deliverables (per REQ-D94/D95/D98/D101/D102/G1)

- REQ-D94 (`scripts/manifest-closure.py`): `$`-words (`$(...)`, `${...}`,
  `$VAR`) report NEEDS-DECLARATION, never skipped (only `${{ }}` GH
  expressions still skip); `node`/`npx` argv resolved (`node_modules/.bin/`
  targets checked, `node -e` fails, `npx <bin>` resolves via aliases);
  `python -c` fails named; `git -c alias.*=!` shell-out fails named while
  plain `git` probes stay green; `.gitlab-ci.yml` (`script:` string/list,
  hooks, `default:`) + `.circleci/` + `pipelines/` discovery; CircleCI
  dict-form `run: {command:}` collected. Corpus: 16 new tests.
- REQ-D95 (`scripts/policy-verifier.py`): `tomllib` structural walk of
  `lints`/`workspace.lints` is authoritative (header-less dotted keys,
  inline-table values); line-scan retained for attribution (+ name-search
  fallback); `[lints] workspace = true` correctly skipped. Pin derives
  from repo-root `rust-toolchain.toml` (`channel = "1.89.0"`, fail-closed
  when absent); snapshot `pin:` = 1.89.0; legacy `toolchain-pin` kept as a
  mirror (V9 passes it explicitly; agreement enforced by test). Corpus:
  8 new tests; live `live-corrected-lints.toml` stays green.
- REQ-D98: upstream 0.6.13 tarball ships NO schema files (verified on the
  installed package) so vendoring would be false provenance; authority is
  the installed CLI's native verbs (`rig bundle check` x8 + `rig spec
  validate` x9, `rig agent validate` excluded — needs a daemon).
  `schemas/contract-schemas.sha256` freezes the 6 locals; V18 runs
  `tests/test_schema_contracts.py` (5 tests, mutation red-proof both
  directions) + inline red-proof + pin re-check.
- REQ-D101: NEW fleet-side patch mechanism (`fleet/skill-patches/<id>.yaml`
  frontmatter repairs applied by `generate-rigs.py` post-vendor, re-parsed,
  `name == id` enforced, unknown targets die). `nextjs-dev` description
  quoted + `react-best-practices` name aligned (the latter found BY the new
  V17 gate on first regen) — both via patch + regen, zero specs/ hand-edits.
  V17 parses EVERY committed SKILL.md (68 shared + role-local, 130 files)
  with `yaml.safe_load` and requires `name == dirname`.
- REQ-D102: V19 canonical guard asserts live docs state the LIVE summary
  (self-including `passes+1`) and trips on stale `31 checks` / `64 ...skills`
  / `0.6.11` strings in live files (history excluded by design). Drift
  corrected through proper sources: audit prompt (68 skills, 12 core SOP
  skills, 0.6.13), tech docs (68 = 12+56), generator comments, README /
  USER_GUIDE / AGENTS.md (35). Historical logs/briefs/snapshots untouched.
- REQ-G1: all new coverage appended (V17/V18/V19, one ok() each); no
  existing check renumbered/reworded (V13 truncation quirk observed, left
  alone — out of wave scope). specs/rigs/rosters/registry changed ONLY via
  regen. #96 untouched (no refresh-policy-only, no drift alert).

## Files changed (sources; +169 regen leaves)

Sources: AGENTS.md, Makefile (+test_schema_contracts to `test` target),
PROMPT_ADVERSARIAL_FLEET_AUDIT.md, README.md,
docs/TECHNICAL_DOCUMENTATION.md, docs/USER_GUIDE.md,
fleet/skill-patches/nextjs-dev.yaml (new),
fleet/skill-patches/react-best-practices.yaml (new),
rust-toolchain.toml (new), schemas/contract-schemas.sha256 (new),
scripts/generate-rigs.py, scripts/manifest-closure.py,
scripts/policy-verifier.known-lints.txt, scripts/policy-verifier.py,
scripts/policy-verifier.toolchain-pin, scripts/verify-rigs.sh (V17/V18/V19),
tests/test_manifest_closure.py, tests/test_policy_verifier.py,
tests/test_schema_contracts.py (new).
Generated (regen e52f2f0): 169 files under specs/ rigs/ registry/ rosters/
+ fleet/skills-lock.json (incl. expected `enabled:false` bake-in from the
V16 renderer on first regen with this host's tool poverty — pre-existing
behavior, verify-green; and bd6ed99 40-hex provenance, accepted re-lag).

## Exact commands run (exit codes)

- `./scripts/verify-rigs.sh --check-only` (baseline) → 0 (32 passed)
- `python3 -m unittest tests.test_manifest_closure` → 0 (44 tests)
- `python3 -m unittest tests.test_policy_verifier` → 0 (42 tests)
- `python3 -m unittest tests.test_schema_contracts` → 0 (5 tests)
- `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py
  --vendor-dir <main-.scratch/vendor>` (dev regen) → 0
- `python3 ./scripts/generate-rigs.py --vendor-dir ...` (clean, x2) → 0
- `python3 ./scripts/generate-rigs.py --check-idempotent --vendor-dir ...` → 0
- `python3 ./scripts/audit_loop.py --self-test` → 0
- `make test` → 1 (313 tests, 12 failures — ALL pre-existing
  test_build_canary mock-harness deny cases; zero overlap with this diff)
- `make verify` → 0 (35 checks passed; live-health daemon SKIPs only)
- `make verify` (2 later retries) → 2 (V13/#70 skopeo Docker-Hub
  `toomanyrequests` rate limit; keyword falls past the pre-existing
  `[:300]` error window → hard FAIL instead of offline NOTE; cascade trips
  V19 count. Environmental + pre-existing truncation, out of scope.
  Tree unchanged since the green run; NOT re-run to avoid burning quota.)

## Commits (feat/checker-batch-d, no push, no --force)

- abbc246 feat(checker-batch-d): sources (D94/D95/D98/D101-mechanism/D102/V17-19)
- 9e80a37 feat(checker-batch-d): react-best-practices fleet patch (V17 finding)
- bd6ed99 fix(checker-batch-d): V19 self-inclusion (passes+1)
- e52f2f0 feat(checker-batch-d): clean regen (leaves only)

## Self-audit notes (unfinished / unverified, stated plainly)

- UNVERIFIED: second green `make verify` after e52f2f0 blocked by Docker-Hub
  rate limiting (see above). Current tree is byte-identical to the committed
  state modulo nothing (clean); the green 35/35 run covered these bytes
  except resolvedCommit re-lag (bd6ed99, 40-hex, gate-accepted).
- UNVERIFIED: loader 68/68 host run (pi 1.3.0 needs daemon/live seats —
  for QA T2; V17 parse gate is the static proxy and is green on 130 files).
- Pre-existing, unchanged: test_build_canary 12/12 deny-case failures
  (mock-harness behavioral; brief's "canary 12/11" note).
- Pre-existing, observed only: V13 `[:300]` truncation vs long digest-ref
  error strings (rate-limit keyword cut → FAIL not NOTE). Out of wave scope
  (REQ-G1); flagged for a future wave, not touched here.
- Design deviation recorded honestly: D98 "vendor 5 upstream schemas" was
  impossible (0.6.13 tarball ships none; 0.6.11-era copies would be false
  provenance) — satisfied via the spec's own alternative (validate against
  installed copies via native verbs) + local freeze pin. Upstream
  `docs/reference/schemas` (0.6.11 checkout) deliberately NOT vendored.
