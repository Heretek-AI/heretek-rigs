# T2 red-proof evidence — output-deny-76 (issue #76, Wave E)

Stage: `output-deny-76` · T2 red-proofs only (drift-guard follows).
Worktree: `.lane/trees/output-deny-76` · branch `feat/output-deny-76` @ `18f6e82`
(T1 commits `6a6dfa9`, `4589759`, `18f6e82`). Unity binding: N/A.
Spec: `openspec/changes/output-deny-76/` (REQ-O1/O2/O3/O4/G1). T1 report:
`docs/reports/output-deny-76-implementation.md`.

## 1. Baseline acceptance (unmodified tree, all exit 0)

| Check | Result |
|---|---|
| `make verify` | exit 0 — gate `SUMMARY: 35 checks passed, 0 failed`; trailing `live-health.py` prints daemon `[SKIP]`s only (no daemon in sandbox; pre-existing, non-blocking) |
| `./scripts/verify-rigs.sh --check-only` | exit 0 — `SUMMARY: 35 checks passed, 0 failed` (audit baseline) |
| `pytest tests/test_render_seat.py tests/test_command_effects.py` | exit 0 — `29 passed, 209 subtests passed` |
| Matcher emulation on rendered cpp-lowlevel-eng bash map (`*`→`.*`, `re.fullmatch`, last-match-wins) | exit 0 — 14/14 per-form verdicts as specified (see §2) |

## 2. Per-form results (baseline, green)

Rendered role: `cpp-lowlevel-eng` / `systems-and-mobile-foundry` / `systems`
(59-key bash map; allows `ctest*`, `git show --stat*`, …; 42-tuple denies last).

ALLOW direction (REQ-O3):
- `ctest --test-dir build --output-on-failure` → `('ctest*','allow')` ✔
- `ctest --test-dir build --output-on-failure -V` → `('ctest*','allow')` ✔
- `yr dump foo --output-format yaml` / `=yaml`, `ruff check --output-format github` / `=github` → **no `--output`-family deny matches** ✔ (full verdict on this role is default `('*','deny')` for lack of a `yr*`/`ruff*` allow prefix — the policy claim is absence-of-deny, which is what the narrowing guarantees; suitably-permitted roles allow them)

DENY direction (REQ-O1/O2):
- `git log --output=x` → `('*--output=*','deny')` ✔
- `git show --stat --output=/tmp/pwned` → `('*--output=*','deny')` ✔
- `git show --stat --output /tmp/pwned` → `('*--output *','deny')` ✔
- `git show --stat --output<TAB>/tmp/pwned` → `('*--output\t*','deny')` ✔
- `ctest --output-junit results.xml` → `('*--output-junit*','deny')` ✔
- `ctest --output-log output.log` → `('*--output-log*','deny')` ✔
- `git log --output-junit=x` / `--output-log=x` → junit/log denies ✔

Corpus: `test_command_effects.py` 42-tuple frozen-order assert + `test_render_seat.py`
full-42-parity corpus green (29 passed).

## 3. Live mock gate (`scripts/gate-role.sh cpp-lowlevel-eng`) — environmental limit

- All **deny** probes pass: `ok ... bash --output write-escape`, `ok ... space-separated`,
  `ok ... tab-separated`, plus all patch/exfil denies (`45` ok lines total).
- All **allow** probes fail environmentally (exit 1 overall, 4 FAILs):
  `bash git log --oneline path-scoped without patch flag`, `bash git status`,
  `bash ctest --output-on-failure diagnostic flag (#76)`, `write inside src/` —
  each with `wanted allow, got "isError":true`.
- Raw cause (reproduced via `gate-run.sh`): `[pi-permission-system] This 'bash' call
  requires approval, but no interactive UI is available.` → `isError:true`.
  Pre-existing sandbox limit (T1: pristine main fails the same 3 allows; this branch
  adds the 4th, the new ctest probe, failing the identical way). **Allow-direction
  proof therefore rests on matcher emulation (§2) + corpus, not on live allows.**
- Sandbox-indistinguishability caveat (proved S5 below): with an `--output` deny
  removed, the live `expect deny` probe for an allowed-prefix write form still prints
  `ok` — the command then fails on `external_directory` approval (`isError:true`)
  instead of the bash deny. So live deny probes are non-decisive for allowed-prefix
  forms in this sandbox; the emulation verdict-flip is the load-bearing deny proof.

## 4. Sabotage log (every check proven fail-closed; all reverted)

Each row: minimal defect → check → RED (non-zero exit) → `git checkout -- <file>` →
`git status --short` clean. Full outputs in §5.

| # | Sabotaged file / defect | Check run | RED result (exit) | Revert |
|---|---|---|---|---|
| S1 | `scripts/render-seat.py`: 5 new entries → old single `"*--output*"` (proves narrowing load-bearing) | emulation script | **exit 1** — `ctest --output-on-failure` → `('*--output*','deny')` (allow flips to deny; `--output-format` forms also denied = old over-block) | `git checkout` ✔ 5 entries restored |
| S1b | same S1 defect | `pytest tests/test_command_effects.py` | **exit 1** — `test_terminal_bash_denies_narrowed_42_ordered` FAILED | same revert ✔ |
| S2a | `render-seat.py`: drop `"*--output-junit*"` (proves Q4 entry load-bearing) | emulation | **exit 1** — `ctest --output-junit results.xml` → `('ctest*','allow')` (file-write smuggling open) | ✔ restored (`grep -c` = 1) |
| S2a | same defect | `pytest test_command_effects + test_render_seat` | **exit 1** — 2 failed (frozen-order + full-parity corpus `KeyError`) | ✔ |
| S2b | `render-seat.py`: drop `"*--output-log*"` | emulation | **exit 1** — `ctest --output-log output.log` → `('ctest*','allow')` | ✔ |
| S2b | same defect | both corpora | **exit 1** — 2 failed | ✔ |
| S3a | `render-seat.py`: drop `"*--output=*"` | emulation | **exit 1** — `git show --stat --output=/tmp/pwned` → `('git show --stat*','allow')` (write-escape open) | ✔ |
| S3a | same defect | `pytest test_command_effects` | **exit 1** — frozen-order FAILED | ✔ |
| S3b | `render-seat.py`: drop `"*--output *"` | emulation | **exit 1** — space form → `('git show --stat*','allow')` | ✔ |
| S3b | same defect | pytest | **exit 1** — FAILED | ✔ |
| S3c | `render-seat.py`: drop `"*--output\t*"` | emulation | **exit 1** — tab form → `('git show --stat*','allow')` | ✔ |
| S3c | same defect | pytest | **exit 1** — FAILED | ✔ |
| S4 | `scripts/verify-rigs.sh`: drop `"*--output-junit*"` from `_TERMINAL_BASH_DENIES` mirror | `./scripts/verify-rigs.sh --check-only` | **exit 1** — `[FAIL] V13/S2a` mirror≠source + cascading V19 count guards (`SUMMARY: 33 checks passed, 4 failed`) | ✔ |
| S5 | `render-seat.py`: drop `"*--output=*"` then live-probe the `=` write-escape via `gate-run.sh` | live gate-run | Informational (no exit assertion): still `isError:true` but reason flips to `external_directory ... requires approval` — proves live deny probes **cannot** distinguish deny-vs-allow here (see §3 caveat); emulation flip (S3a) is the decisive proof | ✔ |

No vacuous checks: every acceptance check (emulation per-form asserts, both corpus
suites, V13 mirror gate) exits non-zero under its targeted defect. Post-sabotage
`git status --short` is empty and baselines re-green (§1 re-ran after final revert:
verify 35/0, pytest 29 passed, emulation 0 failures).

## 5. Raw outputs (abridged)

Baseline:
- `SUMMARY: 35 checks passed, 0 failed.` (verify-rigs --check-only, exit 0)
- `29 passed, 209 subtests passed in 22.52s` (pytest, exit 0)
- emulation: `0 failures` / 14 lines all `ok` (exit 0)
- gate-role cpp-lowlevel-eng: `45` ok lines; 4 FAILs, all `wanted allow, got "isError":true`
  (`git log --oneline path-scoped`, `git status`, `ctest --output-on-failure`, `write inside src/`)

RED excerpts:
- S1 emulate: `FAIL ALLOW 'ctest --test-dir build --output-on-failure': -> ('*--output*', 'deny')`; `2 failures`
- S1 pytest: `FAILED tests/test_command_effects.py::...test_terminal_bash_denies_narrowed_42_ordered`; `1 failed, 10 passed`
- S2a emulate: `FAIL DENY 'ctest --output-junit results.xml': -> ('ctest*', 'allow')`; `1 failures`
- S2a pytest: `2 failed, 27 passed` (incl. `tests/test_render_seat.py:223: KeyError`)
- S2b emulate: `FAIL DENY 'ctest --output-log output.log': -> ('ctest*', 'allow')`
- S3a emulate: `FAIL DENY 'git show --stat --output=/tmp/pwned': -> ('git show --stat*', 'allow')`
- S3b emulate: `FAIL DENY 'git show --stat --output /tmp/pwned': -> ('git show --stat*', 'allow')`
- S3c emulate: `FAIL DENY 'git show --stat --output<TAB>/tmp/pwned': -> ('git show --stat*', 'allow')`
- S4 verify: `[FAIL] V13/S2a: verify-rigs mirror tuple != render-seat TERMINAL_BASH_DENIES`;
  `SUMMARY: 33 checks passed, 4 failed.` (exit 1)
- S5 gate-run: `[pi-permission-system] This 'external_directory' call for tool 'bash' for
  path '/tmp/pwned' requires approval, but no interactive UI is available.` (`isError:true`)

Note on S1 pytest exit capture: the `| tail` pipeline masks pytest's code; rerun with
redirect gives `S1-PYTEST_EXIT:1`. Same discipline used for all pytest exits above.
