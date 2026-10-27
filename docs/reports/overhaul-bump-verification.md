# overhaul-bump drift-guard verification (independent adversarial audit)

- **Stage/wave id:** overhaul-bump
- **Worktree:** `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/overhaul-bump`
- **Branch:** `feat/overhaul-bump` @ `a3e7fe4` (feat `57d5007` + test evidence `a3e7fe4`), base `main` `88cd930`
- **Date (UTC):** 2026-10-27
- **Auditor stance:** assumed broken/stubbed/descoped until disk evidence proved otherwise. No code fixed, nothing committed.
- **Spec read from disk:** `AGENTS.md`, `openspec/changes/overhaul-bump/{proposal.md,design.md,tasks.md,specs/bump/spec.md}` (REQ-BUMP1/BUMP2/G1), `docs/reports/overhaul-bump-implementation.md`, `docs/sprints/CLI-0.7.4-BUMP.md`, `docs/evidence/overhaul-bump/red-proofs.log`.

## 1. REQ-BUMP1 — pinned 0.7.4 toolchain with ledger: HOLD

- `rig --version` re-run live by auditor → `0.7.4 (6d9e8e27)`, exit 0. Matches spec scenario and ledger §1/§4.
- Ledger `docs/sprints/CLI-0.7.4-BUMP.md` contains: version string `0.7.4 (6d9e8e27)` (§1, §4), tarball sha256 `d11dd8a6fc78f0c4d7afeae462c07c2af0fb9fe460990950be495016734920a1` (§1; grep count 1, exact match to proposal/design/spec values), every pin location updated (§3 table), green verify output (§4: 35/0 + SELF-TEST PASSED).
- Pin-edit scope audit — full `git diff 88cd930..HEAD` for the 8 modified production files reviewed hunk-by-hunk; every hunk is a true version-pin assertion only, zero scope creep:
  - `AGENTS.md:4` stack line `0.7.2→0.7.4`; `Makefile:3` target-framework comment; `README.md:9,39,40` stack table + prereq/install lines; `docker/Dockerfile:16` `ARG OPENRIG_VERSION`; `docs/USER_GUIDE.md:3,14,21,24,25,473` toolchain assertions + install block + Docker table; `docs/TECHNICAL_DOCUMENTATION.md:4` framework header incl. commit `8b180689→6d9e8e27` (commit from live binary); `PROMPT_ADVERSARIAL_FLEET_AUDIT.md:5,16,40,70,167` stack/tool references; `scripts/verify-rigs.sh:1838-1839` V13 assert/message + `:2463` V18 info string (status text only, no gate logic).
- Deferred locations (generator inputs, pinned-schema provenance, vendored-byte prose, dated records) correctly untouched per design §"Change shape" step 3 and ledger §3 not-changed list.

## 2. REQ-BUMP2 — green tree, SUMMARY frozen, no renumber: HOLD

- `./scripts/verify-rigs.sh --check-only` re-run by auditor → `SUMMARY: 35 checks passed, 0 failed.` V22/V23/V24 info lines present (V22 bare queue/send deny FAIL-ONLY, V23 seat-grant catalog FAIL-ONLY, V24 runbook --rig mandate FAIL-ONLY).
- `python3 scripts/audit_loop.py --self-test` re-run → `SELF-TEST PASSED`, exit 0.
- No renumber/reword: `git diff 88cd930..HEAD -- scripts/verify-rigs.sh` touches zero `== V…` header lines; the only V-matching changed lines are the V13 fail-string pair (`0.7.2→0.7.4`) and the V18 ok-message. All 22 `== V` headers intact, V1–V24 names/numbers unchanged. SUMMARY format line untouched.
- Accepted non-run (not a finding): `generate-rigs.py --check-idempotent` deliberately NOT executed. Justification verified on disk: no generator input changed (`git diff 88cd930..HEAD` over `specs rigs rosters registry fleet/skills-lock.json schemas fleet/fleet.yaml fleet/mcp-servers.yaml scripts/generate-rigs.py` is byte-empty — see §3), so no regen is owed; running it would resolve `openrig-core` from the now-0.7.4 global install (`generate-rigs.py:623-643`) and vendor Wave B contract content. Idempotence holds vacuously, proven by the empty leaf diff rather than asserted.

## 3. REQ-G1 — append-only, generator rule: HOLD

- `git diff 88cd930..HEAD -- specs rigs rosters registry` → **empty, exit 0** (`--name-only` likewise empty). A pure pin bump changed no generator inputs; zero generated-leaf drift. No hand-edit of leaves. No new V-gates added, none renamed.

## 4. Canary failure correctly attributed pre-existing, correctly NOT fixed: HOLD

- `git diff 88cd930 HEAD -- fleet/fleet.yaml tests/test_build_canary.py | wc -c` → `0`. This wave touches neither the test's input file nor the test. Untouched input ⇒ byte-identical outcome on clean `main` `88cd930`.
- `git log --oneline -S 'bash_deny' -- fleet/fleet.yaml` → exactly one commit: `892e1a7 feat(102-closeout): implement stage requirements` (the 102-closeout HR-F18 triple), consistent with the logged cause. Not this wave.
- Single-test re-run by auditor (`python3 -m pytest tests/test_build_canary.py::CanaryCatalogPins::test_canary_scope_only`): FAILED as expected with the **identical** signature to `red-proofs.log` §4 — `AssertionError: Lists differ` at `tests/test_build_canary.py:181`, first differing element `a11y-specialist` vs `ai-red-teamer`, `First list contains 44 additional elements`, first extra `brand-copy-spec`, diff 1304 chars. No fix applied here (Wave B M5 owns the rework) — correct per design fail-closed rule.

## 5. No stubs / no secrets: HOLD

- Anti-stub scan over the full `git diff 88cd930..HEAD`: zero added `TODO`/`FIXME`/`NotImplemented`/`|| true`/skip sentinels. The only grep hits are pre-existing context lines (`STATUS:` sentinel doc in PROMPT, `Handoff:` prose in the implementation report) — no executable stub content added.
- Secret scan over the diff: zero hits (`ghp_`, private-key headers, API-key shapes).
- Ledger + implementation report carry only version + sha256 + verify outputs; the single token mention is first/last-2 redacted scratch-token prose (`or…2A`), mode-600 scratch files under `/tmp` only, never committed. Real `~/.openrig` untouched per ledger §4/M0 notes.

## 6. Red-proof evidence audit: HOLD

- `docs/evidence/overhaul-bump/red-proofs.log` records: green baseline (rig version, 35/0, SELF-TEST, make verify); ledger-claim verification (version MATCH, SHA independent re-pack MATCH, pin-line spot checks, verify-output MATCH); RED sabotage #1 (Dockerfile `0.7.4→0.7.2` ⇒ verify exit 1 with `[FAIL] V13/#100` + cascading V19 stale-count guard, `33 passed, 4 failed`; `git checkout --` restore ⇒ exit 0, 35/0; `git status --short` clean). Failure signature is non-vacuous (named gate + cascade, not exit-code-only).
- `make test` 359/1 result logged (2× foreground runs) with the single failure named; auditor re-ran the failing test in isolation and reproduced the identical signature (§4). Full suite not re-run per stage orders (already run 3× with the same 359/1 pre-existing outcome).
- `git status --short` at audit time: clean (all work committed in `57d5007` + `a3e7fe4`).

## Findings

None. All three requirements hold on disk; the canary RED is pre-existing, attributed, and correctly left for Wave B; no stubs, no secrets, no leaf drift, no gate renumber.

VERDICT: PASS
