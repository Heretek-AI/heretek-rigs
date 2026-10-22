# Proposal: remediate-44-json-trailer — local --json discipline + one upstream stdout-purity issue

## Status
Spec proposal for heretek-rigs issue #44. Specs only — no implementation in this package.

## Verified facts (encoded, not re-litigated)
- #44 CONFIRMED byte-exact: bare `rig queue show` (and `list`) appends a
  human trailer line starting `… (bounded preview …)` on **stdout**
  (upstream `dist/commands/queue.js:1115-1117`). Any agent doing
  `json.load(stdout)` gets `JSONDecodeError: Extra data`.
- `--json` parses clean on `list` / `show` / `create` — the machine-readable
  path exists; callers just are not told the default is a mix.
- Precedent inside the same upstream file: the transitions notice already
  goes to **stderr** (`queue.js:1116-1143` region, transitions block), so
  moving notices to stderr matches upstream's own convention.
- A second stdout notice lives adjacent: the compact-mode notice
  (`queue.js:1118-1123`). Both notices MUST move together, or stdout stays
  impure under `output.compact`.
- Issue #42 (create receipt) shares this root cause (human text on stdout);
  BOTH this change and `remediate-42-create-receipt` reference ONE single
  upstream issue (filed once, linked from both specs).

## Change (two tracks)
1. Local (this repo, immediate): append `--json` to every queue example in
   generated seat charters (`scripts/generate-rigs.py`) and operator guides
   (`docs/USER_GUIDE.md`, `README.md`, root `AGENTS.md` queue row), with an
   explicit statement that bare output mixes JSON with a human trailer and
   MUST NOT be parsed.
2. Upstream (`mvschwarz/openrig`, requested): move both stdout notices (the
   bounded-preview trailer `queue.js:1115-1117` and the compact notice
   `queue.js:1118-1123`) to stderr, per the transitions-notice precedent.
   `tasks.md` mandates drafting the issue body with byte-exact evidence,
   filing it (`gh` or web), and linking the filed issue URL back into this
   spec package.

## Non-goals
- No local fork/patch of `@openrig/cli`; no vendored queue renderer.
- No change to `--full` semantics; `--full` stays orthogonal.
- No second upstream issue for #42 — one issue covers both notices + receipt.

## Acceptance
- `openspec validate remediate-44-json-trailer` passes clean.
- Implementer checklist in `tasks.md` is fully testable (grep + parse-first-try
  proof + filed upstream issue URL recorded in this package).
