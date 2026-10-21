# Design: topology-fix

## F2 — loop merge
Fold the first loop's guarded read into the second loop: one
`for rig in ...` loop, `try: with open(rig_path) as fh: ry = yaml.safe_load(fh)`
`except (OSError, yaml.YAMLError) as err: rep.fail(...); continue`, then the
existing bidirectional member comparison unchanged. No new failure modes:
the guarded path already existed; the unguarded path (uncaught traceback on
unreadable YAML, leaked fd) is removed. Fail-closed behavior preserved —
unreadable `rig.yaml` still records `rep.fail` and skips that rig.

## F3 — node identity
Replace `short = p.split("@")[0]` identity with full `p`:
node `"pkg:{p}"` with `[label="{short_pkg(p)}", shape=diamond]`, edges
`"seat:{mid}" -> "pkg:{p}"`. DOT-quoting: pins contain `@`, `/`, `.` — all
safe inside double quotes; no existing pin contains `"` or newline
(allowlist is fixed, validated by check 5). `short_pkg` already handles the
leading-`@` scoped case and is proven in `render_matrix`. Unscoped pins keep
working: `p` is unique per allowlist entry.

## F1 — docs only
Two text edits (guide paragraph + workflow header comment). No CI behavior
change. The `pull-requests: write` permission + PR-comment step are
unchanged and out of scope.

## Risks
- Graphviz `dot` must exist for render verification (`make topology`
  shells to `dot -Tsvg`). If absent in the stage environment, `.dot`
  textual assertion (no `"pkg:"` empty nodes) still proves F3; SVG build is
  unchanged code.
- `verify-rigs.sh` and `topology.py --check-only` overlap on member
  validation; both must stay green — acceptance runs both (`make verify`
  and `make topology`).
