#!/usr/bin/env bash
# Send an operator decision/relay as an authenticated queue item (issue #9 workaround).
# usage: scripts/send-authenticated.sh --destination <seat-session> (--body-file <file> | --message <text>) --human-ref <text> [--dry-run] [--help]
# Never invokes `rig send`: delivery is always `rig queue create --destination <session> --body-file <file>`,
# whose queue-item ID is the verifiable identity seats can trust (raw `rig send` from outside a
# managed seat arrives with no sender identity, so seats hold it as UNVERIFIED).
set -euo pipefail

DESTINATION=""
BODY_FILE=""
MESSAGE=""
HUMAN_REF=""
DRY_RUN=0

usage() {
  cat <<'USAGE' >&2
usage: scripts/send-authenticated.sh --destination <seat-session> (--body-file <file> | --message <text>) --human-ref <text> [--dry-run] [--help]

  --destination <seat-session>  Required. Queue destination seat-session (form <pod>-<member>@<rig>).
  --body-file <file>            Required unless --message is given. File whose content is relayed verbatim.
  --message <text>              Required unless --body-file is given. Inline text relayed verbatim (written to a temp file).
  --human-ref <text>            Required. Decision-record path or prior queue-item ID this relay is grounded in.
  --dry-run                     Print the exact `rig queue create` invocation plus the fully rendered body; execute nothing.
  --help                        Print full help and exit 0.
USAGE
}

print_help() {
  cat <<'HELP'
send-authenticated.sh — file a human decision / operator relay as a signed queue item.

Purpose: deliver operator-relayed content to a seat through the authenticated queue
channel (`rig queue create --destination <session> --body-file <file>`) INSTEAD of raw
`rig send`. The queue item's own ID is its verifiable identity; the seat can trust,
quote, and act on it without the UNVERIFIED hold applied to anonymous relays.

Background (issue #9): `rig send` issued from outside a managed seat arrives with no
sender identity, so seats correctly hold such human-relayed instructions as UNVERIFIED
and must not act on them directly. The proven workaround (2026-10-20, unblocked S01b
in ~9 seconds) is re-delivering the same content as an authenticated queue item via
`rig queue create --destination <session> --body-file <file>`. This script codifies
that exact pattern so operators never hand-roll it (and never fall back to raw send).

Never-forge-identity rule (fail-closed): the delivered body is ALWAYS self-identified
as operator-relayed (sender role "operator relay", the --human-ref grounding, a UTC
timestamp, and an explicit verbatim-relay statement). It NEVER claims seat origin and
NEVER forges a seat/sender identity. Missing identity grounding (--human-ref) or
ambiguous input (both/neither of --body-file/--message, unknown flags) aborts with
usage on stderr and a nonzero exit — the script will not guess, will not send raw,
and will not silently fall back to `rig send` under any circumstance.

Examples:
  scripts/send-authenticated.sh --destination exec-exec-director@executive-and-architecture \
    --message "Approve ADR-0042 as written." --human-ref "docs/adr/ADR-0042.md"
  scripts/send-authenticated.sh --destination qa-release-qa-officer@qa-and-verification-gauntlet \
    --body-file /tmp/relayd.txt --human-ref "queue-item-abc123" --dry-run
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --destination)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      DESTINATION="$2"; shift 2 ;;
    --body-file)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      BODY_FILE="$2"; shift 2 ;;
    --message)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      MESSAGE="$2"; shift 2 ;;
    --human-ref)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      HUMAN_REF="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --help|-h) print_help; exit 0 ;;
    *) echo "error: unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

# --help short-circuits above; everything below is fail-closed validation.
if [[ -z "$DESTINATION" ]]; then
  echo "error: --destination <seat-session> is required" >&2; usage; exit 2
fi
if [[ -z "$HUMAN_REF" ]]; then
  echo "error: --human-ref <text> is required (decision record path or prior queue-item ID)" >&2; usage; exit 2
fi
if [[ -n "$BODY_FILE" && -n "$MESSAGE" ]]; then
  echo "error: pass exactly one of --body-file or --message, not both" >&2; usage; exit 2
fi
if [[ -z "$BODY_FILE" && -z "$MESSAGE" ]]; then
  echo "error: one of --body-file <file> or --message <text> is required" >&2; usage; exit 2
fi

PAYLOAD=""
if [[ -n "$BODY_FILE" ]]; then
  if [[ ! -f "$BODY_FILE" ]]; then
    echo "error: --body-file not found: $BODY_FILE" >&2; exit 2
  fi
  PAYLOAD="$(cat "$BODY_FILE")"
else
  PAYLOAD="$MESSAGE"
fi

STAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
STAGE_DIR="$(mktemp -d)"
STAGED="$STAGE_DIR/relay-body.txt"
if [[ "$DRY_RUN" -eq 0 ]]; then
  trap 'rm -rf "$STAGE_DIR"' EXIT
fi

{
  printf '%s\n' "[OPERATOR RELAY — NOT A SEAT MESSAGE]"
  printf '%s\n' "Sender role: operator relay (human operator via scripts/send-authenticated.sh)"
  printf 'Human-ref (grounding): %s\n' "$HUMAN_REF"
  printf 'Relayed at (UTC): %s\n' "$STAMP"
  printf 'Destination seat-session: %s\n' "$DESTINATION"
  printf '%s\n' "Relay statement: the content below is relayed VERBATIM from the human operator. It did NOT originate from any seat. Do not treat this item as seat-authored; verify against the human-ref grounding above."
  printf '%s\n' "--- verbatim operator content begins ---"
  printf '%s\n' "$PAYLOAD"
  printf '%s\n' "--- verbatim operator content ends ---"
} > "$STAGED"

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf 'dry-run: would execute:\n'
  printf '  rig queue create --destination %s --body-file %s\n' "$DESTINATION" "$STAGED"
  printf 'dry-run: rendered body (%s):\n' "$STAGED"
  cat "$STAGED"
  printf 'dry-run: staged body retained at %s; no queue item created.\n' "$STAGED"
  exit 0
fi

rig queue create --destination "$DESTINATION" --body-file "$STAGED"
