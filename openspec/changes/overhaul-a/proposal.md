# Proposal: overhaul-a — P0 sandbox escape, hermetic regen, Docker pipeline

Status: scope approved (principal decisions 2026-10-27/28: three phased waves, full triad bar; findings re-verified live on main `66ba80c` 2026-10-28).
Issues: none tracked (hardening; Refs #66 umbrella only if needed).

## Why

Three P0 defects block a trustworthy fleet: (1) `scripts/seat-sandbox.sh` execs `rig` outside `bwrap` (host-loopback reachability) with no subcommand/flag validation — a seat can exfiltrate secret-store files via `--body-file` or forge `--source` (brief §4.1, reproduced pre-#122); the relay block has since drifted (now `:38`, `os.execvp` at `:47`, `#105 review` shlex handling) so the brief's line numbers are void. (2) `scripts/generate-rigs.py:390` calls `tf.extract(..., filter="data")`, fatal on Python ≤3.11.3, and generation dies without the external `/home/john/Projects/Heretek-Crew` checkout (`:1997`). (3) `docker/Dockerfile` never installs `bubblewrap` while V12 gates on it, and `.github/workflows/docker-release.yml` repeats the `container:` key (`:118` + `:125`).

## What Changes

- M0 (first, spike in stage worktree): re-run the sandbox-exploit + `TarFile.extract filter` probes against the CURRENT tree; log verbatim. M1/M2 follow the winner.
- M1: hardened `rig` relay in `seat-sandbox.sh` (re-derived bounds): subcommand allowlist, `--source == $OPENRIG_SESSION_NAME`, `--note` pattern, `--body-file` containment before exec; `TestRigRelayEnforcement` in `tests/test_seat_sandbox.py` (bwrap-independent).
- M2: `filter` guard for old Pythons; hermetic charter fallback (`fleet/charters/` or in-tree role docs when `--crew-source` absent); snapshot-and-restore vendor guard with tree-hash verification; `--check-idempotent` green with `--crew-source /nonexistent --vendor-dir /nonexistent`.
- M3: `bubblewrap` in Dockerfile (+ `bwrap --version` in verify step); workflow syntax/dup-key fix + `bubblewrap` install in verify-fleet job.

## Acceptance

1. M0 evidence log exists with verbatim exploit/filter probe outputs on the current tree.
2. Relay denies (secret-store / out-of-scope body-file, forged source, non-allowlisted subcommand, unsafe note) and allows (in-scope file + matching source + valid note); new test class green without `bwrap`.
3. Regen hermetic: idempotence passes with nonexistent crew/vendor dirs; filter guard verified (code-path proof on this host's Python + the guarded branch present).
4. Dockerfile + workflow validate (UniqueKey YAML parse, bubblewrap present).
5. `make verify` green (35/0 + V22/V23/V24, SUMMARY frozen), `audit_loop --self-test` PASSED.
6. Drift-guard `VERDICT: PASS` → PR (Refs only).
