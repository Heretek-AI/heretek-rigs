# Design: 2026-10-29-bump-075

## Architecture

Single worktree `.lane/trees/bump-075`, branch `feat/bump-075` from clean
`main` (`c1da1fb`). Single triad (programmer → qa → drift-guard). One PR at
end (Refs only; no `Closes` — bump ledger, no issue).

## Verified upstream facts (live, 2026-10-29)

- npm `@openrig/cli@0.7.5`: `version = '0.7.5'`, tarball
  `https://registry.npmjs.org/@openrig/cli/-/cli-0.7.5.tgz`,
  `time['0.7.5'] = '2026-10-29T07:36:19.571Z'` (npm registry `modified`
  `2026-10-29T07:36:19.834Z`).
- Tarball sha256 `22d67c2c7e0d0ab4a5ec9faac0a725d54f9ead2c0f71564985cf4ae240bb9754`
  (two independent `npm pack` fetches into separate scratch dirs, identical
  bytes; re-fetch of 0.7.4 reproduces
  the ledger value `d11dd8a6…`, proving the method).
- Upstream tag `v0.7.5`: tag object `e9b05fda…`, peeled commit
  `b57c4da3c3ac3fb420a09e5a169d3e85f9529e93` (via `git ls-remote`, matches the
  plan claim `b57c4da` and the installed binary stamp below). npm metadata
  carries no `gitHead` field (0.7.4 has none either); `dist.shasum`
  `00ef5b6777aa02e9cd17a74e013e32c55989d30e` is the tarball sha1, not a commit.
- Installed host `rig` after `npm install -g @openrig/cli@0.7.5`:
  `rig --version` → `0.7.5 (b57c4da3)` (global install,
  `~/.npm-global/bin/rig`).

## Change shape (minimal)

1. `npm install -g @openrig/cli@0.7.5` on the build host; record
   `rig --version`.
2. Ledger doc `docs/sprints/CLI-0.7.5-BUMP.md` following the 0.7.4-ledger
   pattern (version, tarball SHA with two-fetch evidence, pin locations,
   tarball-diff disposition, verify output, rollback).
3. Update the 8 true-pin files that assert 0.7.4 (grep `0.7\.4` /
   `6d9e8e27`; change ONLY true version pins, never unrelated text):
   `AGENTS.md` (stack line + tarball sha ref + docs-map row; diff-stat MUST
   stay ≤15 lines), `README.md`, `Makefile`, `docs/USER_GUIDE.md`,
   `docs/TECHNICAL_DOCUMENTATION.md`, `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`,
   `docker/Dockerfile` (`ARG OPENRIG_VERSION`), `scripts/verify-rigs.sh`
   (V13 Dockerfile assert + V18 fail-closed version gate strings only —
   schema-provenance comments stay 0.7.4 because the vendored bytes ARE still
   0.7.4-derived, same as the 0.7.4 wave left 0.7.2 provenance in place).
4. Clean-tree regen ONLY if generator inputs changed (they did not — see §2);
   no regen owed, no leaves touched.
5. Full gates green; red-proof sabotage of the V18 pin (back to `0.7.4` →
   RED, restore → GREEN).

## Tarball-diff disposition (0.7.4 → 0.7.5, read-only, `/tmp` scratch extracts)

| Upstream change | Fleet impact |
|---|---|
| RigSpec `MEMBER_KEYS` permission sets IDENTICAL (`codex_permissions` ×13 both sides). `rigspec-schema.js` gains only additive `escalates_to` + `isEscalationTargetRef` edge tolerance. | **No generator-input change.** Pinned key sets, `verify-rigs.sh` key gates, and `schemas/rigspec-keys.pinned.json` stay correct as-is. |
| `daemon/docs/reference/schemas/run-record.v1.schema.json` byte-IDENTICAL; all five bundle/registry schemas byte-IDENTICAL; installed 0.7.5 copies equal the tarball copies. | **No re-vendor.** V18 byte-comparisons stay green against the installed CLI. |
| 19/19 `openrig-core` skill dirs identical set; only `queue-handoff/SKILL.md` gains parking prose (`rig queue block --on external:<what> --wake-after …`). openrig-core 0.1.21→0.1.22 (plugin.json version bumps only). | **Deferred (out of scope).** Vendored-via-generator content; same deferral rule as the 0.7.4 wave's 3 skill bodies. Our specs use none of the new prose. |
| New DB migration 126 (`escalation_target_refs`); `rig send` 60s result wait; send refusals 409-vs-500; `rig down` explicit stop; #2200 Codex restart refusal still not fixed. | **Recorded, not acted on.** Scratch-DB wave only — the real-state daemon was never touched; migration one-way caution carried in the ledger rollback §. |

## Fail-closed modes

- If `rig --version` does not print `0.7.5` after install, halt (do not fake the ledger).
- If any gate regresses vs the `c1da1fb` baseline for reasons unrelated to the version string, record the diff and halt rather than loosening gates.
- If the tarball diff had shown a MEMBER_KEYS or run-record change, this wave would halt and defer to a contract-sync wave (same rule as 0.7.4→Wave B) rather than editing provenance without re-vendoring.
- No new V-gate by default (Q9): V18/V13 pin-string updates are pin bumps of existing gates, not new coverage; V19 freeze stays 39.
