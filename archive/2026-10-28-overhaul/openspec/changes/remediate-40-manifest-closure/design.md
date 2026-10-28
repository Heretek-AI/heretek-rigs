# Design: remediate-40-manifest-closure

## Approach
Parse-only static closure, no installs, no network. Implementation sketch
(non-binding): a Python script (matching `scripts/` conventions —
`topology.py`, `audit_sessions.py` are Python) that loads each staged
`package.json` (`scripts` map + `devDependencies` keys + `bin`), each
staged `tsconfig*.json` (`types` arrays), and each staged workflow YAML
(`run:` bodies); tokenizes script bodies with shell-aware splitting
(`shlex`); resolves `pnpm <name>` indirections one level into the same
package's scripts; and reports unresolvable first-tokens. `node_modules`
`.bin` probing is explicitly NOT used — the defect class is "resolves by
accident on this machine", so the check MUST be manifest-text-only.

## Instance-2 limitation (honest scope boundary)
`apps/web` JSX broke on missing `@types/react` with no textual reference
to a binary or a `types` entry a parser could flag. Covering that class
requires type-resolution (tsc's job, already gated). The lint covers the
other three classes (undeclared binary, undeclared `types` entry,
global-leak binary) and the spec's regression fixture for instance #2 is
"declared state passes", not "omission is caught". No vacuous claim.

## Fail-closed modes
- Unreadable/missing manifest or workflow → non-zero exit naming the file
  (never skip-silent; mirrors `topology.py` check-6 guarded-read style).
- Unknown allowlist file → fail, do not default-allow.
- Recursive `pnpm` script indirection cycles → terminate with failure
  naming the cycle (visited-set, depth cap).

## Risks
- Shell-variable/command-substitution edge cases in `run:` lines
  (`${{ }}`, `$VAR`, `cmd1 && cmd2`): tokenizer takes first token of each
  `&&`/`;`/`|`-separated segment; false positives dispositioned via the
  explicit allowlist, which is versioned so drift is reviewable.
- New gate changes `make verify` output shape (22 → 23 checks): the
  audit-baseline rule forbids renumbering/rewording existing checks;
  appending one new block with a distinct name complies.
