# Implementation report: remediate-43-regen-gate (stage wave-43-regen-gate)

Stage: `wave-43-regen-gate` · Change-id: `remediate-43-remediate-43-regen-gate`
Issue: Heretek-AI/heretek-rigs#43 (regen clean-tree gate vs evidence-logging workflow)
Branch: `remediate/43-regen-gate` · Base: `origin/main @ 00acda2`

## Deliverables (tasks.md T1–T6)

- **T1 — Classified dirt check (REQ-RG1/RG2):** `SANCTIONED_UNTRACKED_DIRS`
  (7 prefix entries) + `SANCTIONED_UNTRACKED_FILES` (2 exact entries) with
  per-entry justification comments, adjacent to `resolve_heretek_commit` in
  `scripts/generate-rigs.py`; `_is_sanctioned_untracked()` (fail-closed:
  exceptions/emptied source → not sanctioned) and `_split_porcelain()`
  (status-code-first: only `??` consults the allowlist; every other status
  and every unparseable line is blocking; C-quoted paths unquoted,
  unparseable quoting fails closed). Provenance still `git rev-parse HEAD`.
- **T2 — Classified refusal (REQ-RG3):** refusal prints blocking porcelain
  lines verbatim under `blocking changes:` plus ignored sanctioned paths
  under `ignored sanctioned strays (not dirt):`; remediation hint unchanged;
  happy path prints nothing (silent about dirt, as before).
- **T3 — V7 consistency check (REQ-RG4):** appended block at the end of
  `scripts/verify-rigs.sh` (one `ok()`, no existing check renumbered or
  reworded) asserting (a) every AGENTS.md blessed stray covered — strays read
  from the AGENTS.md bullet itself, not hardcoded; (b) each allowlist entry
  immediately preceded by a `#` justification comment in the generator
  source; (c) `tests/test_regen_gate.py` 8/8 green. AGENTS.md gate paragraph
  updated (classified-gate wording) and both `22` counts in AGENTS.md → `23`.
  `make test` extended with the new test file.
- **T4 — QA red-proofs:** (a) HANDOFF.md-style tracked edit refuses exit 2
  without override (unit test + live-tree equivalent by construction);
  (b) `HERETEK_RIGS_ALLOW_DIRTY=1` proceeds and records the real HEAD SHA
  (unit test, SHA asserted); (c) real regen on this stage worktree with
  session strays present (`docs/evidence/`, `docs/reports/`, `.opencode/`)
  and NO env override succeeded (`REGEN-OK`); regenerated leaves differed
  ONLY in baked `resolvedCommit`/`canonicalUrl` (old `bae5d3a…` → new HEAD),
  then reverted to keep the change surgical.
- **T5 — Acceptance:** returnable proven (T4c); `make verify` green at the
  new count (23/0 + live-health advisory, exit 0); `openspec validate
  remediate-43-regen-gate` → valid.
- **T6 — This report** (+ the `wave-43-regen-gate-implementation.md` twin
  required by the stage instructions; identical content).

## Allowlist source choice (REQ-RG2)

In-code constants adjacent to `resolve_heretek_commit` (design option 1):
single-file review, impossible to desync from the classifier, and the REQ-RG4
check tests that exact source via import. Entries: `docs/evidence/`,
`docs/reports/`, `.agents/`, `.claude/`, `.opencode/`, `.lane/`,
`openspec/changes/` (prefix) + `skills-lock.json`, `PROMPT_REVIEW.md`
(exact). Covers all AGENTS.md:46 strays plus loop scratch, `.lane/`
ephemera, and in-flight openspec scratch (all provably non-inputs: the
generator reads fleet/schemas/vendor, never these paths). `HANDOFF.md`
stays dirt (tracked → status-code-first refusal). `.scratch/` needs no
entry (already `.gitignore`d, invisible to porcelain).

## Files changed

- `scripts/generate-rigs.py` (+classifier, +classified refusal)
- `scripts/verify-rigs.sh` (+V7 block, +`importlib.util` import)
- `tests/test_regen_gate.py` (new, 8 tests, synthetic /tmp git trees only)
- `AGENTS.md` (gate paragraph, 22→23 ×2)
- `Makefile` (`make test` += new test file)
- `docs/reports/remediate-43-regen-gate-implementation.md` (this file)
- `docs/reports/wave-43-regen-gate-implementation.md` (stage twin)

## Verification outputs (exact commands, exit codes)

- `python3 -m unittest tests/test_regen_gate.py` → `Ran 8 tests … OK` (exit 0)
- RED proof: same command pre-implementation → 4 failures, all for the
  expected reasons (sanctioned strays refused; refusal named no paths)
- `make test` → `Ran 58 tests … OK` (exit 0)
- `make verify` → `SUMMARY: 23 checks passed, 0 failed` (exit 0) +
  live-health advisory (stale heartbeats, pre-existing, warn-first)
- Sabotage proof: removed `.claude/` from allowlist → `SUMMARY: 22 checks
  passed, 2 failed` with ONLY the V7 block failing (coverage fail +
  genotype fail), all 22 pre-existing checks green; restored → 23/0
- T4c regen: `env -u HERETEK_RIGS_ALLOW_DIRTY python3 scripts/generate-rigs.py
  --crew-source …/Heretek-Crew --vendor-dir …/.scratch/vendor` → `REGEN-OK`,
  post-regen diff = `resolvedCommit`/`canonicalUrl` SHA advance only
- `openspec validate remediate-43-regen-gate` → `Change … is valid`

## Self-audit / skipped items

- Nothing skipped: all T1–T6 done. `README.md:47` still says "22 checks" —
  deliberately untouched (outside this change's edited files; peer-scope per
  the design's rebase note; flagged for the owning wave).
- Pre-existing quirk left alone (out of scope): `git status` subprocess
  failure defaults to `dirty=""` (proceeds). Not introduced or widened here.
- No stubs, no `|| true`, no empty catches with swallowed errors (the one
  `except` in the C-unquote path appends the line to blocking — fail-closed),
  no skipped tests, no secrets in commands/outputs (dummy fixtures only).
- No merge, no push (per stage instructions; human merges).
