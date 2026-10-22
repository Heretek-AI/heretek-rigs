# Tasks: remediate-44-json-trailer (testable checklist — implementer runs these)

- [ ] T1 — Local: append `--json` to every `rig queue list` / `show` / `create`
  example in `scripts/generate-rigs.py` charter text, `docs/USER_GUIDE.md`,
  `README.md`, and the root `AGENTS.md` queue row, plus a "bare output mixes
  JSON + human trailer, MUST NOT be parsed" statement.
  Testable: grep finds no bare queue example without `--json`.
- [ ] T2 — Regen (`python3 scripts/generate-rigs.py`) + `make verify`.
  Testable: exit 0, 22 checks passed / 0 failed.
- [ ] T3 — Parse-first-try proof: re-run #44's failing `queue show` / `queue
  list` commands with documented flags; `json.load(stdout)` succeeds.
  Testable: transcript in the implementation report.
- [ ] T4 — Draft the upstream issue body: byte-exact trailer bytes from a live
  bare `queue show`, the `JSONDecodeError: Extra data` reproduction, file/line
  cites (`dist/commands/queue.js:1115-1117` trailer, `1118-1123` compact
  notice, transitions-on-stderr precedent in the `1116-1143` region), and the
  single request (both notices to stderr; note #42's create receipt rides the
  same stdout-purity principle).
  Testable: draft saved at `docs/evidence/upstream-queue-stdout-issue.md`.
- [ ] T5 — File the upstream issue against `mvschwarz/openrig` (`gh` or web)
  and record the filed URL in this package (append to proposal.md) AND link it
  from `remediate-42-create-receipt` so both reference ONE issue.
  Testable: URL resolves; both specs cite the identical URL.
- [ ] T6 — Report: `docs/reports/remediate-44-implementation.md` with commands,
  exit codes, T3 transcript, and the upstream issue URL.
