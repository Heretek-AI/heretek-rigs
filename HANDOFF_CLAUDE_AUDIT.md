# HANDOFF — Claude: rerun the adversarial fleet audit (factory question)

Date: 2026-10-23. Author: Agency Wave Coordinator (this session).
Consumer: a Claude session, cold. Read this file top to bottom, then execute.

## 1. Your mission in one paragraph

Rerun the three-subagent adversarial audit in `PROMPT_ADVERSARIAL_FLEET_AUDIT.md`
against current `HEAD`, with one difference from the October 19 run: the
**factory question** below is now the verdict that matters. Audit the code AND
the functionality — live, on the real fleet. Answer: **can the heretek-rigs
51-seat fleet operate as a self-governing factory — taking large missions from
dispatch through build, test, and delivery without operator fallback, across
build, test, design, and reverse-engineering disciplines, and under rising
concurrency without breaking its gates?** (Phrasing is yours to refine; the
bar is: a new game engine, a website, a reverse-engineering target — dispatched
as missions, delivered as verified output, no human hands in the loop.)

## 2. Starting state (verified 2026-10-23, re-verify everything yourself)

- Repo: `/home/john/Projects/heretek-rig-workspace/heretek-rigs`, `main` @
  `70c1edc` (merge PR #64). Tree clean.
- Fleet: `heretek-omni-fleet`, 51/51 running, 0 need attention, daemon port
  7433 (`rig daemon start --no-kernel` if dead; `rig up heretek-omni-fleet`
  resumes from snapshots — both used this week).
- `verify-rigs.sh --check-only`: **27/0**. `make test`: 125 OK.
- Open issues: 7 (`gh issue list --state open`). Backlog that constrains you:
  #9 (send has no sender identity — `scripts/send-authenticated.sh` is the
  workaround), #11 (no single-node policy refresh — running seats enforce OLD
  policy; whole-fleet bounce is the only refresh), #15/#16/#17 (auth lag,
  parallel builds, utilization — directly your load question), #18 (no
  GPU/display runner — display proofs have no execution home).
- Known degraded: `github.pat` absent from secrets → seeding runs
  `--allow-missing-secrets` (GitHub-backed seats degraded). Mission repo
  (`heretek-asset-manager`) exists but is essentially unstarted — prefer
  scratch missions (see bounds).

## 3. What changed since the October 19 audit (your regression ledger seed)

The October 19 run (`AUDIT_REPORT_FINDINGS.md`) predates ALL of this. Every
prior finding must be re-verified from scratch — never carried forward:

- **Remediation phase (issues #37–#45, PRs #50–#58, all VERDICT: PASS):**
  live-health checks (#45), unblock (#38), regen-gate with allowlisted
  session-stray handling (#43), manifest closure (#40), policy verifier (#41),
  queue-ID discipline (#37), queue `--json` discipline — bare queue output
  mixes JSON with a human trailer and MUST NOT be parsed (#44+#42),
  tracker-vs-queue reconcile diff, read-only, TPM-approved (#39).
- **#57 (PRs #61 spec, #62 implementation):** `scripts/generate_trackers.py`
  proposes dispatch-tracker Status cells from queue state (propose-only,
  fresh `--out` guard, shared row model in `scripts/reconcile_model.py`,
  25 tests). Review found and fixed: paste-ready cells citing `queue note
  None`, missing UTF-8 pins, V11 crash on missing proposal file.
- **#12 spike + canary wave (PRs #63, #64):** the "no seat can execute
  builds" investigation. Corrected matrix: ~30 seats hold scoped build/test
  verbs (the "only cpp-lowlevel-eng builds" claim was over-narrow); the true
  gaps were narrower (no `git add` anywhere, read-only committer, dead
  configure/compile for the engine seat). Canary grant: exact `date +%s` on
  `engine-systems-eng` only + `scripts/check-envelope.py` PRE-AUTH verifier
  (47 tests). Review found and fixed 9 more (exact-grant narrowing, expiry-XOR,
  marker anchoring, duplicate-section ambiguity, path-scope classes, PUSH
  refspec rejection). STAGED for follow-up: runner build proof (D1–D4),
  committer path (D5–D7), fleet-wide rollout.
- **Test-lie history to mine:** `REMEDIATION_LOG.md` (694KB) + the wave
  verification reports (`docs/reports/*-verification.md`) document real
  cases of green-that-lied: the reconcile `--out` overwrite hole (exact-match
  guard bypassed by a differently-pathed victim), queue-trailer JSON
  contamination, vacuous `openspec validate` blind spots (tasks.md presence,
  MUST-enforcement) caught only by STRUCT3/MAP gates. These go in your
  Cardinal-Rule section verbatim. Treat every `VERDICT: PASS` in
  `docs/reports/` as a claim under audit, not evidence.
## 4. How to run it

1. Execute `PROMPT_ADVERSARIAL_FLEET_AUDIT.md` as written (Alpha/Beta/Gamma,
   cross-examination, synthesis → overwrite `AUDIT_REPORT_FINDINGS.md`).
   Regression Ledger covers every October 19 finding + every remediated
   issue above.
2. **Then run the factory missions** (your choice of missions — the principal
   explicitly leaves mission choice to you; suggested families, pick at
   least one per family and say why): (a) a scoped engine-style build
   (compile + test + artifact through seats, no operator fallback);
   (b) a designed-and-built website; (c) a reverse-engineering exercise —
   legal boundary: only binaries you own, open-source targets, or provided
   samples, never anyone else's commercial game dump; if the principal's
   PS3 target can't be sourced legitimately, say so and substitute;
   (d) a concurrency/load run aimed at #16/#17 (parallel multi-seat slices,
   queue throughput — find what breaks first).
3. Judge each mission by the factory bar: dispatched → built → tested →
   delivered with evidence, zero operator fallback, gates still green after.

## 5. Bounds (principal-approved — these override the prompt's limits where they conflict)

- **Live freedom, with discipline:** you may use the full fleet, run real
  missions, and experiment with policy/capability changes. MANDATORY:
  snapshot before any mutation (`rig snapshot`), record the rollback recipe,
  prefer canary-first for permission changes, never bounce the fleet to work
  around a refusal (a refusal IS data — see #11).
- **Hard no-gos (unchanged):** no push to `main` (one branch per change, PR,
  human merges — see `AGENTS.md`); no package publishing, no tags, no
  GitHub writes (file findings as report sections; the principal triages);
  no real credentials anywhere (dummy values, `/tmp` scratch, 0600);
  no destructive commands outside scratch; mission work in scratch dirs or
  explicit mission repos, never inside this repo's tracked tree except the
  report + prompt file.
- **Read `AGENTS.md` first** (the one rule: never hand-edit generated
  leaves; `fleet.yaml`/scripts edits + regenerate; verify-rigs checks are
  audit-baselined — add alongside, never renumber). Daemon/CLI pin:
  `@openrig/cli@0.6.13`; upstream `mvschwarz/openrig` issues #1785/#1806
  still open (local mitigations hold).

## 6. What to hand back

1. `AUDIT_REPORT_FINDINGS.md` (overwritten per the prompt protocol) with a
   **Factory Verdict** section answering §1's question per discipline +
   under load, each verdict backed by a mission log.
2. A short brief in chat: the 3 most important findings, what you chose for
   missions and why, anything you could not verify, and the single most
   important fix.
3. Do NOT open PRs for fixes — findings only. Remediation waves follow
   through this repo's coordinator discipline.
