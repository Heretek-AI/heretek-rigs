# Tasks: 2026-10-29-upstream-filing

## Package

- [x] Author change package (proposal/spec/design/tasks per agreed design)
- [x] Verify our issue titles/bodies live (`gh issue view 127`, `80`, `11`
      — titles cited verbatim; note: the plan text rendered #80's title as
      `[object Object]`; the real title is
      "rig snapshot list <rig-name> prints 'No snapshots'; only rig ID
      works" and is cited as such)
- [x] Verify upstream read-only: repo resolves; #2200 open/confirmed;
      #1681/#1707/#2168 merged-confirmed with discrepancy recorded;
      v0.7.5 release confirmed; v0.7.4...v0.7.5 compare shows no `rig
      launch` relaunch fix; local 0.7.5 read-only snapshot-name checks run

## Drafts (PREPARE-ONLY — no filing)

- [x] Draft (a) `docs/evidence/upstream-filing/127-queue-send-attestation.md`
      — URL, problem, wave-9 + #127 evidence, "attribution, not
      authentication" note, attestation ask; self-contained
- [x] Draft (b) `docs/evidence/upstream-filing/080-snapshot-list-by-name.md`
      — URL, problem, #1681-as-covering-fix discrepancy recorded, #1707 /
      #2168 as adjacent, 0.7.5 verification, release-vehicle ask;
      self-contained
- [x] Draft (c) `docs/evidence/upstream-filing/011-full-restart.md` — URL,
      problem + live impact, #2200 adjacent (accurately distinguished), #96
      live-refresh route, relaunch/refresh/help-text ask; self-contained
- [x] Negative-content sweep: `grep` drafts for secret-shaped strings,
      Bearer material, and machine-local paths — zero hits

## Gates

- [x] Compound green in worktree (39/0, `openspec validate`, self-test,
      idempotent; `make test` skipped with reason — zero code/test/script
      diffs)
- [x] Negative check stated in stage report (all upstream interactions
      GETs, listed; zero filed) for QA re-verification
- [ ] Triad → `VERDICT: PASS` before any PR (Refs #127, Refs #80,
      Refs #11 — never Closes)
