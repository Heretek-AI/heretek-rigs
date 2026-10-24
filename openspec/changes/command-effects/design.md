# Design: command-effects overlay (not deny-loosening)

## Why declarative effect, not deny carve-outs
`--note` trips `*|*` / `*>*` / path-substring denies because pps matches the whole bash string. Carving `|` / `/` out of denies would open pipe-execution and path-exfiltration fleet-wide (31→38 deny history shows tab-variant hardening was deliberate). A `commandEffects` allow-effect attached to the `--note` argv value and `--body-file` path keeps the 38 terminal denies intact and scopes the exception to two argv positions. Implementer does not freelance policy (#76/#91 remain principal decisions).

## Why narrow scope (cwd + path_write + pid scratch)
Catalog `path_write` is the authoritative per-role scope; `HERETEK_SANDBOX_WRITE` + `seat-sandbox.sh` inside-cwd + bind construction is the enforced runtime scope. Covering `realpath(cwd)` automatically covers `.lane/trees/<stage>` when the seat runs there, without baking `/.lane/` into configs (V14 forbids baked `/.lane/` in `shellPath`/`packages[]`). Pid-namespaced `seatjail.<pid>.*` is the only `/var/tmp` writable; legacy `seatjail.XXXXXX` stays unswept per #111. Absolute `/tmp`, `prod.env` outside scope, `/etc/passwd` are outside all three roots by construction.

## Why argv, not shell string
`park-typed-block.py:151` and `sweep-typed-blocks.py:156` already build argv lists; `seat-sandbox.sh:38-49` execs bare `rig …` via `shlex.split` with no shell. Passing `--note` as single argv preserves literal `|` (no pipe). Any `sh -c` interpolation would reintroduce execution — forbidden.

## Failure modes (fail-closed)
- realpath failure / missing file / oversize / symlink escape → deny, exit non-zero, no partial write.
- Renderer omits effect on some role → that role keeps old deny behavior (safe default, caught by corpus test asserting effect present on all queue-capable roles).
- Running seats enforce old policy until bounce: reseed + relaunch AFTER human merge; same bounce hazard as docs-write-scopes (collect drafts first).
- Overreach creep: QA red-proofs the negative (deny directions hold); drift-guard audits against this spec + `openspec/changes/command-effects/`.
