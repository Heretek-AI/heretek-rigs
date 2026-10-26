#!/usr/bin/env python3
"""Unit tests for scripts/audit_sessions.py docs scan (no daemon, no seats)."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "audit_sessions", REPO_ROOT / "scripts/audit_sessions.py"
)
audit_sessions = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_sessions)


class TestFalseDeliveryClaim(unittest.TestCase):
    def scan(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "tracker.md").write_text(text)
            findings = []
            audit_sessions.audit_docs(tmp, findings)
        return findings

    def test_one_qitem_does_not_mask_other_bare_rows(self):
        """#102: a cited id on one row must not clear a bare row below it."""
        findings = self.scan(
            "| T1 | DISPATCHED | qitem-20261024023942-656bab8bcb59ee25 |\n"
            "| T2 | DISPATCHED | (pending) |\n"
        )
        self.assertEqual(len(findings), 1)
        self.assertIn("tracker.md:2:", findings[0])

    def test_every_row_cited_is_clean(self):
        self.assertEqual(
            self.scan(
                "| T1 | DISPATCHED | qitem-a1 |\n| T2 | DISPATCHED | qitem-b2 |\n"
            ),
            [],
        )

    def test_bare_rows_each_flagged(self):
        findings = self.scan("DISPATCHED one\nnothing\nDISPATCHED two\n")
        self.assertEqual(len(findings), 2)


if __name__ == "__main__":
    unittest.main()
