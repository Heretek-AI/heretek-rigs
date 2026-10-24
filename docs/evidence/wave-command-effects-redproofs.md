# Wave command-effects red-proofs (issue #106, stage command-effects, T2)

Branch: `feat/command-effects` — T1 implementation commit `724799c`.
Date: 2026-10-24. Worktree: `.lane/trees/command-effects`.
Spec: `openspec/changes/command-effects/{proposal.md,design.md,tasks.md,specs/command-effects/spec.md}` (REQ-C1/C2/C3, REQ-G1/G2).

## 1. Baseline acceptance (unmodified tree, all green)

### 1a. `bash tests/command-effects-redproof.sh` — exit 0

```
[PASS] allow note 'a/b | c'
[PASS] deny note 'a;b'
[PASS] deny note 'x$y'
[PASS] deny note 'a`b'
[PASS] deny note 'x$(id)'
[PASS] deny note 'a\nb'
[PASS] deny note 'OPENRIG_SESSION_NAME=e'
[PASS] deny note 'OPENRIG_URL=e'
[PASS] allow in-scope body-file
[PASS] deny prod.env outside scope
[PASS] deny /etc/passwd
[PASS] deny dotdot escape
[PASS] deny missing file
[PASS] deny absolute /tmp
[PASS] deny symlink escape
[PASS] deny oversize body-file
[PASS] render dry-run exit 0
[PASS] rendered note-effect + body-file-effect
redproof: 0 failures
```

Allow direction (exit 0): `--note "a/b | c"` allowed; in-scope `--body-file` allow-effect.
Deny directions (non-zero with deny record): `prod.env` outside scope, `/etc/passwd`,
`../../etc/passwd`, symlink escape, oversize, missing file, absolute `/tmp`,
`;`/`$`/backtick/`$(`/newline/`OPENRIG_SESSION_NAME=`/`OPENRIG_URL=` notes — all deny.

### 1b. `pytest tests/test_command_effects.py tests/test_render_seat.py` — exit 0

```
23 passed, 209 subtests passed in 21.39s
```

### 1c. Full corpus `pytest tests/test_command_effects.py tests/test_render_seat.py tests/test_seat_sandbox.py tests/test_policy_verifier.py` — exit 0

```
82 passed, 212 subtests passed in 31.38s
```

### 1d. `make verify` — exit 0

```
[PASS] Command effects (#106) green: 102 permission leaves carry note-effect + body-file-effect, denies frozen
SUMMARY: 31 checks passed, 0 failed.
```

Deny count frozen at 38 source / 38 mirror per REQ-G1; no check renumber per REQ-G2.

## 2. Red-proof sabotage (each MUST fail visibly, then revert)

All sabotage targets `scripts/render-seat.py` (the REQ-C1/C2/C3 enforcement point).
Check under sabotage: `bash tests/command-effects-redproof.sh` (binary pass/fail).

### Sabotage S1 — note-allow `|` blocked (REQ-C1 allow direction)

- Injected defect: `NOTE_VALUE_PATTERN = r"^[A-Za-z0-9 _\-/.:|]+$"` → `r"^[A-Za-z0-9 _\-/.:]+$"` (pipe removed).
- Result: `[FAIL] allow note 'a/b | c'`, `redproof: 1 failures`, **exit 1 (RED)**. All other lines stayed PASS.
- Restore: `git checkout -- scripts/render-seat.py`; `git status --short scripts/render-seat.py` clean; re-ran redproof → `redproof: 0 failures`, exit 0. Direct probe `is_note_value_allowed("a/b | c")` → `True` after restore.

### Sabotage S2 — body-file allow in-scope denied (REQ-C2 allow direction)

- Injected defect: in `classify_body_file`, `return ("allow-effect", "in-scope root")` → `return ("deny", "outside own scope")`.
- Result: `[FAIL] allow in-scope body-file — got deny`, `redproof: 1 failures`, **exit 1 (RED)**. Deny-direction lines stayed PASS.
- Restore: `git checkout -- scripts/render-seat.py`; `git status --short scripts/render-seat.py` clean; re-ran redproof → `redproof: 0 failures`, exit 0.

### Sabotage S3 — deny directions `prod.env` + `/etc/passwd` allowed (REQ-C3 fail-closed)

- Injected defect: in `classify_body_file`, deny tail `return ("deny", "absolute /tmp path outside scope")` + `return ("deny", "outside own scope")` → both `return ("allow-effect", "in-scope root")`.
- Result: `[FAIL] deny prod.env outside scope — got allow-effect`, `[FAIL] deny /etc/passwd — got allow-effect`, `[FAIL] deny dotdot escape — got allow-effect`, `[FAIL] deny symlink escape — got allow-effect`, `redproof: 4 failures`, **exit 1 (RED)**.
- Restore: `git checkout -- scripts/render-seat.py`; `git status --short scripts/render-seat.py` clean; re-ran redproof → `redproof: 0 failures`, exit 0; `pytest tests/test_command_effects.py -q` → `11 passed, 80 subtests passed`.

## 3. Verdict

- No vacuous checks: every acceptance direction turns RED under minimal targeted sabotage and GREEN after restore.
- Tree after sabotage cycle: only this evidence file untracked/modified; `scripts/render-seat.py` byte-identical to `724799c`.
- T2 acceptance command `bash tests/command-effects-redproof.sh AND pytest tests/test_command_effects.py tests/test_render_seat.py` passes.
