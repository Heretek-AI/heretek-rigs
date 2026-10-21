# Self-Takeover Sprint — TPM Backlog (2026-10-21)

Source: `qitem-20261021155313-fe1742ceba05b628` (operator relay, human-ref: operator session 2026-10-21, self-takeover evaluation).
Owner: `delivery-tpm-scrum-lead@heretek-omni-fleet`. Status: decomposed, 3 slices dispatched, 3 sequenced.
Prior context: `docs/sprints/TOOLING-B1-RIG5.md` … `TOOLING-B7-RIG4.md`, `docs/sprints/PRE-AUTH-ENVELOPES.md`.

Hard constraints (operator, verbatim in intent): root `AGENTS.md` never touched;
one slice per owner, no two seats editing the same file concurrently; no seat
commits/pushes/merges; catalog/charter/permission edits only via ST-1…ST-4 with
full regen + verify 22/0; commit requests via queue item to OPERATOR with exact
file list + verify output + TPM sign-off; never hand-edit generated leaves.

Scope note: TPM seat holds no `fleet/*` read scope (denied this turn, quoted in
ST-1). Catalog-state claims below come from the B1–B7 ledgers + `grep` over
generated mirrors, marked accordingly. Each implementing owner re-verifies at
source before editing (fail closed, S02 precedent).

## Dispatched now (disjoint files, parallel-safe)

Status 15:56Z: ST-5 DONE (accepted), ST-6 DONE (accepted). ST-1 BLOCKED 15:58Z
(see ST-1 verdict below) — ST-2/3/4 BLOCKED behind the same gate.
Status 16:10Z: ST-1 LANDED at 5c35a73 (operator-applied, 22/0; sabotage grafana
binding explicitly NOT applied, in SELF-TAKEOVER-ST1.md). ST-2/3/4 UNBLOCKED
under proposal rules, serialized. ST-2P dispatched 16:11Z.
Status 17:25Z: ST-2 LANDED at 5c5b46e (24 pins, 22 seats, 22/0; web-access 0.44.0,
rows 40-41 on e2e plus api-contract-tester, red seats REFUSED; ledger
SELF-TAKEOVER-ST2.md). ST-3P dispatched 17:25Z. ST-4 queued behind ST-3.

### ST-1 (B1, unblocked) — Grafana binding for load-stress-tester + sabotage-qa-tester pi_packages bump
- Context & user story: B1 merged to main (grafana catalog entry +
  render-seat.py scoped-name fix). As a load tester I need Grafana MCP bound
  to my seat so dashboards/datasources are queryable; as fleet we need the two
  stale `pi_packages` pins renamed without dropping AST/LSP allows.
- Target: `platform-dependency-patcher@heretek-omni-fleet` (ST-1RR after two scoped handbacks: load-stress-tester `qitem-20261021155527-46779bc3`, architect `qitem-20261021155601-d0144464`; B1 author seat, holds the exact context). Successor row: `qitem-20261021155611-7e91995a`. Prior rows: `qitem-20261021155438-17c7bd79e62951c9` (ST-1), `qitem-20261021155543-cd413bc9` (ST-1R).
- VERDICT 15:58Z — ST-1 BLOCKED, no further reassignment: third owner
  dependency-patcher returned `qitem-20261021155848-2ff4bd03` (summary:
  fleet scope denied in seat, no edits made; row closed done/no-follow-on).
  Three seats (load-stress-tester, system-architect, dependency-patcher) plus
  TPM all hit `fleet/*` deny with zero workarounds. Operator decision needed:
  bounded fleet grant to a named seat, or operator-side edit. ST-2/3/4 stay
  BLOCKED behind the same gate (same files).
- ST-1P proposal 16:03Z: architect authored `docs/architecture/ST-1-PROPOSAL-2026-10-21.md`
  (verified on disk) as a CANNOT-STATE package — both hunks unstated with
  verbatim `fleet/*` + `scripts/*` denials, per-line evidence basis from
  ledgers + generated mirrors, nothing reconstructed from memory. Return row
  `qitem-20261021160337-311fab01` closed done/no-follow-on. Operator-side edit
  is now the only remaining path for ST-1.
- Implementation guide:
  1. Verify merged main state first: grafana entry in `fleet/mcp-servers.yaml`
     (pin `oci:docker.io/grafana/mcp-grafana:2.0.2`) + scoped-name allowlist in
     `scripts/render-seat.py`. If either absent, stop and hand back (stale premise).
  2. Confirm own edit scope before editing; if `fleet/*` write denied, hand back
     with the verbatim denial (S02 precedent — never work around).
  3. Bind `grafana` to `load-stress-tester` in `fleet/fleet.yaml` (B2 evidence:
     one-line follow-up shape; check whether `sabotage-qa-tester` also warrants
     binding per its adversarial charter — record the decision either way).
  4. Bump `sabotage-qa-tester` `pi_packages`: `pi-lsp-extension@1.4.0` →
     `@narumitw/pi-lsp@0.49.10`, `pi-ast-grep@0.1.0` →
     `@nicknisi/pi-ast-grep@0.3.1` (B1 §2 pins); confirm rendered allows intact.
  5. Regen (`python3 ./scripts/generate-rigs.py`, clean tree or
     `HERETEK_RIGS_ALLOW_DIRTY=1` for dev iteration only) +
     `./scripts/verify-rigs.sh --check-only` must read 22/0.
- Acceptance criteria:
  - Given the merged B1 state, when regen + verify run, then 22 checks pass,
    0 fail, and dry-render shows grafana on load-stress-tester with AST/LSP
    allows intact on sabotage-qa-tester.
  - Given any scope denial, when hit, then the denial is quoted verbatim and
    the slice hands back with no workaround attempted.
- DoD: ledger `docs/sprints/SELF-TAKEOVER-ST1.md` + regen/verify evidence +
  commit-request queue item to OPERATOR (exact file list, verify output, QA
  sign-off request). No commit/push/merge by the seat.

### ST-5 (B5) — Stale PR triage (#4 docker, #5 topology, #19 handoff)
- Context & user story: three stale PRs need a recorded recommendation each
  (refresh / rebase / close) with reasons. No merge authority anywhere.
- Target: `delivery-tech-docs-lead@heretek-omni-fleet` (docs remit, delegates_to edge).
- Implementation guide: review each PR head vs current main; record verdict +
  reasons in `docs/sprints/STALE-PR-TRIAGE-2026-10-21.md` (new file, no
  contention). Recommendations only.
- Acceptance criteria:
  - Given PRs #4, #5, #19, when reviewed, then each carries exactly one of
    refresh/rebase/close with a stated reason and base-SHA reference.
  - Given no merge authority, when done, then zero merge/push attempts occurred.
- DoD: triage file on disk + note on the slice qitem. No operator commit needed
  (docs/sprints/* is TPM/tech-docs writable scope — confirm before writing).
- DONE 15:55Z: `docs/sprints/STALE-PR-TRIAGE-2026-10-21.md` verified on disk;
  verdicts #4 REBASE, #5 REFRESH-then-rebase, #19 CLOSE (reopen scoped);
  base SHAs UNVERIFIED (honest); zero merges. Return row
  `qitem-20261021155543-0901a50c` closed done/no-follow-on.

### ST-6 (B6) — MCP connectivity check (codebase-memory-mcp 0.12.1, context7-mcp 4.4.2)
- Context & user story: both binaries are installed on the host. Owning seats
  run `pi mcp list` and report reachability. No credentials invented, ever.
- Target: `exec-system-architect@heretek-omni-fleet` (catalog context holder,
  collaborates_with edge; coordinates the 6 context7 consumers).
- Implementation guide: run `pi mcp list`, report per-server reachability
  (reachable / unreachable + error text, secrets redacted). If a server needs
  credentials, report `BLOCKED: credentials required` — do not invent any.
- Acceptance criteria:
  - Given host-installed binaries, when `pi mcp list` runs, then both servers
    report a reachability verdict with evidence, and no secret material appears
    in any output, file, or command line.
- DoD: verdicts on the slice qitem (+ optional `docs/sprints/SELF-TAKEOVER-ST6.md`).
- DONE 15:55Z: both servers REACHABLE via live tool calls (codebase-memory
  list_projects: 5 rows of 192; context7 resolve: 5 libs incl. /vercel/next.js);
  `pi mcp list` BLOCKED (verbatim rule '*'); pins UNVERIFIED (fleet/* denied).
  No secrets anywhere. Return row `qitem-20261021155543-a434bd4e` closed
  done/no-follow-on.

## ST-2/3/4 under proposal rules (serialized on fleet/* files, ST-1 landed 5c35a73)

### ST-2 (B2) — Pi-extension follow-up batch — ACTIVE (ST-2P proposal)
- Target: `platform-dependency-patcher@heretek-omni-fleet` (ST-2P proposal author;
  row `qitem-20261021161108-108d8c8e5795762b`, dispatched 16:11Z).
- VERDICT 16:13Z — ST-2P cannot-state package `st2p-proposal-package-lock.json`
  (repo root, verified on disk): zero exact hunks, all 7 ledger sections read in
  full, mirrors re-verified post-ST-1 (grafana present, sabotage new pins present,
  ST-2 pins absent everywhere), 4 operator decisions pending (pi-web-access
  0.42.0-vs-0.43.0, B2 rows 40-41 adopting seat, pi-memory/plan-mode scope,
  red-seat pi-web-access confirm-or-refuse). Out-of-scope exclusions recorded
  (pi-memory, plan-mode/usage, pi-web-search Rig-1-only). pi-subagents excluded
  per HR-6.2. Return row `qitem-20261021161344-c4cef038` closed done/no-follow-on.
- Scope: deferred pins across B2/B3/B5/B6/B7 ledgers (pi-lens, pi-btw,
  pi-web-access, pi-mcp-adapter, pi-fff, pi-memory, plan-mode/usage — re-verify
  each pin + license at execution; `pi-subagents` stays EXCLUDED per HR-6.2).
- GWT: given ST-1 landed, when the batch regens, then verify reads 22/0 and no
  seat loses rendered allows. DoD: ledger + commit-request item.

### ST-3 (B3) — context7 cross-rig bump 4.4.2→4.4.4 — PROPOSAL RETURNED (ST-3P)
- Target: `exec-system-architect@heretek-omni-fleet` (ST-3P proposal author;
  row `qitem-20261021172535-07271ba8de94e598`, dispatched 17:25Z).
- VERDICT 17:26Z — CANNOT-STATE package `docs/architecture/ST-3-PROPOSAL-2026-10-21.md`
  (verified on disk): hunk unstated (`fleet/mcp-servers.yaml` unreadable, verbatim
  `fleet/*` denial); sequencing verified at HEAD via git show --stat (ST-1/ST-2
  untouched mcp-servers.yaml); blast radius re-verified via mirrors (6 consumers,
  mcp.json line 9 + command line 12); freshness UNVERIFIED (operator must re-check
  at merge); consumer smoke tests recommended post-bump. Return row
  `qitem-20261021172610-dd51a792` closed done/no-follow-on.
- Blast radius: 6 consumers x 4 rigs (B5 ledger list). Dedicated catalog batch,
  freshness re-check at execution. GWT: given all consumers render, when bumped,
  then verify 22/0 with zero consumer breakage. DoD: ledger + commit-request item.

### ST-4 (B4) — Generator surgery (prisma/supabase/mattpocock pin sources) — QUEUED behind ST-3
- Target (reserved): `exec-system-architect@heretek-omni-fleet` (after ST-3).
- Scope: `pins`-dict surgery + new pinned clones in `scripts/generate-rigs.py`.
  Highest risk; last in sequence. GWT: given new vendor sources, when regen
  runs, then verify 22/0 and vendor SHAs match pins. DoD: ledger + commit-request.

## External blocker (not in backlog scope)

- S02 committer slice: `qitem-20261021155349-a82e7244` (in-progress, TPM-owned).
  Workspace verified this turn: `git status --short` → `?? docs/ops/` only;
  `git diff --stat` clean; HEAD `5af469f`; S02 tree paths absent here — matches
  `docs/ops/S02-committer-drift-2026-10-20.md`. Escalated to product-director
  for the human 6-step stage+commit sequence; SHA return unblocks the operator run.
