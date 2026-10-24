# Delta spec: legacy seatjail sweep

## ADDED Requirements

### REQ-B1: guarded one-time sweep
Operator (or ops agent) MUST delete only paths matching `/var/tmp/seatjail.XXXXXX` (legacy, no pid segment) that satisfy ALL: directory, not symlink, owned by invoking uid (`-O`), unheld (`lsof`/`fuser` negative at sweep instant). Each delete MUST be logged (path + bytes). Rationale: #111 explicitly unswept legacy from #110; pid-namespaced cycling is separate.

### REQ-B1-NEG: never touch
The sweep MUST NOT delete pid-namespaced `/var/tmp/seatjail.<pid>.*`, MUST NOT touch any other `/var/tmp` entry, MUST NOT modify `scripts/seat-sandbox.sh` (leave-alone at `:54` stays deliberate until a #111 decision says otherwise).

## MODIFIED Requirements

None. No code, no regen, no deny/policy/doc-count edits in this change (B2 covers docs).
