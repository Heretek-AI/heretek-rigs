# Implementation report — overhaul-a M1→M3 (agency-programmer)

Stage: overhaul-a M1–M3 (M0 spike done, winner recorded, no deviations).
Worktree: `.lane/trees/overhaul-a` (branch `feat/overhaul-a`, base `07114e3`).
Status: code complete, `make verify` green, tree left DIRTY for coordinator
commit (per stage instructions — NOT committed).

## M1 — hardened `rig` relay (REQ-A1)

Files:

- `scripts/seat-sandbox.sh` — relay block re-derived from the CURRENT bounds
  (`if` was `:38`, `os.execvp` was `:47`; now `:52` and `:149`). Enforcement
  before exec, deny fail-closed with exit 126 + reason on stderr:
  `argv[1]` in `{whoami, ps, queue, send, capture, transcript}`;
  `--source`/`-s` (space and `=` forms, incl. attached `-sV`) equal to
  non-empty `$OPENRIG_SESSION_NAME`; `--note` (both forms) matching
  `^[A-Za-z0-9][A-Za-z0-9 _.,:/@+-]{0,200}$` with explicit newline/CR reject;
  `--body-file` (both forms): not a symlink, existing regular file
  ≤ 256 KiB, never inside `$HERETEK_SECRET_STORE`, no credential
  suffix/name (`*.key`, `*.pem`, `*.env`, `id_rsa`, …; `credential`/`secret`
  substrings), inside the seat workspace or the configured scratch dirs
  (`$TMPDIR`, `$HERETEK_JAIL_SCRATCH`) and clear of protected segments
  (`.git`, `.pi`, `.agents`, `AGENTS.md`). Scope note (in-code): write-roots
  always resolve under the workspace and the whole in-jail workspace is
  readable, so workspace containment plus the store/credential/protected
  denials is the laundering boundary; bare `/tmp` and `/var/tmp` are
  deliberately NOT in scope because the jail masks host `/tmp` (relaying a
  host-`/tmp` file would launder bytes the seat could not read).
  EXIT-trap cleanup untouched (relay still `exec`s python pre-scratch; the
  background-`bwrap` + `wait` shape is unchanged — never exec-replaced).
- `tests/test_seat_sandbox.py` — new `TestRigRelayEnforcement` (7 tests:
  6 deny incl. symlink body-file + 1 allow covering `--source`/`-s` space
  and `=` forms), no bwrap gate; updated `test_rig_route_does_not_interpret_shell`
  (`rig whoami;…` is now denied at the allowlist instead of relayed — the
  behavior change this milestone exists to make).

Commands (exit codes verbatim):

- `python3 -m unittest tests.test_seat_sandbox.TestRigRelayEnforcement`
  → RED pre-fix: `Ran 7 tests … FAILED (failures=20)` (relay allowed all).
- Same → GREEN post-fix: `Ran 7 tests … OK`.
- Bwrap-independence proof (fake `bwrap` tripwire first on PATH + `env -i`
  relay runs): allow path `FAKE-RIG-RAN`, `rc=0`, `BWRAP-NEVER-CALLED`
  (deny path likewise never touched the tripwire). Scratch dirs removed after.
- `python3 -m unittest tests.test_seat_sandbox -v` → `Ran 33 tests … OK`
  (26 existing + 7 new).
- `bash -n scripts/seat-sandbox.sh` → `bash-syntax-ok`.

## M2 — hermetic regen (REQ-A2)

Files:

- `scripts/generate-rigs.py`
  - Filter guard at the old `:390` call (now `_safe_tar_extract` def `:323`,
    call `:484`): `_tar_supports_filter()` feature-detects
    `TarFile.extract(filter=)`; modern Pythons take `filter="data"`, older
    ones take a verified-safe plain extract (callers pre-validate member
    names: no absolute paths, no `..`).
  - Charter fallback: `build_charter(rid, r, crew_dir, root, fallback_text)`
    chain crew checkout → `fleet/charters/<rid>/AGENTS.md` (operator
    overlay; absent in-tree, so skipped) → snapshot `guidance/role.md`
    returned byte-verbatim → `die()` fail-closed.
  - Snapshot-and-restore vendor guard: when `--crew-source` or `--vendor-dir`
    is absent, `_snapshot_for_hermetic` copies committed `specs/agents` +
    `skills-lock.json` to a process-scoped temp dir (atexit-cleaned) BEFORE
    the clean step; shared skills restore from the snapshot with
    `tree_hash == lock entry` verification (lock entry reused verbatim);
    role-local skills restore byte-identical (patch ids counted applied,
    never re-edited); missing pins skip live-clone checks fail-closed per
    skill/entry.
  - `.scratch/vendor` symlink → main-repo `.scratch/vendor` created via
    `python3 -c os.symlink` (gitignored scratch only; `git status` clean of it).
- `tests/test_generate_supplychain.py` — `TestTarFilterGuard` (3: guarded
  no-filter branch via stubbed tf + forced-negative detect, filter branch
  forced-positive, live-interpreter code-path proof on Python 3.15.1),
  `TestHermeticCharterFallback` (3: overlay composes, snapshot verbatim,
  no-source dies), `TestHermeticVendorRestore` (1: restore matches lock,
  tampered snapshot dies). All initially red (`AttributeError`, pre-existing
  `find_skill` death on the first hermetic run), now green.

Commands (exit codes verbatim):

- `HERETEK_RIGS_ALLOW_DIRTY=1 python3 ./scripts/generate-rigs.py
  --check-idempotent --crew-source /nonexistent/crew --vendor-dir /nonexistent/vendor`
  → `rc=0`, `idempotence check passed (two consecutive runs byte-identical)`
  (ALLOW_DIRTY needed: my own edits dirty the tree; first attempt died in
  `find_skill`, fixed by hermetic shared-pool construction).
  Post-run diff vs committed: ONLY `DIRTY-` provenance stamps + the two
  openrig-core env-drift skills (`queue-handoff`, `messaging-the-human` —
  live npm install newer than the committed tree; a normal regen drifts the
  same way, pre-existing and unrelated). Restored via
  `git checkout -- specs rigs registry rosters fleet/skills-lock.json schemas`.
- Normal-path no-drift proof: `HERETEK_RIGS_ALLOW_DIRTY=1 python3
  ./scripts/generate-rigs.py --check-idempotent` → `rc=0`, idempotent;
  changed-file pattern identical to the hermetic run (provenance + the same
  2 env-drift skills) → M2 edits alter zero normal-path output bytes.
  Leaves restored the same way.
- `python3 -m unittest tests.test_generate_supplychain` → `Ran 16 … OK`.

## M3 — Docker pipeline (REQ-A3)

Files:

- `docker/Dockerfile` — `bubblewrap` added to the SLIM apt list (`:93`;
  builder `:24` checked and deliberately untouched: the compiler stage never
  runs the sandbox) + `bwrap --version` in the slim verify RUN step.
- `.github/workflows/docker-release.yml` — duplicate `container:` key removed
  (empty `defaults:` + second block deleted; exactly one remains), broken
  unclosed-`if` guard-profiles block (first `- run: |`, missing `fi`)
  removed in favor of the complete block below it, `bubblewrap` install +
  `bwrap --version` step appended to `verify-fleet`.
- `scripts/verify-rigs.sh` — appended V25 (M1), V26 (M2), V27 (M3) FAIL-ONLY
  gates (no `ok()`, no renumber/reword; V19 count frozen). V25 runs the
  7-test enforcement corpus (exact-count floor); V26 checks the 7 guard/
  fallback markers and runs the 7-test filter/hermetic corpus; V27
  UniqueKey-parses the workflow (duplicate keys die), asserts one smoke
  `container:` block + verify-fleet bubblewrap + Dockerfile markers.
  `TERMINAL_BASH_DENIES` mirror untouched; Makefile test target untouched;
  V19 (`:2502`) untouched (Wave-B M5 scope).

Commands (exit codes verbatim):

- `rg -n bubblewrap docker/Dockerfile .github/workflows/docker-release.yml`
  → Dockerfile `:94`, workflow `:60` (install step).
- UniqueKey proof script → `rc=0`: `UniqueKey YAML parse: OK (no duplicate
  keys)`, `smoke container blocks: 1`, Dockerfile markers present.
- Full `docker build` NOT run — build-skipped-with-reason: multi-arch push
  needs registry credentials + network, and the daemon here has neither
  configured for `ghcr.io`; the spec proof is the static validation above
  (recorded here, reproducible via the V27 gate).

## Acceptance

- `make verify` → `rc=0`: `SUMMARY: 35 checks passed, 0 failed`,
  V25/V26/V27 all print green (FAIL-ONLY, count frozen at 35),
  `audit_loop --self-test` → `SELF-TEST PASSED`.
- `make test` → `Ran 373 tests`, 372 pass, 1 failure:
  `test_build_canary.CanaryCatalogPins.test_canary_scope_only` — PRE-EXISTING,
  proven by running it on a pristine worktree of the base commit `07114e3`
  (same failure, `fleet/fleet.yaml` untouched by this stage; stale
  expected-role list vs the #102 fleet-wide `bash_deny` triple). Left
  untouched as out-of-scope; worktree removed afterwards.
- `git status --porcelain` (final, dirty for coordinator commit):
  `M .github/workflows/docker-release.yml`, `M docker/Dockerfile`,
  `M scripts/generate-rigs.py`, `M scripts/seat-sandbox.sh`,
  `M scripts/verify-rigs.sh`, `M tests/test_generate_supplychain.py`,
  `M tests/test_seat_sandbox.py`. No generated leaves touched; no commit made.

## Self-audit

- Zero stubs/`TODO`/empty-`catch`/skipped tests: the overlay branch
  (`fleet/charters/`) is live code with a composing unit test, not a stub;
  the old-Python extract branch is unreachable here but unit-proved via stub.
- Fail-closed throughout: relay denies (126) on unparseable/unallowlisted/
  unverifiable input; generator dies (2) on missing snapshot entries, lock
  mismatch, or absent sources; hermetic temp dirs cleaned via atexit even on
  `die()`.
- Gotchas honored: no hand-edits to `specs/`/`rigs/`/`rosters/`/`registry/`
  (all regen-proven byte-identical modulo stamps, then restored); no
  `yaml.safe_dump` on `fleet/fleet.yaml` (untouched); no exec-bwrap swap;
  `TERMINAL_BASH_DENIES` mirror byte-identical; no secrets in commands, files,
  or this report (dummy canary content only in `/tmp`, since removed).
- Unfinished / disclosed: (1) the 1 pre-existing canary test failure above
  (out of scope, evidence kept); (2) no full `docker build` (reason recorded
  above); (3) `fleet/charters/` overlay directory does not exist in-tree, so
  the hermetic proof exercised the in-tree snapshot branch — the overlay
  branch is implemented + unit-tested for a future operator-provided overlay.
