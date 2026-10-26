# Proposal: path-arg-grants-91 — scoped build/test path args with live-proof-first enforcement

Status: scope approved (principal policy calls 2026-10-25: scoped arg grants; live-proof first; argv-slot exception for -c/-W; two engine roles; separate wave).
Issue: #91. Closes #91 only on post-merge live proof (each charter command allows on its seat); until then Refs.

## Root cause (verified read-only 2026-10-25, Wave F recon)

- pps checks bash path args against the path map: `pytest tests/rag` denied (rule `*`), trailing-slash/file forms allowed; `go build ./...` denied (`*..*`), `go build .` / `go test ./cmd` denied (`*`); `cmake -S . -B build` denied on all 51; `gcc -c` has zero grants fleet-wide.
- Enforcement risk (§4): installed pps 41.0.0 consumes `commandEffects` as a MAP keyed by bare basename; our rendered LIST form has zero hits in pps src/docs and a zod record will not parse an array — the overlay may render but not enforce (this shadows #106 too). Principal call: LIVE-PROOF FIRST through installed pps; build on the run's outcome (expected: emit native-map declarations alongside the descriptor list).
- Deny tension: `gcc -c` matches `* -c *`, `-Wall` matches `* -W*` (last-match-wins). Principal call: argv-slot exception for the gcc path-operand slot, denies byte-identical on disk (#106 precedent).
- Scope: `gcc*` compile grants + engine `cmake -S . -B build` (own tree) to cpp-lowlevel-eng + engine-systems-eng only.

## Change (evidence-gated)

- M0 (first): live hostile-corpus probe via `gate-role.sh`-style run through installed pps 41.0.0 on `pytest tests/rag` — list form vs native-map form vs both. Outcome recorded in evidence; implementation follows the winner. If NEITHER enforces, stop and re-plan (do not build dead grants).
- On M0 outcome: catalog `command_effects` stanzas (pytest/go/cmake/gcc; Go `...` package-pattern branch separate from literal-path `..` check; cmake `-S/-B` flag-value pairing; gcc `-c` + source pairing) reusing `_expanded_scope_roots` + realpath-containment; missing `bash_allow` prefixes (`gcc*`, engine configure) avoiding `--output`/metachar dies; corpus + redproof + charter-verbatim gate probes; full regen.
- Live proof post-merge (close criterion): each charter-advertised command allows on its seat; traversal/absolute/symlink/shell-token forms deny; greenfield C++ configures without presets dance.

## Acceptance

1. M0 evidence names the enforcing shape; implementation matches it (or wave halts with re-plan note).
2. All four issue-verbatim commands allow on scoped roles; `../../etc/...`, absolute-/tmp, symlink, `;|$|``|`$(`, `OPENRIG_*=` forms deny — red-proofed.
3. `make verify` green (appended blocks, no renumber); 42-tuple byte-identical.
4. Drift-guard `VERDICT: PASS` → PR (Refs #91 until live proof; Closes #91 only after).
