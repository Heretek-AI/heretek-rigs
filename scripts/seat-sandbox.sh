#!/usr/bin/env bash
# seat-sandbox.sh — wrap every seat bash command in a bubblewrap jail.
# pi invokes this as the seat's shell: `seat-sandbox.sh -c "<command>"`.
# Writable roots: HERETEK_SANDBOX_WRITE, colon-separated, relative to cwd.
#   `dir/`   → that directory is bound read-write (created if missing).
#   `file`   → each EXISTING regular file matching the (glob) pattern is
#              bound read-write in place; nothing new can be created beside
#              it, and atomic temp+rename writes onto it fail (EBUSY).
# Secret store to mask: HERETEK_SECRET_STORE (absolute dir), tmpfs'd away.
# Extra paths to mask: HERETEK_SANDBOX_MASK (colon-separated, absolute).
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
cmd=$2; cwd=$(pwd -P)

# #105 review: the jail's private network namespace cannot reach the daemon
# on host loopback, so `rig` itself runs OUTSIDE the jail. It is exec'd from
# a shlex word list, never through a shell: no expansion, globbing, chaining
# or redirection can ride along. Anything else (`FOO=1 rig`, `./rig`,
# `command rig`) stays jailed and simply cannot reach the daemon.
if [[ "$cmd" =~ ^[[:space:]]*rig([[:space:]]|$) ]]; then
  exec python3 -I -c '
import os, shlex, sys
try:
    argv = shlex.split(sys.argv[1])
except ValueError as e:
    sys.exit(f"seat-sandbox: cannot parse rig command: {e}")
if not argv or argv[0] != "rig":
    sys.exit("seat-sandbox: not a bare rig command")
os.execvp("rig", argv)
' "$cmd"
fi

# Scratch MUST NOT overlap cwd or any write root (see Gotcha 1).
scratch=$(mktemp -d "${HERETEK_JAIL_SCRATCH:-/var/tmp}/seatjail.XXXXXX")
trap 'rm -rf "$scratch"' EXIT

# A write root may never resolve outside cwd (symlinked dir/file escape), and
# never touch agent/VCS control paths (.git, .pi, .agents, AGENTS.md).
inside_cwd() {
  [[ "$1" == "$cwd/"* ]] || return 1
  local seg
  IFS='/' read -ra _segs <<< "${1#"$cwd"/}"
  for seg in "${_segs[@]}"; do
    case "$seg" in .git|.pi|.agents|AGENTS.md) return 1 ;; esac
  done
}

binds=(); dir_roots=()
IFS=':' read -ra roots <<< "${HERETEK_SANDBOX_WRITE:-}"
for r in "${roots[@]}"; do
  [[ -n "$r" ]] || continue
  if [[ "$r" == /* || "/$r/" == */../* ]]; then
    echo "seat-sandbox: refusing write root '$r' (absolute or ..)" >&2; exit 126
  fi
  if [[ "$r" == */ ]]; then
    r=${r%/}
    if [[ -z "$r" || "$r" == "." ]]; then
      echo "seat-sandbox: refusing whole-cwd write root" >&2; exit 126
    fi
    # Resolve BEFORE mkdir: this runs unjailed, so a symlinked ancestor must
    # never make us create directories outside cwd.
    abs=$(realpath -m "$cwd/$r")
    if ! inside_cwd "$abs"; then
      echo "seat-sandbox: skipping write root '$r' (resolves outside cwd)" >&2; continue
    fi
    mkdir -p "$abs"
    binds+=(--bind "$abs" "$abs")
    dir_roots+=("$abs")
  else
    shopt -s nullglob
    matches=("$cwd"/$r)
    shopt -u nullglob
    for m in "${matches[@]}"; do
      [[ -f "$m" && ! -L "$m" ]] || continue
      abs=$(realpath -e "$m") && inside_cwd "$abs" || continue
      binds+=(--bind "$abs" "$abs")
    done
  fi
done

# Broad masks first; cwd is re-bound after them in case it lives beneath one.
uid=$(id -u)
broad=(--tmpfs /tmp)
[[ -d "/run/user/$uid" ]] && broad+=(--tmpfs "/run/user/$uid")   # dbus/wayland/agents

# Targeted masks LAST so no later bind re-exposes them.
mask=()
home=${HOME:-$(getent passwd "$uid" | cut -d: -f6)}
cred=()
if [[ -n "$home" ]]; then
  for p in .ssh .gnupg .aws .azure .kube .docker .password-store .config/gh \
           .config/gcloud .config/op .config/hub .config/git/credentials \
           .config/heretek-rigs .openrig .netrc .git-credentials .npmrc .pypirc \
           .vault-token .cargo/credentials .cargo/credentials.toml \
           .local/share/keyrings; do
    cred+=("$home/$p")
  done
fi
IFS=':' read -ra extra <<< "${HERETEK_SANDBOX_MASK:-}"
for p in "${cred[@]}" "${extra[@]}" "${HERETEK_SECRET_STORE:-}"; do
  [[ -n "$p" && "$p" == /* ]] || continue
  if [[ -d "$p" && ! -L "$p" ]]; then mask+=(--tmpfs "$p")
  elif [[ -e "$p" && ! -L "$p" ]]; then mask+=(--ro-bind /dev/null "$p")
  fi
done
# Host daemons reachable over unix sockets (net namespace does not cover them).
for s in /run/docker.sock /run/podman/podman.sock /run/containerd/containerd.sock \
         /run/dbus/system_bus_socket; do
  [[ -e "$s" ]] || continue
  if [[ -d "$s" ]]; then mask+=(--tmpfs "$s"); else mask+=(--ro-bind /dev/null "$s"); fi
done
# Control paths that already exist INSIDE a writable dir root (src/AGENTS.md,
# a nested src/x/.git) are re-bound read-only; later mounts win in bwrap.
for d in "${dir_roots[@]}"; do
  while IFS= read -r -d '' p; do
    mask+=(--ro-bind "$p" "$p")
  done < <(find "$d" -xdev \( -name node_modules -o -name target \) -prune -o \
             \( -name AGENTS.md -o -name .git -o -name .pi -o -name .agents \) -print0 -prune)
done
for p in .git .pi .agents AGENTS.md; do
  [[ -e "$cwd/$p" && ! -L "$cwd/$p" ]] && mask+=(--ro-bind "$cwd/$p" "$cwd/$p")
done

exec bwrap \
  --die-with-parent --new-session \
  --unshare-pid --unshare-ipc --unshare-uts --unshare-net \
  --ro-bind / / --dev /dev --proc /proc \
  "${broad[@]}" --ro-bind "$cwd" "$cwd" \
  --bind "$scratch" "$scratch" --setenv TMPDIR "$scratch" \
  "${binds[@]}" "${mask[@]}" --chdir "$cwd" \
  /bin/bash -c "$cmd"
