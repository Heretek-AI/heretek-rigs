#!/usr/bin/env python3
"""Event-driven re-evaluation sweep for typed-external blocks
(remediate-38-unblock, REQ-BU2/BU3/BU5/BU7).

A row parked on a typed non-qitem blocker (`external:<what>`, `fold:<what>`,
`auth:<what>`) stays blocked after its blocker is satisfied because only timer
wakes revisit it. This sweep re-evaluates each such HELD row when fresh
evidence lands and unparks it via the existing route only:

    rig queue update <id> --state in-progress --reopen --note "UNPARK ..."

Read-only discovery uses ONLY allowlisted verbs:
  rig queue list | show | transitions  (always --json)
Anything else is refused by check_allowed() (fail-closed, REQ-LH8-style).

Fail-closed evaluation (REQ-BU5):
  - satisfaction asserted + no later re-arming evidence -> unpark to
    in-progress (NEVER done: build_unpark_argv() cannot emit state=done).
  - ambiguous / partial / contradictory evidence -> stay blocked + recorded
    evaluation naming what is missing (never unpark, never drop).
  - malformed SATISFIED: record -> ignored + recorded evaluation.
  - blocker verdict-qitem reference unresolvable -> stay blocked + WARN
    naming the dangling reference.
  - daemon unreachable -> no evaluations claimed (raise DataSourceError).

Trigger detection keys on the append-only transitions log with a per-row
cursor (REQ-BU2/BU5 idempotency): reruns over already-evaluated transition
ids emit nothing. --dry-run reports would-unpark rows without any live write
(no update call, no cursor write).

Satisfaction evidence (REQ-BU3, implementer-fixed convention):
  SATISFIED: <blocker> <evidence-ref>
appended via `update` (note-only, no --state). Legacy operator/seat notes
count too when they (a) name the blocker's key token and (b) carry an
un-negated satisfaction token {satisfied, pass, resolved, verified, unblock,
green} with an evidence citation, and no later note cites new
failure/rework (re-arm tokens {fail, failed, failure, rework, overturned,
denied, regressed, regression, broken}). Evidence-free restatements
("blocker stands", "awaiting verdict", "park continues") never override a
prior satisfaction assertion -- that stale-premise restatement is the exact
#38 bug shape.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RIG_BIN = os.environ.get("RIG_PATH", "rig")
FETCH_LIMIT = 100
DEFAULT_CURSOR_FILE = "/tmp/heretek-sweep-typed-blocks/cursor.json"

TYPED_PREFIXES = ("external:", "fold:", "auth:")

SAT_TOKENS = ("satisfied", "pass", "resolved", "verified", "unblock", "green")
REARM_TOKENS = (
    "fail",
    "failed",
    "failure",
    "rework",
    "overturned",
    "denied",
    "regressed",
    "regression",
    "broken",
)
NEGATIONS = (
    "no",
    "zero",
    "without",
    "none",
    "not",
    "still",
    "pending",
    "awaiting",
    "awaits",
    "lacking",
    "missing",
)
CITATION_RE = re.compile(
    r"\b(per|from|via)\s+(t\d+|\S*(report|log|placement|artifact|evidence|wave\d)\S*)"
    r"|\bt\d{2,}|\breport\b|\blog\b",
    re.IGNORECASE,
)

SATISFY_RE = re.compile(r"^\s*SATISFIED:\s*(\S+)(?:\s+(\S.*))?\s*$", re.IGNORECASE)
SATISFY_MARKER_RE = re.compile(r"^\s*SATISFIED\s*:", re.IGNORECASE)


class DataSourceError(Exception):
    """A live data source is unreachable, errored, or unparseable."""


# ---------------------------------------------------------------------------
# Read-only enforcement (same shape as the Wave-1 live-health gate; no shared
# files -- this module carries its own copy per the spec'd interface rule)
# ---------------------------------------------------------------------------


def check_allowed(argv):
    """Refuse anything that is not a known read-only observation verb or the
    single spec'd unpark route (update --state in-progress --reopen)."""
    if not argv:
        raise RuntimeError("refusing empty rig invocation")
    if argv[0] == "queue" and len(argv) > 1:
        if argv[1] in ("list", "show", "transitions"):
            if "--json" not in argv:
                raise RuntimeError(f"refusing {argv}: queue verbs must use --json")
            return
        if argv[1] == "update":
            check_unpark_argv(argv)
            return
    raise RuntimeError(f"refusing non-read-only rig invocation: {argv}")


def check_unpark_argv(argv):
    """The ONLY live write: update --state in-progress --reopen + audit note."""
    if "--state" not in argv or "--reopen" not in argv or "--note" not in argv:
        raise RuntimeError(f"refusing update outside the spec'd unpark route: {argv}")
    state = argv[argv.index("--state") + 1]
    if state != "in-progress":
        raise RuntimeError(
            f"refusing update to state={state}: sweep unparks to in-progress only"
        )
    if "done" in argv:
        raise RuntimeError("refusing update: sweep NEVER closes rows as done")


def build_unpark_argv(qitem_id, blocked_on, citation):
    """Build the single permitted live write. Structural guard: state is
    pinned to in-progress; 'done' can never appear."""
    note = f"UNPARK {blocked_on}: {citation} (sweep re-evaluation, REQ-BU2)"
    argv = [
        "queue",
        "update",
        qitem_id,
        "--state",
        "in-progress",
        "--reopen",
        "--note",
        note,
        "--json",
    ]
    check_unpark_argv(argv)
    return argv


def run_rig(args, timeout=60):
    """Run one allowlisted rig command, return parsed JSON (or raw text)."""
    check_allowed(args)
    try:
        proc = subprocess.run(
            [RIG_BIN, *args], capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise DataSourceError(f"rig binary not found at {RIG_BIN}: {exc}")
    except subprocess.TimeoutExpired:
        raise DataSourceError(f"rig {' '.join(args)} timed out")
    if proc.returncode != 0:
        raise DataSourceError(
            f"rig {' '.join(args)} exited {proc.returncode}: "
            f"{proc.stderr.strip()[:300]}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise DataSourceError(f"rig {' '.join(args)} output unparseable: {exc}")


class RigClient:
    """Live client: read-only discovery + the single spec'd unpark write."""

    def __init__(self, limit=FETCH_LIMIT):
        self.limit = limit

    def fetch_list(self):
        result = run_rig(["queue", "list", "--json", "-A", "--limit", str(self.limit)])
        if not isinstance(result, list):
            raise DataSourceError("rig queue list: expected a JSON list")
        return result

    def fetch_show(self, qitem_id):
        result = run_rig(["queue", "show", "--json", qitem_id])
        if not isinstance(result, dict):
            raise DataSourceError(f"rig queue show {qitem_id}: expected an object")
        return result

    def fetch_transitions(self, qitem_id):
        result = run_rig(["queue", "transitions", "--json", qitem_id])
        if not isinstance(result, list):
            raise DataSourceError(
                f"rig queue transitions {qitem_id}: expected a JSON list"
            )
        return result

    def apply_update(self, argv):
        return run_rig(argv)


# ---------------------------------------------------------------------------
# Pure evaluation helpers (unit-tested, no I/O)
# ---------------------------------------------------------------------------


def is_typed_blocker(blocked_on):
    return isinstance(blocked_on, str) and blocked_on.startswith(TYPED_PREFIXES)


def blocker_key_tokens(blocked_on):
    """Tokenise the blocker's <what> suffix for note matching."""
    if not isinstance(blocked_on, str):
        return set()
    suffix = blocked_on
    for prefix in TYPED_PREFIXES:
        if blocked_on.startswith(prefix):
            suffix = blocked_on[len(prefix) :]
            break
    return {t for t in re.split(r"[-_:]+", suffix.lower()) if t}


def parse_satisfy_note(note):
    """Classify a note against the SATISFIED: convention.

    Returns (status, blocker, evidence) with status in {"ok", "malformed"},
    or None when the note is not a satisfy record at all.
    """
    if not isinstance(note, str):
        return None
    match = SATISFY_RE.match(note)
    if not match:
        if SATISFY_MARKER_RE.match(note):
            return ("malformed", "", "")
        return None
    blocker, evidence = match.group(1), (match.group(2) or "").strip()
    if not evidence:
        return ("malformed", blocker or "", "")
    return ("ok", blocker, evidence)


def _word_hits(note, tokens):
    """Whole-word hits for tokens, discounting negated occurrences
    ('zero rework owed', 'not satisfied')."""
    text = (note or "").lower()
    hits = set()
    for token in tokens:
        for match in re.finditer(rf"\b{re.escape(token)}\b", text):
            window = text[max(0, match.start() - 24) : match.start()]
            if re.search(r"\b(no|zero|without|none|not)\b", window):
                continue
            hits.add(token)
            break
    return hits


def note_names_blocker(note, key_tokens):
    text = (note or "").lower()
    return any(re.search(rf"\b{re.escape(tok)}\b", text) for tok in key_tokens)


def find_qitem_refs(note):
    return set(re.findall(r"\bqitem-[0-9A-Za-z-]+\b", note or ""))


def evaluate_row(row, transitions, fetch_blocker_transitions=None):
    """Re-evaluate one row. Returns a verdict dict.

    verdict: "unpark" | "stay-blocked" | "skip" (not a typed-external HELD row).
    """
    qid = row.get("qitemId", "?")
    if row.get("state") != "blocked" or not is_typed_blocker(row.get("blockedOn")):
        return {
            "verdict": "skip",
            "qitemId": qid,
            "reason": "not a typed-external HELD row",
        }
    blocked_on = row.get("blockedOn")
    key_tokens = blocker_key_tokens(blocked_on)
    ordered = sorted(
        (t for t in transitions if isinstance(t, dict)),
        key=lambda t: t.get("transitionId") or 0,
    )
    # Only post-park transitions are evidence: the park note describes future
    # satisfaction ("SATISFY-WHEN: QA PASS ...") and must never self-satisfy.
    # The current blocked spell starts at the last entry into blocked.
    park_idx = 0
    for i, t in enumerate(ordered):
        if t.get("state") == "blocked" and (
            i == 0 or ordered[i - 1].get("state") != "blocked"
        ):
            park_idx = i
    evidence_notes = ordered[park_idx + 1 :]

    malformed = []
    satisfaction = None  # (transitionId, citation)
    rearm = None  # (transitionId, excerpt)
    for t in evidence_notes:
        note = t.get("transitionNote") or ""
        parsed = parse_satisfy_note(note)
        if parsed is not None:
            status, blocker, evidence = parsed
            if status == "malformed":
                malformed.append(t.get("transitionId"))
                continue
            if (
                blocker == blocked_on
                or blocker_key_tokens(blocker) & key_tokens
                or note_names_blocker(blocker, key_tokens)
            ):
                refs = find_qitem_refs(evidence)
                dangling = []
                if fetch_blocker_transitions is not None:
                    for ref in sorted(refs):
                        try:
                            fetch_blocker_transitions(ref)
                        except DataSourceError:
                            dangling.append(ref)
                if dangling:
                    return {
                        "verdict": "stay-blocked",
                        "qitemId": qid,
                        "reason": "dangling blocker reference(s) unresolvable: "
                        f"{', '.join(dangling)} (from transition "
                        f"{t.get('transitionId')}); refusing to unpark",
                        "missing": sorted(dangling),
                    }
                satisfaction = (t.get("transitionId"), f"{blocker} {evidence}".strip())
                continue
            # Well-formed but naming a different blocker: not evidence for us.
            continue
        if not note_names_blocker(note, key_tokens):
            continue
        sat_hits = _word_hits(note, SAT_TOKENS)
        rearm_hits = _word_hits(note, REARM_TOKENS)
        if sat_hits and not rearm_hits:
            cited = CITATION_RE.search(note) is not None
            actor = t.get("actorSession") or ""
            authoritative = actor.split("@")[0] == "operator"
            if cited or authoritative:
                citation_bits = [note.strip()[:220]]
                satisfaction = (t.get("transitionId"), " | ".join(citation_bits))
            # Else: bare assertion with no evidence citation from a
            # non-verdict authority -- not actionable (fail-closed).
        elif rearm_hits:
            rearm = (t.get("transitionId"), note.strip()[:220])

    if satisfaction is not None and rearm is not None and rearm[0] > satisfaction[0]:
        return {
            "verdict": "stay-blocked",
            "qitemId": qid,
            "reason": f"later note (transition {rearm[0]}) cites new "
            f"failure/rework after satisfaction at transition "
            f"{satisfaction[0]}; block re-armed: {rearm[1]}",
            "missing": ["resolution of the re-armed failure/rework"],
        }
    if satisfaction is not None:
        return {
            "verdict": "unpark",
            "qitemId": qid,
            "evidence_citation": f"transition {satisfaction[0]}: {satisfaction[1]}",
            "reason": f"predicate met by transition {satisfaction[0]}",
        }
    details = []
    if malformed:
        details.append(
            f"malformed SATISFIED: record(s) at transition(s) "
            f"{malformed} ignored (need 'SATISFIED: <blocker> <evidence-ref>')"
        )
    evaluative = [
        t
        for t in evidence_notes
        if note_names_blocker(t.get("transitionNote") or "", key_tokens)
    ]
    if not evaluative:
        details.append(
            f"no post-park note names the blocker {blocked_on}; "
            f"missing: verdict evidence or a "
            f"'SATISFIED: {blocked_on} <evidence-ref>' note"
        )
    else:
        details.append(
            f"{len(evaluative)} blocker-naming note(s) but none asserts "
            f"satisfaction; missing: a satisfaction assertion "
            f"(SAT token + evidence citation) or "
            f"'SATISFIED: {blocked_on} <evidence-ref>'"
        )
    return {
        "verdict": "stay-blocked",
        "qitemId": qid,
        "reason": "; ".join(details),
        "missing": details,
    }


# ---------------------------------------------------------------------------
# Sweep run (cursor idempotency, dry-run, audit log)
# ---------------------------------------------------------------------------


def load_cursor(path):
    try:
        raw = json.loads(Path(path).read_text())
        if isinstance(raw, dict):
            return {k: v for k, v in raw.items() if isinstance(v, int)}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_cursor(path, cursor):
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(cursor, indent=1, sort_keys=True) + "\n")


def run_sweep(client, cursor, dry_run=False, log_lines=None):
    """One sweep cycle. Returns a report dict; appends audit lines to log_lines.

    cursor: {qitemId: last evaluated transitionId}. Never issues state=done.
    Raises DataSourceError when the daemon is unreachable (no evaluations
    claimed).
    """
    if log_lines is None:
        log_lines = []
    report = {
        "evaluated": [],
        "unparked": [],
        "would_unpark": [],
        "stay_blocked": [],
        "skipped": [],
        "cursor": dict(cursor),
    }

    rows = client.fetch_list()  # raises DataSourceError: no news, no claims
    for row in rows:
        if not isinstance(row, dict):
            continue
        qid = row.get("qitemId", "?")
        if row.get("state") != "blocked" or not is_typed_blocker(row.get("blockedOn")):
            report["skipped"].append(qid)
            continue
        try:
            transitions = client.fetch_transitions(qid)
        except DataSourceError as exc:
            log_lines.append(
                f"SKIP {qid}: transitions unreadable ({exc}); "
                f"stays blocked, no evaluation claimed"
            )
            report["stay_blocked"].append(qid)
            continue
        last_seen = cursor.get(qid, -1)
        fresh = [
            t
            for t in transitions
            if isinstance(t, dict)
            and isinstance(t.get("transitionId"), int)
            and t["transitionId"] > last_seen
        ]
        iftransitions_max = max(
            (
                t.get("transitionId", -1)
                for t in transitions
                if isinstance(t, dict) and isinstance(t.get("transitionId"), int)
            ),
            default=last_seen,
        )
        if not fresh and qid in cursor:
            continue  # idempotent: nothing new, no duplicate evaluation
        verdict = evaluate_row(
            row, transitions, fetch_blocker_transitions=client.fetch_transitions
        )
        report["evaluated"].append(qid)
        if verdict["verdict"] == "unpark":
            if dry_run:
                report["would_unpark"].append(qid)
                log_lines.append(
                    f"WOULD-UNPARK {qid} ({row.get('blockedOn')}): "
                    f"{verdict['evidence_citation']}"
                )
            else:
                argv = build_unpark_argv(
                    qid, row.get("blockedOn"), verdict["evidence_citation"]
                )
                client.apply_update(argv)
                report["unparked"].append(qid)
                log_lines.append(
                    f"UNPARKED {qid} -> in-progress ({row.get('blockedOn')}): "
                    f"{verdict['evidence_citation']}"
                )
        else:
            report["stay_blocked"].append(qid)
            log_lines.append(
                f"STAY-BLOCKED {qid} ({row.get('blockedOn')}): {verdict['reason']}"
            )
        report["cursor"][qid] = iftransitions_max
    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        description="Re-evaluate typed-external HELD rows on landed evidence; "
        "unpark via the existing update --state in-progress --reopen route. "
        "Read-only discovery; --dry-run mutates nothing."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report would-unpark rows without any live write",
    )
    parser.add_argument(
        "--limit",
        default=FETCH_LIMIT,
        type=int,
        help=f"per-verb row cap (default {FETCH_LIMIT})",
    )
    parser.add_argument(
        "--cursor-file",
        default=DEFAULT_CURSOR_FILE,
        help=f"per-row transition cursor (default {DEFAULT_CURSOR_FILE})",
    )
    parser.add_argument(
        "--log-file", default=None, help="append the audit trail here as well as stdout"
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    cursor = load_cursor(args.cursor_file)
    client = RigClient(limit=args.limit)
    log_lines = []
    try:
        report = run_sweep(client, cursor, dry_run=args.dry_run, log_lines=log_lines)
    except DataSourceError as exc:
        sys.stderr.write(
            f"sweep: data source unreachable: {exc}; no evaluations claimed\n"
        )
        return 2
    if not args.dry_run:
        save_cursor(args.cursor_file, report["cursor"])
    else:
        log_lines.append("(dry-run: cursor not written, no updates issued)")
    summary = (
        f"sweep: evaluated={len(report['evaluated'])} "
        f"unparked={len(report['unparked'])} "
        f"would-unpark={len(report['would_unpark'])} "
        f"stay-blocked={len(report['stay_blocked'])} "
        f"skipped={len(report['skipped'])}"
    )
    output = "\n".join(log_lines + [summary]) + "\n"
    sys.stdout.write(output)
    if args.log_file:
        with open(args.log_file, "a") as handle:
            handle.write(f"[{datetime.now(timezone.utc).isoformat()}] {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
