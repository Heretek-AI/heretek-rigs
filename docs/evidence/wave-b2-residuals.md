# Evidence: Wave B2 residuals-107 (T2 red-proofs)

Branch: `feat/residuals-107` · Worktree: `.lane/trees/residuals-107` · T1 commit: `503629c`
Date: 2026-10-24 · Stage: residuals-107 (T2 red-proofs only; drift-guard follows as T3)
Acceptance command: `./scripts/verify-rigs.sh --check-only` AND `pytest tests/test_policy_verifier.py tests/test_render_seat.py`

## 1. Baseline (unmodified tree @ 503629c)

- `git log --oneline -5`: `503629c feat(residuals-107): V13 rate-limit skip arm plus doc count/pin refresh` on `feat/residuals-107`. Verified.
- `make verify` → `SUMMARY: 31 checks passed, 0 failed.` + `LIVE-HEALTH WARN (advisory, exit 0)`. Exit 0.
- `./scripts/verify-rigs.sh --check-only` → `SUMMARY: 31 checks passed, 0 failed.` Exit 0.
- `python3 -m pytest tests/test_policy_verifier.py tests/test_render_seat.py` → `46 passed in 7.13s` (34 policy_verifier + 12 render_seat). Exit 0.
- Proposal Acceptance 2: `grep -rn "26 checks" AGENTS.md docs/USER_GUIDE.md README.md` → no matches (exit 1, expected GREEN);
  `grep -rn "31 checks" ...` → 4 hits (AGENTS.md:15, AGENTS.md:46, USER_GUIDE.md:127, README.md:47; exit 0).
- Proposal Acceptance 3: `grep -n "mendable/firecrawl:1.6.0" docs/TECHNICAL_DOCUMENTATION.md` → no matches (exit 1, expected GREEN);
  `grep -n "2.10.19" docs/TECHNICAL_DOCUMENTATION.md` → line 408 `ghcr.io/firecrawl/firecrawl:2.10.19` (exit 0).
- T1 shape confirmed: `scripts/verify-rigs.sh:1781` pattern contains `toomanyrequests|rate limit`;
  live pin `docker-compose.sidecars.yml:93` = `ghcr.io/firecrawl/firecrawl:2.10.19@sha256:50446cbc…6d7ed`, matching `docs/NOTES.md:305`.

## 2. Red-proof (a): V13 rate-limit arm — both directions

Target: `scripts/verify-rigs.sh:1781` skip pattern.

Baseline (arm ON):
- Pattern: `(network|timeout|timed out|connection|refused|Temporary failure|Could not resolve|no such host|TLS|certificate|proxyconnect|proxy connect|toomanyrequests|rate limit)` (re.IGNORECASE).
- Fixture `denied: toomanyrequests: You have reached your pull rate limit` → MATCH → SKIP. Verified exit 0.
- Fixture `ERROR: Rate Limit Exceeded for registry` → MATCH → SKIP. Verified exit 0.
- Pre-existing arm still holds: `connection refused: dial tcp` → MATCH → SKIP.

Sabotage: removed `|toomanyrequests|rate limit` from `:1781` (1-line revert of T1 arm; file copy saved outside worktree, then restored via `git checkout --`).
- Sabotaged pattern: `(network|...|proxy connect)` — no rate-limit arm. Confirmed via `grep -n 're.search(r"(network'`.
- Fixture `denied: toomanyrequests: pull rate limit exceeded` → NO MATCH → `RED fail: V13/#70 sidecar image does not resolve` (fail-closed). Harness exit 1. **RED confirmed.**
- Fixture `ERROR: rate limit exceeded for docker pull` → NO MATCH → RED. Harness exit 1. **RED confirmed.**
- Control: `connection refused: dial tcp ...` → still SKIP (proves sabotage was targeted, not blanket breakage).
- Exact RED harness: python replica of the V13 `if re.search(...): SKIP else fail()` block against the live file content; `toomanyrequests` fixture exited 1 with `FAIL V13/#70: sidecar image does not resolve (fail-closed RED)`.

Restore: `git checkout -- scripts/verify-rigs.sh` → `:1781` arm present again (`grep -n toomanyrequests` hits `:1781`).
- Re-ran both fixtures → SKIP, harness exit 0. **SKIP confirmed (arm ON).**
- `git status --short` clean after restore (no output). No vacuous check: the V13 skip logic REDs without the arm and SKIPs with it.

Note: full `verify-rigs.sh --check-only` was not expected to RED under this sabotage in this offline host (no live quota error at runtime); the RED proof is at the decision-block level with quota fixtures, which is the exact fail-closed path the arm guards. This matches proposal Acceptance 1 parenthetical (`pattern without arm REDs on fixture, with arm SKIPs`).

## 3. Red-proof (b): doc-count guard — both directions

Target: proposal Acceptance 2 (`26 checks` must be absent).

Sabotage: `README.md` `31 checks passed` → `26 checks passed` (1 occurrence, temporary).
- `grep -rn "26 checks" AGENTS.md docs/USER_GUIDE.md README.md` → `README.md:47: ... 26 checks passed ...` (exit 0 = matches found).
- Guard harness (`if grep -rq "26 checks" ...; then RED; fi`) → `ACCEPTANCE-2 RED CONFIRMED: stale count detected (fail-closed)`, exit 1. **RED confirmed.**

Restore: `git checkout -- README.md`.
- `grep -rn "26 checks" ...` → no matches (exit 1, GREEN restored).
- `grep -rn "31 checks" ...` → 4 hits again (exit 0). **GREEN confirmed.**
- `git status --short` clean after restore. No vacuous check: the grep acceptance REDs on a single stale count and greens when restored.

## 4. Sabotage log (commands + exits + restores)

1. `sed -n '1770,1800p' scripts/verify-rigs.sh` — read V13 block (no edit).
2. Fixture-match probe on live `:1781` pattern (arm ON) — exit 0, both rate-limit fixtures SKIP.
3. Sabotage (a) apply: python replace `|toomanyrequests|rate limit)` → `)` in `scripts/verify-rigs.sh` — applied; `grep -n 're.search(r"(network'` shows arm gone.
4. Sabotage (a) RED: python V13-decision replica on sabotaged file — both rate-limit fixtures RED, control SKIP — demonstrated; dedicated RED harness exit 1.
5. Restore (a): `git checkout -- scripts/verify-rigs.sh` — `grep -n toomanyrequests` hits `:1781`; `git status --short` clean.
6. Restore (a) SKIP: python V13-decision replica on restored file — both fixtures SKIP — exit 0.
7. Sabotage (b) apply: python replace `31 checks passed` → `26 checks passed` (1x) in `README.md` — applied; `grep -rn "26 checks"` exit 0.
8. Sabotage (b) RED: `if grep -rq "26 checks" ...` guard — exit 1, RED confirmed.
9. Restore (b): `git checkout -- README.md` — `grep -rn "26 checks"` exit 1 (GREEN), `grep -rn "31 checks"` exit 0; `git status --short` clean.
10. Post-restore acceptance: `./scripts/verify-rigs.sh --check-only` tail `SUMMARY: 31 checks passed, 0 failed`, exit 0 (re-verified after restores).
11. Scratch cleanup: `rm -f /tmp/verify-rigs.sh.bak` (outside worktree, no repo effect).

All sabotage reverted via `git checkout -- <file>`; `git status --short` showed clean after each restore. No production/test code patched; only this evidence file is new.

## 5. Session-URL canonical note (nx9)

- `docs/reports/remediate-sandbox-implementation.md:78` footer uses `...NTYZnx9`; `docs/reports/remediate-supplychain-implementation.md:150` footer uses `...NTYZ9W`. Cosmetic provenance only (3 nx9 vs 1 YZ9W per proposal).
- Per REQ-G2, both historical reports remain byte-identical in this change (no rewrites verified — T1 touches only `scripts/verify-rigs.sh`, `AGENTS.md`, `docs/USER_GUIDE.md`, `README.md`, `docs/TECHNICAL_DOCUMENTATION.md`).
- Canonical for future footers: `nx9`. Recorded here only, as specified.

## 6. Deferred items (stay fail-closed, reasons per design.md)

- Bare-`TPM` shorthand: retirement path already commented (`check-envelope.py:545-548`); removal needs governed-predicate rollout (Wave D or upstream). Untouched.
- `xyz123` human-registry: needs human-registry source (upstream-watch). Untouched.
- `"QA PASS, no issues"` non-terminal reading: anchored-regex + negator already correct; operator error, not code bug. Untouched.
- F9 bare-leading-env: `send-authenticated.sh:16-21` refusal + env-form deny hold; per-seat tokens upstream (M10; #72 mitigated). Untouched — governance probes (`check-envelope.py:544-557`, `reconcile_model.py:39-67`, `send-authenticated.sh:16-21`) byte-identical in T1.
- Firecrawl standalone boot: needs networked host with `--profile web-research up` vs full rabbitmq/nuq-postgres/playwright stack (upstream-watch). Doc pin refreshed; boot unverified caveat stands.
- Authenticated registry pulls (V13 alternative): needs registry credentials on every host (secret-sprawl); skip-arm treats quota as transient transport noise while staying fail-closed on real digest mismatches. Recorded, not built.

## 7. Verdict

T2 red-proofs PASS: V13 arm and doc-count greps both proven non-vacuous (RED under targeted sabotage, GREEN restored). No vacuous acceptance checks found. Tree clean except this evidence file; ready for T3 drift-guard → PR.
