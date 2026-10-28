#!/usr/bin/env python3
"""Pre-fix silence evidence for mission-row gate ownership (issue #77, S0).

FAIL-ONLY record: on the UNPATCHED tree the B2-pattern fixture (a parent row
with verdict recorded and "Standing by for gate" prose, no gate qitem, no
named gate owner) reconciles SILENT (exit 0, no stalled signal), and a
recovery dismissal against byte-identical row state is ALLOWED (the sweep
carries no refusal guard).

This module NEVER asserts live post-fix behavior: the live silence runs are
transcribed verbatim into docs/evidence/77-mission-gates-prefix.md at S0
time, and the permanent tests below pin (a) that transcript's silence
markers, (b) the fixture shape that makes the silence meaningful
(non-vacuous: the fixture genuinely waits on a gate with no gate row), and
(c) zero secret-shaped strings in the evidence. S1's tests/test_mission_gates.py
supersedes the silence with the stalled classification; this file stays
green before and after (frozen transcript, live-fixture shape pins).

Fixtures only: every file lands in /tmp scratch, dummy ids only.
"""

import json
import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = REPO_ROOT / "docs" / "evidence" / "77-mission-gates-prefix.md"

# B2-pattern ids (issue #77 mission-B2 evidence; hex tails are 16 chars so no
# 40+ bearer-shaped run can appear in transcripts).
B2_PARENT = "qitem-20261024023941-8685741b5ce805de"
B2_VERDICT_NOTE = "verdict recorded, findings filed per t41"
B2_STATUS = "verdict recorded; Standing by for gate"


def b2_tracker_text():
    """Gateless awaiting-gate parent: verdict in, gate prose, no gate row."""
    return """\
# Mission Dispatch Tracker (synthetic B2-pattern replica)

## Slices
| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| B2-parent mission-row | owner-seat | verdict recorded | %s | %s |

## Rules (all slices)
No commits by seats.
""" % (B2_PARENT, B2_STATUS)


def b2_queue_state(tmpdir):
    """Parent still in-progress on the queue side; verdict note landed."""
    qlist = [
        {
            "qitemId": B2_PARENT,
            "state": "in-progress",
            "destinationSession": "owner-seat",
            "tsUpdated": "2026-10-24T02:46:00.000Z",
        }
    ]
    trans = {
        B2_PARENT: [
            {
                "transitionId": 40,
                "qitemId": B2_PARENT,
                "ts": "2026-10-24T02:31:00.000Z",
                "state": "in-progress",
                "transitionNote": "claimed",
            },
            {
                "transitionId": 41,
                "qitemId": B2_PARENT,
                "ts": "2026-10-24T02:39:00.000Z",
                "state": "in-progress",
                "transitionNote": B2_VERDICT_NOTE,
            },
        ]
    }
    list_path = Path(tmpdir) / "queue_list.json"
    trans_path = Path(tmpdir) / "transitions.json"
    list_path.write_text(json.dumps(qlist))
    trans_path.write_text(json.dumps(trans))
    tracker_path = Path(tmpdir) / "mission-dispatch-tracker.md"
    tracker_path.write_text(b2_tracker_text())
    return str(tracker_path), str(list_path), str(trans_path)


def b2_recovery_snapshots():
    """Flag-time vs now snapshots of the flagged parent row state.

    The B2 outcome: the stuck sweep fired, the seat dismissed the recovery
    item, and the parent row never moved — both snapshots byte-identical.
    """
    flagged = {
        "qitemId": B2_PARENT,
        "state": "in-progress",
        "blockedOn": None,
        "destinationSession": "owner-seat",
        "statusCell": B2_STATUS,
    }
    current = dict(flagged)
    return flagged, current


class TestB2FixtureShapeGenuine(unittest.TestCase):
    def test_parent_waits_on_gate_with_no_gate_row(self):
        """Non-vacuity pin: the fixture really is the B2 pattern, so the
        transcribed silence (exit 0, no stalled signal) is meaningful."""
        self.assertIn("gate", B2_STATUS.lower())
        self.assertRegex(B2_STATUS, r"(?i)standing by for gate")
        extra_qitems = [q for q in re.findall(r"qitem-\d{14}-[0-9a-f]+", B2_STATUS)]
        self.assertEqual(
            extra_qitems,
            [],
            "B2 pattern has NO gate qitem reference in the Status cell",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tracker, _, _ = b2_queue_state(tmp)
            text = Path(tracker).read_text()
            self.assertIn(B2_PARENT, text)
            self.assertEqual(
                len(re.findall(r"qitem-\d{14}-[0-9a-f]+", text)),
                1,
                "tracker names only the parent qitem (no gate row)",
            )

    def test_recovery_snapshots_are_byte_identical(self):
        """Non-vacuity pin: the dismissal scenario really is a close with
        zero row state change (the B2 dismissal shape)."""
        flagged, current = b2_recovery_snapshots()
        self.assertEqual(
            json.dumps(flagged, sort_keys=True),
            json.dumps(current, sort_keys=True),
            "flag-time and close-time snapshots must be byte-identical",
        )


class TestPrefixEvidenceFrozen(unittest.TestCase):
    def test_evidence_file_exists(self):
        self.assertTrue(EVIDENCE.is_file(), f"missing {EVIDENCE}")

    def test_evidence_records_reconcile_silence(self):
        """The S0 transcript proves the pre-fix tooling does NOT flag the
        gateless parent stalled (FAIL-ONLY: exit 0, signal absent)."""
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn(B2_PARENT, text)
        self.assertIn("reconcile exit: 0", text)
        self.assertIn("stalled-awaiting-gate signal: ABSENT", text)

    def test_evidence_records_dismissal_allowed(self):
        """The S0 transcript proves dismissal without a row state change
        succeeds on the unpatched tree (FAIL-ONLY: ALLOWED)."""
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("dismissal-without-change: ALLOWED", text)
        self.assertIn("byte-identical", text)

    def test_evidence_has_no_secret_shaped_strings(self):
        """Mirrors the S0 grep acceptance: no 40+ bearer-shaped runs."""
        text = EVIDENCE.read_text(encoding="utf-8")
        hits = re.findall(r"[A-Za-z0-9_-]{40,}", text)
        self.assertEqual(hits, [], f"unredacted secret-shaped runs: {hits[:3]}")


if __name__ == "__main__":
    unittest.main()
