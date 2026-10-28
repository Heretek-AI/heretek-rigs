# Design: output-deny-76 (narrow without opening)

## Why equals/space/tab + two targeted denies
Prefix-glob matcher semantics match substrings, so `--output` must be pinned by its right-hand neighbor: `=` (equals form), space/tab (separated form). Hyphen-continuations (`--output-on-failure`, `--output-format`) carry `-` and pass — except the two real file-writers (`--output-junit`, `--output-log`), which get their own denies per principal call. Bare trailing `--output` (end-of-string) matches neither narrowed pattern: accepted residual (every known tool errors without the arg; record, don't chase — the matcher dialect has no end-anchor).

## Why position 1 is kept
V13 asserts ordered-identity between source and mirror; last-match-wins makes position load-bearing for overlapping patterns. The five replacements occupy the exact slot of the removed entry, so order gates stay meaningful and the diff is reviewably `--output`-only.

## Why the render_seat corpus goes to full parity
`test_render_seat.py` already drifted 7 entries behind the 38-tuple; narrowing on top of drift would leave the corpus asserting a tuple that exists nowhere. Full parity (42/42) closes the drift inside the approved exception instead of spreading it.

## Failure modes
- A tool with `--output<newline><path>` → newline is already killed generation-time (metachar die) and undeclarable as a glob; accepted residual, same class as bare `--output`.
- A future `--output-*` file-writer → passes until named; V-number block + corpus pattern (add targeted deny + probe) is the documented response, same as Q4.
- Fleet `bash_allow` stays `--output`-free: generation-time dies unchanged, so no allow can smuggle the substring in.
