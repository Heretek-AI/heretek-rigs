# Proposal: checker-batch-d — close checker evasion gaps + canonical drift guard

Status: scope approved (HANDOFF Wave D + operator "Wave D checker batch", 2026-10-24).
Issues: #94 #95 #98 #101 (code fixes), #102 (guard + docs). #96 DEFERRED (see design.md — contradicts #11 bounce semantics, needs live-seat decision round, no checker to extend).

## Root cause (verified read-only 2026-10-24, Wave D recon)

- #94: `scripts/manifest-closure.py:277` `$`-skip abandons segments (`$(command -v eslint)`, `${VAR:-x}`, `run: $(which vitest)` → exit 0); `node`/`git` allowlist hits (`allowed-system-tools.txt:19,23`) skip argv inspection (`node node_modules/.bin/eslint`, `node -e`, `git -c alias.f='!...'` → exit 0); `.gitlab-ci.yml` never scanned (`:579-592` keeps `.github` only). Corpus `tests/test_manifest_closure.py` has zero hits for any form.
- #95: `scripts/policy-verifier.py:298-351` line-scan skips top-level dotted keys (`current is None`) and never descends inline-table values (`lints = { clippy = {...} }` → exit 0, hiding fake lints); pin gate `:951-960` compares two hand-kept files (`fixture-toolchain-1`, self-declared hand-maintained).
- #98: `schemas/*.v1.schema.json` (6 files) hand-made, verify enforces the loose locals (`verify-rigs.sh:875-893`); no byte-exact vendor pin like the rigspec 3-copy pin (`:148-207`); 0.6.13 native verbs (`rig bundle check`, `rig spec validate`) unused.
- #101: `specs/agents/_shared/skills/nextjs-dev/SKILL.md:3` unquoted `: ` breaks `yaml.safe_load`; gate `:290` is substring-only (passes broken file); loader loads 67 not 68. Fix MUST ride vendor/patch path + regen, never hand-edit `specs/` (AGENTS.md one rule).
- #102: 64-vs-68 skills drift (audit prompt pins 0.6.11, claims 64/`[]`; verify enforces 68) + stale counts (live docs fixed to 31 in Wave B; main may read 32 post-V16 — trust the run). Canonical stale-count guard explicitly deferred to Wave D by residuals-107 REQ-R2.

## Change (checker + corpus + red-proof each; new appended blocks; never renumber)

- #94: `$`-leading words → NEEDS-DECLARATION; resolve `node <path>`/`npx <x>`; flag `node -e`/`python -c`/`git -c alias.*=!`; scan `.gitlab-ci.yml` + CI files. Corpus per-form tests.
- #95: `tomllib` structural walk of `lints`/`workspace.lints` (recurse inline tables); line-scan kept for attribution only; pin derived from `rust-toolchain.toml` (fail-closed offline). Corpus: all spellings + fake lint.
- #98: vendor 5 upstream schemas byte-exact with sha256 pin; verify `cmp`s against installed package (or validates against them); mutation red-proof. New block.
- #101: frontmatter `yaml.safe_load` parse for every SKILL.md + `name == dirname`; description fix via vendor/patch + regen.
- #102: canonical stale-count guard (docs == live SUMMARY) as new block + drift corrections through proper sources.

## Acceptance

1. Each evasion/spelling/mutation/broken-frontmatter form fails loudly (exit 1 / named FAIL) with red-proofs both directions on disk.
2. `make verify` green (blocks appended, no renumber); full corpus green except known pre-existing canary 12/11.
3. Drift-guard `VERDICT: PASS` → PR (Refs #94 #95 #98 #101 #102; closes only what is fully fixed).
