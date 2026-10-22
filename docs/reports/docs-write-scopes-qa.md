# QA verdict: docs-write-scopes — PASS

Branch: `fix/docs-write-scopes` @ `7180444` (`f0ff176` catalog+spec+report, `7180444` regen leaves; parent `bae5d3a`).
Scope verified against: `openspec/changes/docs-write-scopes/` (proposal.md, specs/scopes/spec.md, design.md, tasks.md T1-T4).
Evidence: `docs/evidence/docs-write-scopes/red-proofs.log` (every sabotage + grep + exit code).
T5 (post-merge live reseed/relaunch proof) is explicitly out of scope — fleet still enforces old policy until human merge.

## 1. Acceptance results

| # | Check | Result |
|---|-------|--------|
| 1a | `make verify` | **22 passed, 0 failed** (baseline, post-revert re-run identical) |
| 1b | `python3 tests/test_render_seat.py` | **7/7 OK** (standalone + inside verify) |
| 2 | `git diff bae5d3a..HEAD --stat` source scope | **PASS** — only `fleet/fleet.yaml` (+6), regen leaves (`registry/`, `rigs/`, `rosters/`, `specs/`), spec dir, impl report. No other source path |
| 3 | Generated proof: six roles' `runtime/pi-permission-config.json` (rigs x2 copies + specs) contain new grants | **PASS** (table below) |
| G | Guard: no bash_allow / mcp / git-verb changes | **PASS** — fleet diff has zero removed lines, zero bash/mcp/server/git lines |

### Grant matrix (each verified in 2 rig copies + 1 specs copy = 18 files)

| Role | New grant | rigs copies | specs copy |
|------|-----------|-------------|------------|
| exec-product-director | `docs/brief/*` (+ existing `docs/product/*`) | OK x2 | OK |
| build-ts-node-fullstack | `docs/architecture/*` | OK x2 | OK |
| design-ui-ux-designer | `docs/design-system/*` | OK x2 | OK |
| design-design-system-eng | `docs/design-system/*` | OK x2 | OK |
| design-ux-research-analyst | `docs/design-system/*` (+ existing `docs/research/*`) | OK x2 | OK |
| design-a11y-specialist | `docs/design-system/*` | OK x2 | OK |
| exec-system-architect | unchanged (already `docs/architecture/*`) | n/a | n/a |

## 2. Red-proof results (all RED observed, all reverted)

| Proof | Sabotage | RED observed | Revert -> GREEN |
|-------|----------|--------------|-----------------|
| POSITIVE (pipeline carries change) | Deleted `fleet.yaml:3833` (`- docs/design-system/*` under design-ui-ux-designer), regen ALLOW_DIRTY=1 | ui-ux-designer generated configs show **zero** `docs/*` grants (grep exit 1); sibling design-system-eng still shows grant (exit 0) — leaves replay catalog, not stale | `git checkout -- fleet/fleet.yaml` + regen exit 0, grant grep exit 0 |
| NEGATIVE least-privilege | assertions on final tree, by grep | ts-node configs: `docs/brief` count **0** (3 files); designer: `docs/brief` 0, `docs/architecture` 0 | n/a (holds on unmodified tree) |
| NEGATIVE git verbs | `grep -Ei "git (add\|commit\|stage)"` over all 18 generated configs | **0 hits**; present verbs read-only: `git status/diff/log/show` | n/a |
| NEGATIVE AGENTS.md deny | grep rendered path rules + path_write | `"AGENTS.md": "deny"` present (x2 in ts-node config) | n/a |
| GUARD | fleet diff vs `bae5d3a` | zero minus-lines; zero bash/mcp/server/git lines | n/a |

Vacuous checks: **none** — the grant-presence grep demonstrably fails when the grant is removed.

## 3. Implementation-report verification

`docs/reports/docs-write-scopes-implementation.md` claims re-verified:
T1 +6 surgical lines OK (exact diff reproduced); T2 regen OK (`wrote 51 ...` observed live);
T3 22/0 + 7/7 both re-run by QA OK; dry-run-only / old-policy-until-bounce caveat OK;
T4 guard list OK (all four red-proofed); regen-noise note OK (one addition: regen also
stamps `resolvedCommit=<current HEAD>` into `registry/` — provenance noise per AGENTS.md
convention, restored via `git checkout -- registry/`).

## 4. Tree state + verdict

- `git diff --stat` (tracked) after reverts: **empty** -> tree matches `f0ff176`+`7180444` content.
- `git status --short`: no `M` lines; only pre-existing `??` strays plus the two new QA files
  (`docs/evidence/docs-write-scopes/red-proofs.log`, this report). Nothing committed.
- **Verdict: PASS.** Merge-ready pending human review; T5 live proof (reseed + relaunch +
  slice self-delivery) remains post-merge QA-owned, gated on TPM collect-drafts landing
  first (bounce kills in-memory drafts).
