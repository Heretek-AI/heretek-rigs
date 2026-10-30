#!/usr/bin/env python3
"""#78: docs/SEAT-WRITE-SCOPES.md must match fleet/fleet.yaml path_write."""

import subprocess
import sys
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts/seat-scopes.py"


class SeatScopesDoc(unittest.TestCase):
    def test_committed_table_is_current(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_every_seat_and_glob_listed(self):
        doc = (REPO_ROOT / "docs/SEAT-WRITE-SCOPES.md").read_text()
        roles = yaml.safe_load((REPO_ROOT / "fleet/fleet.yaml").read_text())["roles"]
        self.assertEqual(len(roles), 51)
        for role in roles.values():
            seat = role["session"].split("@", 1)[0]
            line = next((ln for ln in doc.splitlines() if ln.startswith(f"| `{seat}` |")), None)
            self.assertIsNotNone(line, seat)
            for glob in role["permissions"]["path_write"]:
                self.assertIn(f"`{glob}`", line, seat)


if __name__ == "__main__":
    unittest.main()
