# M1 red-proofs: HR-F18 bare queue/send deny (REQ-C18)

Branch: `feat/102-closeout`. Worktree: `.lane/trees/102-closeout`.
Spec: `openspec/changes/102-closeout/{proposal,design,tasks,specs/closeout/spec}.md` (REQ-C18, REQ-G1).

## 1. Mechanism

- `fleet/fleet.yaml`: every seat (`51/51`) gains a `permissions.bash_deny`
  triple (`rig queue list`, `rig queue create`, `rig send`) — surgical
  line-anchored insert, `yaml.safe_load`-verified, never `yaml.safe_dump`.
- `scripts/render-seat.py`: emits `bash_deny` as `deny` entries AFTER role
  allows, BEFORE `TERMINAL_BASH_DENIES` (tuple frozen per REQ-G1), with the
  same metachar/`--output` fail-closed bans as allows.
- `scripts/generate-rigs.py`: matching gen-time guard (dies on
  non-string/metachar/`--output` deny entries).
- `scripts/verify-rigs.sh`: appended FAIL-ONLY V22 (no renumber, SUMMARY
  frozen at 35) asserting fleet parity + rendered order + both-directions
  evaluation under pps wildcard semantics for all 51 seats.
- `AGENTS.md`: Queue-work row extended with the bare-deny operator gate.
- Test: `tests/test_bare_queue_send_deny.py` (standalone, 4 tests).

## 2. RED (pre-fix base `2590a87`, pristine main checkout)

```
HERETEK_TEST_ROOT=/home/john/Projects/heretek-rig-workspace/heretek-rigs \
  python3 tests/test_bare_queue_send_deny.py
# exit 1 — FAILED (failures=2):
#   test_fleet_declares_bare_denies: 51 roles carry no bash_deny
#   test_rendered_maps_deny_bare_forms: 153 offenders (51 seats x 3 bare
#     forms all ALLOW, e.g. "cache-streaming-eng: allows 'rig queue list'")
```

Full log: `/tmp/opencode/102-m1-red.log` (scratch; method re-runnable).

## 3. GREEN (post-fix + dev regen)

```
python3 tests/test_bare_queue_send_deny.py
# Ran 4 tests — OK (exit 0)
```

`./scripts/verify-rigs.sh --check-only`:

```
== V22. Bare Queue/Send Deny in Seat Maps (#102/HR-F18) ==
V22/#102 bare queue/send deny green: 51 seats deny the bare triple and allow the disciplined forms (FAIL-ONLY, SUMMARY frozen)
```

## 4. Live in-seat probes (pi 1.4.0 + installed pps 41.0.0, mock model)

Scratch seat `delivery-tpm-scrum-lead@executive-and-architecture` rendered
with dummy secrets to `/tmp/opencode/seat-m1` (0600), probed via
`scripts/gate-run.sh`:

| command | outcome |
|---|---|
| `rig queue list` | DENY — `[pi-permission-system] Denied by policy: 'bash' (rule 'rig queue list')`, `isError:true` |
| `rig queue list --json` | ALLOW — tool executed (`rig` ran; failed only on absent daemon, not policy) |
| `rig queue create` | DENY — `isError:true` |
| `rig queue create --json --verify --source x --destination y --summary s --body-file f` | ALLOW — tool executed |
| `rig send` | DENY — `isError:true` |
| `rig send delivery-tpm-scrum-lead@executive-and-architecture hello` | ALLOW — tool executed |

Raw: `/tmp/opencode/102-probe-deny.log` (deny names the rendered rule),
`/tmp/opencode/102-probe-allow.log` (allow executes).

## 5. Provenance note (coordinator recovery)

This stage's regen ran under the sanctioned dev hatch
(`HERETEK_RIGS_ALLOW_DIRTY=1`, AGENTS.md) because generator-input edits are
the change itself; leaves therefore carry `DIRTY-2590a87...` stamps and
V4/V5/V13/V19 fail ONLY on that stamp (log `/tmp/opencode/102-verify-m1.log`,
SUMMARY 32/51 — the 51 failures are all `DIRTY-` cascade, zero content
failures, V22 green). Recovery (mechanical, determinism proven by the
`--check-idempotent` shape of the generator): commit source
(`fleet/`, `scripts/`, `tests/`, `AGENTS.md`, `docs/`), re-run
`python3 scripts/generate-rigs.py --vendor-dir
/home/john/Projects/heretek-rig-workspace/heretek-rigs/.scratch/vendor` on
the clean tree (bakes the bare SHA), then `make verify` (expect 35/35 +
V22 green, SUMMARY frozen) and commit leaves.
