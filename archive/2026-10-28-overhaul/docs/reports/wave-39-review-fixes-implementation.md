# Implementation report — wave-39-review-fixes (change remediate-39-reconcile)

- Stage/wave: `wave-39-review-fixes` · Worktree: `/home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-39-reconcile` · Branch: `remediate/39-reconcile`
- Spec read from disk first: `AGENTS.md` (binding: no hand-edits under `specs/ rigs/ rosters/ registry/` — none made), `scripts/reconcile.py` `propose_cell` (~321-330), `diff_row` note extraction (~363-365) + proposal sites (~376/383/395), `main` try/except (~448-521).
- Scope: EXACTLY the two principal-approved review items, nothing else.

## Deliverables

1. **Note normalization for paste-ready proposals** (`scripts/reconcile.py`): new `normalize_proposal_note()` helper — replaces `|` with `/`, collapses every whitespace run (including newlines) to single spaces. Applied in `propose_cell()` (covers both parked True/False branches) and at the missing-convergence-annotation proposal site. `queue:` diagnostic fields keep the raw note byte-identical (verified by diff: only proposal-embedding lines changed).
2. **Fail-closed malformed-input mapping** (`scripts/reconcile.py` `main`): added `except (AttributeError, TypeError, ValueError, KeyError)` after the `ReconcileError` handler — concise one-line stderr message `reconcile: FAILED: malformed input (<Type>: <detail>)`, exit 2. `ReconcileError`→2, diffs-found→1, in-sync→0 unchanged.
3. **Tests** (`tests/test_reconcile.py`, +5): `TestProposalNoteNormalization` (2 tests), `TestMalformedInputFailClosed` (3 tests).

## Control-flow audit (item 2 precondition — confirmed by reading the try block)

No legitimate control flow inside `main`'s try relies on catching `AttributeError`/`TypeError`/`ValueError`/`KeyError`:
- `refuse_out_path` catches `OSError` locally, raises `ReconcileError`.
- `parse_tracker` catches `ValueError` locally (`lowered.index("slice")` fallback); all other failures raised as `ReconcileError`.
- `run_rig` / `load_json_file` catch `FileNotFoundError`/`TimeoutExpired`/`JSONDecodeError` locally (note: `JSONDecodeError` subclasses `ValueError`, but it is consumed by the local handlers first, so the new mapping cannot intercept it).
- `queue_terminal` uses `.get`-with-defaults and `str()`; an `AttributeError`/`TypeError` from `max()` means non-dict trail items — malformed input, never signaling.
- `diff_row` `row[...]` (`KeyError`), `cell.lower()` (`AttributeError`), `int(m)` on regex-digit matches (`ValueError` unreachable) — all malformed-row signals; `recorded_note_ids` cannot raise on well-formed cells.
- `parser.error()` raises `SystemExit` (`BaseException`), untouched by the new handler.

## Per-item verification

### Item 1 — normalization
- Pre-fix repro (scratch `/tmp/opencode/hr39fix/hostile/`, note `"QA PASS a|b\nc   d  placed"`): `PROPOSED-CELL` lines broke across lines and contained `|` (would corrupt a pasted markdown table row). Post-fix: 7 single-line `PROPOSED-CELL` lines, zero `|`, snippet `(queue note 5: QA PASS a/b c d placed;` — finding still fires, exit 1, all 3 drift classes present.
- Clean-note fidelity: post-fix full stdout on the standard drifted fixture is **byte-identical** to the pre-fix capture (`diff` clean); golden test pins exact clean-note proposal strings.
- Scope check: `diff` of pre/post hostile runs shows changes ONLY on proposal-embedding lines (`PROPOSED-CELL`, `PROPOSED Status cell:`, `SUGGESTED` which embeds the proposal); all `queue:` diagnostic lines byte-identical with the raw note.

### Item 2 — fail-closed mapping (pre-fix behavior reproduced, then fixed)
| Malformed shape | Pre-fix | Post-fix |
|---|---|---|
| transitions trail `[42, "not-a-dict"]` (`queue_terminal` `t.get` → `AttributeError`, reconcile.py:272) | traceback, exit 1 | `reconcile: FAILED: malformed input (AttributeError: ...)` exit 2, no traceback |
| queue entry `{"qitemId": ["list-is-unhashable"]}` (unhashable dict key → `TypeError`, reconcile.py:491) | traceback, exit 1 | `... (TypeError: ...)` exit 2, no traceback |
| tracker-derived row missing `status` (`diff_row` `row["status"]` → `KeyError`, reconcile.py:334; via driver monkeypatching `parse_tracker`) | traceback, exit 1 | `... (KeyError: 'status')` exit 2, no traceback |
- Precision notes: a queue entry that is literally not a dict is already filtered by the `isinstance(e, dict)` comprehension (no crash pre or post — silent row-level diff, unchanged); a per-qitem transitions value that is not a list is already handled by the `isinstance(transitions, list)` fallback (unchanged). The crash-bearing shapes above are what the new mapping covers.

## Acceptance (all green)

- `python3 -m unittest tests.test_reconcile` → 24/24 OK (19 pre-existing + 5 new); `make test` → `Ran 94 tests ... OK`.
- `make verify` → `SUMMARY: 26 checks passed, 0 failed`, exit 0 (+ standing live-health heartbeat WARN / seat-idleness SKIP advisory, unchanged).
- `openspec validate remediate-39-reconcile` → `Change 'remediate-39-reconcile' is valid`, exit 0.
- Live read-only run (3 mission trackers vs live queue): exit 1, `14 diff(s) across 23 row(s)` — identical to the pre-fix audit baseline; mission md5s identical before/after (`phase0 d7678fce…`, `wave1 a24fca86…`, `wave2 74f93824…`).
- `git status` shows only `scripts/reconcile.py`, `tests/test_reconcile.py` (+ this report).

## Self-audit notes

- Residual (out of scope, reported not fixed): the `stale-terminal` branch proposal (`queue-side evidence: {latest_note or ...}`, ~line 408+) still interpolates the raw note. The review brief scoped normalization to `propose_cell` + the missing-annotation proposal, so it was left untouched; a hostile note there could still break a pasted row. Recommend a follow-up review item if the TPM wants it covered.
- Nothing found NOT valid: both review items verified VALID against the code at the cited regions (line numbers shifted +~12 after the helper insertion, re-checked).
- No commit/merge/push beyond the stage branch commit; no QA dispatch; no mission files touched (md5-verified).
