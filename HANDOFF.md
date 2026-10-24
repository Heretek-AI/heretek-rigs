# Handoff — next session (2026-10-24, post-#105 triage, PR #104 declined)

> Superseded 2026-10-23 handoff removed below (stale SHA/PR states, superseded frontier); full text in git history.
> This section is the current plan. Live state re-verified this session before writing.

## Live state (re-verified 2026-10-24)

- Repo: `/home/john/Projects/heretek-rig-workspace/heretek-rigs`. `main` @
  `1e2979c` (merge PR #110). `git status --short` clean at time of writing.
- PR #104 (`fix/mcp-browserbridge-provisioning`) CLOSED unmerged 2026-10-24T18:04Z
  (`mergedAt: null`). Do not assume its contents landed.
- Open issues: 24 — #9,#11,#12,#15,#16,#17,#18,#66,#74,#76,#77,#78,#80,#81,
  #91,#94,#95,#96,#98,#101,#102,#106,#107,#111. (#72 closed as mitigated;
  #88/#89/#90 confirmed CLOSED as dups; GitHub #75 CLOSED = problem,
  #106 OPEN = implementation.)
- Since last handoff: PR #105 merged (`72593bc`, 5 gated waves M0–M10 + V14,
  all `VERDICT: PASS` on disk) closing #67,#68,#69,#70,#71,#73,#79,#82–#87,
  #92,#93,#97,#99,#100; Claude follow-ups #109 (audit_loop ledger cell) + #110
  (sandbox scratch, 408 legacy `seatjail.*` deliberately unswept); #103 prompt
  docs consumed. Per-issue record comments left on #66,#68,#72,#74,#79,#106,
  #107,#12 + PR #104.

## Roadmap — where to go next (priority order)

### P0-1 — #106 commandEffects (the one unimplemented P0/P1 hardening)
- Why first: only #105-scope item with zero code hits
  (`grep -rn commandEffects scripts/ fleet/ tests/` = nothing). Relieves #91
  note-half without loosening the 31 terminal denies.
- Acceptance (from issue): seat can pass paths + `|` in `rig queue --note`
  without tripping denies; `--body-file <path>` inside own write scope allowed;
  `--body-file prod.env` and `/etc/passwd` stay denied; red-proof both
  directions into evidence.
- Suggested wave: spec in `openspec/changes/command-effects/` → implement →
  red-proofs → VERDICT PASS → PR. Keep #91 OPEN (path-half remains after #106).

### P0-2 — #111 ops sweep (no code, minutes)
- One-time sweep of legacy `seatjail.XXXXXX` dirs in `/var/tmp` (408 observed in
  #110 body, pre-pid-naming, explicitly unswept). Verify ownership/content,
  count-log, confirm only pid-namespaced dirs cycle afterwards. Close #111,
  note on #68/#66.

### P1 — #107 residuals bundle (quick wins + upstream watch)
- Verify-harness: V13 `toomanyrequests` skip-regex (went RED twice, fail-closed);
  firecrawl standalone boot on networked host (pin corrected on-host only).
- Governance limits (fail-closed, harden later): bare-`TPM` shorthand, `xyz123`
  human, "QA PASS, no issues" non-terminal, F9 bare-leading-env (upstream
  per-seat tokens; #72 closed as mitigated, F9 box tracks the request).
- Noise: footer session-URL (`YZ9W` vs `nx9` — pick one), 26-vs-30 check-count
  drift (also in #102 — fix in one place, ref the other).
- Note: #107's "#88–90 don't exist" box is wrong (they exist, CLOSED as dups) —
  correction comment already left; check the box off.

### P2 — policy decisions needed before code (principal)
- #76 (`*--output*` deny vs `ctest --output-on-failure`): explicit policy call
  now that the tuple is 31 entries. Decision gates #91-path-half too.
- #91 path-half (`pytest tests/rag`, `go build ./...`, `cmake -S . -B build`,
  `gcc -c …` denied): #106 relieves notes only. Decide: per-tool arg grants vs
  wrapper scripts vs stays-denied.
- #74 re-plan (PR #104 declined): per-server provisioning matrix (7/20 MCP +
  r2/rabin2/tshark) + stage-time existence gate (the missing gate from #89).
  Do NOT re-submit the single-slice swap as a #74 close; next proposal must
  cover all servers or scope explicitly to one slice without closing #74.

### P2 — checker hardening batch (can parallelize after decisions)
- #94 manifest-closure evasions, #95 verifier TOML spellings + fixture pin,
  #96 config hot-reload (contradicts #11 bounce semantics), #98 hand-made
  schemas vs 0.6.13, #101 nextjs frontmatter (67/68 loads), #102 P3 bundle
  (incl. 64-vs-68 + 26-vs-30 drift). Each: extend checker + corpus test +
  red-proof; new gate blocks, never renumber.

### Structural / live-behavioral (defer unless principal reprioritizes)
- #77 stuck parent rows (no gate owner), #78 single-workspace pin (#88 dup),
  #80 snapshot-by-name (upstream `mvschwarz/openrig` + local doc mitigation),
  #81 park-after-claim (daemon behavior). All untouched by remediation.
- Older backlog unchanged: #9 (send identity), #11 (launch refresh), #12
  (canary clock-grant only via #63/#64 — full builds still blocked by
  #91 + #75/#106; dwarfs the rest, needs own design tree), #15/#16/#17
  (auth lag / parallel slices / utilization), #18 (GPU runner).
- Tracking: #66 stays OPEN as umbrella until #106/#107 + P2 decisions close.

## Suggested sequencing

1. Wave A: #106 (spec → implement → red-proofs → VERDICT PASS → PR).
2. Wave B (parallel-safe, no code): #111 sweep + #107 V13 regex + firecrawl boot.
3. Decision round: #76 + #91-path-half (principal policy calls).
4. Wave C: #74 re-plan (matrix + existence gate), scoped honestly.
5. Wave D: checker batch #94/#95/#96/#98/#101/#102.
6. Parked: #77/#78/#80/#81, #9/#11/#12/#15–#18 — revisit only on principal call.

## Grilling frontier (adapt-or-adopt)

- Q1 — Wave A scope: #106 alone, or bundle #91-path-half policy with it?
  Recommend: #106 alone (acceptance is crisp; path-half needs a policy decision first).
- Q2 — #74: full provisioning matrix, or scoped slice proposals that leave #74 open?
  Recommend: matrix first (otherwise we repeat #104).
- Q3 — #76/#91: loosen denies per-tool, or hold the line and bless wrappers?
  Recommend: principal decides; implementer does not freelance policy.

## Discipline (unchanged)

Spec in `openspec/changes/<id>/` → implement on isolated branch/worktree →
commit → red-proofs → evidence commit → drift-guard, VERDICT read from disk
(never from summary) → PR, human merges. Never push to `main`. `make verify`
green after merges. Prune only your own worktrees. Archive finished
`openspec/changes/<id>/`.

---
> Superseded 2026-10-23 handoff removed 2026-10-24 (stale SHA/PR states, superseded frontier); full text in git history.
