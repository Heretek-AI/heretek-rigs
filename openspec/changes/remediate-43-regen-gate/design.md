# Design: remediate-43-regen-gate

## Why option (a): allowlist, not side-branch auto-commit or blessed ALLOW_DIRTY
- Option (b) (auto-commit evidence to a side branch) converges the tree but
  invents a commit robot with authorship, signing, and push questions — a
  second system to design, audit, and fail closed. Rejected as
  disproportionate: the evidence has no committed home *by design* today
  (AGENTS.md:46 says leave strays alone), so the gate should match the
  workflow, not re-architect it.
- Option (c) (document ALLOW_DIRTY as standard) legalizes baking provenance
  on genuinely unknown trees — it deletes the safety property instead of
  fixing the false positive. Rejected outright.
- Option (a) is a pure false-positive fix: the gate keeps refusing on every
  input that could change generated leaves, and stops refusing on outputs
  the workflow itself mandates.

## Why untracked-only; why HANDOFF.md stays dirt
Only untracked paths are *provably* non-inputs to the generator (no tracked
file can depend on them). A modified tracked file — even `HANDOFF.md`, which
no generator reads today — *could* coincide with uncommitted generator-input
changes in the same tree, and the gate cannot distinguish "benign handoff
edit" from "fleet.yaml edit you forgot to mention." Fail-closed means the
operator commits or stashes tracked work; the allowlist only forgives what
cannot be an input. This is the property QA red-proofs must discriminate
(tasks.md T4).

## Prefix-vs-exact and the tracked-override rule
Directories (`docs/evidence/`) match by prefix — sessions create arbitrary
filenames underneath. Files (`skills-lock.json`, `PROMPT_REVIEW.md`) match
exact root-relative paths so a same-named file elsewhere is still dirt.
The tracked-override rule (allowlisted path that is also tracked →
modifications are dirt) closes the hole where someone commits an evidence
file and later edits it: `git status` reports it as `M`, not `??`, so the
classifier keys on the status code first, the allowlist second.

## Where the allowlist lives
Recommend the constant adjacent to `resolve_heretek_commit` in
`generate-rigs.py`: single-file review, impossible to desync from the
classifier, and the REQ-RG4 check can import/grep one file. A separate
checked-in allowlist file is the alternative (agent-editable without touching
gate logic) — implementer picks, REQ-RG2 requires the choice documented and
REQ-RG4 requires the check to test that exact source.

## Fail-closed modes
| Condition | Gate behavior |
|---|---|
| Sanctioned strays only | Resolves HEAD, proceeds (returnable) |
| Tracked modification present | Exit 2, blocking lines verbatim (HANDOFF.md stays dirt — by design) |
| Non-allowlisted untracked present | Exit 2, blocking lines verbatim |
| Unresolvable HEAD / git missing | Unchanged: die (or synthetic fallback with explicit flag) |
| Allowlist source unreadable/tampered | Classifier MUST fail closed (treat as no-allowlist → refuse on any untracked), never as allow-all |

## Risks
- Appending a verify check moves the documented count 22 → 23: every
  "22 checks" string this change's docs edits touch MUST move together
  (REQ-RG4). Strings outside this change's edited files are peer changes'
  scope (the #45 package also references the count — parallel packages must
  rebase, not duplicate-edit).
- Porcelain format drift across git versions: the classifier MUST parse only
  the two documented status codes (`??` vs everything tracked) and treat
  anything unparseable as dirt.
