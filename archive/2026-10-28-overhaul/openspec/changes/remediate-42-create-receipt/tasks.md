# Tasks: remediate-42-create-receipt (testable checklist — implementer runs these)

- [ ] T1 — Docs/charters: present `rig queue create --json --verify` as the
  only agent-safe form in `scripts/generate-rigs.py` charter text,
  `docs/USER_GUIDE.md`, `README.md`, and the root `AGENTS.md` queue row, with
  the "bare output is advisory, not proof of persistence" statement.
  Testable: grep finds no bare `rig queue create` example without the flags.
- [ ] T2 — Wrapper: update `scripts/send-authenticated.sh` to pass the
  agent-safe flags and parse the JSON receipt (`qitemId` + state), failing
  closed on unparseable stdout.
  Testable: `--dry-run` shows the flagged invocation; live run prints the
  parsed `qitemId`/state; feeding the wrapper non-JSON stdout exits non-zero.
- [ ] T3 — Single-call proof: one `create --json --verify` yields qitemId +
  state with no follow-up `show` (contrast with `update`, which already
  returns row JSON).
  Testable: transcript in the implementation report.
- [ ] T4 — Shared upstream link: obtain the issue URL filed via
  `remediate-44-json-trailer` T5 and record the IDENTICAL URL in this package
  (append to proposal.md). If that issue is not yet filed, coordinate — do
  NOT file a second issue.
  Testable: both packages cite the identical URL.
- [ ] T5 — Regen (`python3 scripts/generate-rigs.py`) + `make verify`.
  Testable: exit 0, 22 checks passed / 0 failed.
- [ ] T6 — Report: `docs/reports/remediate-42-implementation.md` with commands,
  exit codes, T3 transcript, and the shared upstream issue URL.
