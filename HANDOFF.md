# Handoff — next session (2026-10-23, post-remediation-phase)

Remediation phase COMPLETE: all 9 issues (#37–#45) implemented, each verified on
disk (VERDICT: PASS), merged to `main` (PRs #50–#58, all MERGED), all 9 issues
CLOSED. Docs-hygiene PR #59 (`docs/final-count-hygiene`, live-count refresh to
26) was OPEN at time of writing — verify before merging. Read `AGENTS.md` first;
re-verify everything below before acting.

## Grilling protocol (mandatory)

Next session works **decisions as a design tree, in rounds**. Frontier =
unsettled-prerequisite decisions only. One numbered question per decision, worded
so "yes" accepts the recommendation. FACTS are the agent's job (verify in
repo/CLI); DECISIONS are the principal's. No acting until shared understanding
is confirmed and the frontier is empty. Suggested Round 1 below is
adapt-or-adopt, not pre-decided.

## Live state (re-verified 2026-10-23 by this session)

- Repo: `/home/john/Projects/heretek-rig-workspace/heretek-rigs`. `main` @
  `50d39b0` (merge PR #58). Primary checkout clean except untracked `.lane/`.
- Reconciliation done: pre-phase dirt preserved on local branch
  `session-backup-2026-10-23` @ `45ec8c6`, then primary fast-forwarded to
  `50d39b0`. Backup branch verified to exist.
- Worktrees: `.lane/trees/` holds only `docs-handoff` + `docs-hygiene` (ours).
  Pre-existing `*-self-*`, `*-selftakeover`, `*-remediate-5` worktrees left
  alone — not ours, do not prune without asking.
- `make verify` (run in this worktree): **SUMMARY 26/0** — static 22 + #45
  live-health advisory (heartbeat WARN on stale seats, exit 0 by design).
- Fleet: daemon running (port 7433), `rig ps` = 1 rig · 51 seats · 0 need
  attention (`heretek-omni-fleet`, 51/51 running, uptime 1d 10h). Fleet is UP.
- Mission repo `/home/john/Projects/heretek-asset-manager`: **zero commits**
  (`main` has no commits yet), remote `Heretek-AI/Asset-Manager`, scaffold
  untracked. Read-only confirmed; no mission work started.
- Env: secrets dir `~/.config/heretek-rigs/secrets/` 0700, `opencode-go.key`
  0600 present (never read contents). `opencode.json` allowlists shell commands
  (generate/verify scripts). Shell tooling intermittently rejects commands —
  split, retry once, reroute.

## (a) Remediation phase — 9/9 MERGED, VERDICT PASS each

| Issue | PR | Verdict file |
|---|---|---|
| #45 live-health | #50 MERGED | `docs/reports/wave-45-live-health-verification.md` |
| #38 unblock | #51 MERGED | `docs/reports/wave-38-unblock-verification.md` |
| #43 regen-gate | #52 MERGED | `docs/reports/wave-43-regen-gate-verification.md` |
| #40 manifest-closure | #53 MERGED | `docs/reports/wave-40-manifest-closure-verification.md` |
| #41 policy-verifier | #54 MERGED | `docs/reports/wave-41-policy-verifier-verification.md` |
| #37 id-discipline | #55 MERGED | `docs/reports/wave-37-id-discipline-verification.md` |
| #44+#42 queue-json | #56 MERGED | `docs/reports/wave-44-42-queue-json-verification.md` |
| #39 reconcile | #58 MERGED | `docs/reports/wave-39-reconcile-verification.md` |
| specs #46/#47/#48 | MERGED | (spec packages, no verdict files) |

## (b) Follow-ups still OPEN (owned by this phase)

- #57 (OPEN): deferred generate-from-queue follow-up from #39 (Option B).
  Owns the next reconcile work.
- Upstream `mvschwarz/openrig` #1785 (`queue satisfy`) + #1806 (JSON/trailer to
  stderr) — both verified OPEN. Local mitigations hold; upstream pending.
- PR #59 (OPEN at handoff): `docs/final-count-hygiene`, refresh counts to 26.

## (c) Pre-existing backlog — untouched, out of completed scope

- #9 (OPEN): `rig send` carries no sender identity — seats distrust human relay.
- #11 (OPEN): launch refuses running nodes; no single-node policy refresh.
- #12 (OPEN, load-bearing): no seat can execute builds — needs own design tree,
  dwarfs the rest. Deferred with written rationale.
- #14 (CLOSED): 51-agent enhancement recs — already COMPLETE, no action.
- #15 (OPEN): authorize-then-execute lag goes stale before execution.
- #16 (OPEN): parallel multi-seat builds without breaking gate honesty.
- #17 (OPEN): fleet utilization / what breaks first as concurrency rises.
- #18 (OPEN): no GPU/display runner for S03 swapchain proofs.

## Suggested Round 1 frontier (adapt-or-adopt)

- Q1 — Next mission: #12 scoping spike vs Asset-Manager mission vs #57
  generation? Recommend: principal picks; note #12 dwarfs the rest.
- Q2 — Merge PR #59 now or with next batch? Recommend: merge now, one click.
- Q3 — Upstream #1785/#1806: watch/wait vs contribute fixes? Recommend: wait;
  local mitigations hold.

## Implementation discipline (next session)

Spec in `openspec/changes/<id>/` → agency-programmer on isolated
branch/worktree → commit → agency-qa red-proofs → evidence commit →
agency-drift-guard, VERDICT read from disk (never from summary) → PR, human
merges. Never push to `main`. `make verify` green after merges. Prune only your
own worktrees. Archive finished `openspec/changes/<id>/`.
