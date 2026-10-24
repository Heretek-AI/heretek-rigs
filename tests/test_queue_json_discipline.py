#!/usr/bin/env python3
"""Queue JSON discipline (issues #44 + #42): --json everywhere + parsing wrapper.

- REQ-44-A1: every `rig queue list` / `show` / `create` example in the
  generator charter text, operator guides, and root AGENTS.md carries
  `--json`, plus a "bare output mixes JSON with a human trailer, MUST NOT
  be parsed" statement.
- REQ-42-A1: `rig queue create --json --verify` is the only agent-safe
  create form; guides state bare create output is advisory, not proof of
  persistence.
- REQ-42-A2: scripts/send-authenticated.sh invokes create with the
  agent-safe flags and parses the JSON receipt (qitemId + state),
  failing closed on unparseable stdout.

Hermetic (fake `rig` on PATH; never a live daemon or mutating create).
Run: python3 -m unittest tests/test_queue_json_discipline.py -v
"""

import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "scripts/generate-rigs.py"
WRAPPER = REPO_ROOT / "scripts/send-authenticated.sh"
GUIDE_FILES = [
    GENERATOR,
    REPO_ROOT / "docs/USER_GUIDE.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / "AGENTS.md",
]

READ_OR_CREATE_OP = re.compile(r"rig queue (list|show|create)\b")

CANNED_RECEIPT = (
    '{"qitemId":"qitem-20261022000000-deadbeefdeadbeef",'
    '"state":"pending","persisted":true,'
    '"receipt":{"omitted":[],"fullCommand":"rig queue show '
    "'qitem-20261022000000-deadbeefdeadbeef' --full --json\"}}"
)


def lines_with_matches(path):
    out = []
    for i, line in enumerate(path.read_text().splitlines(), start=1):
        if READ_OR_CREATE_OP.search(line):
            out.append((i, line))
    return out


def run_wrapper(args, rig_stdout, rig_exit=0):
    """Run send-authenticated.sh with a fake `rig` printing rig_stdout."""
    with tempfile.TemporaryDirectory() as tmp:
        bindir = Path(tmp) / "bin"
        bindir.mkdir()
        fake = bindir / "rig"
        # The fake rig ignores its argv and prints exactly rig_stdout.
        fake.write_text(
            "#!/usr/bin/env bash\nprintf '%s' "
            + _shq(rig_stdout)
            + f"\nexit {rig_exit}\n"
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        body = Path(tmp) / "body.txt"
        body.write_text("fixture relay body")
        env = {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"}
        return subprocess.run(
            [
                "bash",
                str(WRAPPER),
                "--destination",
                "exec-exec-director@executive-and-architecture",
                "--body-file",
                str(body),
                "--human-ref",
                "docs/adr/ADR-0042.md",
                *args,
            ],
            capture_output=True,
            text=True,
            env=env,
        )


def _shq(s):
    return "'" + s.replace("'", "'\\''") + "'"


class TestQueueJsonExamples(unittest.TestCase):
    def test_every_queue_example_carries_json(self):
        """REQ-44-A1 + REQ-42-A1: no bare list/show/create example."""
        bare = []
        total = 0
        for path in GUIDE_FILES:
            for lineno, line in lines_with_matches(path):
                total += 1
                if "--json" not in line:
                    bare.append(
                        f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}"
                    )
        self.assertGreater(total, 0, "expected queue examples to pin")
        self.assertEqual(
            bare, [], "bare queue examples without --json:\n" + "\n".join(bare)
        )

    def test_every_create_example_carries_verify(self):
        """REQ-42-A1: create examples use the agent-safe --json --verify form."""
        missing = []
        total = 0
        for path in GUIDE_FILES:
            for lineno, line in lines_with_matches(path):
                if re.search(r"rig queue create\b", line):
                    total += 1
                    if "--verify" not in line:
                        missing.append(
                            f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}"
                        )
        self.assertGreater(total, 0, "expected create examples to pin")
        self.assertEqual(
            missing, [], "create examples without --verify:\n" + "\n".join(missing)
        )

    def test_bare_output_statements_present(self):
        """REQ-44-A1 + REQ-42-A1: MUST-NOT-parse + advisory statements."""
        for path in GUIDE_FILES:
            text = path.read_text()
            self.assertIn(
                "MUST NOT be parsed",
                text,
                f"{path.relative_to(REPO_ROOT)} must state bare output MUST NOT be parsed",
            )
            self.assertIn(
                "not proof of persistence",
                text,
                f"{path.relative_to(REPO_ROOT)} must state bare create is not proof of persistence",
            )


class TestSendAuthenticatedWrapper(unittest.TestCase):
    def test_dry_run_shows_agent_safe_flags(self):
        """REQ-42-A2: --dry-run prints the flagged create invocation."""
        proc = run_wrapper(["--dry-run"], CANNED_RECEIPT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--json", proc.stdout)
        self.assertIn("--verify", proc.stdout)

    def test_json_receipt_parsed_to_qitem_id_and_state(self):
        """REQ-42-A2: valid JSON receipt yields qitemId + state."""
        proc = run_wrapper([], CANNED_RECEIPT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("qitem-20261022000000-deadbeefdeadbeef", proc.stdout)
        self.assertIn("pending", proc.stdout)

    def test_non_json_stdout_fails_closed(self):
        """REQ-42-A2: human/advisory stdout exits non-zero, no delivery claim."""
        proc = run_wrapper(
            [], "Queue create request ID: qitem-abc (not proof of persistence)."
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn("delivered", (proc.stdout + proc.stderr).lower())

    def test_receipt_missing_identity_fails_closed(self):
        """REQ-42-A2: JSON without qitemId/state exits non-zero."""
        proc = run_wrapper([], '{"ok":true}')
        self.assertNotEqual(proc.returncode, 0)

    def test_source_fleet_identity_forms_refused(self):
        """#93 / #105 review: --source can't be a role id or session name."""
        for source in (
            "exec-director",
            "command-exec-director",
            "engine-engine-systems-eng",
            "design-a11y-specialist",
        ):
            with self.subTest(source=source):
                proc = run_wrapper(["--source", source], CANNED_RECEIPT)
                self.assertEqual(proc.returncode, 2, proc.stderr)
                self.assertIn("fleet member/role id", proc.stderr)

    def test_source_operator_label_accepted(self):
        """An operator-side label still sends."""
        proc = run_wrapper(["--source", "operator"], CANNED_RECEIPT)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
