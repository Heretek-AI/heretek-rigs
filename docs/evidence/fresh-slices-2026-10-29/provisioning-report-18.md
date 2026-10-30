# #18 provisioning report — fresh-slices Wave 3 (FINAL)

Source: deep-researcher dossier 2026-10-30 (fetches dated 2026-10-30; LAN
chain unreachable, Tavily+jina fallback; dossier states nothing invented).
Every UNVERIFIED mark from dossier §4 is preserved verbatim below — gaps
are never upgraded to facts; no price, pin, or flag is invented here.

Refs #18 (never Closes — closes only on triad `VERDICT: PASS`).

## SDK pin (all options)

- Pinned: Vulkan SDK **1.3.296.0**, released 08-Oct-2024, still
  downloadable from the LunarG archive page (SHAs listed on the archive
  page itself — not reproduced here, take from the version row; do not
  hard-code a mirror).
- Drift warning (dossier-sourced): latest SDK is **1.4.363.0**
  (29-Sep-2026); host loader 1.4.357 vs pinned 1.3.296 drift is real and
  growing. Pin 1.3.296 deliberately for the frame proof.
- (c)-first headless available immediately: pin SDK 1.3.296
  (headers/loader/validation layers), unit-test swapchain selection,
  `vulkaninfo` documents the zero-device baseline.

## Option (a)-virtual: display path on existing host — COSTED

| Item | Pin / source | Spend |
|---|---|---|
| Runner | Existing Debian-class (trixie) host, no new hardware | ~$0 hardware spend (dossier) |
| Driver | `mesa-vulkan-drivers` 25.0.7-2+deb13u1 (lavapipe CPU software renderer) | $0 |
| Packages | `apt-get install mesa-vulkan-drivers vulkan-tools xvfb` | $0 |
| SDK | 1.3.296.0 Linux tarball from LunarG archive page (link from version row); extract, `source setup-env.sh` | $0 |
| Display | `Xvfb :99 &; DISPLAY=:99 vkcube` capture | $0 |
| Pin check | `vulkaninfo --summary` must show loader 1.3.296 + lavapipe (lvp) device | — |

Exact steps: install the three packages; download the 1.3.296.0 tarball
from the archive page; extract; `source setup-env.sh`; start Xvfb;
run `vkcube` under `DISPLAY=:99`; capture the frame; run
`vulkaninfo --summary` for the loader/device pin check.

- CONFIRMED caveat (dossier): lavapipe is a Mesa CPU software renderer,
  conformant Vulkan 1.3 only (1.4 extensions exposed, conformance not
  submitted) — a lavapipe frame proves harness/loader/WSI/app correctness,
  NEVER driver behavior/timing/vendor quirks.
- UNVERIFIED (doc-page level, confirm on the runner): setup-env.sh/glslc
  layout (confirm `ls $VULKAN_SDK/x86_64/bin/glslc`); vkcube/Xvfb flag
  spellings (confirm via local `--help`); Debian glslc/shaderc
  system-package alternative (`apt-cache` on the runner decides);
  lavapipe exact version string in Mesa 25.0.7 (runner must report).

## Option (a)-physical: real-GPU runner — COSTED (gap disclosed)

| Item | Pin / source | Spend |
|---|---|---|
| Physical SKU + price | **UNVERIFIED — none found.** No physical-runner SKU or price was located by the dossier | Unknown (not quoted) |
| Closest rentable real-GPU equivalent | Cloud GPU pass-through, e.g. AWS G5 Nitro (≈ bare metal) — see option (b) | See (b); re-verify at spend time |

No physical-runner price is stated because none was found; stating one
would be invention. Driver-faithful frame proof waits on either a
located physical SKU (future wave) or option (b).

## Option (b): cloud GPU reference machine — COSTED (secondary-source)

All prices secondary-source — re-verify at spend time (dossier).

| Item | Pin / source | Spend (secondary-source, re-verify at spend time) |
|---|---|---|
| AWS G6 (L4) | Dossier, secondary-source | from $0.80/hr |
| AWS G5 (A10G) | Dossier, secondary-source | from $1.00/hr |
| GCP G2 (L4) | Dossier, secondary-source | ~$0.70–0.71/hr |
| Azure NVadsA10 v5 (A10, 1/6 slices) | Price **UNVERIFIED** | Unknown (not quoted) |
| Region availability / quota | **UNVERIFIED** (all clouds) | — |
| SDK on image | 1.3.296.0 (same archive pin as (a)) | $0 above instance cost |

`rig host` registration (VERIFIED from upstream v0.7.5 docs):
`rig host add --id <id> --transport <transport>
[--target/--user/--url/--bearer-env/--bearer-file/--notes]`;
`select`/`rename`/`pair`/`list`/`doctor`; `up`/`ps`/`down`/`send`/`queue`/
`transcript`/`capture`/`broadcast` accept `--host`; remote FEED opt-in;
SSH entries need an HTTP entry for FEED.
- UNVERIFIED: `rig host` transport kinds / auth semantics beyond the
  registration flags (use `rig host --help` on installed 0.7.5).
- Pairing tests simulated — run pilot `host doctor` before relying.

## Acceptance mapping (dossier)

- Headers/loader version → (c).
- Device listing → (a)-virtual minimum.
- `vkcube` frame + `s02-window.png` → (a)-virtual minimum;
  physical/(b) for driver-faithful.
- Driver-behavior assertions → physical/(b) only; lavapipe passes labeled
  as such.

## Option (c): DECISION — sequence non-visual slices first (RECORDED)

Decision: proceed with non-visual slices first on the existing fleet;
defer any GPU/display-dependent work until (a)/(b) is costed AND approved
in a later wave. Rationale: the #16 parallel-slice execution model and
#17 telemetry need no GPU — Stage B proves them with zero spend; spending
before the model is proven would put cost ahead of evidence. This decision
needs no external facts and stands regardless of the (a)/(b) numbers.

## Frame proof — tracked as Sprint-blocking (RECORDED)

- `vulkaninfo` against SDK 1.3.296 + headers — TBD (blocked on runner)
- `vkcube` frame capture — TBD (blocked on runner)
- `s02-window.png` artifact — TBD (blocked on runner)

These stay Sprint-blocking until a provisioned runner (via a future
approved wave, never this one) produces them.

## Zero side effects — VERIFIED

- `rig host ls` → "No hosts registered" (rc=0); `~/.openrig/hosts.yaml`
  does not exist. No host added, paired, or selected.
- No installs: the exercise's complete command set is recorded in
  `runbook.md` §§1–6 — every command was read-only (`rig ps`,
  `queue list/show/transitions/overdue`, `audit_loop --self-test`, file
  writes under `docs/evidence/` + `/tmp`) except 6 queue writes on
  synthetic rows (3 creates + 3 `done`/`no-follow-on` closes, zero open
  residue). No `apt-get`/`dnf install`, no package operations, no cloud
  console actions appear anywhere in the recorded set; no apt/dpkg logs
  exist on this host to contradict it.
- No spend: $0 incurred. The lavapipe path, if ever executed, is also $0
  hardware spend — but it was NOT executed in this wave (report only).
