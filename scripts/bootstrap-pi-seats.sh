#!/usr/bin/env bash
# bootstrap-pi-seats.sh — Provision $OPENRIG_HOME/state/pi/<session>/agent/ for Muse Spark 1.3 Contributor via OpenCode Go.
#
# Wrapper around scripts/seed-rig.py supporting:
#   ./scripts/bootstrap-pi-seats.sh [--rig <rig-slug> | --all] [--profile all-51] [--dry-run] [--strict-secrets | --allow-missing-secrets]
# Strict secrets by default; --allow-missing-secrets opts into degraded seats.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

OPENRIG_HOME="${OPENRIG_HOME:-$HOME/.openrig}"
TARGET_RIG="all"
DRY_RUN="false"
# HR-4.2 (fail-closed): strict secrets by default — degraded `"enabled": false`
# seats must be an explicit opt-in, never the silent default.
ALLOW_MISSING=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rig) TARGET_RIG="$2"; shift 2 ;;
    --all) TARGET_RIG="all"; shift ;;
    --dry-run) DRY_RUN="true"; shift ;;
    --strict-secrets) ALLOW_MISSING=""; shift ;;
    --allow-missing-secrets) ALLOW_MISSING="--allow-missing-secrets"; shift ;;
    --profile)
      if [[ "$2" == "all-51" ]]; then TARGET_RIG="all-51"; else echo "Unknown profile: $2" >&2; exit 2; fi
      shift 2 ;;
    --help|-h)
      echo "Usage: $0 [--rig <rig-slug> | --all] [--profile all-51] [--dry-run] [--strict-secrets | --allow-missing-secrets]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

ARGS=()
if [[ "${DRY_RUN}" == "true" ]]; then
  ARGS+=("--dry-run")
fi
if [[ -n "${ALLOW_MISSING}" ]]; then
  ARGS+=("${ALLOW_MISSING}")
fi

TOTAL=0
if [[ "${TARGET_RIG}" == "all-51" ]]; then
  # HR-4.2: the 51-seat static profile is a separate target, never additive to --all.
  OUT=$(python3 "${REPO_ROOT}/scripts/seed-rig.py" "rigs/heretek-omni-fleet/rig.all-51.yaml" "${ARGS[@]}")
  COUNT=$(printf '%s\n' "${OUT}" | awk '/^seeded / {print $2}')
  TOTAL=$((TOTAL + ${COUNT:-0}))
elif [[ "${TARGET_RIG}" == "all" ]]; then
  # HR-4.2: seed each rigs/*/rig.yaml exactly once (incl. the omni 3-seat
  # command rig); rig.all-51.yaml needs --profile all-51 explicitly.
  for rfile in rigs/*/rig.yaml; do
    OUT=$(python3 "${REPO_ROOT}/scripts/seed-rig.py" "${rfile}" "${ARGS[@]}")
    COUNT=$(printf '%s\n' "${OUT}" | awk '/^seeded / {print $2}')
    TOTAL=$((TOTAL + ${COUNT:-0}))
  done
else
  OUT=$(python3 "${REPO_ROOT}/scripts/seed-rig.py" "rigs/${TARGET_RIG}/rig.yaml" "${ARGS[@]}")
  COUNT=$(printf '%s\n' "${OUT}" | awk '/^seeded / {print $2}')
  TOTAL=$((TOTAL + ${COUNT:-0}))
fi

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "bootstrap-pi-seats: [DRY-RUN] would provision ${TOTAL} Pi seat directories under ${OPENRIG_HOME}/state/pi"
else
  echo "bootstrap-pi-seats: provisioned ${TOTAL} Pi seat directories under ${OPENRIG_HOME}/state/pi"
fi
