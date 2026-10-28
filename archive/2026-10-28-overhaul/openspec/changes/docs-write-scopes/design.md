# Design: docs-write-scopes

## Why per-area, not per-file or docs-wide
Per-file grants couple the fleet catalog to mission file names (godot paths
differ from asset-manager paths). docs-wide grants to authors erase the
staging/relay separation and let any author clobber any doc. Per-AREA grants
match role identity (brief/architecture/design-system are the roles' own
documentation areas) and are mission-agnostic: every future docs mission
reuses them with zero catalog churn.

## Why not just use the scribe
delivery-tech-docs-lead already holds docs/*, but scribe-relay was rescinded
as a pattern (authorship must stay with slice owners; verbatim copies add a
hop and mismatch risk). Owners writing their own files is the exec-ruling
recommendation from the godot mission ("targeted write grants").

## Failure modes
- Regen dirties generated leaves: Mitigated — change is catalog-only;
  generate-rigs.py replays deterministically. Verify 22/0 gates it.
- Running seats enforce old policy until bounce: reseed + relaunch AFTER
  human merge; in-memory drafts die on bounce — collect-drafts qitem must
  land first (TPM report). If drafts are not secured, bounce waits.
- Overreach creep: QA red-proofs the negative (denials hold outside area).
