# Delta spec: output-deny-76

## ADDED Requirements

### REQ-O1: narrowed write-forms deny
The terminal bash deny tuple MUST contain `"*--output=*"`, `"*--output *"`, and `"*--output\t*"` (equals/space/tab file-write forms) in place of the substring `"*--output*"`, keeping position 1 to preserve order-gate semantics. Rationale: `--output=FILE` / `--output FILE` smuggle writes past path_write under prefix-glob matcher semantics.

### REQ-O2: targeted junit/log denies
The tuple MUST additionally contain `"*--output-junit*"` and `"*--output-log*"` (principal decision Q4: real ctest file-writers that pass naive narrowing). Total tuple size MUST be 42. Rationale: zero file-write smuggling through `--output-*`.

### REQ-O3: legit flags pass
`ctest --test-dir build --output-on-failure` (cpp-lowlevel-eng / engine-systems-eng `ctest*` allows), `yr dump … --output-format yaml`, and `ruff check --output-format=github` MUST be allowed by the bash policy on suitably-permitted roles. A mock-gate `expect allow` probe for the ctest form MUST exist. Rationale: the friction #76 reports.

### REQ-O4: lockstep updates
Mirror (`verify-rigs.sh:588`), order/presence asserts (`:589-604`), emitter asserts (`:1153-1160`), V15 frozen assert (allowlist the --output-only diff), `test_command_effects.py` expected tuple + frozen-order test, `test_render_seat.py` corpus (to full new-tuple parity, closing its 7-entry tab gap) + `:508` leading-binary literal, `gate-role.sh` probes (keep `=` deny; add space/tab deny probes + ctest allow probe), and all 51×2 generated leaves (via `generate-rigs.py` regen) MUST reflect the 42-tuple. Docs counts/entries (TECHNICAL_DOCUMENTATION, PROMPT_ADVERSARIAL claim 5.5, charter taxonomy text, USER_GUIDE probe count) MUST be refreshed; `PROMPT_REMEDIATION_REAUDIT.md:26` acceptance row cited as the end-state criterion.

## MODIFIED Requirements

### REQ-G1: freeze exception scoped
The TERMINAL_BASH_DENIES freeze exception covers ONLY `--output`-family entries (1 removed, 5 added). No other deny entry may be added, removed, reordered, or reworded in this change.
