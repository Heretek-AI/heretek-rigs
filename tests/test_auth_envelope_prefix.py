#!/usr/bin/env python3
"""S0 pre-fix silence evidence — 15-auth-envelope (Refs #15, never Closes #15).

FAIL-ONLY record: on the UNPATCHED tree (@ 471f628) the #15-pattern fixture
(an authorized one-liner premise — TPM-verified diff hash + one-liner scope
+ premise/verify timestamps — against a live multi-file drifted landing
record on the queue trail) reconciles SILENT (exit 0, no premise-drift
signal); the premise-age spread has no attribution field anywhere; and no
envelope authorizes or refuses the landing (no envelope module exists).

This module NEVER asserts live post-fix behavior: the live silence runs are
transcribed verbatim into docs/evidence/15-auth-envelope-prefix.md at S0
time, and the permanent tests below pin (a) that transcript's silence
markers, (b) the fixture shape that makes the silence meaningful
(non-vacuous: the fixture genuinely is premise-vs-landing drift with a
premise-age spread), and (c) zero secret-shaped strings in the evidence.
S1/S2's tests/test_auth_envelope.py supersedes the silence with the
premise-drift classification and envelope validation; this file stays
green before and after (frozen transcript, live-fixture shape pins).

Fixtures only: every file lands in /tmp scratch, dummy ids and dummy
16-hex diff hashes only.
"""

import json
import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = REPO_ROOT / "docs" / "evidence" / "15-auth-envelope-prefix.md"

# #15-pattern ids (dummy; 16-hex hashes stay under the 40+ secret floor so
# no 40+ bearer-shaped run can appear in transcripts).
PARENT = "qitem-20261020100001-a1b2c3d4e5f60718"
PREMISE_HASH = "aaaaaaaaaaaaaaaa"
LANDING_HASH = "bbbbbbbbbbbbbbbb"
PREMISE_TS = "2026-10-20T10:00:00.000Z"
VERIFY_TS = "2026-10-20T10:05:00.000Z"
LANDING_TS = "2026-10-20T10:12:00.000Z"

PREMISE_STATUS = (
    "authorized premise %s scope src/include/hash.h; "
    "premise at %s; verified at %s; TPM verified"
    % (PREMISE_HASH, PREMISE_TS, VERIFY_TS)
)
LANDING_NOTE = "landing diff %s paths %s at %s" % (
    LANDING_HASH,
    "src/include/hash.h,src/extra/eleven.c",
    LANDING_TS,
)


def premise_tracker_text():
    """Authorized one-liner premise: TPM-verified hash + one-liner scope +
    premise/verify timestamps (the ae55c83 + #include hash.h order)."""
    return """\
# Mission Dispatch Tracker (synthetic 15-auth-envelope replica)

## Slices
| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| S02 landing slice | owner-seat | hash.h one-liner | %s | %s |

## Rules (all slices)
No commits by seats.
""" % (PARENT, PREMISE_STATUS)


def premise_queue_state(tmpdir):
    """Parent in-progress: claimed, then the multi-file drifted landing
    record (hash differs, paths reach outside the one-liner scope)."""
    qlist = [
        {
            "qitemId": PARENT,
            "state": "in-progress",
            "destinationSession": "owner-seat",
            "tsUpdated": LANDING_TS,
        }
    ]
    trans = {
        PARENT: [
            {
                "transitionId": 61,
                "qitemId": PARENT,
                "ts": PREMISE_TS,
                "state": "in-progress",
                "transitionNote": "claimed",
            },
            {
                "transitionId": 62,
                "qitemId": PARENT,
                "ts": LANDING_TS,
                "state": "in-progress",
                "transitionNote": LANDING_NOTE,
            },
        ]
    }
    qlist_path = Path(tmpdir) / "queue_list.json"
    trans_path = Path(tmpdir) / "transitions.json"
    tracker_path = Path(tmpdir) / "mission-dispatch-tracker.md"
    qlist_path.write_text(json.dumps(qlist))
    trans_path.write_text(json.dumps(trans))
    tracker_path.write_text(premise_tracker_text())
    return str(tracker_path), str(qlist_path), str(trans_path)


def premise_age_spread():
    """Premise/verify/landing timestamps: the staleness spread REQ-E2
    attribution consumes (720s premise age, 420s verify-to-landing)."""
    return {
        "qitemId": PARENT,
        "premise_ts": PREMISE_TS,
        "verify_ts": VERIFY_TS,
        "landing_ts": LANDING_TS,
        "premise_hash": PREMISE_HASH,
        "landing_hash": LANDING_HASH,
    }


class TestPremiseFixtureShapeGenuine(unittest.TestCase):
    def test_tracker_declares_verified_one_liner_premise(self):
        """Non-vacuity pin: the fixture really is an authorized premise —
        TPM-verified hash, one-liner scope, premise + verify timestamps."""
        self.assertIn(PREMISE_HASH, PREMISE_STATUS)
        self.assertIn("src/include/hash.h", PREMISE_STATUS)
        self.assertIn(PREMISE_TS, PREMISE_STATUS)
        self.assertIn(VERIFY_TS, PREMISE_STATUS)
        with tempfile.TemporaryDirectory() as tmp:
            tracker, _, _ = premise_queue_state(tmp)
            text = Path(tracker).read_text()
            self.assertIn(PARENT, text)
            self.assertEqual(
                len(re.findall(r"qitem-\d{14}-[0-9a-f]+", text)),
                1,
                "tracker names only the parent qitem",
            )

    def test_landing_record_is_multi_file_drift(self):
        """Non-vacuity pin: the landing hash differs from the premise hash
        and the landing paths reach outside the one-liner scope."""
        with tempfile.TemporaryDirectory() as tmp:
            _, _, trans_path = premise_queue_state(tmp)
            trans = json.loads(Path(trans_path).read_text())[PARENT]
            notes = " \n ".join(t["transitionNote"] for t in trans)
            self.assertIn(LANDING_HASH, notes)
            self.assertNotIn(PREMISE_HASH, notes)
            self.assertIn("src/extra/eleven.c", notes)
            self.assertNotEqual(PREMISE_HASH, LANDING_HASH)

    def test_premise_age_spread_has_premise_verify_landing_shape(self):
        """Non-vacuity pin: the spread fixture orders premise < verify <
        landing with a genuinely aged premise at landing."""
        spread = premise_age_spread()
        self.assertEqual(spread["qitemId"], PARENT)
        self.assertLess(spread["premise_ts"], spread["verify_ts"])
        self.assertLess(spread["verify_ts"], spread["landing_ts"])
        self.assertNotEqual(spread["premise_hash"], spread["landing_hash"])


class TestPrefixEvidenceFrozen(unittest.TestCase):
    def test_evidence_file_exists(self):
        self.assertTrue(EVIDENCE.is_file(), f"missing {EVIDENCE}")

    def test_evidence_records_premise_drift_silence(self):
        """The S0 transcript proves the pre-fix tooling does NOT flag the
        premise-vs-landing drift (FAIL-ONLY: exit 0, signal absent)."""
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn(PARENT, text)
        self.assertIn("reconcile exit: 0", text)
        self.assertIn("stalled-premise-drift signal: ABSENT", text)

    def test_evidence_records_attribution_absent(self):
        """The S0 transcript proves no premise-age attribution exists on
        the unpatched tree (FAIL-ONLY)."""
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("premise-age attribution: ABSENT", text)
        self.assertIn(LANDING_TS, text)

    def test_evidence_records_envelope_absent(self):
        """The S0 transcript proves no envelope authorizes or refuses the
        landing on the unpatched tree (FAIL-ONLY: no module, no validate)."""
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("envelope validation: ABSENT", text)
        self.assertIn("landing authorization: NONE", text)

    def test_evidence_has_no_secret_shaped_strings(self):
        """Mirrors the S0 grep acceptance: no 40+ bearer-shaped runs."""
        text = EVIDENCE.read_text(encoding="utf-8")
        hits = re.findall(r"[A-Za-z0-9_-]{40,}", text)
        self.assertEqual(hits, [], f"unredacted secret-shaped runs: {hits[:3]}")


if __name__ == "__main__":
    unittest.main()
