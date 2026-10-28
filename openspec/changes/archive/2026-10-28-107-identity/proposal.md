# Proposal: 107-identity — per-seat bearer-token grants for MCP-over-HTTP (and queue-half disposition)

Status: scope approved (principal decisions 2026-10-27, grilling Rounds 1–3 all settled per round).
Issues: #107 (identity follow-up). Refs #66 umbrella. Closes #107 only if the MCP path is fully fixed per scope; the queue half may land as documented-upstream-blocked.

## Why

Seats prove identity with a spoofable env var: `OPENRIG_SESSION_NAME=<seat>` records `identityProvenance: transport:v1`, and pps strips leading `VAR=` before matching so the `*OPENRIG_SESSION_NAME=*` deny never fires on the bare-leading form (see `docs/REMEDIATION_IMPLEMENTATION_PROMPT.md:131`, `scripts/gate-role.sh:146`). Mitigation today is claim-only (`send-authenticated.sh` refuses when the var is set; `--source` is `claimed:v1`). Upstream OpenRig #1860 (merged PR, milestone v0.7.1) ships the identity primitive for the MCP path in our pinned `@openrig/cli@0.7.2` (`8b180689`, verified live via `rig --version`): `rig mcp serve --http` validates per-request bearer grants from `$OPENRIG_HOME/mcp-http-tokens.json` (sha256, mode 600), never falling back to the env seat once a grant exists. This change adopts that primitive for MCP communications and dispositions the queue/send half on live evidence.

## What Changes

- M0 (first, live spike on this host where `rig` 0.7.2 is installed): isolated-`OPENRIG_HOME` scratch probe of `token add` + `serve --http` — Bearer allow, bad-token 401, revoked-token 401, `rig_whoami` authenticated-vs-declared, plus a queue-half probe. Outcome recorded in `docs/evidence/107-identity-m0.md`; implementation follows the winner (fail-closed: no dead grants if the queue half proves daemon-blocked).
- M1: per-seat grants + seed-time issuance automation (`seed-rig.py` runs `token add`, stores the once-printed token under the secrets dir, renders into seat MCP client config via the existing `!cat` pattern); stdio default unchanged.
- M2: revoke + re-add rotation runbook + docs, with revoked-token 401 red-proof (0.7.2 has no expiry flags).
- M3: queue-half disposition — repo-side fix if M0 shows it possible, else documented-upstream-blocked note with evidence (upstream filing only if principal authorizes).

## Acceptance

1. M0 evidence log exists with all four live outputs (Bearer 200 / bad 401 / revoked 401 / whoami) plus the queue-half probe result.
2. M1: scoped grants allow their seat, cross-seat/revoked deny; `make verify` green (appended blocks, no renumber).
3. M2: rotation runbook executed end-to-end live, revoked token 401s.
4. M3: disposition note exists; if implementable, its gate is green.
5. Drift-guard `VERDICT: PASS` on disk → PR (`Refs #107`; `Closes #107` only if MCP path fully fixed).
