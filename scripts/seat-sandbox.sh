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
# REQ-A1 (overhaul-a M1): before exec, the relay enforces the allowlist and
# flag rules below and denies fail-closed (exit 126, reason on stderr):
# argv[1] in {whoami, ps, queue, send, capture, transcript}; --source/-s
# (space and `=` forms) equal to non-empty $OPENRIG_SESSION_NAME; --note
# (both forms) matching ^[A-Za-z0-9][A-Za-z0-9 _.,:/@+-]{0,200}$ with no
# newlines or shell tokens; --body-file (both forms) realpath-contained
# (existing regular non-symlink file, <= 256KiB, never inside
# $HERETEK_SECRET_STORE, no credential suffix/name, inside the seat workspace
# or the configured scratch dirs, clear of protected segments). Scope note:
# write-roots always resolve under the workspace, and in-jail the whole
# workspace is readable, so workspace containment plus the store/credential/
# protected-segment denials is the laundering boundary; bare /tmp and
# /var/tmp are deliberately NOT in scope (the jail masks host /tmp, so
# relaying a host-/tmp file would launder bytes the seat could not read).
if [[ "$cmd" =~ ^[[:space:]]*rig([[:space:]]|$) ]]; then
  exec python3 -I -c '
import os, re, shlex, sys
try:
    argv = shlex.split(sys.argv[1])
except ValueError as e:
    sys.exit("seat-sandbox: cannot parse rig command: " + str(e))
if not argv or argv[0] != "rig":
    sys.exit("seat-sandbox: not a bare rig command")
_ALLOW = ("whoami", "ps", "queue", "send", "capture", "transcript")
if len(argv) < 2 or argv[1] not in _ALLOW:
    sys.exit("seat-sandbox: rig relay denied: subcommand not allowlisted: " + (argv[1] if len(argv) > 1 else "(missing)"))
srcs = []
notes = []
bodies = []
i = 2
while i < len(argv):
    tok = argv[i]
    if tok == "--source" or tok == "-s" or tok == "--note" or tok == "--body-file":
        if i + 1 >= len(argv):
            sys.exit("seat-sandbox: rig relay denied: flag without value: " + tok)
        if tok == "--source" or tok == "-s":
            srcs.append(argv[i + 1])
        elif tok == "--note":
            notes.append(argv[i + 1])
        else:
            bodies.append(argv[i + 1])
        i += 2
        continue
    if tok.startswith("--source=") or tok.startswith("--note=") or tok.startswith("--body-file="):
        key, _, val = tok.partition("=")
        if key == "--source":
            srcs.append(val)
        elif key == "--note":
            notes.append(val)
        else:
            bodies.append(val)
        i += 1
        continue
    if tok.startswith("-s="):
        srcs.append(tok[3:])
        i += 1
        continue
    if tok.startswith("-s") and not tok.startswith("--"):
        srcs.append(tok[2:])
        i += 1
        continue
    i += 1
session = os.environ.get("OPENRIG_SESSION_NAME", "")
for v in srcs:
    if not session or not v or v != session:
        sys.exit("seat-sandbox: rig relay denied: --source must equal non-empty $OPENRIG_SESSION_NAME")
_NOTE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.,:/@+-]{0,200}$")
for v in notes:
    if "\n" in v or "\r" in v or not _NOTE.match(v):
        sys.exit("seat-sandbox: rig relay denied: --note fails restrictive pattern")
store = os.environ.get("HERETEK_SECRET_STORE", "")
store_real = os.path.realpath(store) if store else ""
if bodies and not store_real:
    sys.exit("seat-sandbox: rig relay denied: --body-file needs HERETEK_SECRET_STORE set (fail closed)")
scratch = []
for _e in (os.environ.get("TMPDIR", ""), os.environ.get("HERETEK_JAIL_SCRATCH", "")):
    if _e:
        scratch.append(os.path.realpath(_e))
_CRED_SUFFIX = (".key", ".pem", ".p12", ".pfx", ".jks", ".keytab", ".env", ".token", ".secret", ".asc", ".gpg", ".age")
_CRED_NAME = (".netrc", ".npmrc", ".pypirc", "credentials", "secrets", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa")
_PROTECTED = (".git", ".pi", ".agents", "AGENTS.md")
def _under(_p, _b):
    return _p == _b or _p.startswith(_b + os.sep)
for v in bodies:
    if os.path.islink(v):
        sys.exit("seat-sandbox: rig relay denied: --body-file must not be a symlink: " + v)
    real = os.path.realpath(v)
    if not os.path.isfile(real):
        sys.exit("seat-sandbox: rig relay denied: --body-file not a regular file: " + v)
    try:
        _size = os.path.getsize(real)
    except OSError:
        sys.exit("seat-sandbox: rig relay denied: --body-file unreadable: " + v)
    if _size > 262144:
        sys.exit("seat-sandbox: rig relay denied: --body-file over 256KiB: " + v)
    if _under(real, store_real):
        sys.exit("seat-sandbox: rig relay denied: --body-file inside secret store: " + v)
    _base = os.path.basename(real).lower()
    if _base in _CRED_NAME or _base.endswith(_CRED_SUFFIX) or "credential" in _base or "secret" in _base:
        sys.exit("seat-sandbox: rig relay denied: --body-file looks like a credential: " + v)
    _cwd = os.path.realpath(os.getcwd())
    _home = None
    for _r in [_cwd] + scratch:
        if _under(real, _r):
            _home = _r
            break
    if _home is None:
        sys.exit("seat-sandbox: rig relay denied: --body-file outside scratch and seat workspace: " + v)
    _rel = real[len(_home):].lstrip(os.sep)
    if any(_seg in _PROTECTED for _seg in _rel.split(os.sep)):
        sys.exit("seat-sandbox: rig relay denied: --body-file touches a protected segment: " + v)
os.execvp("rig", argv)
' "$cmd"
fi

# Scratch MUST NOT overlap cwd or any write root (see Gotcha 1).
# The dir name carries the wrapper's PID. pi aborts a command with SIGKILL to
# its process group, which skips the EXIT trap, so each run first sweeps our
# own dirs whose wrapper is gone. Legacy seatjail.XXXXXX dirs are left alone.
# Removal is best effort: a jailed command can chmod 000 a dir in its scratch,
# so restore our own modes first and never let a stuck orphan block a run.
jail_rm() { chmod -R -- u+rwx "$1" 2>/dev/null || true; rm -rf -- "$1" 2>/dev/null || true; }
jail_tmp=${HERETEK_JAIL_SCRATCH:-/var/tmp}
for old in "$jail_tmp"/seatjail.[0-9]*.*; do
  [[ -d "$old" && ! -L "$old" && -O "$old" ]] || continue
  pid=${old##*/seatjail.}; pid=${pid%%.*}
  [[ "$pid" =~ ^[0-9]+$ ]] && ! kill -0 "$pid" 2>/dev/null && jail_rm "$old"
done
scratch=$(mktemp -d "$jail_tmp/seatjail.$$.XXXXXX")
# Cleaned on exit, so bwrap below must not be exec'd (exec drops the trap).
trap 'jail_rm "$scratch"' EXIT

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

# bwrap runs in the background so a signal sent only to this wrapper is
# handled at once (bash defers traps until a foreground child exits). The
# handler stops bwrap, reaps it and exits, which runs the EXIT cleanup; the
# jailed tree goes with it (--die-with-parent). Stdin is passed on fd 3
# because bash points a background command's stdin at /dev/null.
child=""
jail_stop() {
  if [[ -n "$child" ]]; then
    kill -TERM "$child" 2>/dev/null || true
    wait "$child" 2>/dev/null || true
  fi
  exit "$1"
}
trap 'jail_stop 129' HUP; trap 'jail_stop 130' INT; trap 'jail_stop 143' TERM
{ exec 3<&0; } 2>/dev/null || exec 3</dev/null
bwrap \
  --die-with-parent --new-session \
  --unshare-pid --unshare-ipc --unshare-uts --unshare-net \
  --ro-bind / / --dev /dev --proc /proc \
  "${broad[@]}" --ro-bind "$cwd" "$cwd" \
  --bind "$scratch" "$scratch" --setenv TMPDIR "$scratch" \
  "${binds[@]}" "${mask[@]}" --chdir "$cwd" \
  /bin/bash -c "$cmd" <&3 3<&- &
child=$!
exec 3<&-
rc=0
wait "$child" || rc=$?
exit "$rc"
