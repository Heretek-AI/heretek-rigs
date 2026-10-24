#!/usr/bin/env bash
# seat-sandbox.sh — wrap every seat bash command in a bubblewrap jail.
# pi invokes this as the seat's shell: `seat-sandbox.sh -c "<command>"`.
# Writable roots: HERETEK_SANDBOX_WRITE, colon-separated, relative to cwd.
# Secret store to mask: HERETEK_SECRET_STORE (absolute dir), tmpfs'd away.
#
# M4 (#68) env bootstrap: the pi-runner child env is deny-by-default
# (buildPiChildEnv in @openrig/cli passes only baseline + OPENRIG vars +
# PI_CODING_AGENT_DIR + the provider key; rig-spec `env:` likewise reaches the
# terminal but NOT the pi agent process). PI_CODING_AGENT_DIR always points at
# this seat's agent dir, so load the renderer-written sandbox.env from there
# when the vars are not already set. Without any roots the jail still confines
# (whole tree read-only except scratch) — fail-closed.
if [[ -z "${HERETEK_SANDBOX_WRITE:-}" || -z "${HERETEK_SECRET_STORE:-}" ]]; then
  _sandbox_env="${PI_CODING_AGENT_DIR:-}/sandbox.env"
  if [[ -n "${PI_CODING_AGENT_DIR:-}" && -f "$_sandbox_env" ]]; then
    # shellcheck disable=SC1090
    . "$_sandbox_env"
  fi
  unset _sandbox_env
fi
set -euo pipefail
if [[ "${1:-}" != "-c" || $# -ne 2 ]]; then
  echo "seat-sandbox: expected -c <command>" >&2; exit 126
fi
cmd=$2; cwd=$PWD
# Scratch MUST NOT overlap cwd or any write root (see Gotcha 1).
scratch=$(mktemp -d "${HERETEK_JAIL_SCRATCH:-/var/tmp}/seatjail.XXXXXX")
trap 'rm -rf "$scratch"' EXIT
binds=()
IFS=':' read -ra roots <<< "${HERETEK_SANDBOX_WRITE:-}"
for r in "${roots[@]}"; do
  [[ -n "$r" ]] || continue
  abs="$cwd/$r"; mkdir -p "$abs"; binds+=(--bind "$abs" "$abs")
done
mask=()
[[ -n "${HERETEK_SECRET_STORE:-}" && -d "$HERETEK_SECRET_STORE" ]] && mask+=(--tmpfs "$HERETEK_SECRET_STORE")
exec bwrap \
  --die-with-parent --new-session \
  --unshare-pid --unshare-ipc --unshare-uts --unshare-net \
  --ro-bind / / --dev /dev --proc /proc \
  --bind "$scratch" "$scratch" --setenv TMPDIR "$scratch" \
  "${binds[@]}" "${mask[@]}" --chdir "$cwd" \
  /bin/bash -c "$cmd"
