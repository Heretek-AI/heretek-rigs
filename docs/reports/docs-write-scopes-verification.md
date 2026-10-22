# Verification report: docs-write-scopes (drift-guard audit)

Branch: `fix/docs-write-scopes` @ `b8da27a`
(`f0ff176` catalog+spec+report, `7180444` regen leaves, `b8da27a` QA evidence; parent `bae5d3a`).
Auditor method: independent re-read and re-execution from disk. No source files modified.

## D1 — Scope: fleet diff + regen deletions

- `git diff bae5d3a..HEAD -- fleet/fleet.yaml` is **exactly +6 additive lines, 0 removals**:
  `docs/design-system/*` x4 (a11y-specialist:581, design-system-eng:1664,
  ui-ux-designer:3833, ux-research-analyst:3895),
  `docs/brief/*` x1 (product-director:2911),
  `docs/architecture/*` x1 (ts-node-fullstack:3756).
- `git diff bae5d3a..HEAD --stat`: 83 files, +407/−94.
  Every minus line classified exhaustively
  (`git diff ... | grep -E "^-[^-]"` full output reviewed):
  registry `resolvedCommit`/`canonicalUrl`/`packageDigest`/`bodyDigest` provenance
  replay, `bundle.yaml` integrity-hash lines for touched files only (spot-checked
  `rigs/fullstack-and-web-studio/bundle.yaml` and `rigs/heretek-omni-fleet/bundle.yaml`
  line by line — all `agents/<role>/{guidance/role.md,runtime/*.json}: <sha256>`
  pairs, no other content), roster `caveat` prose updates (6 lines, each paired
  with a `+` line adding the new grant), and guidance `role.md`
  "Writes are confined to:" prose updates (paired 1:1 with grant additions).
  **Zero functional deletions.** Spot-checked `registry/status.json`,
  `registry/entries/executive-and-architecture.yaml`,
  `rigs/executive-and-architecture/agents/product-director/{guidance/role.md,runtime/pi-permission-config.json}`
  line by line — all match the replay-only pattern.
- No scope leak: `git diff --name-only` restricted to
  `fleet/ registry/ rigs/ rosters/ specs/ openspec/changes/docs-write-scopes/
  docs/reports/docs-write-scopes-* docs/evidence/docs-write-scopes/` (grep for
  anything outside these prefixes: exit 1, no hits).

## D2 — Correctness: grants under right role, exact REQ match

Role-block mapping confirmed via `fleet.yaml` block offsets
(`a11y-specialist:540`, `design-system-eng:1619`, `product-director:2866`,
`ts-node-fullstack:3695`, `ui-ux-designer:3783`, `ux-research-analyst:3856` —
each grant line falls inside its role's `permissions: path_write:` stanza):
- REQ-S1: `exec-product-director` gets `docs/brief/*` alongside `docs/product/*`. Exact glob.
- REQ-S2: `build-ts-node-fullstack` gets `docs/architecture/*` alongside `src/*`, `package.json`. Exact glob.
- REQ-S3: all four design roles get exactly `docs/design-system/*` alongside existing entries. Exact globs, no typos.
- `exec-system-architect` unchanged (already held `docs/architecture/*` — confirmed present in both rig copies + specs copy).
- Generated replay verified in **all 18 files** (6 roles x 2 rig copies + 1 specs copy):
  `grep -rE "docs/(brief|architecture|design-system)/\*"` over all
  `runtime/pi-permission-config.json` returns exactly the 18 expected
  `"allow"` lines, plus the pre-existing system-architect lines. No glob is
  over-broad (`docs/*` appears only for the pre-existing scribe role, untouched);
  no grant lands in a wrong role's file.
- `policy-enforcement.json` mirrors each grant (checked product-director,
  ts-node-fullstack, ux-research-analyst, a11y-specialist copies); guidance
  `role.md` "Writes are confined to:" prose updated consistently (6 roles x 3 copies).

## D3 — Guards (REQ-G1)

- `git diff bae5d3a..HEAD -- fleet/fleet.yaml | grep -E "bash|mcp|server|git|tool"`: **no hits** — zero `bash_allow`, MCP, or git-verb changes.
- Six roles' rendered configs contain no `git add|commit|stage` verbs (loop-checked
  all six; note: `dependency-patcher` holds a pre-existing `git commit*` allow —
  out of scope, untouched by this diff).
- Rendered `path_write` default-deny intact (`"*": "deny"` first entry) and
  `AGENTS.md: deny` (+ `*/AGENTS.md: deny`) present in both `path` and
  `path_write` stanzas (checked ts-node, ui-ux-designer, product-director copies).
  Root `AGENTS.md` remains outside every role's write scope; `fleet/*`,
  `scripts/*`, `*..*` denies intact.
- Least-privilege cross-check re-run on final tree: ts-node configs show
  `docs/brief` count **0** (3 files); ui-ux-designer shows `docs/brief` 0 and
  `docs/architecture` 0. Each role holds only its own area.
- `verify-rigs.sh` still 22 checks, no renumbering (re-ran `make verify` myself:
  `SUMMARY: 22 checks passed, 0 failed`, including `tests/test_render_seat.py` 7/7).

## D4 — QA honesty (red-proofs.log)

- The log is a narrative summary (no timestamps / raw shell capture), but it is
  grounded, not fabricated: the sabotage reference `fleet.yaml:3833` matches the
  actual `docs/design-system/*` line under `ui-ux-designer` at HEAD exactly;
  the three-copy pipeline detail (fullstack + omni-fleet + specs/web-design) and
  the sibling-control observation (design-system-eng still greps exit 0) are
  structurally correct for this generator.
- Every negative discrimination re-verified independently on the final tree
  (counts above in D3; `docs/brief|architecture|design-system` grant grep over
  all 21 rendered configs; `AGENTS.md deny` grep; fleet additive-only diff).
- Baseline outputs corroborated by my own run (`22/0`, `7/7`).
- Forward-direction pipeline claim (catalog -> leaves) verified by me: all 18
  generated files carry the grants; reverse direction (removal -> RED) rests on
  QA's sabotage account, corroborated as above. No vacuous check found.
- Advisory (not a finding): future red-proofs should capture raw command
  transcripts with exit codes to remove reliance on auditor corroboration.

## D5 — Hygiene

- `f0ff176` parent is exactly `bae5d3a` (clean branch, linear chain
  `bae5d3a -> f0ff176 -> 7180444 -> b8da27a`); no evidence of force-push
  (linear history, single branch).
- `git diff bae5d3a..HEAD` contains no secret-shaped strings
  (`ghp_`/private-key scan: 0 hits); no credentials in evidence/reports.
- `git status --short`: only pre-existing `??` strays
  (`docs/evidence/asset-manager-*`, `phase-0-gate/`, `commit-all-regen/`,
  `s02-rebuild/`, `remediation-*.md`, `FLEET_EDGE_MAP.md`, `skills-lock.json`,
  etc.) — per AGENTS.md these are prior sessions' artifacts, correctly untouched.
  The three stage files are committed (not stray untracked additions).
- `make verify` re-run by auditor: **22 passed, 0 failed**.

## D6 — Blast radius (running fleet)

- No `state/`, live-session, or workspace paths exist or appear in the diff
  (no `state/` dir in repo; `--name-only | grep state/|live|session`: empty).
  Change is catalog + generated leaves only, which take effect solely on
  reseed/relaunch. Implementation report's dry-run-only / old-policy-until-bounce
  caveat is accurate. **No live-state mutation occurred; running fleet still
  enforces old policy until post-merge reseed.**

## Findings

None.

VERDICT: PASS
