# Delta spec: path-arg-grants-91

## ADDED Requirements

### REQ-A0: live-proof-first gate
Before any grant implementation, a live probe through the INSTALLED pps 41.0.0 MUST determine which `commandEffects` shape relieves `pytest tests/rag` on vector-rag-spec (list form vs native-map form vs both vs neither). The outcome MUST be recorded in evidence. If NEITHER shape enforces, the wave MUST halt with a re-plan note and MUST NOT land dead grants. Rationale: principal decision Q5; §4 map-vs-list mismatch shadows #106.

### REQ-A1: scoped per-tool argv effects
On the M0 outcome, the renderer MUST emit scoped argv-position effects for `pytest` / `go` / `cmake` / `gcc` (bare basenames, exact subcommand words where pps descent applies: `go build`, `go test`; cmake `-S`/`-B` are options — entry-level effects apply). Path operands MUST be resolved via reused `_expanded_scope_roots` + realpath-containment (traversal/`..`-escape/absolute-/tmp/symlink → deny); shell-control tokens in arg values MUST be rejected (same token set as note-effect). Go `...`-suffixed package args MUST be classified as package patterns within scope, never as literal paths (so `./...` allows while `../../etc/...` denies).

### REQ-A2: argv-slot exception for -c/-W
The gcc path-operand effect MUST take precedence over terminal denies `* -c *` (and `* -W*` for warning flags) FOR THAT ARGV SLOT ONLY (principal decision Q6). `TERMINAL_BASH_DENIES` MUST remain byte-identical on disk (42 entries). The exception MUST be documented as overlay precedence, mirroring #106, with red-proofs showing the deny still fires outside the slot.

### REQ-A3: grant scope
New `bash_allow` prefixes (`gcc*` compile forms; engine-systems-eng `cmake -S . -B build` scoped to its tree) MUST go to cpp-lowlevel-eng + engine-systems-eng ONLY (principal decision Q7), avoiding `--output`/metachar die-gates. No other role gains build verbs in this change.

### REQ-A4: probes + corpus
Charter-verbatim gate probes (each advertised verification command expects allow) MUST be added alongside existing `gate-role.sh` expects. Corpus MUST cover per-tool allow/deny both directions; the `command-effects-redproof.sh` id-list assertion MUST be updated deliberately to the new expected order.

## MODIFIED Requirements

### REQ-G1: frozen tuple, no renumber
`TERMINAL_BASH_DENIES` (42) byte-identical; no check renumber/reword; `specs/` `rigs/` `rosters/` `registry/` only via generator.
