# Design: 102-closeout

## Architecture

Single worktree `.lane/trees/102-closeout`, branch `feat/102-closeout` from clean `main` (`2590a87`). Single triad (programmer → qa → drift-guard) covering M1→M4 in order. One PR at end.

## Milestone order (principal-approved)

1. **M1 HR-F18 deny + regen (code, highest collision risk, first).** Edit `fleet/fleet.yaml` seat `bash_allow` / `bash_deny` (surgical text edits, never `yaml.safe_dump` — strips comments). Run `python3 scripts/generate-rigs.py` on clean tree to bake `resolvedCommit`. Add appended verify block for bare-deny (new V-block, no renumber). Append `AGENTS.md` one-liner. Full regen required before any later milestone to avoid leaf drift.
2. **M2 HR-2.5 docs (no code).** Update operator docs to state spec-validate-canonical + bundle-8-intentional. No verify-script change.
3. **M3 writing-skills (patch + regen).** Add `fleet/skill-patches/` entry, regen, confirm 68/68. Second regen — MUST run on clean M1+M2 tree.
4. **M4 DAG note (evidence only).** Write `docs/evidence/102-closeout-dag.md`, reference `:896` check. No code.

## Trade-offs

- Deny vs warn (Q1): chose deny — warn leaves HR-F18 open, docs-only does not enforce in-seat.
- Single vs split (Q2): chose single — one triad + one PR for P3 bundle; split = 4x overhead.
- Vendor/patch vs direct (Q3): chose vendor/patch — direct violates one-rule; upstream-only leaves tree dirty.
- HR-2.5 document-only vs extend (Round 2): chose document-only — extending `bundle check` to all-51 risks upstream failure, needs separate spike.
- DAG local-only vs upstream (Round 2): chose local-only — no principal authorization for external filing, no gh side-effects.

## Fail-closed modes

- Regen on dirty tree refuses (allowlist) — always `git status --short` clean before `generate-rigs.py`.
- Missing secrets → seed strict-fails; use dummy keys in `/tmp` scratch (0600) for harness.
- If M1 deny breaks `--json --verify` allows, halt wave (do not loosen other denies to compensate).
- If M3 regen changes leaf count beyond expected patch, halt and diff `rigs/` vs `specs/` provenance before proceeding.

## Validation plan

Per-milestone red-proofs both directions into `docs/evidence/102-closeout-*.md`; global `make verify` + `audit_loop.py --self-test`; drift-guard reads verdict from disk.
