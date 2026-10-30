# Tasks: 2026-10-30-seat-hygiene

## Authoring (this landing — read-only throughout)

- [x] Author change package (proposal/spec/design/tasks per approved design)
- [x] Pre-audit snapshot `rig ps --nodes -A` → `ps-pre.txt` (111 lines,
  51 fleet `run` + kernel rows, baseline shape) rc=0
- [x] Full scan: 70 seat dirs enumerated; 54 with agent state fully
  field-checked; 16 sessions-only dirs listed unscannable-with-reason;
  every referenced absolute path existence-checked rc=0
- [x] `launch_cwd` sweep: `rig seat status --json` × 51 live seats rc=0
  (all `../../heretek-asset-manager`, exists)
- [x] Post-audit snapshot → `ps-post.txt`; `cmp` byte-identical rc=0
  (REQ-H3 zero-mutation proof)
- [x] Evidence: `audit.md` (per-seat table, counts, impact) +
  `dangling-seats.json` (24 entries, 2 lobotomized / 22 stale) filed
- [x] Bearer-shaped grep: none (prose "Bearer-shaped strings: none" only)
- [ ] Triad (agency-qa red-proof + agency-drift-guard audit) → VERDICT
  before any PR (Refs #147 — never Closes)
