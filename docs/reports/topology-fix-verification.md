# Drift-guard verification: topology-fix (stage topology-fix)

- Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/topology-fix`
- Head: `860de39` (impl `deced5f` + QA evidence). Base: `939fc9d`.
- Spec: `openspec/changes/topology-fix/` (proposal.md, specs/topology-render/spec.md, design.md, tasks.md).
- Method: independent adversarial audit. Nothing trusted; everything below re-read/re-run from disk. No source files modified; `git status --short` clean at audit time. Only this report written.

## D1 — Scope discipline: PASS

`git diff 939fc9d..HEAD --name-only` = exactly 10 files:
`scripts/topology.py`, `docs/USER_GUIDE.md`, `.github/workflows/topology.yml`
(implementation) + `docs/evidence/topology-fix/red-proofs.log`,
`docs/reports/topology-fix-implementation.md`, `docs/reports/topology-fix-qa.md`,
4× `openspec/changes/topology-fix/*` (reports/evidence/spec, not implementation).
Zero contact with `fleet/`, `specs/`, `rigs/`, `rosters/`, `registry/`
(no regen required, no digest impact). No gate-outcome behavior change beyond the
spec: `git diff -w` proves all non-whitespace hunks are exactly the F2 loop merge
and the F3 identity swap (see D2/D3). Gate outcomes on the current tree unchanged
(`make verify` 22/0 before per QA baseline and after per my re-run).

## D2 — F2 loop merge: PASS

- Exactly one `6. rig.yaml members` loop (`grep -c` == 1, verified).
- Guarded read is the read path for member validation: `try: with open(rig_path)
  as fh: ry = yaml.safe_load(fh)` / `except (OSError, yaml.YAMLError) as err:
  rep.fail(...); continue` (scripts/topology.py:146-157). Handle closed via
  context manager; leaked-handle `open()` removed.
- Comparison block byte-equivalent to pre-fix second loop modulo
  black-style re-wrapping: `git diff -w` shows the only deletions are the
  duplicated loop header (3 lines), the `if not rig.get("id"): continue`
  (2 lines), and the unguarded `ry = yaml.safe_load(open(...))` (1 line).
  Every `disk_members` / `fleet_members` / bidirectional `rep.fail` line is
  present and identical ignoring whitespace.
- No other unguarded rig.yaml read remains: remaining `open(...)` call sites
  (topology.py:53,55,57 fleet loads; :187 member fragments check-7, out of scope
  and unchanged; :403,415,441,471,505,537 render outputs) contain no
  `open(os.path.join(ROOT, "rigs"` rig.yaml pattern.

## D3 — F3 full-pin identity: PASS

- `render_bipartite` (topology.py:463-470) emits `"pkg:{dot_escape(p)}"` node +
  `"seat:{mid}" -> "pkg:{dot_escape(p)}"` edge with
  `[label="{dot_escape(short_pkg(p))}", shape=diamond]`. No `split("@")[0]`
  identity remains anywhere in the render path: the only `split("@")` left is
  inside `short_pkg` (topology.py:477), which feeds the human-readable DOT
  `label` only — the spec-allowed use, already proven in `render_matrix`.
- DOT-quoting safe: all 10 allowlisted pins contain only `@ / .` alphanumerics
  (verified by reading the full `ALLOWED_PI_PACKAGES` set, topology.py:31-41);
  none contains `"` or newline (checked programmatically). `dot_escape`
  additionally escapes `"` on both ID and label paths, and `build_graph`
  already used full-`p` `pkg:{p}` IDs, so render and graph are consistent.
- Independent render confirms: my own `make topology OUT=/tmp/topo-dg` yields
  zero `"pkg:"` empty nodes (`grep -rn '"pkg:"'` exit 1) and distinct scoped
  nodes, e.g. `"pkg:@gotgenes/pi-permission-system@41.0.0"
  [label="pi-permission-system", shape=diamond]` (12 hits in
  bipartite-executive-and-architecture.dot).

## D4 — F1 trigger-docs accuracy: PASS

Actual triggers read from `.github/workflows/topology.yml:19-35`: `push`
`branches: [main]` + 7 path filters, `pull_request` + same 7 path filters,
`workflow_dispatch`. New header comment (lines 1-2: "on push to main
(path-scoped), pull_request (path-scoped), and manual workflow_dispatch") and
new guide sentence (USER_GUIDE.md:399-401: "on push to `main` limited to the
listed paths, on pull requests limited to the listed paths, and on manual
`workflow_dispatch`") both match. Forbidden phrase gone: `rg "every push/PR"`
over both files returns nothing (re-run). Artifact statement accurate:
workflow uploads SVGs + graph.json + matrix.md (lines 7, 75-79) with
`retention-days: 30` (line 79); guide claims "(30-day retention)". No CI
behavior change (single comment hunk only).

## D5 — QA red-proof honesty: PASS (cross-verified, non-vacuous)

- F3: sabotage mechanism verified from first principles
  (`'@gotgenes/x@1'.split('@')[0]` == `''`, reproduced in Python) and
  arithmetically cross-checked against my independent fixed render: per-file
  `"pkg:@` node-line counts in `/tmp/topo-dg` are
  26/14/12/22/18/16/8 = 116 total — exactly the "116 empty-node lines" and
  per-file distribution claimed in red-proofs.log. The `"pkg:"` grep gate is
  therefore proven discriminating, not vacuous.
- F2: structural single-loop gate (`grep -c` == 1) correctly REDs under loop
  duplication while `make verify` stays 22/0 — consistent with the spec boundary
  ("same PASS/FAIL set"). The unhandled-`OSError` fail-open path of the old
  `open()` is real (unguarded `yaml.safe_load(open(...))` propagates). Gate
  non-vacuous.
- F1: `rg "every push/PR"` gate REDs on the sabotaged phrase, GREEN on the
  fixed tree (re-run both states logically; fixed state confirmed exit 1).
- Tree state honest: `git status --short` clean (confirmed empty output);
  `git diff deced5f --stat` empty of tracked changes per log (my
  `939fc9d..HEAD` diff shows only the expected files; QA artifacts committed
  in `860de39` per stage protocol).

## D6 — Hygiene: PASS

- Base/linearity: `git log --format='%H %P %s' 939fc9d..HEAD` shows
  `deced5f` parent == `939fc9d`, `860de39` parent == `deced5f`. Linear,
  branched from `939fc9d`, no merges. (Reflog unavailable — shell tool
  permission rejection, retried; parent chain is sufficient evidence of
  linearity. No force-push markers observable.)
- No secrets: diff grepped for `ghp_|github_pat|sk-ant-|AKIA|PRIVATE|password`
  — no hits.
- No stubs: diff grepped for TODO/FIXME/NotImplemented/`|| true`/bare-except-pass/
  skips — no hits. `.meta` N/A (non-Unity repo, no Unity assets touched).
- Strays untouched: status clean; no deletions/modifications of
  `docs/evidence/`, `docs/reports/`, `.agents/`, `.claude/`, `PROMPT_REVIEW.md`
  beyond this stage's own new files.
- `make verify` (re-run by auditor): `SUMMARY: 22 checks passed, 0 failed.`
- `make topology OUT=/tmp/topo-dg` (re-run by auditor): exit 0, graph.json
  238 nodes / 1069 edges, zero `"pkg:"` empty nodes, scoped pins distinct.

## Observation (not a finding)

The implementation reformatted all of `scripts/topology.py` in black style
(~240 cosmetic lines). `git diff -w` proves zero behavioral content in the
noise. Style nit only — not FAIL per the severity rule — but future stages
should keep formatting-only churn out of functional diffs to ease review.

VERDICT: PASS
