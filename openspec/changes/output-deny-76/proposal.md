# Proposal: output-deny-76 — narrow *--output* to write-forms + targeted junit/log denies

Status: scope approved (principal policy calls 2026-10-25: narrow the deny; targeted denies for --output-junit/--output-log; two separate waves).
Issue: #76. Closes #76 on merge.

## Root cause (verified read-only 2026-10-25, Wave E recon)

- Terminal deny `*--output*` (substring) kills the harmless `ctest --output-on-failure` (live evidence: mission A2, `systems-cpp-lowlevel-eng` denied; bare retry passed but diagnostics lost on failing tests).
- The deny exists because `--output=FILE` smuggles file writes past path_write (HR-5.5-render-output-allow); generation-time dies + sole gate probe (`gate-role.sh:58`, `=` form) cover only part of the write surface (space/tab forms have zero probes).
- Tuple is exactly 38 (`render-seat.py:81-127` source of truth + `verify-rigs.sh:588` ordered-identical mirror). Principal-approved exception to the freeze: ONLY `--output` entries may change.

## Change

Replace `"*--output*"` (position 1, order preserved) with:
- `"*--output=*"` (equals form), `"*--output *"` (space form), `"*--output\t*"` (tab form — JSON `\t` decodes to TAB at match time, per existing tab-gap hardening),
- `"*--output-junit*"` + `"*--output-log*"` (principal decision Q4: real ctest file-writers that pass naive narrowing).
38 → 42 entries. Mirrors + asserts + corpus + probes updated in lockstep (V13 equality auto-greens on identical mirrors; V15 frozen assert allowlists the --output-only diff; `test_command_effects.py` EXPECTED_38 → 42; `test_render_seat.py` corpus to full new-tuple parity, also closing its pre-existing 7-entry tab gap; `gate-role.sh`: keep `=` deny probe, add space/tab deny probes + `ctest --output-on-failure` allow probe on cpp-lowlevel-eng).
Legit flags newly passing: `--output-on-failure`, `--output-format ...` (space and `=` forms — substring after `--output` is `-`, matching neither narrowed pattern).

## Acceptance

1. `ctest --test-dir build --output-on-failure` allowed (mock gate + V1 checks); `git log --output=x`, `--output /tmp/x`, `--output\t/tmp/x`, `git show --stat --output=/tmp/pwned`, `--output-junit x`, `--output-log x` all denied — red-proofed both directions.
2. `make verify` green (new V-number block if needed for the allow-probe wiring; no renumber); full corpus green except known pre-existing canary 12/11.
3. Drift-guard `VERDICT: PASS` → PR with `Closes #76`.
