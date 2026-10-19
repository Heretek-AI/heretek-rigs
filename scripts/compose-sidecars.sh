#!/usr/bin/env bash
# compose-sidecars.sh — Fail-closed wrapper for sidecar Docker Compose (HR-7.3).
#
# Raw `docker compose -f docker-compose.sidecars.yml --profile ...` bypasses
# `make guard-profiles` by design (see docker-compose.sidecars.yml:13-14).
# Always invoke sidecars via `make sidecars-up SIDECAR_PROFILES="..."` or this
# wrapper, never raw compose. CI must invoke via make/wrapper, never raw compose.
#
# Usage:
#   SIDECAR_PROFILES="web-research" ./scripts/compose-sidecars.sh up -d
#   ./scripts/compose-sidecars.sh --profile web-research up -d
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PROFILES=""
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILES="${PROFILES} $2"
      ARGS+=("--profile" "$2")
      shift 2
      ;;
    --profile=*)
      P="${1#--profile=}"
      PROFILES="${PROFILES} ${P}"
      ARGS+=("$1")
      shift
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "${PROFILES// }" && -n "${SIDECAR_PROFILES:-}" ]]; then
  PROFILES="${SIDECAR_PROFILES}"
  # shellcheck disable=SC2206
  SPLIT=(${SIDECAR_PROFILES})
  for p in "${SPLIT[@]}"; do
    ARGS=("--profile" "${p}" "${ARGS[@]}")
  done
fi

# Fail-closed co-scheduling guard (mirrors `make guard-profiles` tokenization):
# the privileged /dev/kvm emulator (heretek-mobile) must stay isolated.
# Tokenize on whitespace/commas and match whole tokens only (HR-7.3-wrapper-substring:
# the old `*"mobile"*` substring test disagreed with the Makefile space/comma
# patterns and would false-positive on a hypothetical `automobile` profile).
_normalized="${PROFILES//,/ }"
_has_mobile=0; _has_blocker=0
for _tok in ${_normalized}; do
  case "${_tok}" in
    "mobile") _has_mobile=1 ;;
    "devsec"|"web-research") _has_blocker=1 ;;
  esac
done
if (( _has_mobile && _has_blocker )); then
  echo "error: refusing to co-schedule --profile mobile with devsec/web-research (privileged /dev/kvm emulator must stay isolated)" >&2
  exit 1
fi

exec docker compose -f docker-compose.sidecars.yml "${ARGS[@]}"
