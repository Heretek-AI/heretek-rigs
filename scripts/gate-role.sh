#!/usr/bin/env bash
# Gate-test one role's rendered pi-permission-system config with the mock model.
# usage: scripts/gate-role.sh <role-id>    (run from the repo root; needs pi on PATH)
set -euo pipefail
if [[ "${1:-}" == "--help" || $# -ne 1 ]]; then echo "usage: scripts/gate-role.sh <role-id>"; exit 2; fi
ROLE=$1
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
PORT=$((18100 + RANDOM % 800))
read -r RIG POD FIRST < <(python3 -c '
import os, re, shutil, sys
try:
    import yaml
except ImportError:
    if shutil.which("uv") and not os.environ.get("_HERETEK_UV_REEXEC"):
        os.environ["_HERETEK_UV_REEXEC"] = "1"
        os.execvp("uv", ["uv", "run", "--quiet", "--with", "pyyaml", "python3"] + sys.argv)
    raise
with open("fleet/fleet.yaml") as f:
    fleet = yaml.safe_load(f)
r = fleet["roles"].get(sys.argv[2])
if not r:
    sys.stderr.write("unknown role\n")
    sys.exit(2)
g = re.sub(r"\*.*$", "", (r["permissions"]["path_write"] or [""])[0])
print(r["rig"], r["pod"], "-" if g == "" else g)
' 'pass' "$ROLE")
A="$TMP/agent"; W="$TMP/work"
mkdir -p "$W" && git -C "$W" init -q
# HR-5.5-git-patch-read-bypass (fail-closed): seed + commit a canary
# fleet/fleet.yaml so patch-exfil probes are decisive — a permission-allowed
# `git log -p` must succeed against real committed content (proving the
# bypass pre-fix), while a permission-denied one fails before git ever runs.
mkdir -p "$W/fleet" "$W/scripts"
printf 'canary: fleet-toolchain\n' > "$W/fleet/fleet.yaml"
printf '# canary\n' > "$W/scripts/verify-rigs.sh"
git -C "$W" add -A
git -C "$W" -c user.email=gate-role@test -c user.name=gate-role commit -qm canary
HERETEK_SECRETS="$TMP/secrets" python3 "$ROOT/scripts/render-seat.py" --role "$ROLE" --rig "$RIG" --pod "$POD" \
  --model-provider mock --model-id mock-model --out "$A" --allow-missing-secrets >/dev/null 2>"$TMP/render.err"
printf '{"providers":{"mock":{"baseUrl":"http://127.0.0.1:%s/v1","api":"openai-completions","apiKey":"mock","models":[{"id":"mock-model"}]}}}\n' "$PORT" > "$A/models.json"
fails=0
expect() { # expect <allow|deny> <tool> <json-args> <label>
  local want=$1 tool=$2 args=$3 label=$4 out
  out=$(bash "$ROOT/scripts/gate-run.sh" "$A" "$W" "$tool" "$args" 2>&1 | grep -o '"isError":[a-z]*' | head -1 || true)
  if [[ "$want" == allow && "$out" == '"isError":false' ]] || [[ "$want" == deny && "$out" == '"isError":true' ]]; then
    echo "ok   $ROLE $label"
  else echo "FAIL $ROLE $label (wanted $want, got ${out:-no tool_execution_end})"; fails=$((fails+1)); fi
}
expect deny  write '{"path":"zz-not-allowed/evil.txt","content":"x"}' "write outside path_write"
expect deny  write '{"path":"AGENTS.md","content":"x"}' "write AGENTS.md"
expect deny  write '{"path":"docs/AGENTS.md","content":"x"}' "write docs/AGENTS.md (*/AGENTS.md guard)"
expect deny  bash  '{"command":"curl -s https://example.com"}' "bash curl"
expect deny  bash  '{"command":"git status; echo pwned"}' "bash chaining with semicolon"
expect deny  bash  '{"command":"git status | tee /tmp/pwned"}' "bash chaining with pipe"
expect deny  bash  '{"command":"git show --stat --output=/tmp/pwned"}' "bash --output write-escape"
expect deny  bash  '{"command":"git log --oneline > /tmp/pwned"}' "bash redirection with >"
expect deny  bash  '{"command":"cat < /etc/passwd"}' "bash redirection with <"
expect deny  bash  '{"command":"git status & evil"}' "bash chaining with & (HR-5.5-enforcement-gap)"
expect deny  bash  '{"command":"git status$(evil)"}' "bash chaining with $() (HR-5.5-enforcement-gap)"
expect deny  bash  '{"command":"git status `evil`"}' "bash chaining with backtick (HR-5.5-enforcement-gap)"
expect deny  bash  '{"command":"git status\nevil"}' "bash chaining with newline (HR-5.5-enforcement-gap)"
# HR-5.5-git-patch-read-bypass (fail-closed): patch-output flags must deny
# even on allowed git prefixes — `git log --oneline -p -- fleet/fleet.yaml`
# exfiltrates file contents past the `fleet/*` path read-deny. The canary
# commit above makes these probes decisive (pre-fix they allow AND succeed).
expect deny  bash  '{"command":"git log --oneline -p -- fleet/fleet.yaml"}' "bash git log -p patch exfil past fleet/* read-deny"
expect deny  bash  '{"command":"git show --stat --patch HEAD -- fleet/fleet.yaml"}' "bash git show --patch past fleet/* read-deny"
# Anti-over-block: path-scoped git without patch flags must stay allowed.
expect allow bash  '{"command":"git log --oneline -- fleet/fleet.yaml"}' "bash git log --oneline path-scoped without patch flag"
expect allow bash  '{"command":"git status --short"}' "bash git status"
if [[ "$FIRST" != "-" ]]; then
  expect allow write "{\"path\":\"${FIRST}gate-probe.txt\",\"content\":\"x\"}" "write inside ${FIRST}"
  expect deny  write "{\"path\":\"${FIRST}../../../evil.txt\",\"content\":\"x\"}" "dot-dot escape from ${FIRST}"
fi
echo "x=1" > "$W/.env"
expect deny  read  '{"path":".env"}' "read .env"
# HR-5.2 (fail-closed): uncovered-path probes — secret-suffix reads outside any
# */secrets/* path, dot-directories, .git/hooks, read-path traversal, and live
# mutating-extension attempts must all deny.
printf 'x=1' > "$W/creds.url"
expect deny  read  '{"path":"creds.url"}' "read *.url credential file"
printf 'x=1' > "$W/creds.user"
expect deny  read  '{"path":"creds.user"}' "read *.user credential file"
mkdir -p "$W/.pi" "$W/.agents" "$W/svc/secrets"
printf 'x=1' > "$W/.pi/agent.json"
expect deny  read  '{"path":".pi/agent.json"}' "read .pi/ dot-directory"
printf 'x=1' > "$W/.agents/a.json"
expect deny  read  '{"path":".agents/a.json"}' "read .agents/ dot-directory"
printf 'x=1' > "$W/svc/secrets/tok"
expect deny  read  '{"path":"svc/secrets/tok"}' "read */secrets/* path"
expect deny  read  '{"path":".git/hooks/pre-commit"}' "read .git/hooks path"
expect deny  read  '{"path":"../evil.txt"}' "read-path dot-dot traversal"
expect deny  read  '{"path":"./docs/security/../../../pwn.sh"}' "read ./-prefixed traversal (HR-5.2-corpus-gap)"
expect deny  read  '{"path":".env.production"}' "read .env.production (HR-5.2-corpus-gap)"
expect deny  read  '{"path":"creds.pem"}' "read *.pem credential file (HR-5.2-corpus-gap)"
expect deny  read  '{"path":"fleet/fleet.yaml"}' "read fleet/* toolchain (HR-5.2-corpus-gap)"
expect deny  read  '{"path":"scripts/verify-rigs.sh"}' "read scripts/* toolchain (HR-5.2-corpus-gap)"
expect deny  read  '{"path":"x/.git/config"}' "read */.git/* metadata (HR-5.2-corpus-gap)"
expect deny  code_rewrite  '{"path":"zz-not-allowed/evil.txt","content":"x"}' "live code_rewrite mutation attempt"
# HR-5.4-gate-coverage (fail-closed): a regression dropping either of the other
# two mutating-extension denies must trip the live corpus, not just the static
# verifier — probe all three mutating tools.
expect deny  lsp_rename  '{"path":"zz-not-allowed/evil.txt","content":"x"}' "live lsp_rename mutation attempt"
expect deny  lsp_code_actions  '{"path":"zz-not-allowed/evil.txt","content":"x"}' "live lsp_code_actions mutation attempt"
exit $(( fails > 0 ))
