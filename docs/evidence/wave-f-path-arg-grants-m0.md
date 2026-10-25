# Evidence: path-arg-grants-91 M0 live probe (REQ-A0) + mechanism probes

Date: 2026-10-25. Enforcer: INSTALLED `@gotgenes/pi-permission-system@41.0.0`
(`~/.local/share/heretek-rigs/tools/pi-packages/node_modules/@gotgenes/pi-permission-system`).
Harness: gate-role.sh-style mock-model runs (`scripts/gate-run.sh`) against
freshly rendered seats; ground truth = `permission_request.blocked` review-log
events + tool execution. pps sources read, never from memory:
`src/config/config-schema.ts:399-401` (`commandEffects` is a zod record keyed
by bare basename), `src/config/command-effects-config.ts:45-60`
(`foldDeclaredCommandEffects`, shallow by command),
`src/access-intent/bash/declared-command-effects.ts:49-62` (exact-word
descent, `unlessOption` withdrawal, undeclared = unproven).

## M0 verdict (pytest `tests/rag` on vector-rag-spec): NATIVE MAP wins

| variant | `pytest tests/rag` | control `git status --short` | `pytest ../../etc/passwd` |
|---|---|---|---|
| (0) no `commandEffects` | DENY (`blocked`, surface=`path`, pattern=`*`, effect=`unproven`) | ALLOW | DENY |
| (a) LIST form (as-rendered overlay) | ASK (`waiting` on `bash` → `denied`, `confirmation_unavailable`, "No live authority was reachable") | ASK (same) | ASK |
| (b) NATIVE MAP `{"pytest":{"effects":"read"}}` | ALLOW (pytest executed, exit 0) | ALLOW | DENY (`external_directory_read`, pattern=`*`, effect=`read`, source=`declared-global`) |
| (c) BOTH (map + descriptor sidecar) | ALLOW (identical to b) | ALLOW | DENY |

Baseline deny (variant 0) review record (verbatim):
`permission_request.blocked ... "command":"pytest tests/rag", "path":"tests/rag",
"surface":"path", "matchedPattern":"*", "decidingPath":"tests/rag",
"effect":"unproven", "effectSource":"unproven", ... "resolution":"policy_denied",
"decidedBy":{"kind":"rule","surface":"path","pattern":"*","origin":"global"}`
(origin=global because the seat config loads as the global layer in
`PI_CODING_AGENT_DIR` mode — no machine-global interference.)

Traversal-deny with declaration active (variant b/c):
`permission_request.blocked ... "command":"pytest ../../etc/passwd",
"surface":"external_directory_read", "matchedPattern":"*",
"effect":"read", "effectSource":"declared-global", "resolution":"policy_denied"`.

M0 outcome: NEITHER-vs-either is decided — the map enforces, the list does
not. Stronger: the list form is not merely dead but POISONOUS — with it
present, even explicit bash allows (`git status --short`) degrade to ask,
i.e. the whole permission layer fails closed. Wave proceeds (no HALT);
implementation emits the native map in `commandEffects` and keeps the
descriptor list as the audit sidecar (`command-effects.descriptors.json`,
proven inert: variant (c) allows identically).

## Extended mechanism probes (same harness)

- go (`go-backend-eng`, decl `{go:{unlessOption:[-o],
  subcommands:{build:read,test:read}}}`): `go build ./pkg/foo`, `go test
  ./pkg/foo`, `go build .` ALLOW. `go build ./...` DENIES on
  `path_read` pattern `*..*` (the `...` operand trips the dotdot guard) —
  relieved by explicit `path_read {"*/...":"allow"}` (final say over the
  sugar-expanded deny), after which `./...` and `./pkg/...` ALLOW while
  `go build ../../etc/...` still DENIES (`external_directory_read *`).
  `-o /tmp/evil` withdraws the declaration (`unlessOption`) and DENIES on
  `external_directory *` (effect `unproven`). Traversal without `-o`
  DENIES on `external_directory_read *`.
- cmake (`engine-systems-eng`, bash `cmake -S *` + decl
  `{cmake:{effects:read}}`): `cmake -S . -B build` ALLOWS (cmake executes).
  `cmake -S ../../etc -B /tmp/x`, `cmake -S . -B /tmp/evil`,
  `cmake -P /tmp/evil.cmake` all DENY (`external_directory_read *`).
- gcc (`cpp-lowlevel-eng`, overlay `gcc *`/`g++ *` AFTER the 42 terminal
  denies + decl `{gcc,g++:{effects:read,unlessOption:[-o]}}`):
  `gcc -c src/foo.c` and `gcc -Wall -Wextra -c src/foo.c` ALLOW;
  `gcc -c ../../evil.c` DENIES (`external_directory_read *`);
  `gcc -c src/foo.c -o /tmp/evil.o` DENIES (`external_directory *`,
  unproven via `-o` withdrawal); `gcc -c src/foo.c; evil` DENIES
  (`bash *` via chain decomposition); `sh -c evil` DENIES (`* -c *` —
  the deny still fires outside the slot). Baseline `gcc -c src/foo.c`
  DENIES on `bash` pattern `* -c *` (terminal deny, not path).
- Overlay POSITION is load-bearing (probed both ways): the same `gcc *`
  entry placed BEFORE the terminal denies loses to `* -c *` (DENY);
  placed AFTER, it wins for the gcc slot only (ALLOW). Renderer appends
  catalog-listed overlay patterns at the very end.

## Harness pitfalls found (documented so T2 does not re-trip them)

- `gate-run.sh` truncates `tool_execution_end` to 400 chars: commands with
  long stdout preambles (pytest warnings) lose the `isError` field, so
  `expect allow` (isError-grep) cannot assert them — T1 gate uses
  policy-level `expect_run` (tool RAN ⟺ policy allowed) for the four
  verbatims; exit-0 execution for pytest was measured directly in the
  sandbox (`1 passed`).
- A bash map whose FIRST key is not `*` + a `commandEffects` map makes
  pi 1.3.0 drop the `bash` tool from the execution context ("Tool bash
  not found", no permission events; read/ls unaffected). The renderer
  keeps `*` first always (also asserted by verify V1); probe patches that
  moved `*` produced this artifact — all M0/extension readings above use
  faithful `*`-first maps.
- Sandbox execution limits (policy-allow ≠ exit 0): GOCACHE lives on the
  read-only `/` bind (`go build` exits 1 without an in-tree GOCACHE —
  live prerequisite, operator env concern, out of wave scope);
  `cmake -B build` needs a writable `build/` (added to
  engine-systems-eng `path_write` in this wave); `gcc -c` writes `foo.o`
  to the cwd root (read-only — use `-o` into the tree live).

## Winner to implement (recorded before implementation)

Native-map declarations + descriptor sidecar ("both forms"), per-tool
entries and grants exactly as probed above. No HALT: at least one shape
enforces.
