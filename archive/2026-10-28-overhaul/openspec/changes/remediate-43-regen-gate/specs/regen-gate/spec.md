# Delta spec: sanctioned-untracked allowlist in the regen gate

(No canonical `regen-gate` spec exists yet, so all requirements are ADDED;
REQ-RG1 constrains the pre-existing `resolve_heretek_commit` behavior.)

## ADDED Requirements

### Requirement: REQ-RG1 — Dirt check ignores sanctioned untracked, refuses everything else
`resolve_heretek_commit`'s `git status --porcelain` evaluation MUST be
changed from whole-output-nonempty to classified: untracked (`??`) paths
matching the REQ-RG2 allowlist are IGNORED for the dirt decision; the gate
MUST still refuse (exit 2, same message family) on (a) any modified/staged/
deleted tracked entry, (b) any untracked path NOT on the allowlist, and (c)
unresolvable HEAD — unless the pre-existing escapes (`ALLOW_DIRTY=1`,
`--allow-synthetic-provenance`) apply with unchanged semantics. Ignored
paths MUST NOT alter the baked provenance (still `git rev-parse HEAD`).

#### Scenario: Sanctioned strays pass, real dirt refuses
- WHEN the tree contains only allowlisted untracked paths THEN the gate
  resolves HEAD and proceeds; WHEN a tracked modification OR a
  non-allowlisted untracked path is added THEN the gate exits 2.

### Requirement: REQ-RG2 — In-repo allowlist with per-entry justification
The allowlist MUST live in-repo as a single source (constant adjacent to
`resolve_heretek_commit` or a checked-in file it reads — implementer picks,
documents the choice, and the REQ-RG4 check tests that exact source). It
MUST cover at minimum the AGENTS.md:46 strays — `docs/evidence/`,
`docs/reports/`, `.agents/`, `.claude/`, root `skills-lock.json`,
`PROMPT_REVIEW.md` — plus loop/session scratch (`.opencode/…`). Every entry
MUST carry a comment stating which workflow demand produces the path.
Matching MUST be prefix-based for directories, exact-path for files; a path
that is BOTH allowlisted and tracked-modified (e.g. a committed
`docs/evidence/` file later edited) MUST count as tracked dirt, not as
ignored.

#### Scenario: Tracked edit under an allowlisted prefix is still dirt
- WHEN a file under an allowlisted directory prefix is committed and then
  modified (status `M`, not `??`) THEN the gate treats it as blocking dirt.

### Requirement: REQ-RG3 — Refusal message classifies, never just dies
On refusal the gate MUST print the blocking `git status --porcelain` lines
verbatim AND separately list the ignored sanctioned paths (informational,
proving the filter ran). A clean-but-ignored run MUST be silent about dirt
(no new stdout on the happy path beyond today's behavior).

#### Scenario: Refusal names both classes
- WHEN the gate refuses on a tree with mixed blocking dirt and ignored
  sanctioned paths THEN stderr shows the blocking porcelain lines verbatim
  in one section and the ignored sanctioned paths in a separate section.

### Requirement: REQ-RG4 — Audit-baseline consistency check, appended not renumbered
A NEW `verify-rigs.sh` check (next sequential number, appended at the end —
no existing check renumbered or reworded) MUST assert: (a) every AGENTS.md:46
blessed stray is covered by the allowlist; (b) every allowlist entry carries
its justification comment; (c) the gate still refuses on synthetic real dirt
(tracked modification AND non-allowlisted untracked fixtures). Wherever this
change's docs edits reference the old 22-count, the new expected count MUST
be updated in the same edit (no stale "22" left behind by this change).

#### Scenario: Allowlist drift fails the new check only
- WHEN one AGENTS.md:46 stray is removed from the allowlist (sabotage)
  THEN the new appended check fails WHILE all pre-existing checks stay
  green.
