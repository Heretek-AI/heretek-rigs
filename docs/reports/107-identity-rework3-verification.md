# 107-identity rework cycle 3 (FINAL, 3 of 3) — drift-guard binding verification

Stage/wave: 107-identity rework cycle 3 FINAL re-audit (rework budget exhausted after this).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/107-identity`
(branch `feat/107-identity` at `f80bb35`, tree clean: `git status --short` empty at audit).
Auditor changed no code and made no commits; this report is the only new file.
Read from disk: AGENTS.md, `openspec/changes/107-identity/{proposal.md,specs/identity/spec.md,design.md,tasks.md}`,
`docs/reports/107-identity-{implementation,rework1,rework2,rework3}.md`,
`docs/reports/107-identity-{verification,rework1-verification,rework2-verification}.md`,
`docs/evidence/107-identity-{m0,rotation,queue}.md`,
`docs/evidence/107-identity/{red-proofs.log,rework1-red-proofs.log,rework2-red-proofs.log,rework3-red-proofs.log,qa-run.log}`.

## 1. R1/R2 fixes hold and are bounded (runbook text + one spec line; no code beyond rework 2)

- R1 (runbook step 3 carries `--rig`): `docs/evidence/107-identity-rotation.md:27-33` reads
  `` `rig mcp token add <name> --seat <session> --rig <managed-rig>` `` with the
  seeder-scope / `_grant_scope_matches` / revoke-and-replace rationale. §2 executed-live
  history (seat-only M1 shape, pre-F5) deliberately untouched — history preserved, not rewritten.
  Prose-only doc fix; `git diff 2b2fc12..HEAD -- scripts/ tests/ fleet/` is EMPTY (no code change).
- R2 (REQ-I1 opt-in limit): `openspec/.../specs/identity/spec.md:12` now limits issuance to
  "seats whose role binds a catalog entry marked `seat_grant: true` (or via explicit opt-in)";
  unmarked HTTP + stdio unchanged. One-line diff (`git diff 2b2fc12..HEAD -- openspec/` = 1 file, 1+/1-).
  Behavior already covered by `SeatNeedsGrantTests`; no test change needed.
- Boundedness: `git diff 2b2fc12..HEAD --stat` = 6 files only: rotation.md (R1, 9 lines),
  spec.md (R2, 1 line), rework2-verification.md, rework3.md, rework2/3-red-proofs.log.
  Zero `scripts/`/`tests/`/`fleet/`/`specs/`/`rigs/`/`rosters/`/`registry/` content change since rework 2.

## 2. Benign verdicts N1–N4 + old threads accurate (verified against code on disk)

- N1 (list-form subprocess): all 5 `subprocess.run` sites in `scripts/seed-rig.py`
  (:212 list, :255 revoke, :358 rig-scoped add, :552/:557 render argv) are list-form;
  `shell=True` zero hits. BENIGN confirmed — accurate.
- N2 (choke-point covers :297): `_fail` first statement is `msg = _redact_for_log(msg)` (:290),
  covering the :297 strict error and all six call sites; sole direct print (:401) carries its own
  `{_redact_for_log(e)}`. COVERED confirmed — accurate, no dead-code second redaction added.
- N3/N4 (0644 fixtures): `tests/test_identity_m1.py:270,281` `os.chmod(p, 0o644)` intact inside
  the two F4 attack-setup fixtures; corpus 25/25 green unmodified. BY-DESIGN confirmed — accurate.
- Old threads (alerts 85–90): all six flagged-class expressions still route through the rework-2
  choke point; pure name/session/filename lines (:309–312, :320–327, :330–333, :374–377, :405)
  interpolate no external output. CONFIRMATION accurate — nothing new found.

## 3. R3 refutation evidence on disk

`docs/reports/107-identity-rework3.md` §R3 records the scratch-isolation live proof
(`OPENRIG_HOME=/tmp/107-r3-20261027`, daemon `:18453`, serve `:18457`):
two same-rig grants (`blue-a`/`blue-b@testrig`), `token add --help` confirms no seat-level scope
flag in 0.7.2, A's bearer → whoami resolves `blue-a@testrig`, B's → `blue-b@testrig`
(404s are the expected no-sessions-up scratch artifact; the discriminating fact is WHICH seat
each bearer resolved to). Server banner states the rule verbatim
("each caller acts as its grant's seat"). Cross-seat impersonation impossible by construction;
note-only disposition, no dead seat-level mechanism, no code change. Evidence present — accurate.

## 4. QA-noted R1 coverage gap is real and accurately described as docs-only

`docs/evidence/107-identity/rework3-red-proofs.log` §R1 honestly records: rig-less step-3 sabotage
trips NO committed gate (corpus 25/25 + verify 35/0 stay green); only the ad-hoc `/tmp/107-r1-gate.sh`
detector trips RED. Auditor independently confirms: `grep -n rotation scripts/verify-rigs.sh`
returns no gate lines — V23 checks catalog shape + filename helper + corpus count only.
Gap description is accurate: absent committed coverage (not a vacuous check), docs-only prose with
zero committed-code impact, residual risk explicitly disclosed with a V24/future-gate recommendation.
Not a FAIL under the severity rule (no stub, no vacuous check, no failing command, no missing deliverable).

## 5. V1–V23 unrenamed, SUMMARY frozen, generator rule holds

- V1, V2&V3, V4&V5, V6–V23 headers all present in order (V23 at line 2757, FAIL-ONLY, floor `>= 15`
  holds at 25). No renumber/reword in the rework-3 diff. SUMMARY frozen at 35.
- `git diff 51d7df1..HEAD --name-only -- specs/ rigs/ rosters/` → EMPTY (no hand-edits).
- `git diff 51d7df1..HEAD -- registry/` → 16 files, every line a `resolvedCommit`
  `892e1a7…→47e71aa…` provenance re-stamp + matching `canonicalUrl` pins; `grep -c DIRTY` → 0.
  Provenance-only delta, zero DIRTY — compliant (accepted re-lag per AGENTS.md).

## 6. No stubs/skips, no committed secrets

- `TODO|FIXME|...|NotImplementedError|skip|assert True||| true` over `seed-rig.py`,
  `test_identity_m1.py`, `render-seat.py` → no code hits. No skips, no bare pass, no `|| true`.
- `[A-Za-z0-9_-]{40,}` hits are ONLY long snake_case test/report identifiers; the single 47-char
  runtime value is `"Q" * 47` constructed in-test. Evidence logs carry redacted forms
  (`or...Tk`, `Q...Q (47)`) + `tokenSha256` hashes only. No `yaml.load`/`safe_dump` in touched code
  (`yaml.safe_load` only). No bearer material committed.

## 7. Red-proof audit (recorded by agency-qa, verified by auditor)

- T2 `red-proofs.log` S1–S8: every sabotage RED non-vacuously with exact failure signatures
  (V23 transport, `.key` suffix, header tamper, parser gut, V21 hand-edit, live deny matrix,
  live revoke→401, queue detector) and GREEN on restore; `git status --short` clean.
- `rework1-red-proofs.log` S1–S6: F2/F3/F4/F5/F1/V23 sabotages each RED then GREEN on restore.
- `rework2-red-proofs.log`: single-line redaction bypass (`msg = _redact_for_log(msg)` → `msg = msg`,
  1+/1-) → both redaction tests RED with verbatim 47-Q run in stderr; restore GREEN.
- `rework3-red-proofs.log`: baselines GREEN; R2 sabotage (`return bool(opt_in)` → `return True`)
  → 2 failures RED, restore GREEN (NON-VACUOUS); R1 honestly logged as GAP (see §4);
  N1–N4 verification-only; post-restore hashes byte-identical, status clean.

## 8. Re-run — real output (this audit, unmodified tree)

- `python3 -m pytest tests/test_identity_m1.py -q` → `25 passed` (expect 25: MET), exit 0.
- `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`, exit 0.
- `./scripts/verify-rigs.sh --check-only` → `V23/107-identity M1 green: ... 25 corpus tests pass
  (FAIL-ONLY, SUMMARY frozen)` + `SUMMARY: 35 checks passed, 0 failed`, exit 0.
- Failed/skipped commands: none failed; live-health `[SKIP]`s are the normal no-daemon data-source
  skips (also recorded in `qa-run.log`).

## Findings

None. R1/R2 bounded doc-s fixes hold; N1–N4/old-thread verdicts verified accurate; R3 refutation
on disk; the R1 coverage gap is real, docs-only with zero committed-code impact, and explicitly
disclosed (residual risk: a future edit could drop `--rig` from runbook step 3 without tripping a
committed gate — recommend a V24/future appended gate per the append-only rule). Stage shippable
as the last budgeted cycle.

VERDICT: PASS
