# Delta spec: checker-batch-d

## ADDED Requirements

### REQ-D94: manifest-closure evasions
`scripts/manifest-closure.py` MUST report NEEDS-DECLARATION (never skip) for `$`-leading command words (`$(...)`, `${...}`, `run: $(...)`); MUST resolve `node <path>` through `node_modules/.bin/` and `npx <x>`; MUST flag `node -e` / `python -c` / `git -c alias.*=!` exec forms; MUST discover `.gitlab-ci.yml` and other CI files beyond `.github/workflows`. Corpus `tests/test_manifest_closure.py` MUST cover each form failing-first.

### REQ-D95: TOML structural walk + derived pin
`scripts/policy-verifier.py` MUST walk `tomllib`-parsed `lints` and `workspace.lints` structurally (recursing into inline tables) for lint entries; the text line-scan MUST be retained for `file:line` attribution only. The toolchain pin MUST derive from `rust-toolchain.toml` (fail-closed when offline/toolchain absent); lint names MUST validate against the toolchain lint list. Corpus MUST cover top-level dotted keys, inline-table values, and fake-lint naming.

### REQ-D98: vendored upstream schemas
The 5 upstream `@openrig/cli@0.6.13` reference schemas MUST be vendored byte-exact with a sha256 pin (rigspec 3-copy-pin precedent); verify MUST `cmp` them against the installed package's schemas (or validate artifacts against the installed copies). A mutated `status.json` MUST fail local validation (red-proof).

### REQ-D101: frontmatter parse + name==dirname
Verify MUST `yaml.safe_load`-parse every `SKILL.md` frontmatter (invalid YAML fails) and MUST require `name == dirname`. The nextjs-dev description fix MUST ride the vendor/patch path + `generate-rigs.py` regen, never a hand-edit of `specs/`. Red-proof MUST record loader 68/68 with no DIAG (pi 1.3.0 host run) or mark host-run unverified.

### REQ-D102: canonical stale-count guard
A new appended verify block MUST assert live documented counts equal the live `SUMMARY` (stale-string tripwire and/or SUMMARY-vs-doc equality), failing on drift. Drift corrections (skills 64→68, counts, 0.6.11 pin) MUST go through proper sources.

## MODIFIED Requirements

### REQ-G1: append-only, generator rule
New coverage MUST be new appended blocks (or new scripts), never renumber/reword of existing checks. `specs/` `rigs/` `rosters/` `registry/` MUST change only via generator (`generate-rigs.py`); the #101 one-line patch MUST use the vendor/patch mechanism.

### REQ-D96-DEFER: hot-reload out of scope
#96 is EXCLUDED from this change (no checker to extend; verification needs a live fleet; contradicts #11 bounce semantics — needs the live-seat decision round). No `--refresh-policy-only`, no health drift alert here.
