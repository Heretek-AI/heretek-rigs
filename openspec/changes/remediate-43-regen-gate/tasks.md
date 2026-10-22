# Tasks: remediate-43-regen-gate

Execution waves: implement classifier (T1–T2) → consistency check + docs
(T3) → acceptance incl. returnable (T4–T5) → report (T6). Map 1:1 to
`specs/regen-gate/spec.md`. Specs ONLY — no implementation in this package.

- [ ] T1 — Classified dirt check (REQ-RG1/RG2): implement the allowlist +
      classifier in `scripts/generate-rigs.py` (single in-repo source,
      per-entry justification comments, prefix-for-dirs / exact-for-files,
      status-code-first with tracked-override, fail-closed on unreadable
      source, provenance still `rev-parse HEAD`).
      Testable (synthetic git trees in /tmp, never the live checkout):
      sanctioned-strays-only → resolves SHA; tracked `M` added → exit 2;
      non-allowlisted `??` added → exit 2; committed-then-edited allowlisted
      path → exit 2.
- [ ] T2 — Refusal message (REQ-RG3): blocking lines verbatim + ignored
      sanctioned paths listed separately; happy path silent about dirt.
      Testable: refusal output on the T1 fixtures shows both classes; clean
      run output byte-identical to today's clean-run output.
- [ ] T3 — Consistency check + docs (REQ-RG4): append the allowlist-vs-
      AGENTS.md:46 check to `scripts/verify-rigs.sh` (next number, no
      renumbering); update every old-count reference touched by this
      change's docs edits (AGENTS.md gate paragraph + any edited file's
      "22" strings).
      Testable: `make verify` green with the new count; removing one
      AGENTS.md:46 stray from the allowlist (sabotage) fails the new check
      while the other checks stay green.
- [ ] T4 — QA red-proofs: (a) HANDOFF.md-style tracked modification still
      refuses without `ALLOW_DIRTY=1`; (b) `ALLOW_DIRTY=1` semantics
      unchanged (proceeds + records real SHA); (c) real regen on the stage
      worktree with session strays present and no env override succeeds.
      Record all three.
- [ ] T5 — Acceptance: fresh session producing normal evidence
      (`docs/evidence/…`, `docs/reports/…`, loop JSON) runs
      `generate-rigs.py` with NO env override (returnable); `make verify`
      green at the new count.
- [ ] T6 — Report: write `docs/reports/remediate-43-regen-gate-
      implementation.md` (files changed, allowlist source choice,
      verification outputs).
