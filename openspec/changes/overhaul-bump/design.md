# Design: overhaul-bump

## Architecture

Single worktree `.lane/trees/overhaul-bump`, branch `feat/overhaul-bump` from clean `main` (`88cd930`). Single triad (programmer → qa → drift-guard). One PR at end.

## Verified upstream facts (live, 2026-10-28)

- npm `@openrig/cli@0.7.4`: `version = '0.7.4'`, tarball `https://registry.npmjs.org/@openrig/cli/-/cli-0.7.4.tgz`, sha256 `d11dd8a6fc78f0c4d7afeae462c07c2af0fb9fe460990950be495016734920a1` (via `npm pack`, /tmp scratch).
- Published `package/daemon/dist/domain/rigspec-schema.js` contains `codex_permissions` (Wave B contract material, not this wave).
- Installed host `rig` is `0.7.2 (8b180689)` — this wave upgrades the host install.

## Change shape (minimal)

1. `npm install -g @openrig/cli@0.7.4` on the build host; record `rig --version`.
2. Ledger doc `docs/sprints/CLI-0.7.4-BUMP.md` following the 0.7.2-ledger pattern (version, tarball SHA, pin locations, verify output).
3. Update any in-repo version pins that assert 0.7.2 (grep `0.7.2` / `8b180689` across docs/scripts/schemas; change ONLY true version pins, never unrelated text).
4. Clean-tree regen ONLY if generator inputs changed (a pure pin bump should need none); if regen runs, chore-commit leaves separately.
5. Full gates green.

## Fail-closed modes

- If `rig --version` does not print `0.7.4` after install, halt (do not fake the ledger).
- If any gate regresses vs the `88cd930` baseline for reasons unrelated to the version string, record the diff and halt rather than loosening gates.
- Bearer-token behavior was proven on 0.7.2 (107-identity M0); if 0.7.4 changes `token add`/`serve --http` CLI surface, record the delta in the ledger and re-run the M0 probe forms (read-only, scratch env) — do not redesign issuance here.
