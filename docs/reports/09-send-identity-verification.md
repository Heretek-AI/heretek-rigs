# 09-send-identity — independent adversarial verification (drift-guard)

Wave: `2026-10-28-09-send-identity` (branch `feat/09-send-identity`, tip `12fba9a`, base `4b453a2`).
Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/09-send-identity`.
Auditor: independent (no code changed except this report; no commits; no pushes).
Files read from disk (no summaries trusted): `AGENTS.md`,
`openspec/changes/2026-10-28-09-send-identity/{proposal,design,specs/send-identity/spec,tasks}.md`,
`docs/reports/09-send-identity-implementation.md`, `docs/reports/09-send-identity-qa.md`,
`docs/evidence/09-send-identity/red-proofs.log`, `docs/evidence/09-send-identity-spoof.md`,
`docs/evidence/09-send-identity-rotation.md`, `scripts/send_identity.py`,
`tests/test_send_identity.py`, `scripts/verify-rigs.sh` (diff + V-headers),
`scripts/seed-rig.py` + `scripts/render-seat.py` (diffs), registry diff filter.

## 1. Traced-requirements table (REQ-S1…S4, every scenario)

| Req / scenario | Implementation | Test | Evidence / re-run |
|---|---|---|---|
| REQ-S1 attested send accepted | `scripts/send_identity.py:230-251` `mint_attestation` + `:270-339` `verify_attestation` → `attested`; wired at seed `scripts/seed-rig.py` (`issue_sender_binding` call) and render `scripts/render-seat.py` (`send-identity.json` `!cat` block) | `test_valid_fresh_attestation_records_attested_sender` | corpus 25/25 OK re-run; verify 36/0 |
| REQ-S1 unattested held UNVERIFIED | `verify_attestation` missing/malformed/MAC-fail → `unverified` (`:300-329`); `seen=None` fails closed | `test_missing_attestation_holds_unverified`, `test_malformed_attestation_is_unverified`, `test_tampered_attestation_is_unverified`, `test_wrong_binding_secret_is_unverified` | same green re-run |
| REQ-S2 spoofed `--source` ignored | `:333-339` attested sender wins; conflicting claim only logged redacted, never recorded | `test_spoofed_claimed_source_is_ignored` | red-proof S1a + QA-R3a; auditor spot-check §6 (RED then GREEN) |
| REQ-S2 replay rejected | `:330-331` `nonce in seen` → `rejected`, redacted log | `test_replay_of_valid_attestation_is_rejected` | red-proof S1b + QA-R3b; auditor spot-check §6 (RED then GREEN) |
| REQ-S2 cross-rig impossible | `:314-318` `rig != expected_rig` → `unverified`; grant scope via reused `_grant_scope_matches` | `test_cross_rig_presentation_fails_scope` + `test_scope_mismatch_heals_via_revoke_and_re_add` | red-proof S1c + QA-R3c (auditor did not re-run this sabotage; 2-of-4 minimum met) |
| REQ-S2 bare-send still denied | fleet triple untouched; leaves regenerated stamp-only | `test_fleet_declares_exact_bare_deny_triple` + `test_rendered_maps_deny_bare_send_allow_addressed_send` | red-proof S1d + QA-R3d; V22 header intact |
| REQ-S3 V28 gate (append-only) | `scripts/verify-rigs.sh` V28 block (filename/grant-name rules, issuance+verify markers, `!cat` markers, corpus rc=0 with ≥20 floor, S0 evidence checks) | corpus itself (25 tests) | verify 36/0 re-run; FAIL-ONLY in red-proofs.log (dynamic exit 1 / 35+4 + static `git show 4b453a2:` zero markers) |
| REQ-S3 post-fix gates green | V28 PASS + 36/0 + corpus + `make test` claim | `tests/test_send_identity.py` (25) | verify 36/0 + corpus 25/25 + self-test PASS + idempotent PASS re-run (full `make test` NOT re-run by auditor — see §7) |
| REQ-S4 rotation runbook | `docs/evidence/09-send-identity-rotation.md` §1 (revoke + re-add, every mint `--seat`+`--rig`) + §2 live scratch (port 18439, re-key both directions) | N/A (runbook) | `--seat` ×7, `--rig` ×8, rig-less mint lines 0 re-run; verdict lines present |
| REQ-S4 secrets discipline | 0600 mkstemp+replace (`:197-217`), pre-mint 0600 refuse (`:164-170`), `!cat` render, `_redact_for_log` on every new log path (`_fail`, store-error, `_deny`, claim-conflict) | `test_unparseable_issuance_output_revokes_and_fails` (no 40+ run in err), `test_existing_non_0600_store_refuses_pre_mint`, render `!cat` test with `BEARER_RUN_RE` assert | spoof+rotation grep exit 1 re-run (zero unredacted) |
| tasks S0 (spike + transcript + non-vacuous grep) | scratch-only spike (never committed) | N/A | `docs/evidence/09-send-identity-spoof.md` has `accepted forged sender:` + `SPOOF-OK pre-fix` lines; grep 40+ exit 1 re-run |
| tasks S1 (S1.1–S1.3 + 4 red-proofs) | `send_identity.py` + seed/render wiring + 25-test corpus, dummy keys | all above | red-proofs.log S1a–S1d each RED-for-right-reason then reverted |
| tasks S2 (V28 + asserts + FAIL-ONLY) | V28 block + V19 bump + docs | corpus floor | §2 + §6 |
| tasks S3 (rotation + docs-map + reports + unarchived) | rotation.md executed; AGENTS.md:73 docs-map line pre-exists from base spec package (no-op honored); change dir unarchived | N/A | confirmed on disk |
| tasks closeout (Refs #9, no upstream) | all 9 wave commits carry `Refs #9` | N/A | `git log` re-checked; zero `Closes/Fixes/Resolves #9` in commit subjects/bodies; no upstream filing paths in diff |

## 2. Anti-stub scan results

- `git diff 4b453a2..HEAD --stat`: 31 files (scripts 4 incl. new `send_identity.py` 339 lines; tests 2 incl. new 514-line/25-test corpus; 3 live-count doc lines; 4 new evidence/report files; 16 registry provenance-stamp files; this report).
- Pattern scan over `scripts/send_identity.py`, `tests/test_send_identity.py`, and the `seed-rig.py`/`render-seat.py` hunks for `TODO|FIXME|XXX|NotImplemented|pass #|\|\| true|skipTest|@unittest.skip|assert True`: **zero matches**.
- `except` audit: `OSError` (symlink unlink, store, add-spawn), `FileNotFoundError` (lstat-absent → `_st=None`), `(OSError, TimeoutExpired)` (add-spawn → `_fail`), `BaseException` (tmp-cleanup re-raise — correct, not swallowed), inner `OSError` (tmp unlink best-effort `pass` inside cleanup only), `Exception` (MAC compute → `unverified` deny). Every handler either fails closed (`_fail`/`_deny`/rc=2) or re-raises. No swallowed errors.
- Vacuous-test check: issuance tests assert `--seat`/`--rig` on the fake-rig log, 0600 mode bits, revoke-and-replace body inequality, and absence of 40+ runs; verify tests assert exact `attested`/`rejected`/`unverified`+`None` transitions; render tests assert exact `!cat <path>` value and strict/degraded/unbound branches; bare-send tests probe every rendered leaf (`pps_decide` deny bare / allow addressed, `probed > 0`). Fake `rig` is stateful (grants dict with seat/rigs/roots/workspace/owner, counter-minted tokens, list/add/revoke semantics), not a pass-through. The one weak assertion (`assertIsNone(BEARER_RUN_RE.search(body) and None or None)` in `test_issue_mints_with_seat_and_rig_scope`) is dead-weight but harmless — the companion `test_unparseable_issuance_output_revokes_and_fails` and V28's own 40+ scans on module/render/evidence sources carry the real redaction weight. Not a finding.
- Production-reachability of the four refusals: the refusal logic lives in `verify_attestation` (spoof-ignore `:333-339`, replay `:330-331`, scope `:314-318`) reused by import (never duplicated), with issuance discipline (`--seat`+`--rig`, 0600, fail-closed parse, revoke-on-fail) executed in the real `seed-rig.py` path and the `!cat` reference rendered by the real `render-seat.py` path for grant-bound roles. NOTE (non-blocking): no existing relay script (`seat-sandbox.sh`, `send-authenticated.sh`) was modified to call `verify_attestation` — enforcement is library + seed/render + gate level, which is exactly what the spec/tasks require (no relay-script edit is specified anywhere in REQ-S1…S4 or tasks S1.2). The queue/daemon path still holds unattested sends UNVERIFIED by default (availability-preserving, per design). No theater finding.

## 3. Drift diff analysis (One Rule + V-gates)

- `git diff 4b453a2..HEAD --name-only -- specs/ rigs/ rosters/ fleet/`: **empty** — zero hand-edits in generated-leaf trees. (One transient `fleet/fleet.yaml` line removal during red-proof S1d was reverted via `git checkout`; tree verified clean after.)
- Registry diff filter (`^[+-]` minus `++/--`, grouped): only `resolvedCommit: 253413f… → 8ff71cc…` (×8 yaml + ×8 json) and `canonicalUrl: …/tree/253413f… → …/tree/8ff71cc…` (×8). **Zero non-provenance lines.** Generator-output only, never hand-edited.
- V-headers: base and head print identical `== V1 ==`…`== V27 ==` lines (titles byte-identical incl. V22 `Bare Queue/Send Deny`, V23 `Per-Seat MCP Bearer Grants (107-identity M1)`, V24 `Rotation Runbook Step-3 --rig Mandate (107-identity R1)`); `diff` of the `== V[0-9]+` line sets shows exactly one added line: `== V28. Send-Identity Attestation (09-send-identity S1) ==`. No renumber/reword.
- Sanctioned companions of the V28 append: `_v19_canonical` 35→36, `passes + 1`→`passes + 2` checks + message with explanatory comments (V19's own bump rule for a new `ok()`-bearing gate), and the three live-count doc lines (`AGENTS.md`, `README.md`, `docs/USER_GUIDE.md`) 35→36. Each V-header diff line inspected individually — no other V1–V27 line touched.
- `openspec/changes/2026-10-28-09-send-identity/` unarchived (base spec package + wave work only). `HANDOFF.md` / `docs/IMPLEMENTATION_PROMPT.md` still state the old 35-count — V19 does not scan them; pre-disclosed coordinator-owned state, untouched by design. Not a finding.

## 4. Secrets re-check (auditor re-ran)

- `grep -rE '[A-Za-z0-9_-]{40,}' docs/evidence/09-send-identity-spoof.md docs/evidence/09-send-identity-rotation.md` → no output, exit 1. PASS.
- Rotation mandate: `--seat` ×7, `--rig` ×8, rig-less mint lines (`mcp token add|sender.*add` without `--rig`) 0. PASS.
- Full-diff 40+ grep hits are limited to `tests/__pycache__/*.pyc` binaries, `archive/2026-10-28-overhaul/` pre-existing content, and long test identifiers (`test_replay_of_valid_attestation_is_rejected`, `test_fleet_declares_exact_bare_deny_triple`, `test_binding_filename_*` — matched by the naive character class because they exceed 40 word/underscore chars). No bearer-shaped secret material. `red-proofs.log` contains one quoted 47-char sabotage token string (`orAbCd…`, QA-R6) presented as the injected canary and reverted — a documented non-vacuous-grep demonstration, not a live credential. Evidence files free of bearer-shaped strings. PASS.
- No real credentials in commands, files, reports, or audit output; dummy keys only in tests/scratch (`/tmp`, 0600); `~/.config/heretek-rigs/secrets/` untouched. PASS.

## 5. Scope check

- Zero daemon changes, zero upstream filings, zero fleet-host mutations: diff paths contain no `daemon`/upstream/fleet-host files; proposal non-goals honored. PASS.
- All 9 wave commits (`51228f3`…`12fba9a`) carry `Refs #9`; `git log --grep=Closes` empty; case-insensitive `closes/fixes/resolves #9` scan of commit subjects+bodies: none. The only `Closes #9` string in the wave dir is the backticked `(never \`Closes #9\`)` instruction in the base-committed `tasks.md:13` prose — not a commit/PR body, no GitHub closing effect. Issue #9 stays open. PASS.
- No `--force`/push performed by the wave (linear branch history, no merge commits); auditor performed no push/force. History verified read-only. PASS.

## 6. QA spot-checks (auditor sabotage, both reverted, tree clean)

- SPOT-1 (spoof, mirrors S1a/QA-R3a): final `attested` return changed to `sender=claimed_source or sender` → `test_spoofed_claimed_source_is_ignored` RED (`FAILED (failures=1)`, forged claim recorded: `- red-actor@other-rig / + blue-probe@test-rig` diff) → backup restored → single test OK.
- SPOT-2 (replay, mirrors S1b/QA-R3b): `if nonce in seen:` → `if nonce in seen and False:` → `test_replay_of_valid_attestation_is_rejected` RED (`FAILED (failures=1)`, `- attested / + rejected` diff) → backup restored → full corpus 25/25 OK.
- Baseline re-runs (clean tree): `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 36 checks passed, 0 failed` (V28 PASS listed), exit 0; `python3 -m unittest tests.test_send_identity` → 25/25 OK; `python3 scripts/audit_loop.py --self-test` → `SELF-TEST PASSED`; `python3 scripts/generate-rigs.py --check-idempotent` → byte-identical PASS (post-run registry re-stamp verified provenance-only — `resolvedCommit`+`canonicalUrl` lines exclusively — then reverted with `git checkout -- registry/`). `git status --short` clean apart from this report.
- `red-proofs.log` failure signatures are non-vacuous in both directions (each RED names the exact violated invariant, each restore returns to GREEN).

## 7. What was not verified

- Full `make test` (530 tests, ~104s) was NOT re-run by this auditor; the corpus (25/25), V28's in-gate corpus run, verify 36/0, self-test, and idempotence were re-run instead. The `make test` 530-OK claim rests on the implementation report + QA report (3× runs recorded there), not on an auditor run.
- Live-daemon behavior (S0 spoof transcript, S3 rotation scratch run) was verified from the committed redacted transcripts and the re-run greps, not by relaunching scratch daemons.
- Push/force absence beyond the local history (no remote access attempted).

## Findings

None. F1…: none raised.

VERDICT: PASS