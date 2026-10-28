# Design: checker-batch-d (close the holes, guard the prose)

## Why structural walks beat pattern patches
#94's `$`-skip and #95's line-scan are the same bug class: a text shortcut that abandons inputs it cannot parse. Patching the shortcut with more patterns preserves the bypass shape. The fix in both is to make the structured form authoritative (`node` argv resolution + CI discovery; `tomllib` document walk) and demote text handling to attribution (line numbers) only.

## Why vendor instead of tighten locals (#98, #101)
Hand-tightened locals drift from upstream by construction (the issue's mutation proof: local errs `[]`, upstream 3 errs). Vendoring byte-exact + `cmp` makes drift structurally impossible and rides the existing rigspec pin precedent. For #101 the same rule forbids hand-editing `specs/`: fleet-side patch + regen keeps provenance clean.

## Why #96 stays out
#96's verification needs a live fleet (mid-session policy edit on a running seat) and its rollout contradicts #11's bounce semantics — a principal-level safety call (live policy control surface + subprocess escape → supported posture?). A gate block cannot prove it. Correct venue: live-seat decision round with #11; docs-split reconcile (maps refresh, everything else bounces) as the interim record.

## Why the stale-count guard is canonical (#102)
Wave B fixed three live docs to 31; post-V16 the run says 32. prose rots by default — every prior count refresh has decayed. A fail-closed SUMMARY-vs-doc equality block makes the next drift a red gate instead of a fresh issue.

## Failure modes
- `tomllib` walk newly flags a live committed TOML (false positive) → corpus pins the exact live fixture (`live-corrected-lints.toml`) green; any new FAIL must name a real undeclared lint.
- Vendored schema `cmp` fails on hosts with a different installed CLI → pin the check to the repo-pinned 0.6.13 package path (same as rigspec recipe), SKIP (never healthy) when absent.
- `.gitlab-ci.yml` discovery newly scans files with exotic YAML → parse defensively, findings only, never hard-fail the scan itself.
