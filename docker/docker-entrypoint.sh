#!/usr/bin/env bash
# docker-entrypoint.sh -- Fail-closed container entrypoint for heretek-rigs.
#
# Solves three container-specific invariants:
#   1. Secret staging for render-seat.py secret_ok() triple defense: host bind
#      mounts / K8s secrets at $HERETEK_SECRET_MOUNT often carry host UIDs,
#      0644 modes, or ..data symlinks -- all of which render-seat.py rejects
#      fail-closed. Each mounted file is dereferenced into a fresh regular file
#      owned by the runtime UID with mode 0600 before seeding.
#   2. Gated seat seeding: seeds each target once per OPENRIG_HOME, or when
#      HERETEK_SEED=1. Never logs secret values -- only basenames.
#   3. Daemon lifecycle under tini (PID 1 reaper): starts the OpenRig daemon
#      and FAILS LOUDLY if it will not start (a daemon-less container is useless).
set -euo pipefail

HERETEK_HOME="${HERETEK_HOME:-/opt/heretek/heretek-rigs}"
HERETEK_SECRETS="${HERETEK_SECRETS:-$HOME/.config/heretek-rigs/secrets}"
HERETEK_SECRET_MOUNT="${HERETEK_SECRET_MOUNT:-/run/heretek-secrets}"
HERETEK_WORKSPACE="${HERETEK_WORKSPACE:-/workspace}"
HERETEK_START_DAEMON="${HERETEK_START_DAEMON:-1}"
HERETEK_SEED="${HERETEK_SEED:-auto}"
HERETEK_SEED_MODE="${HERETEK_SEED_MODE:---allow-missing-secrets}"

# 0. The container user must own a writable HOME and secrets dir.
if [ ! -w "${HOME:-/nonexistent}" ]; then
  echo "[heretek-entrypoint] FATAL: HOME ($HOME) is not writable by uid $(id -u)." >&2
  echo "[heretek-entrypoint] Run with --user 1000:1000 so HOME=/home/heretek is writable." >&2
  exit 2
fi
mkdir -p -m 0700 "${HERETEK_SECRETS}"
chmod 0700 "${HERETEK_SECRETS}"

# 1. Stage mounted secrets into $HERETEK_SECRETS as 0600 regular files.
staged=0
if [ -d "${HERETEK_SECRET_MOUNT}" ]; then
  shopt -s nullglob
  for src_file in "${HERETEK_SECRET_MOUNT}"/*; do
    [ -f "${src_file}" ] || continue
    fname="$(basename "${src_file}")"
    dst_file="${HERETEK_SECRETS}/${fname}"
    install -m 0600 /dev/null "${dst_file}"
    cat "${src_file}" > "${dst_file}"
    chmod 0600 "${dst_file}"
    echo "[heretek-entrypoint] staged secret: ${fname} (0600)" >&2
    staged=$((staged + 1))
  done
  shopt -u nullglob
fi

# 2. Seed seats: always when HERETEK_SEED=1, never when 0, once-per-target on auto.
OPENRIG_HOME_DIR="${OPENRIG_HOME:-$HOME/.openrig}"
seed_marker="${OPENRIG_HOME_DIR}/.heretek-seeded-${HERETEK_RIG:-all}"
do_seed=0
case "${HERETEK_SEED}" in
  1) do_seed=1 ;;
  0) do_seed=0 ;;
  auto)
    if [ ! -f "${seed_marker}" ] && { [ "${staged}" -gt 0 ] || [ -n "${HERETEK_RIG:-}" ]; }; then
      do_seed=1
    fi
    ;;
  *) echo "[heretek-entrypoint] FATAL: HERETEK_SEED must be 1, 0, or auto." >&2; exit 2 ;;
esac
if [ "${do_seed}" = "1" ]; then
  mkdir -p "${OPENRIG_HOME_DIR}"
  cd "${HERETEK_HOME}"
  if [ -n "${HERETEK_RIG:-}" ]; then
    echo "[heretek-entrypoint] Seeding rig '${HERETEK_RIG}' (${HERETEK_SEED_MODE})..." >&2
    # shellcheck disable=SC2086
    python3 ./scripts/seed-rig.py "rigs/${HERETEK_RIG}/rig.yaml" ${HERETEK_SEED_MODE}
  else
    echo "[heretek-entrypoint] Seeding all 8 default rigs (${HERETEK_SEED_MODE})..." >&2
    # shellcheck disable=SC2086
    bash ./scripts/bootstrap-pi-seats.sh --all ${HERETEK_SEED_MODE}
  fi
  date -u +%FT%TZ > "${seed_marker}"
fi

# 3. Start the OpenRig daemon (fail loudly -- a daemon-less container is useless).
if [ "${HERETEK_START_DAEMON}" = "1" ]; then
  echo "[heretek-entrypoint] Starting OpenRig daemon (--no-kernel)..." >&2
  if ! rig daemon start --no-kernel; then
    echo "[heretek-entrypoint] FATAL: OpenRig daemon failed to start." >&2
    exit 1
  fi
fi

# 4. Optional auto-launch of a target rig.
if [ "${HERETEK_AUTO_UP:-0}" = "1" ] && [ -n "${HERETEK_RIG:-}" ]; then
  echo "[heretek-entrypoint] Launching rig '${HERETEK_RIG}' against workspace '${HERETEK_WORKSPACE}'..." >&2
  (cd "${HERETEK_HOME}/rigs/${HERETEK_RIG}" && rig up rig.yaml --cwd "${HERETEK_WORKSPACE}" --yes)
fi

exec "$@"
