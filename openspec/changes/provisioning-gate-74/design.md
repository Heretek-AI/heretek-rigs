# Design: gate-only, matrix-wide

## Why gate before provisioning
Provisioning 7 npm servers + r2/rabin2/tshark on every host (bare-metal + images + `$TOOLS` builder parity) is host-mutating, credential-touching work that needs its own rollout. The gate is host-safe (read-only resolution: `shutil.which` + path-exists, no installs, no pulls) and immediately converts silent incapability (mission C2's exit-127 surprise) into loud degradation. Gate-first also matches #89's own ask order.

## Why render + seed + verify + live-health (four layers, not one)
Each layer sees a different blind spot: render sees catalog bindings, seed sees staged per-seat files, verify sees committed strings (CI), live-health sees the running host. V12's `[NOTE]`-only precedent shows single-layer checks decay into advisories nobody reads; the four layers make missing tools fail loudly at build time and warn loudly at runtime.

## Why `enabled:false` + stderr (not hard fail at render)
Hard-failing render would brick `generate-rigs.py` on tool-poor hosts (docs laptops, CI without docker). Degraded `enabled:false` preserves the secrets precedent: fleet renders everywhere, seats start with honest reduced capability, and the warn line tells the operator exactly which row to provision. The verify block (not the renderer) is the hard gate.

## Failure modes
- PATH-dependent resolution differs per host → gate resolves with the same `$TOOLS`/PATH the seat will see (no bare `which` without env); matrix records host variance.
- `uvx`/`docker` shallow presence (binary ok, package/image missing) → recorded as follow-up deep probes, not this change (avoids network pulls in verify).
- Browser-backed servers (playwright/chrome-devtools need Chromium) → binary presence is necessary, not sufficient; sufficiency probes belong to mission-time checks.
