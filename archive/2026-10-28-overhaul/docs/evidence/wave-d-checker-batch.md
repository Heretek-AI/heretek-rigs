# Evidence: checker-batch-d T2 red-proofs (QA)

- Stage/wave: checker-batch-d T2 (red-proofs only; drift-guard T3 follows)
- Worktree: `.lane/trees/checker-batch-d`, branch `feat/checker-batch-d`
- Base commit at QA start: `0fd8ea5` (after T1 `771d0b3` + addendum)
- Date (UTC): 2026-10-25
- QA agent: Wave D checker-batch T2 (red-proof sabotage per `red-proof-sabotage` skill, 7-step protocol)

## 1. Baseline acceptance (unmodified tree, all green)

| Command | Result |
|---|---|
| `make verify` | rc=0, `SUMMARY: 35 checks passed, 0 failed` (live-health daemon SKIPs only, by design) |
| `./scripts/verify-rigs.sh --check-only` | rc=0, `SUMMARY: 35 checks passed, 0 failed` |
| `python3 -m pytest tests/test_manifest_closure.py tests/test_policy_verifier.py tests/test_schema_contracts.py` | rc=0, **91 passed** (44 + 42 + 5) |

Canary spot-check (no full re-prove, per task): `tests/test_build_canary.py` is
**unmodified vs base `b9008b4`** (`git diff --name-only b9008b4..HEAD` shows only
`test_manifest_closure.py`, `test_policy_verifier.py`, `test_schema_contracts.py`
under `tests/`; canary file last touched `bd05c65`, pre-base). Zero diff overlap
with this stage — the 12 pre-existing mock-harness deny failures are carried as
pre-existing, unchanged.

## 2. Sabotage log (each: inject → RED with non-zero exit → `git checkout` revert → GREEN)

All sabotages were temporary, reverted with `git checkout -- <file>`, and
`git status --short` confirmed clean after every revert (empty output each time).

### S1 — reintroduced `$`-skip (REQ-D94, checker-side)
- Target: `scripts/manifest-closure.py` `check_script_body` — replaced the
  `$`-leading NEEDS-DECLARATION note block with a bare `continue`
  (`# SABOTAGE-T2S1: reintroduced pre-D94 $-skip`).
- RED: `pytest tests/test_manifest_closure.py -k dollar` → **rc=1, 4 failed**
  (`test_dollar_substitution_needs_declaration`,
  `test_dollar_brace_expansion_needs_declaration`,
  `test_dollar_variable_head_needs_declaration`,
  `test_dollar_run_step_needs_declaration`), 40 deselected.
- Revert: `git checkout -- scripts/manifest-closure.py`, status clean.
- GREEN: full `test_manifest_closure.py` → **44 passed, rc=0**.

### S2 — reintroduced inline-table TOML bypass (REQ-D95, checker-side)
- Target: `scripts/policy-verifier.py` `scan_lint_entries` — replaced the
  `_search_lineno` attribution fallback with `continue`
  (`# SABOTAGE-T2S2: line-scan authoritative again`), i.e. entries with no
  line-scan anchor (inline-table values, header-less dotted keys) are dropped —
  the exact pre-D95 bypass semantics.
- RED: `pytest tests/test_policy_verifier.py -k "inline or dotted"` → **rc=1,
  4 failed** (`test_inline_table_lints_value_fires`,
  `test_inline_table_under_header_fires`,
  `test_top_level_dotted_plain_lints_fires`,
  `test_top_level_dotted_workspace_lints_fires`); header-spelled tests still
  passed (targeted, as designed).
- Revert: `git checkout -- scripts/policy-verifier.py`, status clean.
- GREEN: full `test_policy_verifier.py` → **42 passed, rc=0**.

### S3 — mutated status.json (REQ-D98, artifact-side)
- Target: `registry/status.json` — dropped the `bodyDigest` key (the issue's
  mutation proof), written back as JSON.
- RED: `pytest tests/test_schema_contracts.py` → **rc=1, 1 failed**
  (`test_committed_status_validates_clean`); the two red-direction mutation
  tests still passed (they mutate their own copies).
- Revert: `git checkout -- registry/status.json`, status clean.
- GREEN: `test_schema_contracts.py` → **5 passed, rc=0**.

### S4 — broken frontmatter (REQ-D101, artifact-side)
- Target: `specs/agents/_shared/skills/nextjs-dev/SKILL.md` — inserted an
  unquoted-`: ` line (`description: Use when building: unquoted colon breakage`)
  into the `---` frontmatter (faithful recurrence of the #101 breakage).
- RED: `./scripts/verify-rigs.sh --check-only` → **rc=1,
  `SUMMARY: 30 checks passed, 5 failed`**, including the named
  `[FAIL] V17/#101: .../nextjs-dev/SKILL.md frontmatter unparseable: mapping
  values are not allowed here`, plus the fail-closed cascade (skills tree-hash
  gate + 3× V19 live-count, since live passes dropped 35→30 while docs state
  35 — the interlock working as designed).
- Revert: `git checkout -- specs/agents/_shared/skills/nextjs-dev/SKILL.md`,
  status clean.
- GREEN: full `--check-only` → **35 passed, 0 failed, rc=0**.

### S5 — stale count string (REQ-D102, artifact-side)
- Target: `README.md` — appended a line containing `31 checks passed`
  (`# SABOTAGE-T2S5`); the live `35 checks passed` statement was left intact.
- RED: `./scripts/verify-rigs.sh --check-only` → **rc=1,
  `SUMMARY: 34 checks passed, 1 failed`**, exactly
  `[FAIL] V19/#102: README.md carries stale string '31 checks passed'
  (refresh through the proper source)` — surgical, no cascade.
- Revert: `git checkout -- README.md`, status clean.
- GREEN: full `--check-only` → **35 passed, 0 failed, rc=0**.

No vacuous checks: every sabotaged form failed visibly (non-zero exit) and every
revert restored green. `CRITICAL: Vacuous acceptance check` — none.

## 3. UNVERIFIED items (carried, with disposition)

- **Loader 68/68 host run (REQ-D101 red-proof): UNVERIFIED.** Daemon probe at
  QA time: `rig queue list --json -A --limit 1` → `Error: Daemon not running`
  (rc=1); `rig daemon status` → `Daemon PID is absent (stale state)`. Starting
  a daemon / `rig up`ing a live fleet is out of T2 scope (live side effects).
  Static proxy stands in: V17 parses all 130 committed SKILL.md leaves with
  `yaml.safe_load` + `name == dirname`, green (proven non-vacuous by S4 above).
- **V13 `[:300]` truncation quirk: pre-existing, observed only, out of scope**
  (REQ-G1 append-only). Carried from T1; untouched by this stage.
- **D98 vendor deviation: recorded design deviation, not a gap.** The 0.6.13
  tarball ships no schema files, so byte-exact vendoring was impossible without
  false provenance; satisfied via the spec's own alternative (native verbs
  `rig bundle check` ×8 + `rig spec validate` ×9 on installed 0.6.13) + the
  `schemas/contract-schemas.sha256` local freeze pin. V18 green; S3 proves the
  mutation red-proof both directions (inline + corpus).
- **Canary 12/11 failures: pre-existing, no diff overlap** (see §1). Not re-run.

## 4. Final state

- `git status --short`: clean except this evidence file (staged/committed per §5).
- End-state green re-confirmed after all reverts: `--check-only` 35/0 (S4, S5
  restores) + focused corpus greens (S1 44/44, S2 42/42, S3 5/5).

## 5. Evidence commit

- File: `docs/evidence/wave-d-checker-batch.md` (this file)
- Commit: TBD by QA agent (explicit staging; see QA report to coordinator)
