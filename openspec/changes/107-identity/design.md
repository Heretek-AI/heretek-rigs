# Design: 107-identity

## Architecture

Single worktree `.lane/trees/107-identity`, branch `feat/107-identity` from clean `main` (`51d7df1`). Single triad (programmer → qa → drift-guard) with M0 spike gating M1–M3. One PR at end.

## Verified upstream facts (live, `rig` 0.7.2 `8b180689`, 2026-10-27)

- `rig mcp serve --http [--bind host:port]` (default `127.0.0.1:7437`); no token file → loopback acts as `OPENRIG_SESSION_NAME`, declared and unauthenticated, like stdio. First grant created → every request needs bearer, loopback included; caller acts as its grant's seat within its rigs/roots. Token file missing/unreadable → refuse-all; serving unauthenticated again takes a restart with no token file.
- `rig mcp token add <name> --seat <session> [--rig …] [--root …] [--workspace] [--owner]`; prints token once, stores hash only. `token list` never shows tokens/hashes. `token revoke <name>` effective next request; handed-over work stays with owners. No expiry/audience/rotation flags.
- #1860 is a merged PR (milestone v0.7.1), not an open issue; follow-ups (#1872, #1970, #2095, #2096, #2112, #2121/#2125/#2127, #2135) already merged upstream.
- Scope boundary: the MCP HTTP adapter is the authentication boundary; the daemon itself still trusts the loopback seat header → queue/send half likely upstream-blocked (M0 proves it either way).

## Milestone order (principal-approved)

1. **M0 spike (isolated, this host).** Scratch `OPENRIG_HOME=/tmp/107-spike-<ts>` (NEVER the real `$OPENRIG_HOME`; never disturb a running daemon), non-default bind port (e.g. `127.0.0.1:17437`). Probes: `token add` → Bearer 200; bad token → 401; `revoke` → 401; `rig_whoami` authenticated vs declared (grant vs no-grant server); queue-half probe (bare-leading `OPENRIG_SESSION_NAME=` form). Log everything verbatim into `docs/evidence/107-identity-m0.md`. Exit non-zero on any unexpected result.
2. **M1 grants + seed issuance.** Follow the M0 winner. `seed-rig.py` issuance path, secrets-dir storage, `!cat` render into seat MCP config; stdio default unchanged. New tests + appended verify gate.
3. **M2 rotation.** Revoke + re-add runbook executed live; revoked-token 401 red-proof; docs.
4. **M3 queue disposition.** Implement with green gate if M0 allows; else `docs/evidence/107-identity-queue.md` upstream-blocked note (no upstream filing without authorization).

## Trade-offs (all principal-decided)

- Both-paths scope with fail-closed split verdict (Q1+R2Q1): honors intent, no dead grants.
- Spike-first (M0) over spec-blind build (#91 M0 precedent): the automation shape depends on server behavior (token file location, whoami output, daemon coupling).
- Seed automation over manual runbook: fits the repo's secret flow (`!cat`).
- Revoke-based rotation: only mechanism 0.7.2 offers.

## Fail-closed modes

- M0 spike MUST NOT touch real `$OPENRIG_HOME`, real token files, or any running daemon (isolated env + scratch port only).
- If M0 contradicts this design (e.g. expiry flags exist, daemon validates), fix this design file first, then proceed.
- Regen only on clean tree; evidence commits between triad steps per coordinator protocol.
