# Tasks: remediate-37-id-discipline (testable checklist — implementer runs these)

- [ ] T1 — Patch `scripts/generate-rigs.py` (~line 701) charter primer: add
  `--json` list example + never-retype-ID rule.
  Testable: `grep -n -- --json scripts/generate-rigs.py` hits the primer.
- [ ] T2 — Patch `docs/USER_GUIDE.md` (~lines 215, 226), `README.md` (~line 61),
  and root `AGENTS.md` queue row (~line 29): `--json` on every queue read
  example + copy-never-retype sentence.
  Testable: grep shows no bare `rig queue list` / `rig queue show` example
  without `--json` or an adjacent never-retype warning.
- [ ] T3 — Regen (`python3 scripts/generate-rigs.py`) + `make verify`.
  Testable: exit 0, 22 checks passed / 0 failed; rendered leaves contain the
  new primer (seed dry-run grep).
- [ ] T4 — Live proof: copy an ID from plain `rig queue list` into
  `rig queue show <id>`; zero `qitem_not_found`.
  Testable: paste the passing transcript into the implementation report.
- [ ] T5 — Report: `docs/reports/remediate-37-implementation.md` with commands
  run, exit codes, and the T4 transcript.
