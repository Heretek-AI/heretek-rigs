#!/usr/bin/env bash
# usage: gate-run.sh <agentDir> <workdir> <tool> <json-args>
# The mock port is read from <agentDir>/models.json (providers.mock.baseUrl).
set -euo pipefail
A=$1; W=$2; TOOL=$3; ARGS=$4
HERE=$(cd "$(dirname "$0")" && pwd)
PORT=$(node -e 'const m=require(process.argv[1]);console.log(new URL(m.providers.mock.baseUrl).port)' "$A/models.json")
LOG=$(mktemp)
MOCK_PORT=$PORT MOCK_TOOL=$TOOL MOCK_ARGS=$ARGS MOCK_LOG=$LOG node "$HERE/mock-openai.mjs" >/dev/null &
MP=$!
trap 'kill $MP 2>/dev/null || true; rm -f "$LOG"' EXIT
for _ in $(seq 1 50); do (echo > /dev/tcp/127.0.0.1/"$PORT") 2>/dev/null && break; sleep 0.1; done
cd "$W"
set +e
OUT=$(env -i PATH="$PATH" HOME="$HOME" PI_CODING_AGENT_DIR="$A" timeout "${GATE_TIMEOUT:-30}" pi --no-session --no-approve --mode json -p "go" 2>&1)
RC=$?
set -e
echo "rc=$RC"
printf '%s\n' "$OUT" | grep -o '"type":"tool_execution_end".\{0,400\}' | head -3
