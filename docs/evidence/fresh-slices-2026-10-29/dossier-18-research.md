# Wave 3 (#18) Dossier — Display/GPU-Capable Runner Options

All fetches dated 2026-10-30. LAN chain (SearXNG, Firecrawl-LAN) was unreachable (connection refused/EHOSTUNREACH on both), so every web fact below comes from metered Tavily fallback or direct/jina fetches of primary pages. Nothing below is invented; unsourced points sit in §4.

## 1. TL;DR

- **SDK 1.3.296.0 is still downloadable today** from the LunarG archive (released 08-Oct-2024; page also lists SHAs). Latest SDK is 1.4.363.0 (29-Sep-2026) — the host's loader 1.4.357 vs pinned 1.3.296 drift is real and growing.
- **Cheapest credible display path is (a)-virtual: Xvfb + lavapipe on the existing Debian-class host — ~$0 one-time hardware spend**, using Debian trixie's `mesa-vulkan-drivers` (Mesa 25.0.7) plus `xvfb` and `vulkan-tools`. It unblocks `vkcube` frames and `s02-window.png`.
- **The issue text's warning is confirmed, not merely plausible:** lavapipe is Mesa's CPU software renderer, conformant only to Vulkan 1.3 (1.4 extensions exposed but *not* conformance-submitted). A lavapipe frame proves harness/loader/WSI/app correctness — never driver behavior, timing, or vendor quirks.
- **Cloud fallback (b): AWS G6 (L4, from $0.80/hr) / G5 (A10G, from $1.00/hr)** and **GCP G2 (L4, ~$0.70–0.71/hr)**; Azure's visualization line is **NVadsA10 v5 (A10, incl. 1/6-GPU slices)**. All prices are secondary-source; none were verified against the vendors' first-party pricing APIs.
- **(c)-first is available immediately on the headless host:** pin SDK 1.3.296 (headers/loader/validation layers), unit-test swapchain-selection logic, run `vulkaninfo` to document the zero-device baseline. Only device-backed proofs need (a)/(b).
- **`rig host` syntax is VERIFIED from upstream v0.7.5 docs**: `rig host add --id <id> --transport <transport> [--target/--user/--url/--bearer-env/--bearer-file/--notes]`; `up/ps/down/send/queue` all accept `--host`.

## 2. Findings

### Option (a)-virtual — Xvfb + lavapipe (recommend as first runner)

- **Components, pinned:** LunarG Vulkan SDK **1.3.296.0** (archive page live, 08-Oct-2024, SHA-256 listed per artifact); Debian trixie `mesa-vulkan-drivers` **25.0.7-2+deb13u1**; `vulkan-tools` package exists on trixie (provides `vulkaninfo`/`vkcube`).
- **Install recipe (Debian-class host):**
  1. `apt-get install mesa-vulkan-drivers vulkan-tools xvfb` — lavapipe ICD registers with the loader; `vulkan-tools` supplies `vulkaninfo`/`vkcube`.
  2. Download the **1.3.296.0 Linux SDK tarball from the archive page** (do not hard-code a mirror URL; take the link from the version row); extract, and `source setup-env.sh` (standard SDK env script) to put headers, loader 1.3.296, validation layers, and `glslc` on PATH. (The `setup-env.sh`/`x86_64/bin/glslc` layout is standard SDK convention — **doc-page-level UNVERIFIED**, confirm with `ls $VULKAN_SDK/x86_64/bin/glslc` post-install.)
  3. `Xvfb :99 &; DISPLAY=:99 vkcube`-style capture (Xvfb provides the X11 display `vkcube`/S03 needs; flag spellings per local `vkcube --help` — UNVERIFIED).
  4. Pin check: `vulkaninfo --summary` must report loader **1.3.296** and a lavapipe (`lvp`) device; record outputs as display proofs.
- **Scoping — what a lavapipe frame proves vs what it does not (confirms the issue text):** lavapipe is "Mesa's software renderer for Vulkan," currently **conformant to Vulkan 1.3** and exposing all core 1.4 extensions **without having been submitted for 1.4 conformance**. Selection via the loader's `VK_DRIVER_FILES` env var is documented. Therefore a virtual-display + lavapipe `vkcube` frame proves: the harness launches a display target, the 1.3.296 loader resolves an ICD, WSI/swapchain creation succeeds, and the app's Vulkan usage passes validation layers. It proves **nothing** about: real-GPU driver correctness or version quirks, presentation timing/vsync, memory/performance behavior, or multi-vendor coverage. Contrast: AWS G5 documents Nitro **pass-through GPU provisioning "comparable to bare-metal"** — that is the property lavapipe can never supply.

### Option (a)-physical — real GPU runner

- No in-repo precedent for a physical GPU host was found. A physical runner means a workstation with an AMD/NVIDIA GPU + RADV/NVK or proprietary driver, or a bare-metal GPU cloud box. **No verified current list-price found for a suitable bare-metal/physical SKU — UNVERIFIED**. Cheapest verified-adjacent real-GPU path is cloud (b) pass-through.

### Option (b) — cloud GPU as reference machine

| Vendor | Suitable type | GPU / VRAM | List price (secondary source, Oct 2026) | Notes |
|---|---|---|---|---|
| AWS | **g6.xlarge** | 1× NVIDIA L4 24 GB | **$0.80/hr** on-demand | Fractional-GPU slices down to 1/8 GPU. ~$584/mo if run 730 h |
| AWS | **g5.xlarge** | 1× NVIDIA A10G 24 GB | **$1.00/hr** on-demand | Nitro pass-through ≈ bare metal. ~$730/mo at 730 h |
| GCP | **g2-standard-4** | 1× NVIDIA L4 24 GB | **~$0.71/hr** | Cheapest verified-adjacent. ~$518/mo at 730 h |
| Azure | **NVadsA10 v5** | A10, 1/6-GPU slices up to full A10 24 GB | **UNVERIFIED** — no first-party hourly figure captured | Visualization/VDI line; partial GPUs fit a display-proof runner |

- Region availability: **UNVERIFIED per-region** for all (quota/availability not checked; Azure GPU VMs are quota-gated by default). Verify in the target region before promising dates.
- **Re-pinning the toolchain ADR to that host:** the repo's ratification-ceremony shape is documented in the CLI-0.7.5 wave ledger (`docs/sprints/CLI-0.7.5-BUMP.md`): two independent tarball fetches with byte-identical SHA-256, installed-binary stamp (`rig --version`), paired pin updates, `verify-rigs.sh` gates green (39/0), red-proof sabotage, dated `docs/sprints/*.md` ledger. **The 2026-10-20 ITS pin ceremony itself was NOT found in-repo** — so "same ceremony as the ITS pin" is **UNVERIFIED**; the 0.7.5-bump ledger is the closest verified template.

### Option (c) — sequencing: what runs headless today

- **Runs headless NOW (no runner):** (i) install SDK 1.3.296 → headers + loader 1.3.296 + validation layers present; (ii) swapchain *selection logic* as pure unit tests (no `VkInstance` needed); (iii) `vulkaninfo` executes headless and should report **zero devices** — that empty listing is itself the documented baseline.
- **Needs (a)-virtual minimum:** any `vulkaninfo` device listing (lavapipe `lvp` device), `vkcube` frame, `s02-window.png` capture.
- **Needs (a)-physical or (b):** acceptance items asserting *driver* behavior — real `VkPhysicalDevice` properties/limits, presentation timing, multi-vendor coverage. A lavapipe-only pass must be labeled as such.
- **Acceptance mapping:** `vulkaninfo 1.3.296 + headers` → (c) for headers/loader version + (a)-virtual for the device section; `vkcube` frame → (a)-virtual minimum, (a)-physical/(b) for driver-faithful; `s02-window.png` → same as `vkcube`.

### `rig host` (OpenRig 0.7.x) — VERIFIED

From the upstream CLI reference for the v0.7.5 tree: `rig host add --id <id> --transport <transport>` (**both required**) `[--target <target>] [--user <user>] [--url <url>] [--bearer-env <name>] [--bearer-file <path>] [--notes <text>] [--json]`; `rig host select/rename/pair/list/doctor`; cross-host verbs carry `--host` (`up/down/ps/send/queue/transcript/capture/broadcast`). Registration "makes a host visible in topology"; remote FEED attention is **opt-in**; **SSH entries need an HTTP entry for FEED**. Pairing tests are simulated — pilot `host doctor` against the real runner before relying on it.

## 3. Gaps / Unknowns (Not verified)

1. **Exact lavapipe Vulkan *version string* shipped in Mesa 25.0.7** (runner must report it).
2. **`glslc` present in the 1.3.296.0 Linux tarball at `x86_64/bin/glslc`** — standard layout but no file-manifest fetched. Verify post-install with `ls`.
3. **Exact `vkcube` screenshot/validation flags and `Xvfb` server flags** — verify against local `--help`/man at build time.
4. **Debian `glslc`/`shaderc` system-package alternative** — not checked (`apt-cache show` on the runner decides).
5. **All cloud list-prices** — secondary sources only; no first-party pricing figure captured. Re-verify at purchase time; region availability and quota unchecked.
6. **Physical-runner SKU + price** — no verified bare-metal option captured.
7. **The 2026-10-20 ITS pin ceremony** — not found in-repo; do not cite it as precedent.
8. **`rig host` transport kinds and auth semantics** — registration flags only; action semantics need `rig host --help` on an installed 0.7.5 CLI.
