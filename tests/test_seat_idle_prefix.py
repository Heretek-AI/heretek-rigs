#!/usr/bin/env python3
"""Pre-fix silence evidence for seat idle-park + daemon source (issue #81, S0).

FAIL-ONLY record: on the UNPATCHED tree the #81-pattern fixture (a seat that
claimed a qitem, logged "Handoff received — pulling the queue item", then
parked idle at prompt under a parked-owner-consumer watchdog while holding
1 open obligation, with no work action anywhere) reconciles SILENT (exit 0,
no idle-park signal); the park-to-wake vs work latency spread has no
attribution field anywhere; and a daemon-originated stuck-sweep recovery
handoff labeled `From: operator` passes with the operator label intact (no
distinct daemon source rule in the tree).

This module NEVER asserts live post-fix behavior: the live silence runs are
transcribed verbatim into docs/evidence/81-seat-idle-prefix.md at S0 time,
and the permanent tests below pin (a) that transcript's silence markers,
(b) the fixture shape that makes the silence meaningful (non-vacuous: the
fixture genuinely is claim-then-park with an open obligation and no work),
and (c) zero secret-shaped strings in the evidence. S1's
tests/test_seat_idle.py supersedes the silence with the idle-park
classification; this file stays green before and after (frozen transcript,
live-fixture shape pins).

Fixtures only: every file lands in /tmp scratch, dummy ids only.
Refs #81 (never Closes #81 — the issue stays open for the live-fleet proof).
"""

import json
import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = REPO_ROOT / "docs" / "evidence" / "81-seat-idle-prefix.md"

# Mission-A pattern ids (issue #81 factory audit 2026-10-23/24; hex tails are
# 16 chars so no 40+ bearer-shaped run can appear in transcripts).
IDLE_PARENT = "qitem-20261023213329-7ad896bfc962330d"
RECOVERY_DAEMON = "qitem-recovery-3b06228ed0da95e8"
CLAIM_NOTE = "claimed"
HANDOFF_NOTE = "Handoff received \u2014 pulling the queue item"
WATCHDOG_NOTE = (
    "[OpenRig watchdog scheduler \u00b7 policy: parked-owner-consumer \u2026] "
    "You are parked (arbitrated: idle at prompt) while holding 1 open obligation"
)
IDLE_STATUS = (
    "claimed, 1 open obligation; Handoff received \u2014 pulling the queue item; "
    "parked (arbitrated: idle at prompt)"
)

# Latency spread fixture (issue #81: claim latency 8-31s, close latency
# 22-53s, part of the spread is park-then-wake, not work).
CLAIM_TS = "2026-10-23T21:33:29.000Z"
HANDOFF_TS = "2026-10-23T21:33:37.000Z"
PARK_TS = "2026-10-23T21:34:00.000Z"
WAKE_TS = "2026-10-23T21:34:53.000Z"


def idle_tracker_text():
    """Claim-then-park parent: claim + handoff receipt + parked-at-prompt,
    holding 1 open obligation, no work action."""
    return """\
# Mission Dispatch Tracker (synthetic 81-seat-idle replica)

## Slices
| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| A-parent seat-row | owner-seat | claim recorded | %s | %s |

## Rules (all slices)
No commits by seats.
""" % (IDLE_PARENT, IDLE_STATUS)


def idle_queue_state(tmpdir):
    """Parent in-progress: claimed, handoff receipt, watchdog park line. No
    work action in the trail; the seat holds 1 open obligation."""
    qlist = [
        {
            "qitemId": IDLE_PARENT,
            "state": "in-progress",
            "destinationSession": "owner-seat",
            "tsUpdated": PARK_TS,
        }
    ]
    trans = {
        IDLE_PARENT: [
            {
                "transitionId": 11,
                "qitemId": IDLE_PARENT,
                "ts": CLAIM_TS,
                "state": "in-progress",
                "transitionNote": CLAIM_NOTE,
            },
            {
                "transitionId": 12,
                "qitemId": IDLE_PARENT,
                "ts": HANDOFF_TS,
                "state": "in-progress",
                "transitionNote": HANDOFF_NOTE,
            },
            {
                "transitionId": 13,
                "qitemId": IDLE_PARENT,
                "ts": PARK_TS,
                "state": "in-progress",
                "transitionNote": WATCHDOG_NOTE,
            },
        ]
    }
    list_path = Path(tmpdir) / "queue_list.json"
    trans_path = Path(tmpdir) / "transitions.json"
    list_path.write_text(json.dumps(qlist))
    trans_path.write_text(json.dumps(trans))
    tracker_path = Path(tmpdir) / "mission-dispatch-tracker.md"
    tracker_path.write_text(idle_tracker_text())
    return str(tracker_path), str(list_path), str(trans_path)


def latency_spread():
    """Claim/work/wake timestamps: the park-to-wake spread vs work input
    REQ-I2 attribution consumes (work_ts None: no work action recorded)."""
    return {
        "qitemId": IDLE_PARENT,
        "claim_ts": CLAIM_TS,
        "handoff_ts": HANDOFF_TS,
        "park_ts": PARK_TS,
        "wake_ts": WAKE_TS,
        "work_ts": None,
    }


def daemon_handoff():
    """Stuck-sweep recovery handoff of daemon origin labeled From: operator
    (issue #81 B2 recovery qitem-recovery-3b06228ed0da95e8 pattern)."""
    return {
        "qitemId": RECOVERY_DAEMON,
        "origin": "daemon:stuck-sweep",
        "presented_from": "operator",
        "note": "stuck-sweep recovery: parked owner holds 1 open obligation",
    }


class TestIdleFixtureShapeGenuine(unittest.TestCase):
    def test_parent_is_claim_then_park_with_open_obligation(self):
        """Non-vacuity pin: the fixture really is the #81 pattern — claim
        recorded, handoff receipt, parked-at-prompt watchdog line holding
        an open obligation."""
        self.assertIn("claimed", IDLE_STATUS.lower())
        self.assertIn("handoff received", IDLE_STATUS.lower())
        self.assertIn("idle at prompt", IDLE_STATUS.lower())
        self.assertIn("open obligation", IDLE_STATUS.lower())
        extra_qitems = [q for q in re.findall(r"qitem-\d{14}-[0-9a-f]+", IDLE_STATUS)]
        self.assertEqual(
            extra_qitems,
            [],
            "Status cell names no qitem (the claim lives in the Slice qitem column)",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tracker, _, _ = idle_queue_state(tmp)
            text = Path(tracker).read_text()
            self.assertIn(IDLE_PARENT, text)
            self.assertEqual(
                len(re.findall(r"qitem-\d{14}-[0-9a-f]+", text)),
                1,
                "tracker names only the parent qitem",
            )

    def test_trail_has_no_work_action(self):
        """Non-vacuity pin: the trail is claim + handoff receipt + watchdog
        park only — no verdict, no file, no QA prose (nothing that counts
        as a first work action)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, _, trans_path = idle_queue_state(tmp)
            trans = json.loads(Path(trans_path).read_text())[IDLE_PARENT]
            notes = " \n ".join(t["transitionNote"] for t in trans)
            self.assertIn(CLAIM_NOTE, notes)
            self.assertIn("Handoff received", notes)
            self.assertIn("idle at prompt", notes)
            self.assertIn("1 open obligation", notes)
            for work_token in ("verdict", "QA PASS", "PLACED", "DONE", "filed"):
                self.assertNotIn(
                    work_token,
                    notes,
                    f"trail must carry no work action ({work_token!r} found)",
                )

    def test_latency_spread_has_claim_work_wake_shape(self):
        """Non-vacuity pin: the latency fixture carries claim/park/wake
        timestamps with no work timestamp — the park-to-wake vs work
        spread REQ-I2 measures."""
        spread = latency_spread()
        self.assertEqual(spread["qitemId"], IDLE_PARENT)
        self.assertLess(spread["claim_ts"], spread["park_ts"])
        self.assertLess(spread["park_ts"], spread["wake_ts"])
        self.assertIsNone(spread["work_ts"])

    def test_daemon_handoff_shape_genuine(self):
        """Non-vacuity pin: daemon origin with an operator label — the #9
        trust-model collision REQ-I3 closes."""
        handoff = daemon_handoff()
        self.assertTrue(handoff["origin"].startswith("daemon:"))
        self.assertEqual(handoff["presented_from"], "operator")


class TestPrefixEvidenceFrozen(unittest.TestCase):
    def test_evidence_file_exists(self):
        self.assertTrue(EVIDENCE.is_file(), f"missing {EVIDENCE}")

    def test_evidence_records_idle_park_silence(self):
        """The S0 transcript proves the pre-fix tooling does NOT flag the
        claim-then-park parent idle-park stalled (FAIL-ONLY: exit 0,
        signal absent)."""
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn(IDLE_PARENT, text)
        self.assertIn("reconcile exit: 0", text)
        self.assertIn("idle-park signal: ABSENT", text)

    def test_evidence_records_attribution_absent(self):
        """The S0 transcript proves no park-to-wake vs work attribution
        exists on the unpatched tree (FAIL-ONLY)."""
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("park-to-wake attribution: ABSENT", text)
        self.assertIn(WAKE_TS, text)

    def test_evidence_records_operator_labeled_daemon_handoff(self):
        """The S0 transcript proves the operator-labeled daemon handoff
        passes with the operator label intact (FAIL-ONLY: no distinct
        daemon source rule)."""
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn(RECOVERY_DAEMON, text)
        self.assertIn("daemon source rule: ABSENT", text)
        self.assertIn("recorded source: operator", text)

    def test_evidence_records_daemon_handoff_invocation_result(self):
        """The S0 transcript captures the dummy daemon-origin handoff
        invocation result (FAIL-ONLY: no validator present, so the
        operator label passes through with no relabel) — not marker
        absence alone."""
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("validate_handoff_source present: False", text)
        self.assertIn(
            "handoff invocation result: recorded source operator "
            "(rule ABSENT, no relabel)",
            text,
        )

    def test_evidence_has_no_secret_shaped_strings(self):
        """Mirrors the S0 grep acceptance: no 40+ bearer-shaped runs."""
        text = EVIDENCE.read_text(encoding="utf-8")
        hits = re.findall(r"[A-Za-z0-9_-]{40,}", text)
        self.assertEqual(hits, [], f"unredacted secret-shaped runs: {hits[:3]}")


if __name__ == "__main__":
    unittest.main()
