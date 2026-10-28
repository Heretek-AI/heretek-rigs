# QA report: wave-44-42-queue-json (heretek-rigs #44 + #42, one upstream issue)

Stage: wave-44-42-queue-json · Commit under test: 9a8c272
(`feat(44-42-queue-json): mandate --json/--verify queue discipline, fail-closed create wrapper, shared upstream issue`)
Worktree: /home/john/Projects/heretek-rig-workspace/heretek-rigs/.lane/trees/wave-44-42-queue-json
Verdict: **QA-CLEAN** — no blocking findings. No commits made; sabotage-only edits, all restored.

Contract tested (BOTH packages, every numbered requirement):
REQ-44-A1 (every queue example carries --json + MUST-NOT-parse), REQ-44-A2
(upstream issue with byte-exact evidence), REQ-44-A3 (parse-first-try),
REQ-44-M1 (bare examples replaced in place, regen green),
REQ-42-A1 (create --json --verify only agent-safe form + advisory statement),
REQ-42-A2 (wrapper parses receipt fail-closed), REQ-42-A3 (exactly one shared
upstream issue), REQ-42-M1 (bare creates replaced in place, regen green).

## 1. Baseline acceptance (unmodified tree)

| Check | Command | Result |
|---|---|---|
| Verify | `make verify` | PASS — `SUMMARY: 25 checks passed, 0 failed`, exit 0; live-health advisory only (heartbeat WARN, exit 0). NOTE: spec text says "22 checks" but tree baseline is 25 — no new gate added, zero regressions either way (V1–V9 behavior-identical). |
| Full suite | `python3 -m unittest discover -s tests` | PASS — 153 tests OK |
| Make test | `make test` | PASS — 70 tests OK (incl. 7 new `test_queue_json_discipline`) |
| Spec valid #44 | `openspec validate remediate-44-json-trailer` | valid (exit 0; pre-existing INFO that archive would refuse the delta for a not-yet-existing spec — informational, present for all new-spec changes) |
| Spec valid #42 | `openspec validate remediate-42-create-receipt` | valid (exit 0; same informational INFO) |

## 2. Red-proof sabotage (all 7 steps per check; fixture/fake-rig only, NEVER a live create)

Full transcript: `docs/evidence/wave-44-42-queue-json/red-proofs.log`.
`docs/evidence/wave-44-42-queue-json/qa-run.log` holds the baseline outputs.

- (a) Bare queue example: appended a bare `rig queue list` line (no --json) to
  README.md → `test_every_queue_example_carries_json` FAILED (failures=1),
  naming `README.md:88`; unittest exit 1. Restored, clean. **PASS.**
- (a2) --verify-less create: appended a `--json`-without-`--verify` create
  example to docs/USER_GUIDE.md → `test_every_create_example_carries_verify`
  FAILED (failures=1), exit 1. Restored, clean. **PASS.**
- (b) Byte-exact trailer, live read-only (show/list only, no create): bare
  `rig queue show qitem-20261022111416-78213c07c3272cbc` → exit 0, 3628 bytes
  stdout / 0 bytes stderr (matches report); tail is the bounded-preview
  trailer; `json.loads(bare)` → exit 1,
  `JSONDecodeError: Extra data: line 96 column 1 (char 3472)` (matches report
  byte-exact). Same command + `--json` → exit 0, parses first try (qitemId +
  full key set, stderr empty). Fake-rig replay of the recorded bare bytes
  reproduces the identical Extra data (char 3472) failure.
  **PASS (REQ-44-A3 reproduced independently).**
- (c1) Success receipt via fake `rig`: wrapper exits 0 printing
  `created qitem-20261022000000-deadbeefdeadbeef state=pending persisted=True`.
  **PASS (REQ-42-A1 single-create shape).**
- (c2) Malformed receipt (advisory text) via fake `rig`: wrapper exits 3,
  prints unparseable-receipt + raw stdout on stderr, stdout empty (no delivery
  claim). Identity-less JSON `{"ok":true}`: exits 4 with receipt-lacks
  message. **PASS (REQ-42-A2 fail-closed, no silent mis-parse).**
- (c3) --verify-less shape not agent-safe: wrapper's only execution line
  (send-authenticated.sh:175) hard-codes `--json --verify`; `--dry-run`
  prints the flagged invocation and executes nothing; discipline test (a2)
  rejects --verify-less examples. (Note: :52 prose inside print_help recounts
  the pre-wrapper bare pattern — out of T1 grep scope, not an invocation.)
  **PASS.**
- (d) Neutered fail-closed parse: replacing sys.exit(3)/sys.exit(4) with
  spoof-defaults + skipped identity check → both fail-closed tests FAIL
  (failures=2), unittest exit 1. (Partial neuter also RED: failures=1.)
  Restored, `bash -n` clean. **PASS (tests non-vacuous).**
- (e) Live-create impossibility under test: 7-test wrapper module run with a
  tripwire `rig` (logs argv, exits 42) shadowing the real binary — 7/7 OK
  with zero tripwire hits (all create flows used the tests' own
  fake-rig-on-PATH; daemon never touched). **PASS.**

No vacuous checks found. (One sabotage attempt with unbalanced shell quoting
broke `bash -n` instead of the assertion — discarded, redone surgically;
recorded in the log for honesty.)

## 3. Upstream issue honesty

- Exactly ONE issue filed: twin-hunt over `mvschwarz/openrig` shows only #1806
  on the trailer/receipt/stdout topic (author's other issues are unrelated).
  Targeted search returns 1806 alone. **PASS.**
- Recorded URL resolves: `mvschwarz/openrig#1806` OPEN, body fetched via
  `gh issue view`; contains the byte-exact evidence (3628 bytes, char 3472,
  line 96 col 1), code cites, and all three asks (trailer + compact notice +
  receipt text to stderr). **PASS.**
- Both packages cite the identical URL: grep finds
  `https://github.com/mvschwarz/openrig/issues/1806` in both proposal.md files
  and the evidence doc. No second issue. **PASS (REQ-44-A2 + REQ-42-A3).**

## 4. Regen honesty (189-file commit)

- 189 files = 11 non-leaf + 178 generated leaves under
  specs/rigs/rosters/registry. Every non-leaf file justified against the two
  specs (queue rows, test harness line, statements, URL records, primer,
  wrapper, proofs, T6 report). **PASS.**
- Sampled 8 leaves across rigs/specs/registry; full-census audit of all 608
  changed leaf lines: 306 primer + 302 digest/provenance, 0 unexplained.
  Zero hand-edits beyond regen output. **PASS (REQ-44-M1 + REQ-42-M1).**

## 5. Wave-6 overlap

Spot-checked claimed already-fixed anchors against HEAD~1: README:61 and
USER_GUIDE:215 list --json examples already flagged (genuinely fixed); this
wave's diffs there are statement-appends only, no flag churn. AGENTS.md
pre-commit still had a bare queue-create example — this wave's fix is new
work, not duplication. **PASS.**

## 6. Skipped / out-of-scope (confirmed, not gaps)

- NO CLI code changed: repo has no dist/CLI sources; commit touches zero
  CLI/vendor paths. **PASS.**
- NO live queue mutations: verifier issued only read-only queue show/list;
  all create-path proof via fake rig (argv audit: zero creates reached a real
  binary); git status clean except this QA's own docs/evidence/ log dir.
  **PASS.**

## Findings

No blocking findings. Two informational notes (not findings):
1. Spec "22 checks" vs tree baseline "25 checks" — pre-existing drift, no new
   gate added per the never-renumber rule; 25/0 green.
2. `openspec validate` INFO about archive refusing new-spec deltas —
   pre-existing, informational, present for all new-spec changes.
