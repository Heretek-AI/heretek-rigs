# Design: overhaul-a

## Architecture

Single worktree `.lane/trees/overhaul-a`, branch `feat/overhaul-a` from clean `main` (`66ba80c`). M0 spike first (programmer, scratch-only probes), then M1→M3 in order on the spike winner. Single triad, one PR.

## Verified findings (live, main `66ba80c`, 2026-10-28 — brief deltas corrected)

- Sandbox relay: `if` at `:38`, `os.execvp("rig", argv)` at `:47`. Brief's "lines 30–42" are VOID — re-derive bounds from the current `#105 review` shlex block. `bwrap --unshare-net` still isolates host loopback, so the relay-before-jail shape stays.
- Tar filter: `tf.extract(_m, path=tmp, filter="data")` at `generate-rigs.py:390` — live. Host python version decides which branch the guard takes (record it in M0).
- Crew default: `Path("/home/john/Projects/Heretek-Crew")` at `:1997`; `--crew-source` flag at `:2006`; `build_charter` reads `crew_dir / roles / rid / AGENTS.md` at `:656` with `die()` at `:658`.
- Docker: apt-install lines at `docker/Dockerfile:24` (base) and `:93`; `bubblewrap` absent from both — confirmed by grep.
- Workflow: `container:` twice (`:118`, `:125`); guard-profiles block `:57–65` (brief's `:56–61` unclosed-`if` description is stale — re-derive).
- Suites: 21 `tests/test_*.py`; `Makefile:38` still hardcodes 15 files (6 unwired — M5/Wave-B scope, not here; do not touch the Makefile test target in this wave).
- V19 cascade (`passes + 1` at `:2502`) is Wave-B M5 scope — do not touch V19 here.

## Milestone order

1. **M0 spike (scratch only):** fake-`rig` exfiltration probe (fake binary printing the `--body-file` target, like the brief's M0 script, adapted to the current relay bounds) + `filter=` capability probe (`"filter" in TarFile.extract.__code__.co_varnames` on this host). No repo edits except the evidence log.
2. **M1 relay:** re-derived hardened relay + `TestRigRelayEnforcement` (must pass with `bwrap` absent — relay runs pre-jail).
3. **M2 hermetic:** filter guard + charter fallback + snapshot/restore guard; hermetic idempotence proof.
4. **M3 docker:** Dockerfile + workflow fixes; YAML validation proof (no full image build required — record if `docker build` was attempted or skipped and why).

## Fail-closed modes

- M0 probes use a FAKE `rig` on PATH in /tmp (never the real binary for the exfiltration probe); secret canaries are dummy strings.
- If M0 contradicts this design (relay shape differs, filter supported everywhere), fix this design file first.
- Regen only on clean tree; `.scratch/vendor` symlink trick applies if the generator needs vendor dirs (python `os.symlink`, gitignored scratch only).
- Gotcha #1 from the brief applies: never replace background+`wait` with `exec bwrap` (EXIT-trap cleanup).
