# Implementation report: wave-44-42-queue-json (heretek-rigs #44 + #42, one upstream issue)

Stage: wave-44-42-queue-json · Branch: remediate/44-42-queue-json ·
Worktree: /home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-44-42-queue-json

Satisfies T6 of BOTH `remediate-44-json-trailer` and `remediate-42-create-receipt`
(single combined report for the combined wave).

## Upstream issue (ONE, shared — filed once, referenced twice)

- URL: https://github.com/mvschwarz/openrig/issues/1806
- Filed: 2026-10-23 via `gh issue create -R mvschwarz/openrig`
  (repo slug verified from installed `@openrig/cli@0.6.13`
  `package.json` `repository.url = https://github.com/mvschwarz/openrig`).
- Covers BOTH the #44 trailer/compact notices AND the #42 create-receipt
  ask (same stdout-purity principle). No second issue filed.
- Recorded in: `docs/evidence/upstream-queue-stdout-issue.md` (## Filed),
  `openspec/changes/remediate-44-json-trailer/proposal.md` (## Filed upstream),
  `openspec/changes/remediate-42-create-receipt/proposal.md`
  (## Shared upstream issue). Both packages cite the identical URL.
- gh filing succeeded first try (exit 0); no fallback needed.

## Byte-exact evidence (read-only; daemon live, no mutations)

- Bare `rig queue show qitem-20261022111416-78213c07c3272cbc`:
  exit 0, 3628 bytes stdout / 0 bytes stderr; tail is the trailer
  `… (bounded preview — complete body is 815 bytes; full record 3017 JSON bytes: …)`.
- `json.loads(bare_stdout)` → `JSONDecodeError: Extra data: line 96 column 1 (char 3472)`.
- Same command + `--json` → parses first try (`qitemId` + full key set,
  stderr empty). `rig queue list --json` → parses (21 rows).
- Code cites (installed 0.6.13
  `/home/john/.npm-global/lib/node_modules/@openrig/cli/dist/commands/queue.js`):
  trailer `console.log` at :1116 (guard `:1115`), compact notice
  stderr/stdout branch at :1118-1124, transitions-on-stderr precedent at
  :1142, create request-ID already `console.error` at :648,
  receipt projection `printWriteResult` :278-286 +
  `dist/queue-receipt.js:230 buildWriteReceipt` (`qitemId`+`state` ALWAYS
  present in `--json`, :41-43).

## Local changes (per-anchor grounding; wave-6 overlaps noted)

Wave 6 had already added `--json` to the generator charter primer
(`generate-rigs.py:810`, `rig queue list --json`), root AGENTS.md list
example, `README.md:61`, and `USER_GUIDE.md:215` — those were verified
with grep and NOT re-edited (no duplicate churn). New in this wave:

| Anchor | Change |
|---|---|
| root `AGENTS.md` queue row | create example → `rig queue create --json --verify …`; appended MUST-NOT-parse + not-proof-of-persistence clause |
| `docs/USER_GUIDE.md:214-216` | appended "Bare queue output … MUST NOT be parsed — always pass --json" |
| `docs/USER_GUIDE.md:227` | create example → `--json --verify`; appended bare-create-advisory sentence |
| `README.md:61-63` | appended MUST-NOT-parse + agent-safe-form lines |
| `scripts/generate-rigs.py:810` | charter primer + "Bare queue output … MUST NOT be parsed … only agent-safe create form is `rig queue create --json --verify`" (regen carried it into 153 rendered leaves; `grep -rl` confirms 153/153) |
| `scripts/send-authenticated.sh` | invokes `rig queue create --json --verify …`; captures stdout; parses JSON receipt with python3 (requires `qitemId` + `state`); prints `created <id> state=<s> persisted=<p>`; fails closed (non-zero + raw stdout on stderr) on create failure OR unparseable receipt OR missing identity |
| `tests/test_queue_json_discipline.py` (new) | 7 hermetic tests: no bare list/show/create examples, create ⇒ `--verify`, both statements present in all 4 files, dry-run shows flags, JSON receipt ⇒ qitemId/state, non-JSON ⇒ non-zero + no delivery claim, identity-less JSON ⇒ non-zero (fake `rig` on PATH; never a live create) |
| `Makefile` test line | added new test file to `make test` |
| regen | `HERETEK_RIGS_ALLOW_DIRTY=1 python3 scripts/generate-rigs.py --vendor-dir <main-checkout>/.scratch/vendor` exit 0 (worktree lacks `.scratch/vendor`; used main checkout pins read-only). 183 generated leaves modified, all under `specs/`/`rigs/`/`rosters/`/`registry/`; no hand-edits there |

Out-of-scope anchors left untouched (prose mentions, not examples, or
generated-skill docs owned by other packages): `docs/TECHNICAL_DOCUMENTATION.md:131`,
`docs/ops/*`, `docs/sprints/*`, `PROMPT_*`, `claude/*`, `gemini/*`,
`rigs/*/skills/*` (regenerated leaves carry only the charter primer change),
`docs/live-health.md` (already `--json`-annotated), `fleet/fleet.yaml`
(no queue examples).

## No-live-mutation record

- NO `rig queue create` / `rig send` executed at any point. Create-path
  proof is fixture-only: canned `--json` receipt bytes (shape per
  `queue-receipt.js` ALWAYS keys) piped through the wrapper via a fake
  `rig` on PATH; advisory-text stdout and identity-less JSON fixtures
  prove fail-closed. T3 single-call transcript therefore uses the
  recorded receipt shape, not a live create — stated plainly per spec.
- Only live commands: read-only `queue show` / `queue list` with and
  without `--json` (evidence above).

## Acceptance outputs

- `make verify` → exit 0, `SUMMARY: 25 checks passed, 0 failed`
  (no new gate block added; spec text said 22 but tree baseline is 25 —
  zero regressions either way).
- `openspec validate remediate-44-json-trailer` → valid.
- `openspec validate remediate-42-create-receipt` → valid.
  (Both emit the pre-existing INFO that archive would refuse the delta
  for a not-yet-existing spec — informational, present for all new-spec
  changes, not a failure.)
- Full suite `python3 -m unittest discover -s tests` → 153 tests OK;
  `make test` (70 tests incl. 7 new) → OK.
- RED→GREEN: new test file failed 6/7 before the fix, passes 7/7 after
  (plus one parser SyntaxError caught and fixed during GREEN:
  backslash inside f-string expression, Python <3.12).

## Skipped / deviations

- T3 live single `create --json --verify` proof: replaced by
  fixture-based wrapper proof (wave constraint forbids mutating creates).
- No `verify-rigs.sh` gate added (specs mandate grep/parse/file proofs,
  which the new unittest file provides; baseline 25 checks untouched per
  the never-renumber rule).
- `docs/live-health.md` queue references already carry `(--json)`
  annotations; left as-is.
