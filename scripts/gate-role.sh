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
IFS='|' read -r RIG POD FIRST HAS_CTEST HAS_PYTEST PYTEST_PROBE HAS_GO GO_PROBE HAS_CMAKE_CONFIGURE HAS_GCC < <(python3 -c '
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
ba = r["permissions"].get("bash_allow") or []
has_ctest = "1" if any(str(b).startswith("ctest") for b in ba) else "0"
pytest_verbs = [str(b) for b in ba if str(b).startswith("pytest")]
has_pytest = "1" if pytest_verbs else "0"
pytest_probe = ""
if pytest_verbs:
    _pp = pytest_verbs[0].rstrip("*").rstrip()
    pytest_probe = _pp if _pp != "pytest" else "pytest tests"
has_go = "1" if any(str(b).split(" ")[0] == "go" for b in ba) else "0"
go_probe = ""
if any(str(b).startswith("go build") for b in ba):
    go_probe = "go build ./..."
elif has_go == "1":
    go_probe = "go test ./..."
has_cmake_configure = "1" if any(str(b).startswith("cmake -S") for b in ba) else "0"
has_gcc = "1" if any(str(b).startswith("gcc ") or str(b).startswith("g++ ") for b in ba) else "0"
print("|".join([r["rig"], r["pod"], "-" if g == "" else g, has_ctest, has_pytest, pytest_probe or "-", has_go, go_probe or "-", has_cmake_configure, has_gcc]))
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
# #91 scoped build/test fixtures (fail-open for execution, policy still
# gates): each charter-verbatim allow probe needs its operand tree present
# so an allowed tool runs against real content. Deny probes stay decisive
# without fixtures (policy denies before execution).
if [[ "$HAS_PYTEST" == "1" && "$PYTEST_PROBE" != "-" ]]; then
  _ppath=${PYTEST_PROBE#pytest }
  mkdir -p "$W/$_ppath"
  printf 'def test_gate_probe():\n    assert True\n' > "$W/$_ppath/test_gate_probe.py"
fi
if [[ "$HAS_GO" == "1" ]]; then
  printf 'module gateprobe\n\ngo 1.23\n' > "$W/go.mod"
  mkdir -p "$W/pkg/foo"
  printf 'package foo\nfunc Foo() int { return 1 }\n' > "$W/pkg/foo/foo.go"
fi
if [[ "$HAS_CMAKE_CONFIGURE" == "1" ]]; then
  printf 'cmake_minimum_required(VERSION 3.20)\nproject(gateprobe)\n' > "$W/CMakeLists.txt"
fi
if [[ "$HAS_GCC" == "1" && "$FIRST" != "-" ]]; then
  mkdir -p "$W/${FIRST}"
  printf 'int main(void){return 0;}\n' > "$W/${FIRST}foo.c"
fi
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
expect_run() { # expect_run <allow> <tool> <json-args> <label>  (#91 policy-level)
  # Policy-level allow: the tool RAN (no ask, no policy deny, tool found).
  # Exit code is NOT asserted — sandbox FS limits (GOCACHE, build/ mkdir,
  # cwd .o writes) can fail an allowed build after policy approved it; live
  # post-merge proof covers execution. A policy deny or ask fails here.
  local want=$1 tool=$2 args=$3 label=$4 out
  out=$(bash "$ROOT/scripts/gate-run.sh" "$A" "$W" "$tool" "$args" 2>&1 || true)
  if [[ "$want" == allow ]] && grep -q '"type":"tool_execution_end"' <<<"$out" \
    && ! grep -q "requires approval\|Denied by policy\|Tool .* not found" <<<"$out"; then
    echo "ok   $ROLE $label"
  else echo "FAIL $ROLE $label (wanted policy-$want)"; fails=$((fails+1)); fi
}
expect deny  write '{"path":"zz-not-allowed/evil.txt","content":"x"}' "write outside path_write"
expect deny  write '{"path":"AGENTS.md","content":"x"}' "write AGENTS.md"
expect deny  write '{"path":"docs/AGENTS.md","content":"x"}' "write docs/AGENTS.md (*/AGENTS.md guard)"
expect deny  bash  '{"command":"curl -s https://example.com"}' "bash curl"
expect deny  bash  '{"command":"git status; echo pwned"}' "bash chaining with semicolon"
expect deny  bash  '{"command":"git status | tee /tmp/pwned"}' "bash chaining with pipe"
expect deny  bash  '{"command":"git show --stat --output=/tmp/pwned"}' "bash --output write-escape"
# #76 narrowing (fail-closed): the space/tab-separated write forms must deny
# even on allowed git prefixes (JSON `\t` decodes to TAB, probing the
# `"*--output\t*"` terminal deny the same way the tab-p probes do).
expect deny  bash  '{"command":"git show --stat --output /tmp/pwned"}' "bash --output space-separated write-escape (#76)"
expect deny  bash  '{"command":"git show --stat --output\t/tmp/pwned"}' "bash --output tab-separated write-escape (#76)"
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
# HR-5.5-tab-p-suffix-gap (fail-closed): tab-separated -p plus the two
# unprobed patch flags must deny even on allowed git prefixes (JSON `\t`
# decodes to TAB, so this probes the `"*\t-p*"` terminal deny).
expect deny  bash  '{"command":"git log --oneline\t-p -- fleet/fleet.yaml"}' "bash git log tab-separated -p patch exfil past fleet/* read-deny"
expect deny  bash  '{"command":"git log --oneline --full-diff -- fleet/fleet.yaml"}' "bash git log --full-diff past fleet/* read-deny"
expect deny  bash  '{"command":"git show --textconv HEAD -- fleet/fleet.yaml"}' "bash git show --textconv past fleet/* read-deny"
# M5 (#69): unified/cross-commit diff-output flags must deny even on allowed
# git prefixes (same patch-exfil rationale as -p).
expect deny  bash  '{"command":"git log --oneline -u -- fleet/fleet.yaml"}' "bash git log -u past fleet/* read-deny"
expect deny  bash  '{"command":"git log --oneline --cc -- fleet/fleet.yaml"}' "bash git log --cc past fleet/* read-deny"
# #105 review: tab-separated short flags whose deny needs surrounding spaces.
expect deny  bash  '{"command":"git log --oneline\t-c\tHEAD -- fleet/fleet.yaml"}' "bash git log tab-separated -c combined diff past fleet/* read-deny"
expect deny  bash  '{"command":"git log --oneline\t-m\tHEAD -- fleet/fleet.yaml"}' "bash git log tab-separated -m diff past fleet/* read-deny"
expect deny  bash  '{"command":"git log --oneline\t-W -- fleet/fleet.yaml"}' "bash git log tab-separated -W diff past fleet/* read-deny"
# M5 (#72): env-prefixed identity override must deny via the
# *OPENRIG_SESSION_NAME=* terminal deny. (A bare leading `VAR=x rig ...`
# assignment is stripped by pps before matching (F9) so the policy layer
# cannot catch it — closed in send-authenticated.sh instead; see NOTES.)
expect deny  bash  '{"command":"env OPENRIG_SESSION_NAME=x rig whoami"}' "bash env-prefixed OPENRIG_SESSION_NAME rig call"
# Anti-over-block: path-scoped git without patch flags must stay allowed on a
# non-denied path (README.md is outside every `path` deny rule for all roles).
expect allow bash  '{"command":"git log --oneline -- README.md"}' "bash git log --oneline path-scoped without patch flag"
# Bash+path interaction: file arguments to allowed commands are still policed
# against the `path` map, so scoping an allowed prefix to a denied path denies.
expect deny  bash  '{"command":"git log --oneline -- fleet/fleet.yaml"}' "bash git log path-scoped to fleet/* (path-arg policing)"
expect allow bash  '{"command":"git status --short"}' "bash git status"
# #76 narrowing (fail-closed): the harmless `ctest --output-on-failure`
# diagnostic flag must stay allowed — but only on roles holding a `ctest*`
# allow (cpp-lowlevel-eng, engine-systems-eng); other roles still deny it for
# lack of an allow prefix, so the probe is conditional on the fleet grant.
if [[ "$HAS_CTEST" == "1" ]]; then
  expect allow bash  '{"command":"ctest --test-dir build --output-on-failure"}' "bash ctest --output-on-failure diagnostic flag (#76)"
fi
# #91 scoped build/test path args (charter-verbatim gate probes, REQ-A4):
# each advertised verification command expects allow on its seat (policy
# level via expect_run where sandbox FS limits exit codes; exit-code level
# via expect where the sandbox permits it). Traversal/absolute/-o/-P forms
# deny; the gcc slot exception still denies outside the slot.
if [[ "$HAS_PYTEST" == "1" && "$PYTEST_PROBE" != "-" ]]; then
  expect_run allow bash  "{\"command\":\"$PYTEST_PROBE\"}" "bash $PYTEST_PROBE charter-verbatim (#91)"
  expect deny  bash  '{"command":"pytest ../../etc/passwd"}' "bash pytest traversal past scope (#91)"
fi
if [[ "$HAS_GO" == "1" && "$GO_PROBE" != "-" ]]; then
  expect_run allow bash  "{\"command\":\"$GO_PROBE\"}" "bash $GO_PROBE charter-verbatim (#91)"
  expect deny  bash  '{"command":"go build ../../etc/..."}' "bash go traversal past scope (#91)"
  expect deny  bash  '{"command":"go build -o /tmp/evil ./..."}' "bash go -o /tmp write-escape (#91)"
fi
if [[ "$HAS_CMAKE_CONFIGURE" == "1" ]]; then
  expect_run allow bash  '{"command":"cmake -S . -B build"}' "bash cmake -S . -B build charter-verbatim (#91)"
  expect deny  bash  '{"command":"cmake -S . -B /tmp/evil"}' "bash cmake -B /tmp write-escape (#91)"
  expect deny  bash  '{"command":"cmake -P /tmp/evil.cmake"}' "bash cmake -P script outside scope (#91)"
fi
if [[ "$HAS_GCC" == "1" && "$FIRST" != "-" ]]; then
  expect_run allow bash  "{\"command\":\"gcc -c ${FIRST}foo.c\"}" "bash gcc -c in-scope charter-verbatim (#91)"
  expect deny  bash  '{"command":"gcc -c ../../evil.c"}' "bash gcc traversal past scope (#91)"
  expect deny  bash  "{\"command\":\"gcc -c ${FIRST}foo.c -o /tmp/evil.o\"}" "bash gcc -o /tmp write-escape (#91)"
  expect deny  bash  '{"command":"sh -c evil"}' "bash sh -c still denied outside gcc slot (#91)"
fi
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
