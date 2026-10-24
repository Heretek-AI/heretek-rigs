#!/usr/bin/env python3
"""check-envelope.py — PRE-AUTH envelope verifier (issue #12 wave, 12b).

Validates a standing pre-authorization envelope file against the template in
docs/sprints/PRE-AUTH-ENVELOPES.md section 2 (REQ-BC4). Binary fail-closed
verdicts: every REQUIRED field present and well-formed, expiry live,
revocation channel named, all 3 audit links present, TPM verifier not an
owning seat, and every enumerated action inside the COMMIT / FILE-QUEUE-ITEM
<queue> / PUSH <branch-ref> verb set — else REFUSE (operator holds, no
execution). Accepts both the single-line and the template-verbatim wrapped
header forms (`Permitted operator` / `actions:`, `TPM verification` /
`gate:`, `Path scope` / `(exact repo paths):`).

M8 (#92) semantics: path scopes deny leading-dot/.git/.pi/.agents/fleet//
scripts//AGENTS.md/leading `-`/colon/non-ASCII/`%`; PUSH to HEAD/main/master
refused; all deadlines parsed with the earliest governing, requiring
issued_at <= now < deadline <= issued_at + 14d; owning seats validated
against fleet.yaml; BY WHOM must be the TPM seat (or bare `TPM`, which
resolves to the fleet's single tpm/scrum seat) or a named human; every
audit record must be link-shaped (URL, qitem id, hex SHA with a digit, the
word `commit`, or a slashed path).

Usage:
  check-envelope.py --envelope FILE [--at "YYYY-MM-DD HH:MMZ"]
                    [--consumed] [--revoked]

  --at       reference UTC time for deadline checks (default: now).
  --consumed the single-slice envelope already had its execution attempt
             (voids single-slice envelopes; deadline envelopes unaffected).
  --revoked  a revocation has issued on the revocation channel (voids all).

Exit codes: 0 = ACCEPT (envelope live); 1 = REFUSE (void, expired, invalid
or unreadable — operator holds); 2 = usage error. Reasons name the field.
Tests: tests/test_check_envelope.py (one fail-closed test per field, N2).
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}Z$")
ENVELOPE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
SEAT_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
QUEUE_RE = re.compile(r"^[A-Za-z0-9._-]+$")
EXPIRY_DEADLINE_RE = re.compile(r"expires\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}Z)")
EXPIRY_OPEN_RE = re.compile(r"never|open-ended|indefinite", re.IGNORECASE)
REVOCATION_VOID_VALUES = {"none", "n/a", "na", "not applicable", "-", "tbd", "todo"}
ENVELOPE_MAX_LIFETIME_DAYS = 14

# M8 (#92): verifiers that name nobody (or a non-verifier) verify nothing.
VOID_VERIFIERS = frozenset(
    {
        "nobody",
        "none",
        "n/a",
        "na",
        "tbd",
        "todo",
        "unknown",
        "unnamed",
        "anonymous",
        "anyone",
        "someone",
        "vacant",
    }
)


class Refusal(Exception):
    """A fail-closed finding naming the envelope field."""


def parse_stamp(text, field):
    text = text.strip()
    if not STAMP_RE.match(text):
        raise Refusal(
            f"{field}: malformed UTC timestamp {text!r} (want YYYY-MM-DD HH:MMZ)"
        )
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%d %H:%MZ").replace(
            tzinfo=datetime.timezone.utc
        )
    except ValueError:
        raise Refusal(f"{field}: impossible calendar timestamp {text!r}")


def split_sections(lines):
    """Split envelope lines into (header-key, same-line-value, body-lines).

    Recognises the single-line and template-wrapped header forms. A
    letter-led `Word ...:` line at column 0 that matches no known header is
    kept as an unknown section (refused later) rather than silently absorbed.
    """
    sections = []
    current = None
    i = 0
    pending_wrap = None
    while i < len(lines):
        raw = lines[i].rstrip("\n")
        stripped = raw.strip()
        i += 1
        if not stripped:
            continue
        key = value = None
        if pending_wrap == "path" and re.match(
            r"^\(exact repo paths\):\s*(.*)$", stripped
        ):
            key = "path_scope"
            value = re.match(r"^\(exact repo paths\):\s*(.*)$", stripped).group(1)
            pending_wrap = None
        elif pending_wrap == "actions" and re.match(r"^actions:\s*(.*)$", stripped):
            key = "actions"
            value = re.match(r"^actions:\s*(.*)$", stripped).group(1)
            pending_wrap = None
        elif pending_wrap == "tpm" and re.match(r"^gate:\s*(.*)$", stripped):
            key = "tpm_gate"
            value = re.match(r"^gate:\s*(.*)$", stripped).group(1)
            pending_wrap = None
        elif re.match(r"^PRE-AUTH ENVELOPE\s+(\S+)\s*$", stripped):
            key = "envelope_id"
            value = re.match(r"^PRE-AUTH ENVELOPE\s+(\S+)\s*$", stripped).group(1)
        elif re.match(r"^Slice class:\s*(.*)$", stripped):
            key = "slice_class"
            value = re.match(r"^Slice class:\s*(.*)$", stripped).group(1)
        elif re.match(r"^Issued by:\s*(.*)$", stripped):
            key = "issued_by"
            value = re.match(r"^Issued by:\s*(.*)$", stripped).group(1)
        elif re.match(r"^Issued at \(UTC\):\s*(.*)$", stripped):
            key = "issued_at"
            value = re.match(r"^Issued at \(UTC\):\s*(.*)$", stripped).group(1)
        elif re.match(r"^Expiry:\s*(.*)$", stripped):
            key = "expiry"
            value = re.match(r"^Expiry:\s*(.*)$", stripped).group(1)
        elif re.match(r"^Path scope\s*$", stripped):
            pending_wrap = "path"
            continue
        elif re.match(r"^Path scope.*:\s*(.*)$", stripped):
            key = "path_scope"
            value = re.match(r"^Path scope.*:\s*(.*)$", stripped).group(1)
        elif re.match(r"^Owning seats:\s*(.*)$", stripped):
            key = "owning_seats"
            value = re.match(r"^Owning seats:\s*(.*)$", stripped).group(1)
        elif re.match(r"^Permitted operator\s*$", stripped):
            pending_wrap = "actions"
            continue
        elif re.match(r"^Permitted operator actions:\s*(.*)$", stripped):
            key = "actions"
            value = re.match(r"^Permitted operator actions:\s*(.*)$", stripped).group(1)
        elif re.match(r"^TPM verification\s*$", stripped):
            pending_wrap = "tpm"
            continue
        elif re.match(r"^TPM verification gate:\s*(.*)$", stripped):
            key = "tpm_gate"
            value = re.match(r"^TPM verification gate:\s*(.*)$", stripped).group(1)
        elif re.match(r"^Revocation:\s*(.*)$", stripped):
            key = "revocation"
            value = re.match(r"^Revocation:\s*(.*)$", stripped).group(1)
        elif re.match(r"^Audit trail:\s*(.*)$", stripped):
            key = "audit_trail"
            value = re.match(r"^Audit trail:\s*(.*)$", stripped).group(1)
        elif re.match(r"^OPTIONAL notes:\s*(.*)$", stripped):
            key = "notes"
            value = re.match(r"^OPTIONAL notes:\s*(.*)$", stripped).group(1)
        elif re.match(r"^[A-Za-z].*:", raw):
            if (
                current is not None
                and current["key"] == "actions"
                and re.match(r"^(COMMIT|FILE-QUEUE-ITEM|PUSH)(\s|$)", stripped)
            ):
                # Action-shaped line inside the actions section (e.g. a PUSH
                # refspec containing ':'): keep it as body so check_actions —
                # not the unknown-section gate — rules on it, fail-closed.
                current["body"].append(stripped)
            else:
                key = f"unknown:{stripped[:40]}"
                value = ""
        if key is not None:
            pending_wrap = None
            current = {"key": key, "head": value, "body": []}
            sections.append(current)
        elif pending_wrap is not None:
            raise Refusal(
                "envelope: expected wrapped header continuation after "
                f"'{pending_wrap}' block, got {stripped!r}"
            )
        elif current is None:
            raise Refusal(f"envelope: content before any header: {stripped!r}")
        else:
            current["body"].append(stripped)
    if pending_wrap is not None:
        raise Refusal(f"envelope: dangling wrapped header for '{pending_wrap}' block")
    return sections


def section_text(section):
    parts = [section["head"]] + section["body"]
    return "\n".join(part for part in parts if part.strip())


def require(sections, key, label):
    found = [section for section in sections if section["key"] == key]
    if not found:
        raise Refusal(f"{label}: REQUIRED section missing — envelope void on its face")
    if len(found) > 1:
        raise Refusal(
            f"{label}: AMBIGUOUS — {len(found)} '{key}' sections; "
            "duplicates refused, operator holds"
        )
    return found[0]


def check_identity(sections):
    envelope_id = require(sections, "envelope_id", "PRE-AUTH ENVELOPE")["head"].strip()
    if not ENVELOPE_ID_RE.match(envelope_id):
        raise Refusal(f"PRE-AUTH ENVELOPE: malformed envelope id {envelope_id!r}")
    for key, label in (("slice_class", "Slice class"), ("issued_by", "Issued by")):
        value = section_text(require(sections, key, label)).strip()
        if not value:
            raise Refusal(f"{label}: REQUIRED value empty — envelope void on its face")
    issued_at = section_text(require(sections, "issued_at", "Issued at (UTC)")).strip()
    return envelope_id, parse_stamp(issued_at, "Issued at (UTC)")


def check_expiry(sections, now, consumed, issued_at):
    # M8 (#92): parse ALL deadlines and govern by the earliest; a standing
    # envelope lives at most ENVELOPE_MAX_LIFETIME_DAYS past issuance, and an
    # envelope issued after --at (or after its own deadline) is void.
    text = section_text(require(sections, "expiry", "Expiry"))
    if EXPIRY_OPEN_RE.search(text):
        raise Refusal(
            "Expiry: open-ended expiry is a standing permission in disguise — refused"
        )
    single_slice = "single-slice" in text.lower()
    deadlines = [
        parse_stamp(found, "Expiry") for found in EXPIRY_DEADLINE_RE.findall(text)
    ]
    deadline = min(deadlines) if deadlines else None
    if single_slice and deadline is not None:
        raise Refusal(
            "Expiry: single-slice AND an explicit UTC deadline combined — "
            "expiry is one or the other (XOR), not both — refused"
        )
    if not single_slice and deadline is None:
        raise Refusal(
            "Expiry: neither single-slice nor an explicit UTC deadline — refused"
        )
    if issued_at > now:
        raise Refusal(
            "Issued at (UTC): envelope issued after the reference time — "
            "not yet live — refused"
        )
    if deadline is not None:
        if deadline <= now:
            raise Refusal("Expiry: deadline passed — envelope expired")
        if deadline > issued_at + datetime.timedelta(days=ENVELOPE_MAX_LIFETIME_DAYS):
            raise Refusal(
                "Expiry: deadline more than "
                f"{ENVELOPE_MAX_LIFETIME_DAYS}d past issuance — over-broad "
                "window — refused"
            )
    if consumed and single_slice:
        raise Refusal("Expiry: single-slice envelope already attempted — VOID")


def split_entries(text):
    return [entry.strip() for entry in re.split(r"[,\n]", text) if entry.strip()]


def check_path_scope(sections):
    text = section_text(require(sections, "path_scope", "Path scope"))
    entries = split_entries(text)
    if not entries:
        raise Refusal("Path scope: no enumerated paths — envelope void on its face")
    for entry in entries:
        if entry.startswith("/") or ".." in entry or re.search(r"\s", entry):
            raise Refusal(
                f"Path scope: out-of-scope entry {entry!r} "
                "(absolute, parent-traversal or whitespace — refused)"
            )
        if entry.rstrip("/").strip() in ("", "."):
            raise Refusal(
                f"Path scope: repository-root alias {entry!r} "
                "(enumerates everything — refused)"
            )
        if entry.startswith("~"):
            raise Refusal(
                f"Path scope: home-prefixed entry {entry!r} "
                "(outside the repo — refused)"
            )
        if re.search(r"[*?\[\]{}!]", entry):
            raise Refusal(
                f"Path scope: glob metacharacter in {entry!r} "
                "(patterns widen scope — refused)"
            )
        # M8 (#92): the jailbreak tail. A leading dot escapes the repo
        # (.git/.pi/.agents/dots), fleet//scripts//AGENTS.md escape the slice
        # into governance, and leading -/:/non-ASCII/% smuggle
        # option/refspec/encoding tricks. (A body-line entry containing `:`
        # is additionally diverted by the section parser into an unknown
        # section — refused either way.)
        if entry.startswith("."):
            raise Refusal(
                f"Path scope: dot-prefixed entry {entry!r} "
                "(.git/.pi/.agents/all-dotfiles — refused)"
            )
        if any(part in (".git", ".pi", ".agents") for part in entry.split("/")):
            raise Refusal(
                f"Path scope: tool-state directory in {entry!r} "
                "(.git/.pi/.agents — refused)"
            )
        if entry == "fleet" or entry.startswith("fleet/"):
            raise Refusal(
                f"Path scope: fleet catalog scope {entry!r} "
                "(governance, not slice work — refused)"
            )
        if entry == "scripts" or entry.startswith("scripts/"):
            raise Refusal(
                f"Path scope: tooling scope {entry!r} "
                "(governance, not slice work — refused)"
            )
        if entry.rsplit("/", 1)[-1] == "AGENTS.md":
            raise Refusal(
                f"Path scope: seat-charter scope {entry!r} "
                "(governance, not slice work — refused)"
            )
        if entry.startswith("-"):
            raise Refusal(
                f"Path scope: option-shaped entry {entry!r} (leading dash — refused)"
            )
        if ":" in entry:
            raise Refusal(
                f"Path scope: refspec-shaped entry {entry!r} (colon — refused)"
            )
        if re.search(r"[^\x00-\x7f]", entry):
            raise Refusal(
                f"Path scope: non-ASCII entry {entry!r} (homoglyph risk — refused)"
            )
        if "%" in entry:
            raise Refusal(
                f"Path scope: percent-encoded entry {entry!r} "
                "(encoding trick — refused)"
            )


def _fleet_catalog_path():
    return Path(__file__).resolve().parent.parent / "fleet" / "fleet.yaml"


_FLEET_SETS_CACHE = {}


def fleet_gate_sets(catalog_path=None):
    """(fleet_vocab, tpm_ids): read-only seat vocabulary from fleet.yaml.

    fleet_vocab: every role id, every member/ binding `role:` value, and
    every `session:`/`address:` value plus its @-local-part (lowercased).
    tpm_ids: the subset staffing a tpm/scrum role. Cached per process.
    Fail-closed: an unreadable catalog refuses every envelope (the seats
    cannot be validated, so the operator holds).
    """
    if "sets" in _FLEET_SETS_CACHE:
        return _FLEET_SETS_CACHE["sets"]
    path = Path(catalog_path) if catalog_path is not None else _fleet_catalog_path()
    try:
        import yaml
    except ImportError as exc:
        raise Refusal(
            f"Owning seats: fleet catalog unreadable ({exc}) — "
            "seats cannot be validated — refused"
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise Refusal(
            f"Owning seats: fleet catalog unreadable ({exc}) — "
            "seats cannot be validated — refused"
        )
    if not isinstance(data, dict):
        raise Refusal(
            "Owning seats: fleet catalog unparseable — "
            "seats cannot be validated — refused"
        )
    vocab = set()
    tpm = set()
    roles = data.get("roles", {}) or {}
    if isinstance(roles, dict):
        for role_id, role in roles.items():
            if not isinstance(role_id, str):
                continue
            vocab.add(role_id.lower())
            session = role.get("session") if isinstance(role, dict) else None
            if isinstance(session, str) and session:
                vocab.add(session.lower())
                vocab.add(session.split("@")[0].lower())
            if "tpm" in role_id.lower() or "scrum" in role_id.lower():
                tpm.add(role_id.lower())
                if isinstance(session, str) and session:
                    tpm.add(session.lower())
                    tpm.add(session.split("@")[0].lower())

    def _walk(node):
        if isinstance(node, dict):
            role = node.get("role")
            if isinstance(role, str) and role:
                vocab.add(role.lower())
                tpm_role = "tpm" in role.lower() or "scrum" in role.lower()
                if tpm_role:
                    tpm.add(role.lower())
                for key in ("session", "address"):
                    value = node.get(key)
                    if isinstance(value, str) and value:
                        vocab.add(value.lower())
                        vocab.add(value.split("@")[0].lower())
                        if tpm_role:
                            tpm.add(value.lower())
                            tpm.add(value.split("@")[0].lower())
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for value in node:
                _walk(value)

    _walk(data)
    _FLEET_SETS_CACHE["sets"] = (frozenset(vocab), frozenset(tpm))
    return _FLEET_SETS_CACHE["sets"]


def check_owning_seats(sections):
    text = section_text(require(sections, "owning_seats", "Owning seats"))
    seats = split_entries(text)
    if not seats:
        raise Refusal("Owning seats: no enumerated seats — envelope void on its face")
    vocab, _ = fleet_gate_sets()
    for seat in seats:
        if not SEAT_RE.match(seat):
            raise Refusal(f"Owning seats: malformed seat token {seat!r} — refused")
        # M8 (#92): the seat must exist in the fleet catalog — a standing
        # envelope for a phantom seat is void on its face.
        if seat.lower() not in vocab:
            raise Refusal(
                f"Owning seats: unknown seat {seat!r} — not in fleet.yaml — refused"
            )
    return seats


def check_actions(sections):
    text = section_text(require(sections, "actions", "Permitted operator actions"))
    action_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not action_lines:
        raise Refusal("Permitted operator actions: no enumerated actions — refused")
    for line in action_lines:
        if line == "COMMIT":
            continue
        queue_match = re.match(r"^FILE-QUEUE-ITEM\s+([A-Za-z0-9._-]+)$", line)
        if queue_match:
            continue
        push_match = re.match(r"^PUSH\s+(\S+)$", line)
        if push_match:
            branch = push_match.group(1)
            # M8 (#92): pushing to a protected trunk ref is never envelope
            # work — HEAD was already refused; main/master join it.
            if branch.upper() in ("HEAD", "MAIN", "MASTER"):
                raise Refusal(
                    f"Permitted operator actions: PUSH to trunk ref {branch!r} "
                    "(HEAD/main/master — refused)"
                )
            if (
                branch[:1] in ("+", "-", "/", ".", ":")
                or branch.endswith(("/", ".", ".lock"))
                or ".." in branch
                or ":" in branch
                or re.search(r"[*?\[\]{}!~^\\]", branch)
            ):
                raise Refusal(
                    f"Permitted operator actions: bad branch ref {branch!r} "
                    "(force/refspec/wildcard/dotdot/leading-punctuation — refused)"
                )
            continue
        raise Refusal(
            f"Permitted operator actions: {line!r} is not COMMIT, "
            "FILE-QUEUE-ITEM <queue> or PUSH <branch-ref> — forbidden under any envelope"
        )


def marker_value(text, marker):
    """Value of a `MARKER: value` record line, or None when absent.

    Line-start anchored: optional whitespace, optional numbered prefix
    (`1.`, `2)`, `(a)`), then the marker, then a REQUIRED colon delimiter.
    Embedded marker text mid-record satisfies nothing.
    """
    pattern = re.compile(
        r"^\s*(?:\(\s*[A-Za-z0-9]+\s*\)\s*|\d+\s*[.)]\s*)?"
        + re.escape(marker)
        + r"\s*:\s*(.*)$",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return None


def check_tpm_gate(sections, seats):
    text = section_text(require(sections, "tpm_gate", "TPM verification gate"))
    what = marker_value(text, "WHAT")
    by_whom = marker_value(text, "BY WHOM")
    artifacts = marker_value(text, "ARTIFACTS")
    for marker, value in (
        ("WHAT", what),
        ("BY WHOM", by_whom),
        ("ARTIFACTS", artifacts),
    ):
        if value is None:
            raise Refusal(
                f"TPM verification gate: {marker} record missing — no execution"
            )
    what = marker_value(text, "WHAT")
    by_whom = marker_value(text, "BY WHOM")
    artifacts = marker_value(text, "ARTIFACTS")
    if not what or not artifacts:
        raise Refusal(
            "TPM verification gate: WHAT/ARTIFACTS record empty — no execution"
        )
    if not by_whom:
        raise Refusal("TPM verification gate: BY WHOM verifier unnamed — no execution")
    # M8 (#92): BY WHOM must be the TPM seat or a named human. A void/generic
    # verifier ("nobody") and any fleet seat that is not the TPM seat verify
    # nothing — least of all an owning seat verifying its own work.
    lowered = by_whom.strip().lower()
    if lowered.rstrip(".") in VOID_VERIFIERS:
        raise Refusal(
            f"TPM verification gate: verifier {by_whom!r} names nobody — refused"
        )
    for seat in seats:
        if seat.lower() in lowered:
            raise Refusal(
                f"TPM verification gate: verifier {by_whom!r} is an owning seat "
                "for its own work — refused"
            )
    _, tpm_ids = fleet_gate_sets()
    # The envelope template designates the verifier role as "TPM"; the fleet
    # staffs exactly one tpm/scrum-role seat, so bare "TPM" resolves to it.
    # (If the fleet ever staffs two TPM seats this shorthand turns ambiguous
    # and must be retired — see NOTES.)
    if lowered in tpm_ids or lowered == "tpm":
        return
    vocab, _ = fleet_gate_sets()
    if lowered in vocab:
        raise Refusal(
            f"TPM verification gate: verifier {by_whom!r} is a fleet seat, "
            "not the TPM seat or a named human — refused"
        )
    # Otherwise: a named human — accepted, and recorded in the audit trail.


def check_revocation(sections, revoked):
    text = section_text(require(sections, "revocation", "Revocation")).strip()
    if not text or text.lower() in REVOCATION_VOID_VALUES:
        raise Refusal(
            "Revocation: no revocation channel named — envelope void on its face"
        )
    if revoked:
        raise Refusal("Revocation: revocation issued on the channel — envelope VOID")


def _has_link_token(record):
    """A record is link-shaped when it carries a machine-resolvable reference.

    Definition (recorded; see NOTES): an http(s):// URL, a qitem:// URL, a
    `qitem-<digits>-<hex>` id, a hex run of length >= 7 containing a digit
    (commit/tree SHA), the word "commit" (execution-record reference — the
    template's canonical execution line cites no SHA), or a repo-relative
    path token containing a slash. Bare prose ("filed in the usual place")
    is not link-shaped.
    """
    if re.search(r"https?://\S+|qitem://\S+", record, re.IGNORECASE):
        return True
    if re.search(r"\bqitem-\d+-[0-9a-z]+\b", record, re.IGNORECASE):
        return True
    for match in re.finditer(r"\b[0-9a-f]{7,64}\b", record, re.IGNORECASE):
        if any(ch.isdigit() for ch in match.group(0)):
            return True
    if re.search(r"\bcommit\b", record, re.IGNORECASE):
        return True
    if re.search(r"(?<![\w:])~?[\w][\w.~-]*\/[\w.~\/+-]+", record):
        return True
    return False


def check_audit_trail(sections):
    # M8 (#92): each of the three records must be link-shaped, not merely
    # keyword-shaped. Numbered records split on their markers; unnumbered
    # continuations append to the current record.
    text = section_text(require(sections, "audit_trail", "Audit trail"))
    records = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\d+\s*[.)]\s*|^[-*]\s+", stripped):
            records.append(re.sub(r"^\d+\s*[.)]\s*|^[-*]\s+", "", stripped))
        elif records:
            records[-1] += " " + stripped
        else:
            records.append(stripped)
    need = {"envelope": False, "verif": False, "exec": False}
    for record in records:
        low = record.lower()
        hits = []
        if "envelope" in low:
            hits.append("envelope")
        if "verif" in low:
            hits.append("verif")
        if "execution" in low or "commit" in low:
            hits.append("exec")
        for hit in hits:
            need[hit] = True
        if hits and not _has_link_token(record):
            raise Refusal(
                f"Audit trail: {hits[0]} record is not link-shaped "
                f"({record!r}) — incomplete execution"
            )
    if not need["envelope"]:
        raise Refusal("Audit trail: envelope link missing — incomplete execution")
    if not need["verif"]:
        raise Refusal(
            "Audit trail: TPM verification link missing — incomplete execution"
        )
    if not need["exec"]:
        raise Refusal(
            "Audit trail: execution-record link missing — incomplete execution"
        )


def check_unknown(sections):
    for section in sections:
        if section["key"].startswith("unknown:"):
            raise Refusal(
                f"envelope: unknown section {section['key'][8:]!r} — "
                "template conformance required, refused"
            )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify a PRE-AUTH envelope file.")
    parser.add_argument("--envelope", required=True, help="envelope file to verify")
    parser.add_argument(
        "--at",
        default=None,
        help='reference UTC time "YYYY-MM-DD HH:MMZ" (default: now)',
    )
    parser.add_argument(
        "--consumed",
        action="store_true",
        help="a single-slice execution attempt already happened",
    )
    parser.add_argument(
        "--revoked",
        action="store_true",
        help="a revocation has issued on the revocation channel",
    )
    args = parser.parse_args(argv)

    try:
        now = (
            parse_stamp(args.at, "--at")
            if args.at
            else datetime.datetime.now(datetime.timezone.utc)
        )
    except Refusal as exc:
        print(f"check-envelope: {exc}", file=sys.stderr)
        return 2
    try:
        text = Path(args.envelope).read_text()
    except OSError as exc:
        print(
            f"check-envelope: REFUSE (envelope): unreadable file ({exc}) — operator holds"
        )
        return 1
    try:
        sections = split_sections(text.splitlines())
        check_unknown(sections)
        envelope_id, issued_at = check_identity(sections)
        check_expiry(sections, now, args.consumed, issued_at)
        check_path_scope(sections)
        seats = check_owning_seats(sections)
        check_actions(sections)
        check_tpm_gate(sections, seats)
        check_revocation(sections, args.revoked)
        check_audit_trail(sections)
    except Refusal as exc:
        print(f"check-envelope: REFUSE ({exc}) — operator holds, no execution")
        return 1
    print(f"check-envelope: ACCEPT {envelope_id} — envelope live")
    return 0


if __name__ == "__main__":
    sys.exit(main())
