# Delta spec: overhaul-a

## ADDED Requirements

### Requirement: REQ-A0 — M0 spike gates M1/M2
M1/M2 MUST follow a live M0 spike re-run against the current tree (`seat-sandbox.sh` rig block at `:38`, `os.execvp` at `:47`; `generate-rigs.py:390` filter call). The evidence log MUST record verbatim probe outputs before M1 is designed.

#### Scenario: spike log gates implementation
- When M1 begins, `docs/evidence/overhaul-a-m0.md` exists with the sandbox-exploit and filter-probe outputs on the unmodified tree, and M1 cites which winner it follows.

### Requirement: REQ-A1 — hardened rig relay
The `rig` relay in `scripts/seat-sandbox.sh` MUST validate before exec: `argv[1]` in `{whoami, ps, queue, send, capture, transcript}`; `--source`/`-s` (both forms) equal to non-empty `$OPENRIG_SESSION_NAME`; `--note` (both forms) matching a restrictive pattern with no newlines/shell tokens; `--body-file` (both forms) realpath-contained (regular file ≤ 256KiB, never inside the secret store, no credential suffix, inside scratch or seat write-roots, clear of protected segments). `TestRigRelayEnforcement` in `tests/test_seat_sandbox.py` MUST cover deny-secret-store, deny-out-of-scope, deny-forged-source, deny-subcommand, deny-note, and allow-valid — all without requiring `bwrap`.

#### Scenario: exploit denied, valid allowed
- When the relay receives `--body-file <secret-store-file>` it exits non-zero naming the refusal; when it receives an in-scope file with matching `--source` and valid `--note` it execs `rig`.

### Requirement: REQ-A2 — hermetic regen
`generate-rigs.py` MUST NOT crash on Python without `TarFile.extract(filter=)` (feature-detect and degrade to a verified-safe path) and MUST regenerate without `/home/john/Projects/Heretek-Crew` or `.scratch/vendor` (hermetic charter fallback + snapshot/restore with `skills-lock.json` tree-hash verification). `--check-idempotent` MUST pass with `--crew-source /nonexistent/crew --vendor-dir /nonexistent/vendor`.

#### Scenario: hermetic idempotence
- When idempotence runs with nonexistent crew/vendor dirs it prints the byte-identical pass line with exit 0.

### Requirement: REQ-A3 — Docker pipeline fixed
`docker/Dockerfile` MUST install `bubblewrap` in the build image and assert `bwrap --version` in its verify step; `.github/workflows/docker-release.yml` MUST parse under a duplicate-key-rejecting YAML loader with exactly one `container:` block per job, and its verify-fleet job MUST install `bubblewrap`.

#### Scenario: pipeline validates
- When the workflow file is parsed with duplicate-key rejection it loads with no error, and `bubblewrap` is greppable in both the Dockerfile and the verify-fleet job.

## MODIFIED Requirements

### Requirement: REQ-G1 — append-only, generator rule
New coverage MUST be new appended blocks (or new scripts), never renumber/reword of V1–V24. `specs/` `rigs/` `rosters/` `registry/` MUST change only via `generate-rigs.py`; `yaml.safe_load` MUST be used for YAML parsing; never `yaml.safe_dump` on `fleet/fleet.yaml`.

#### Scenario: gates intact
- When `make verify` runs after this change, V1–V24 pass unrenamed and SUMMARY stays frozen.
