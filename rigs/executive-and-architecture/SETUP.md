# Setup Guide: `executive-and-architecture`

## Prerequisites
1. Install OpenRig (`@openrig/cli@0.6.13`) and Pi Coding Agent (`@earendil-works/pi-coding-agent@1.3.0`).
2. Install `@gotgenes/pi-permission-system@41.0.0` under `$HERETEK_TOOLS/pi-packages`.
3. Provision `$HERETEK_SECRETS/opencode-go.key` (mode `0600`) and run:
   ```bash
   python3 scripts/seed-rig.py rigs/executive-and-architecture/rig.yaml --allow-missing-secrets
   ```
4. Launch the rig:
   ```bash
   (cd rigs/executive-and-architecture && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)
   ```
