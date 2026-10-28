# 09-send-identity rework-2 implementation report (Refs #9, never Closes #9)

Wave: 09-send-identity-r2 | Branch: fix/09-send-identity-r2 | Base: main @ 5bbb846
Scope: address 5 CodeQL findings on PR #128 (C1…C5) in
`scripts/send_identity.py` + `tests/test_send_identity.py`.
No V-gate changes (V28 text untouched); nothing under `specs/`, `rigs/`,
`rosters/`, `registry/`, `openspec/`.

**CodeQL re-scan substitute (stated honestly):** CodeQL cannot run
locally in this environment. Validation substitutes for the re-scan:
(1) per-fix red-proofs (sabotage → RED → revert → GREEN, logged in
`docs/evidence/09-send-identity/red-proofs.log`), (2) the gate battery
below — `verify-rigs.sh --check-only` (36/0, V28 PASS), `make test`
(532 OK), `python3 -m unittest tests.test_send_identity -v` (27 OK),
`audit_loop.py --self-test`, `generate-rigs.py --check-idempotent`,
secrets grep clean. The coordinator should report exactly this.

## Per-finding verdicts (each verified against on-disk code, not trusted blindly)

| ID | Verdict | Evidence |
|----|---------|----------|
| C1 — `tests/test_send_identity.py` refusal fixture `chmod 0o644` (py/overly-permissive-file) | **True positive (hygiene class), zero live exposure; fixed** | HEAD file confirmed `os.chmod(target, 0o644)` in `test_existing_non_0600_store_refuses_pre_mint`; fixture content is the literal `"dummy"` in 0700 `/tmp` scratch, so exposure is nil. Mask changed to `0o640` (non-0600 → refusal still triggers; others-bits 0 → not world-readable). |
| C2 — `send_identity.py` mismatch-warn interpolates `{session}` (py/clear-text-logging) | **Taint-flow true positive, no live leak; hardened** | HEAD line ~153 confirmed raw `{session}`. Data-flow: `session` carries only the seat identifier; the minted token flows `proc.stdout → parse_issued_token → 0600 mkstemp+replace` and never reaches this sink. Routed through `_redact_for_log` (`_session_log`) per REQ-S4. |
| C3 — symlink-removed warn interpolates `{session}` + `{binding_path.name}` | **Same as C2; hardened** | HEAD lines ~157–159 confirmed. `binding_path.name` is session-derived (`send-id-<session>.key`, `/`+`..` refused at the choke point). Both values now redacted (`_session_log`, `_binding_log`). |
| C4 — missing-file warn interpolates `{session}` + `{binding_path.name}` | **Same as C2; hardened** | HEAD lines ~161–163 confirmed. Same fix, same justification. |
| C5 — issued-ok stdout line interpolates `{session}` + `{binding_path.name}` (double-flagged) | **Same as C2; hardened** | HEAD line ~227 (`ok {session}: sender binding issued (...)`) confirmed. Same fix. The sibling reuse-ok line (same class, unflagged) was hardened identically. |

No finding was refuted as false: C1 is a real (if harmless) permissive
mask; C2–C5 are real taint-to-sink flows carrying identifiers only.
No token/key bytes could reach any of them (traced; see H2).

## Hypothesis outcomes

- **H1 (C1) — PROVEN.** The flagged chmod builds a deliberately
  non-0600 fixture (content `"dummy"`) to prove pre-mint refusal.
  `0o640` preserves semantics exactly: the pre-mint gate refuses
  anything `!= 0o600`, and the refusal test passes under both masks
  (shown during sabotage). Red-proof RP-R2-C1: 0644 sabotage → probe
  asserting `mode & 0o007 == 0` RED (mode 644, world-bits 4);
  restore → GREEN (mode 640, world-bits 0, still != 0600).
- **H2 (C2–C5) — PROVEN.** Sinks carry identifiers only (trace above);
  prior work already proves tokens absent from stdio
  (`assertNotIn(body, out/err)` in the mint test). Fix routes every
  message through the existing `_redact_for_log` choke point (never
  duplicated). Byte-identical stdout/stderr for real identifiers
  proven: `_redact_for_log(x) == x` for `blue-x@rig-y`,
  `send-id-blue-x@rig-y.key`, `blue-x@rig-y/send-identity` (regex needs
  40+ `[A-Za-z0-9_-]` runs; `@`/`.` break them; all < 200 chars).
  Red-proof RP-R2-C2C5: raw-`{session}` sabotage + `"A"*45` session →
  RED (45-char run on stdout verbatim); restore → GREEN (redacted).
  Corpus extended ONLY with `test_reuse_path_emits_no_token_material`
  (reuse path emits neither stored token bytes nor any 40+ run).
- **H3 (own sweep) — DONE, no new fix needed.** Audited every
  print/raise site in `scripts/send_identity.py`: all subprocess and
  exception detail already flows through redacting `_fail`
  (`cannot list grants`, `cannot remove symlinked …: {e}`,
  `cannot revoke … {binding_name}`, `refusing to store …`,
  `token add failed: {e}` / `{detail}`) or `_deny` (all
  verify-side reasons). The one same-class-adjacent site — L350 raw
  `{e}` inside `f"mac computation failed: {e}"` — flows into `_deny`,
  which redacts. Red-proof RP-R2-H3: `_deny`-without-redact sabotage
  + attacker attestation with bearer-shaped rig field (`"B"*45`) →
  RED (raw in stderr); restore → GREEN (`'…redacted…'`).
  Caller-facing ValueErrors (L75/L262/L268) carry identifiers/static
  text only — left untouched per minimal-diff.

## Files changed

- `scripts/send_identity.py` (+28/−10 with test file): `_session_log` /
  `_binding_log` precomputed via `_redact_for_log`; all 7
  session/filename log interpolations in `issue_sender_binding`
  (mismatch warn, symlink warn, reuse ok, missing warn, unparseable
  error, store-OSError error, issued ok) use them. No logic touched.
- `tests/test_send_identity.py`: refusal fixture `0o644` → `0o640`;
  added `test_reuse_path_emits_no_token_material`.
- `docs/evidence/09-send-identity/red-proofs.log`: appended
  RP-R2-C1 / RP-R2-C2C5 / RP-R2-H3 (append-only, history preserved).

## Acceptance (all green, exact outputs)

- `./scripts/verify-rigs.sh --check-only` → exit 0,
  `SUMMARY: 36 checks passed, 0 failed.`, V28 PASS (V1–V27 intact).
- `make test` → exit 0, `Ran 532 tests … OK` (118.9s).
- `python3 -m unittest tests.test_send_identity -v` → exit 0,
  `Ran 27 tests … OK` (26 pre-existing + 1 new).
- `python3 scripts/audit_loop.py --self-test` → exit 0,
  `SELF-TEST PASSED`.
- `python3 scripts/generate-rigs.py --check-idempotent` → exit 0 on the
  clean (committed) tree, byte-identical (no regen needed: change
  touches no fleet/catalog/generator inputs).
- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md docs/evidence/09-send-identity-rotation.md` → exit 1, no output.

## Commits (branch fix/09-send-identity-r2, Refs #9)

- `7932e80` fix(09-send-identity): address CodeQL findings C1–C5
  (`scripts/send_identity.py`, `tests/test_send_identity.py`,
  `docs/evidence/09-send-identity/red-proofs.log`).
- Report commit (this file): docs(09-send-identity): rework-2 report
  (Refs #9) — see `git log` for its hash.
- `8bbde89` chore(09-send-identity): regenerate leaves for provenance
  (Refs #9) — 16 registry files, `resolvedCommit` re-bake only (known,
  accepted per AGENTS.md); post-regen `verify-rigs.sh --check-only`
  re-run: 36 passed, 0 failed, V28 PASS.

## Self-audit (unfinished stated plainly)

- CodeQL itself was NOT re-run (unavailable locally); re-scan
  outstanding on the coordinator/PR side. All substitutes above are green.
- The prior partial attempt's uncommitted edits were adopted only after
  full re-verification (HEAD-vs-worktree diff review, data-flow trace,
  three red-proofs); nothing was taken on trust.
- Nothing failed, nothing skipped, no stubs introduced.
