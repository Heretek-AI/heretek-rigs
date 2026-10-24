# remediate-lane-guard — implementation report (#67 worktree-stale baked-path guard)

Stage: remediate-lane-guard (Wave 5 hardening micro-stage) · Branch: remediate/audit-66-lane-guard · HEAD base: 2b103db

## Finding
Post-Wave-4 merge check caught generated leaves merged from the Wave-4 worktree baking an absolute `shellPath` into the worktree dir (`.lane/trees/remediate-supplychain/scripts/seat-sandbox.sh`; confirmed via `git show` of the pre-fix blob). Fixed by re-baking on the canonical checkout (2b103db). Root cause: `render-seat.py` emits `shellPath` from the rendering checkout's own path, so any worktree bake is checkout-stale by construction. The V12 per-seat assert (`verify-rigs.sh:1679-1683`) only checks `endswith("scripts/seat-sandbox.sh")`, which a stale absolute path satisfies — while pi fails closed ("Custom shell path not found") at seat startup. Gotcha 5 incompletely met for the baked VALUE.

## Guard location
NEW `== V14. No Worktree-Stale Absolute Paths (#67) ==` block in `scripts/verify-rigs.sh`, placed after the V13 `ok()` and before `SUMMARY` (V13 label already taken by the supply-chain wave; V1–V13 lines untouched — diff is 32 insertions, 0 deletions). For every committed `specs/agents/*/*/runtime/pi-settings.json` and `rigs/*/agents/*/runtime/pi-settings.json`, it FAILs when `shellPath` or any `packages[]` value contains `/.lane/`; the message names the seat, file, key, and offending value plus `#67 worktree-stale absolute path — re-bake on a canonical checkout`.

## Proofs
- Green baseline (unmodified tree): `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 29 checks passed, 0 failed`, exit 0.
- Green with guard: `SUMMARY: 30 checks passed, 0 failed`, exit 0 (`[PASS] Worktree-stale paths (#67) green: 153 committed pi-settings.json leaves carry no /.lane/ baked paths`).
- Red-proof shellPath: temp-planted `/.lane/trees/evil/scripts/seat-sandbox.sh` on `cache-streaming-eng` (temp-edit + `git checkout --` revert, never committed) → exit 1, `29 checks passed, 1 failed`, named V14 gate. The planted value still satisfies V12's `endswith` — the exact gap closed.
- Red-proof packages[]: temp-planted `/.lane/`-bearing `packages[0]` → exit 1, same named gate.
- Revert: `git status --short` shows only `M scripts/verify-rigs.sh`; verify re-run → 30/0.
- `make test`: `Ran 257 tests ... OK` across all 11 Makefile suites, exit 0 (untouched).
- `scripts/generate-rigs.py` not run (no catalog edits; nothing to re-bake). No regen needed.

## NOTES pointer
Full log appended to `docs/NOTES.md` § `remediate-lane-guard (#67 worktree-stale baked-path guard — Wave 5 micro-stage)` (catch evidence, fix, V12 gap, guard placement, commands + outputs).

## Commit
Single commit on `remediate/audit-66-lane-guard` (explicit `git add` of `scripts/verify-rigs.sh`, `docs/NOTES.md`, this report): `remediate(#67): reject worktree-stale absolute paths in baked seat settings` + mandated attribution footer.
