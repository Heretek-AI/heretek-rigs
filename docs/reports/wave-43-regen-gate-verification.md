# Verification report: wave-43-regen-gate (remediate-43-regen-gate)

Stage: `wave-43-regen-gate` · Change: `remediate-43-regen-gate` · Issue: Heretek-AI/heretek-rigs#43
Auditor role: independent adversarial auditor (no fixes, no commits).
Commits under audit: `32c1233` (implementation) + `5748758` (reports) + `4fe192a` (QA evidence)
Base: `origin/main @ 00acda2`. Worktree branch: `remediate/43-regen-gate`.
Spec sources read from disk: `AGENTS.md`, `openspec/changes/remediate-43-regen-gate/proposal.md`,
`specs/regen-gate/spec.md` (REQ-RG1–RG4), `design.md`, `tasks.md` (T1–T6),
`docs/reports/wave-43-regen-gate-implementation.md`, `docs/reports/qa-wave-43-regen-gate.md`,
`docs/evidence/wave-43-regen-gate/red-proofs.log`, `gh issue view 43`.

## 1. Diff audit (binding rules)

- `git diff 00acda2..HEAD --stat`: 9 files — `AGENTS.md`, `Makefile`,
  `docs/evidence/wave-43-regen-gate/red-proofs.log`, `docs/reports/qa-wave-43-regen-gate.md`,
  `docs/reports/remediate-43-regen-gate-implementation.md`,
  `docs/reports/wave-43-regen-gate-implementation.md`, `scripts/generate-rigs.py`,
  `scripts/verify-rigs.sh`, `tests/test_regen_gate.py`. Every file is justified by
  tasks.md (T1–T3 code/tests, T4–T6 evidence/reports, AGENTS.md+Makefile by T3).
  No scope creep: no fleet catalog edits, no generator-output hand-tuning.
- Zero hand-edits under `specs/`, `rigs/`, `rosters/`, `registry/`:
  `git diff 00acda2..HEAD --stat -- registry/ specs/ rigs/ rosters/` is empty.
  The openspec package itself is untouched by this diff (spec-only, landed earlier).
- `verify-rigs.sh`: `git diff 00acda2..HEAD -- scripts/verify-rigs.sh | grep "^-"`
  (excluding `---`) returns ZERO removed lines. Only additions: `import importlib.util`
  and the appended V7 block with exactly one new `ok()`. Append-only pattern holds;
  V1–V6 byte-identical. AGENTS.md:45 audit-baseline rule satisfied.
- `Makefile` delta: one line — appends `tests/test_regen_gate.py` to `make test`.
  Additive only, non-masking (adds coverage, removes/skips nothing).

## 2. Classifier audit (scripts/generate-rigs.py:65–214, read in full)

- Status-code-first: `_split_porcelain` consults the allowlist ONLY for `??` entries
  (generate-rigs.py:138); every other status and every unparseable line is blocking
  (lines 134–136, 152–153). Tracked-override holds by construction.
- C-quote handling (lines 141–147): C-quoted paths are unquoted via
  `unicode_escape`/`latin-1` round-trip; any exception appends the raw line to blocking
  (fail-closed, lines 145–147). Correct.
- Empty-source fail-closed: `_is_sanctioned_untracked` returns False on exception or
  emptied source (lines 104–122). Correct.
- Refusal (lines 195–213): blocking porcelain lines verbatim under `blocking changes:`,
  ignored strays listed separately under `ignored sanctioned strays (not dirt):`;
  remediation hint text byte-identical to pre-change wording (line 203–204).
  Happy path prints nothing new (proceeds silently to `rev-parse` SHA).
- `ALLOW_DIRTY` semantics unchanged: `if dirty and not allow_dirty` (line 195) untouched;
  when set, behavior is byte-identical (proceeds, records real HEAD).
- Pre-existing quirk left alone (out of scope, not introduced): `git status` subprocess
  failure defaults to `dirty=""` (lines 187–194). Present in base, unchanged. Not a finding.
- Live probes (scratch `/tmp` repo, worktree never touched):
  (a) classifier probe: `M docs/evidence/kept.md` → blocking, `?? scripts/evil.py` →
  blocking, `?? docs/evidence/new.md` → ignored — PASS;
  (b) real-git scratch repo: committed `docs/evidence/kept.md` then edited
  (`M docs/evidence/kept.md`) → `resolve_heretek_commit` exits 2 naming the file — PASS;
  (c) same repo after checkout + untracked `docs/evidence/session-note.md` only →
  resolves to HEAD SHA — PASS. Tracked-modification-inside-sanctioned-dir refuses;
  sanctioned-untracked-only resolves. REQ-RG1/RG2 hold on live git, not just fixtures.

## 3. Allowlist precision (REQ-RG2)

Entries: 7 dir prefixes (`docs/evidence/`, `docs/reports/`, `.agents/`, `.claude/`,
`.opencode/`, `.lane/`, `openspec/changes/`) + 2 exact files (`skills-lock.json`,
`PROMPT_REVIEW.md`), each with a per-entry justification comment (lines 76–101).
Probe results: `scripts/generate-rigs.py`→False, `fleet/fleet.yaml`→False,
`Makefile`→False, `fleet/skills-lock.json`→False (exact-match is root-only, correctly
distinct from the tracked `fleet/skills-lock.json`), `docs/PROMPT_REVIEW.md`→False,
`openspec/specs/bar/spec.md`→False. No entry covers `scripts/`, `fleet/`, `Makefile`,
or any generator input (`generate_all` reads `fleet/`, `schemas/`, vendor checkouts —
never `openspec/`, `.lane/`, or session strays). `openspec/changes/` prefix is broad but
provably a non-input. No overly broad entries (`*.log`, root `*`, `.git/`). No shelter
for real code changes. PASS.

## 4. Count updates (22→23) and README.md:47 — independent decision

- Updated: AGENTS.md:15 (expect 23), AGENTS.md:45 (23 baseline). V7 `ok()` message
  references 8/8; SUMMARY computed. Complete within edited files.
- NOT updated: README.md:47 still says `expect: 22 checks passed, 0 failed`; several
  `REMEDIATION_LOG.md` historical entries still say 22.
- Decision (mine, not deferred to QA): ACCEPTABLE, not a finding. REQ-RG4 binds
  "wherever THIS CHANGE'S DOCS EDITS reference the old 22-count" — README.md is absent
  from this change's edited files (`git diff 00acda2..HEAD --name-only`), so the clause
  holds literally. design.md anticipates exactly this ("strings outside this change's
  edited files are peer scope — parallel packages must rebase, not duplicate-edit"),
  and editing README here would risk the cross-package conflicts AGENTS.md:43 warns
  against. REMEDIATION_LOG.md entries are append-only historical records, correctly
  immutable. Follow-up belongs to the README-owning wave. Severity rule confirms:
  a stale count in an untouched file is not a stub, vacuous check, failing command,
  or missing deliverable.

## 5. Provenance / revert honesty

- `git diff 00acda2..HEAD -- registry/` is empty; zero `resolvedCommit`/`canonicalUrl`
  hunks. Nothing to half-revert: regenerated leaves were reverted in full, and the
  revert is verified by absence of churn, not by trust. Implementer's T4c story
  (regen differed ONLY in baked SHA, then reverted) is consistent with the observed tree.
- QA did not re-execute the full regen (requires pinned vendor checkouts + crew source);
  honesty is evidenced by zero churn. Acceptable: re-running regen is the implementer's
  burden (met and recorded), and my audit confirms no residual provenance drift.

## 6. Tests (8 cases, synthetic /tmp trees only — never the live checkout)

- Ran myself: `python3 -m unittest tests/test_regen_gate.py` → `Ran 8 tests … OK` (exit 0).
- Spot-read both directions:
  (a) `test_sanctioned_strays_only_resolves` — under the pre-change gate (any-dirt
  refuses) this test exits 2 and FAILS; under a gutted gate it passes. Discriminating. PASS.
  (b) `test_refusal_classifies_both_sections` — asserts the `ignored sanctioned` section
  exists AND the blocking section excludes the stray; the old message had no sections,
  so it FAILS pre-change; a classifier that ignored everything would fail the blocking
  assertions. Non-vacuous in both directions. PASS.
  (c) `test_committed_allowlisted_path_edit_is_dirt` guards the opposite error mode
  (prefix-matching that forgot status-code-first) — passes under the old gate too, but
  fails under the over-broad-mutation direction. The suite as a whole is load-bearing
  in every mutation direction. PASS.
- V7 load-bearing: code-reading confirms (a) strays parsed from the AGENTS.md bullet
  itself (not hardcoded), (b) justification-comment assertion on the exact in-code source,
  (c) full unit-file re-run inside the check. QA's recorded sabotage (removed `.claude/`
  → `SUMMARY: 22 checks passed, 2 failed`, ONLY V7 failing, all 22 pre-existing green →
  restored to 23/0) is consistent with the code I read. No re-sabotage performed by this
  auditor (would require worktree modification); code path + recorded transcript suffice.

## 7. Commands re-run (adversarial, not trusted)

- `make verify` → `SUMMARY: 23 checks passed, 0 failed` (exit 0) + pre-existing
  LIVE-HEALTH advisory (heartbeat stale age-unknown ×7, warn-first, exit 0). Matches
  implementer/QA claims exactly.
- `openspec validate remediate-43-regen-gate` → `Change 'remediate-43-regen-gate' is valid`.
- `python3 -m unittest tests/test_regen_gate.py` → 8/8 OK.
- Secrets scan over `git diff 00acda2..HEAD` (private-key / `ghp_` / `AKIA` / long-key
  patterns): zero hits. Reports contain SHA/digest-shaped hex only (expected provenance
  evidence), no secret-shaped strings.
- `git status --short` post-audit: clean (this report written but uncommitted at check
  time; the file itself lands under sanctioned `docs/reports/`).

## 8. Spec fidelity vs issue #43

Issue #43 offers (a)/(b)/(c) and demands the returnable: a fresh session producing normal
evidence runs `generate-rigs.py` with no env override. The change implements (a) exactly:
sanctioned-untracked evidence strays no longer force `ALLOW_DIRTY=1`. `HANDOFF.md` (tracked)
stays dirt — by explicit design ("Why HANDOFF.md stays dirt"): a tracked edit is
indistinguishable from uncommitted generator-input edits, so fail-closed requires
commit/stash, which is normal git hygiene, not the dev-escape hatch. The structural
incompatibility (steady-state evidence dirt ⇒ override mandatory) is resolved; the
remaining tracked-dirt refusal is the gate's intended safety property, preserved.
No (b) robot, no (c) legalization. Faithful to the issue's chosen option. PASS.

## Notes (not findings)

- N1: README.md:47 follow-up for the owning wave (see §4).
- N2: `git status` failure ⇒ `dirty=""` proceeds — pre-existing, out of scope.
- N3: Full-regen honesty via absence-of-churn, not re-execution (see §5).
- N4: `docs/reports/remediate-43-regen-gate-implementation.md` and the stage twin
  `wave-43-regen-gate-implementation.md` are byte-identical; both required (tasks.md T6
  + stage instructions). Not duplication-creep.

No numbered findings. No stubs, no `|| true`, no swallowed errors, no skipped tests,
no secrets, no hand-edits under generated dirs, no renumbering, no scope creep.

## 9. Re-audit 2026-10-22: follow-up fixes b5d4487 + 3bfd010 (stage wave-43-strip-reaudit)

Commits under audit: `b5d4487` (porcelain strip fix) + `3bfd010` (V7 label
8/8→9/9) + `e208287` (QA evidence, reports/evidence only). Base: `00acda2`.
Spec sources re-read from disk: `AGENTS.md`, `openspec/changes/remediate-43-regen-gate/specs/`
(REQ-RG1–RG4), `tasks.md`, `docs/reports/qa-wave-43-regen-gate.md` (follow-up
§13 re-verification — one claim spot-checked independently, see R5).

- R1 Diff scope: `git diff 00acda2..HEAD --stat` = 10 files, identical set to
  the prior audit plus the two fix deltas. `b5d4487` touches exactly
  `scripts/generate-rigs.py` (1 line) + `tests/test_regen_gate.py` (+1 test);
  `3bfd010` touches exactly `scripts/verify-rigs.sh` (1 label string);
  `e208287` touches exactly `docs/evidence/.../red-proofs.log` +
  `docs/reports/qa-wave-43-regen-gate.md`. No other drift.
  `git diff 00acda2..HEAD -- scripts/verify-rigs.sh | grep "^-[^-]"` = 0
  removed lines vs base (the 8/8→9/9 delta exists only inter-commit; vs base
  the V7 block is pure addition). V1–V6 byte-identical. PASS.
- R2 `.rstrip("\n")` fix (generate-rigs.py:192): correct — strips only
  terminal newlines, preserves leading porcelain status spaces (verified by
  the new verbatim test asserting `"   M fleet/fleet.yaml"`). Other `.strip()`
  sites audited: line 176 `rev-parse HEAD` (SHA-only, validated by
  `re.fullmatch(r"[0-9a-f]{40}")` immediately after — no status semantics),
  line 329 `npm root` path, line 362 charter-section regex group, line 692
  `rev-parse --short=7` pin SHA. None operate on porcelain-shaped data. PASS.
- R3 Label 8/8→9/9: display-only inside the wave's own new V7 `ok()` string.
  The load-bearing gate is returncode-based
  (`utr43.returncode != 0 → fail(...)`); a wrong label still passes 23/0 while
  a real test break still fails V7 (QA's Fd-red + original sabotage F prove
  both directions). `grep -c "    def test_"` = 9 matches the 9/9 label. PASS.
- R4 Re-run myself: `make verify` → `SUMMARY: 23 checks passed, 0 failed`
  exit 0 (+ pre-existing LIVE-HEALTH WARN heartbeat-stale ×7, SKIP
  seat-idleness — advisory, unchanged); `python3 -m unittest
  tests/test_regen_gate.py` → 9/9 OK; `openspec validate
  remediate-43-regen-gate` → valid. Real-secret-pattern scan over
  `git diff 00acda2..HEAD` (ghp_/gho_/AKIA/private-key shapes): zero hits
  (the only `ghp_` substring is report prose naming the pattern, not a
  secret). PASS.
- R5 Spot-check of appended QA claim Fa (independent repro, /tmp scratch
  repo, live checkout untouched): unstaged edit of `fleet/fleet.yaml` →
  `resolve_heretek_commit` exits 2 with verbatim `   M fleet/fleet.yaml`
  (leading space preserved — would have rendered `  M ...` staged-looking
  under the old `.strip()`). Matches QA's recorded Fa/Fa-red. PASS.
- R6 Prior PASS basis still holds: `git diff 00acda2..HEAD --stat --
  registry/ specs/ rigs/ rosters/` empty (no generated-dir edits, no
  provenance churn); allowlist entries unchanged since prior audit (7 dir
  prefixes + 2 exact files with justification comments); no stubs introduced
  (new test has real assertions, no `|| true`/skips). `git status --short`
  clean at check time. PASS.

No numbered findings in this re-audit.

VERDICT: PASS
