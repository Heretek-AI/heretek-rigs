# Wave B1 seatjail sweep evidence (#111)

Date: 2026-10-24. Host: /var/tmp. Operator: coordinator-guarded sweep per `openspec/changes/ops-sweep-111/specs/sweep/spec.md` (REQ-B1, fail-closed guards).

## Before
- `ls -1d /var/tmp/seatjail.* | wc -l` = 21 (HANDOFF/#110 claimed 408 — delta unexplained in-tree; sweep bounds to today's 21).
- All 21 legacy `seatjail.XXXXXX`, zero pid-namespaced. All `john:john` (1000:1000); invoking UID `id -u` = 1000 (`john`), matching the `-O` guard used for all 21 deletes.
- Classes: 14 node-compile-cache at 126,936 B + 3 other-sized cache dirs (146,612 / 148,464 / 168,140 B) + 4 tiny 2-byte `x`-only. Total 560 files / 2,240,328 B.
- Age (mtime span from recon): oldest `YySA6M` 00:31 through `1Ptr7M` 13:18 (~13 h span, all 2026-10-24 -0400).
- Secrets scan (names + `sk-/ghp_/AKIA/PRIVATE KEY/api[_-]?key` content patterns): 0 hits. `lsof +D /var/tmp | grep seatjail`: no holders. `fuser`: no output.

## Sweep (guards: legacy-glob `seatjail.[A-Za-z0-9]{6}` + `-d` + `! -L` + `-O`, liveness re-verified)
- SWEPT /var/tmp/seatjail.1Ptr7M bytes=2
- SWEPT /var/tmp/seatjail.4n7iw5 bytes=146612
- SWEPT /var/tmp/seatjail.7gBcuA bytes=126936
- SWEPT /var/tmp/seatjail.7UpFGd bytes=126936
- SWEPT /var/tmp/seatjail.9uKbTQ bytes=2
- SWEPT /var/tmp/seatjail.bIWrvE bytes=2
- SWEPT /var/tmp/seatjail.CzgqtL bytes=126936
- SWEPT /var/tmp/seatjail.d8HXdt bytes=126936
- SWEPT /var/tmp/seatjail.dRSYQn bytes=126936
- SWEPT /var/tmp/seatjail.EuqRvx bytes=126936
- SWEPT /var/tmp/seatjail.hgn6cu bytes=126936
- SWEPT /var/tmp/seatjail.Kh4upZ bytes=148464
- SWEPT /var/tmp/seatjail.NhReLV bytes=168140
- SWEPT /var/tmp/seatjail.nXKtMB bytes=126936
- SWEPT /var/tmp/seatjail.Qvqaxg bytes=126936
- SWEPT /var/tmp/seatjail.tDZtuy bytes=126936
- SWEPT /var/tmp/seatjail.uH8Kq1 bytes=126936
- SWEPT /var/tmp/seatjail.Vftmby bytes=126936
- SWEPT /var/tmp/seatjail.WZXoya bytes=126936
- SWEPT /var/tmp/seatjail.yxhXkk bytes=2
- SWEPT /var/tmp/seatjail.YySA6M bytes=126936
- swept=21 skipped=0 freed_bytes=2240328

## After
- `ls -1d /var/tmp/seatjail.*` → `No such file or directory`, count 0.
- `scripts/seat-sandbox.sh:54` leave-alone untouched (no code change). UNVERIFIED: no fresh-run before/run/after trace was collected proving exactly one pid-namespaced `seatjail.<pid>.XXXXXX` is created and removed per run — future runs cycling only pid-namespaced dirs is expected from `:58-66` by code reading, not demonstrated here.

## Red-proof (both directions)
- Allow-direction: all 21 legacy orphans deletable under guards (swept, exit 0 each).
- Deny-direction: sentinel dry-run in scratch (same predicate, no deletes, 2026-10-24): `seatjail.ABC123` → WOULD-SWEEP; `seatjail.12345.SENTINEL` (pid-namespaced shape) → SKIP unchanged; `unrelated-dir` (non-seatjail `/var/tmp`-style path) → SKIP unchanged; all sentinels remained afterwards, scratch cleaned. Real sweep: `-O`/`!-L`/liveness guards triggered 0 skips (no live sentinels existed); no non-legacy `/var/tmp` entries touched.
