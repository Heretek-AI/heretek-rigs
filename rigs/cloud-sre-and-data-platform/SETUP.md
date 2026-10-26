# Setup Guide: `cloud-sre-and-data-platform`

## Prerequisites
1. Install OpenRig (`@openrig/cli@0.7.2`) and Pi Coding Agent (`@earendil-works/pi-coding-agent@1.4.0`).
2. Install `@gotgenes/pi-permission-system@41.0.0` under `$HERETEK_TOOLS/pi-packages`.
3. Provision `$HERETEK_SECRETS/opencode-go.key` (mode `0600`) and run:
   ```bash
   python3 scripts/seed-rig.py rigs/cloud-sre-and-data-platform/rig.yaml --allow-missing-secrets
   ```
4. Launch the rig:
   ```bash
   (cd rigs/cloud-sre-and-data-platform && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)
   ```
