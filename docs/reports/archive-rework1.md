# archive-waves rework cycle 1 — implementation report (agency-programmer)

- Stage/wave: archive-waves rework cycle 1 (post-PASS review findings; cycle 1 of 3).
- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/archive-wave`
  (branch `feat/archive-waves`, tree was clean at start).
- Date: 2026-10-28. Author: agency-programmer (Muse Spark 1.3 Contributor).
- Disposition: **dirty, uncommitted** — left for coordinator commit. No commit made.
- Note on editing archived copies: the archive PR is **unmerged**, so the
  archived record is not sealed; the coordinator instruction explicitly permits
  editing the archived copies here. All archived-copy edits below mirror the
  live-copy edits byte-identically (requirement bodies only).

## Rule compliance

- No renumber/reword of V1–V27; SUMMARY frozen (verify confirms 35/0).
- `yaml.safe_dump` never used; `specs/` `rigs/` `rosters/` `registry/` untouched
  (all edits are `openspec/`, `tests/`, `docs/reports/`, plus one staged
  `git mv` restore).
- No secrets touched. `one-rule` / `safe_load` / secrets rules observed.

## Per-finding verdicts (all six verified against disk, all fixed)

### F1 — VALID, fixed (plus `!`-negation, recorded)
`openspec/changes/archive/2026-10-28-102-closeout/tasks.md:25` used literal
`AND`. Fixed to `&&` — but plain `&& grep -rn … (expect 0)` can never exit 0
because grep exits 1 on zero matches (demonstrated: verify green yet compound
`EXIT=1`). Acceptance therefore uses `&& ! grep -rn …`, the correct shell idiom
for "expect 0". Proven end-to-end exit 0:
`./scripts/verify-rigs.sh --check-only && ! grep -rn
'superpowers:writing-skills' specs/ fleet/` → `F1-FIXED-COMPOUND-EXIT=0`
(verify `VERIFY_EXIT=0`, `SUMMARY: 35 checks passed, 0 failed`).
Also fixed the same file's T0 paths (lines 3–4, `openspec/changes/102-closeout/…`
→ `openspec/changes/archive/2026-10-28-102-closeout/…`): the pre-archive dir
does not exist (`ls` → No such file), the archived paths list clean
(`T0-102-OK`). Same stale-path class as F2b, fixed minimally and recorded here.

### F2a — VALID, fixed, proven exit 0
`openspec/changes/archive/2026-10-28-107-identity/tasks.md:25` used literal
`AND`. Fixed to `&&`. Plain `&&` suffices here because `grep -c 401 …` exits 0
when matches exist. Proven: `./scripts/verify-rigs.sh --check-only && grep -c
401 docs/evidence/107-identity/red-proofs.log` → prints `9`,
`F2A-FIXED-COMPOUND-EXIT=0`.

### F2b — VALID, fixed, proven with ls
Same file lines 3–4 referenced pre-archive `openspec/changes/107-identity/…`.
Verified stale: `ls openspec/changes/107-identity/` → No such file or
directory; archived locations exist. Fixed to
`openspec/changes/archive/2026-10-28-107-identity/…`; both acceptance `ls`
commands exit 0 (`T0-107-OK`, plus `T0-102-OK` for the F1-adjacent fix).

### F3 — VALID, fixed via `git mv` restore
Verified (a): the ledger **was** moved — `docs/sprints/` does not exist,
`archive/2026-10-28-overhaul/docs/sprints/CLI-0.7.4-BUMP.md` existed.
Verified (b): it is **live-referenced** — `openspec/specs/bump/spec.md:15`
(REQ-BUMP) MUSTs the ledger at the live path `docs/sprints/CLI-0.7.4-BUMP.md`
and its scenario asserts that live path's contents; this is a live requirement,
not a historical mention (the 0.7.2/PI-1.4.0 cites in
`docs/TECHNICAL_DOCUMENTATION.md:12` are historical prose and were left alone).
Restored: `git mv
archive/2026-10-28-overhaul/docs/sprints/CLI-0.7.4-BUMP.md
docs/sprints/CLI-0.7.4-BUMP.md` (staged rename, history preserved). Restored
file satisfies the scenario (version string ×19, tarball sha ×1, `35 checks
passed` ×1). REQ-C6 keep-list updated in **both** copies
(`openspec/specs/archive/spec.md:15`,
`openspec/changes/archive/2026-10-28-overhaul-c/specs/archive/spec.md`) to
exclude the ledger from the `docs/sprints/` move; correction note appended to
`docs/reports/overhaul-c-implementation.md` (record-preserving, not rewritten).

### F4a — VALID, fixed in both copies identically
Grant mapping verified against `fleet/fleet.yaml` (every seat: `bash_allow`
carries `rig queue *` + `rig send *` adjacent — e.g. lines 648–649 — with
`bash_deny` exactly the bare triple `rig queue list` / `rig queue create` /
`rig send` after all allows, e.g. lines 657–660) and a rendered seat map
(`rigs/cloud-sre-and-data-platform/agents/analytics-metrics-eng/runtime/pi-permission-config.json`:
`'rig queue *' → allow`, `'rig send *' → allow`, bare triple → deny).
The V22 gate (`scripts/verify-rigs.sh:2726–2740`) confirms the semantics:
`--json` queue forms + addressed send allow, bare triple denies. REQ-C18 now
states the mapping separately in **both** copies
(`openspec/specs/closeout/spec.md:15`,
`openspec/changes/archive/2026-10-28-102-closeout/specs/closeout/spec.md:6`);
bare-form denials kept verbatim. No deviation from the finding was needed.

### F4b — VALID, fixed in both copies identically (bounds trust-but-verified)
Measured current bounds (no trust): bundle-check loop opens at line 2447
(`for _slug18 in EXPECTED_8_RIGS:`) and its block closes at 2469 (trailing
`fail(…)` paren); spec-validate loop opens at 2470 (`for _spec18 in …`) and
closes at 2482. The finding's proposed `:2447-2469` / `:2470-2482` match
exactly. REQ-C25 citations updated to those ranges in **both** copies; the
canonical/intentional statement is otherwise byte-identical.

### F5 — VALID, fixed red-first (test added, spec aligned)
Verified the gap: `tests/test_schema_contracts.py` only asserted pin-file vs
disk consistency (`test_pin_file_matches_disk`, lines 57–70) — refreshable
together with the schema — plus upstream `$id`/shape checks; **no** committed
check pinned the fixed digest `b3c7ac64…`. V18's byte-compare against the
installed CLI is skipped with NOTE when `rig` is absent, so it is not a
committed fixed-identity pin either. Red-first: added
`test_run_record_pins_fixed_074_digest` (sha256 of the vendored file equals the
fixed digest), corrupted one byte → `FAILED (failures=1)` (RED), restored from
`/tmp` backup → `OK` (GREEN); `sha256sum` confirms `b3c7ac64…` and `git diff`
on the schema file is empty. Spec sentence updated minimally in **both**
copies (`openspec/specs/contracts/spec.md:15` + overhaul-b archived delta) to
describe the fixed-digest pin test.

### F6 — VALID, fixed in both copies identically
Verified the workflow: `.github/workflows/docker-release.yml` contains exactly
**one** `container:` block (line 113, smoke job); `verify-fleet` (lines 48–60)
and `build` (62–102) define none. The old "exactly one `container:` block per
job" text was over-strict vs reality. REQ-A3 now says "at most one
`container:` block per job (today only the smoke job defines one; verify-fleet
and build define none)" in **both** copies
(`openspec/specs/p0/spec.md:33` + overhaul-a archived delta); duplicate-key
parse + bubblewrap requirements preserved verbatim.

## Files changed (working tree, uncommitted — coordinator to commit)

- `openspec/changes/archive/2026-10-28-102-closeout/tasks.md` (F1 + T0 paths)
- `openspec/changes/archive/2026-10-28-107-identity/tasks.md` (F2a + F2b)
- `openspec/specs/archive/spec.md` + archived overhaul-c delta copy (F3 keep-list)
- `openspec/specs/closeout/spec.md` + archived 102-closeout delta copy (F4a, F4b)
- `openspec/specs/contracts/spec.md` + archived overhaul-b delta copy (F5 spec)
- `openspec/specs/p0/spec.md` + archived overhaul-a delta copy (F6)
- `tests/test_schema_contracts.py` (F5 fixed-digest pin test)
- `docs/reports/overhaul-c-implementation.md` (F3 correction note, appended)
- Staged rename: `archive/2026-10-28-overhaul/docs/sprints/CLI-0.7.4-BUMP.md`
  → `docs/sprints/CLI-0.7.4-BUMP.md` (F3 restore; R100, history preserved)

## Proofs (exact commands, exit codes)

1. F1 compound: `./scripts/verify-rigs.sh --check-only && ! grep -rn
   'superpowers:writing-skills' specs/ fleet/` → exit 0 (`F1-FIXED-COMPOUND-EXIT=0`).
2. F2a compound: `./scripts/verify-rigs.sh --check-only && grep -c 401
   docs/evidence/107-identity/red-proofs.log` → `9`, exit 0.
3. F2b/T0: both archived `ls` acceptance commands → exit 0.
4. F3: `grep -c` on restored ledger → `0.7.4` ×19, tarball sha ×1,
   `35 checks passed` ×1.
5. F5 red: byte-flip → `FAILED (failures=1)`; restore → `OK`, sha256 =
   `b3c7ac64…`, `git diff` on schema empty.
6. `make test` → `Ran 505 tests … OK`, exit 0 (run because a test file changed).
7. `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 35 checks passed,
   0 failed.`, exit 0 (V22–V27 green, V19 SUMMARY frozen).
8. `python3 ./scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`, exit 0.

## Self-audit notes

- Nothing skipped: every finding verified still-valid before fixing; no
  finding was dismissed.
- One deliberate extension beyond the letter of F1: the fixed F1 acceptance
  uses `&& ! grep` rather than bare `&& grep`, because bare grep can never
  exit 0 when zero hits are expected (proven `EXIT=1` on the green tree).
  Intent ("expect 0" + exit 0) preserved; reasoning above.
- One adjacent fix recorded under F1: 102-closeout T0 had the identical
  stale-path defect as F2b; fixed the same way.
- `schemas/run-record.v1.schema.json` was mutated only in-memory for the RED
  proof and restored byte-identical (no diff); backup at `/tmp/opencode/rr-backup.json`.
- No `generate-rigs.py` run needed (no generator inputs changed); regen-gate
  unaffected.
