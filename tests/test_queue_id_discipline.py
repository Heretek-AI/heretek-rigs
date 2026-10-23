#!/usr/bin/env python3
"""Seat-side qitem ID discipline (issue #37): --json-only ID sources.

Issue #37's truncation premise was refuted live (rig 0.6.13 already emits
full 37-char qitem IDs); the fix is seat-side discipline: copy IDs only from
`--json` output, never retype. These tests pin the doc/generator side:

- REQ-37-A1: the generated seat primer (scripts/generate-rigs.py startup
  context template) shows a `--json` list example plus a never-retype rule.
- REQ-37-A2: every `rig queue list` / `rig queue show` example in the
  operator guides shows `--json`.
- REQ-37-M1: regen carries the primer into every rendered
  `startup/context.md` leaf.

Hermetic (no daemon); run: python3 -m unittest tests/test_queue_id_discipline.py -v
"""

import re
import shlex
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "scripts/generate-rigs.py"
GUIDE_FILES = [
    GENERATOR,
    REPO_ROOT / "docs/USER_GUIDE.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / "AGENTS.md",
]

READ_OP = re.compile(r"rig queue (list|show)\b")
SNIPPET = re.compile(r"`(rig queue [^`]*)`")


def read_lines_with_matches(path):
    """All (lineno, line) pairs in path that show a queue read example."""
    out = []
    for i, line in enumerate(path.read_text().splitlines(), start=1):
        if READ_OP.search(line):
            out.append((i, line))
    return out


class TestJsonOnlyIdSources(unittest.TestCase):
    def test_every_queue_read_example_shows_json(self):
        """REQ-37-A2: no bare `rig queue list` / `show` example in guides."""
        total = 0
        bare = []
        for path in GUIDE_FILES:
            matches = read_lines_with_matches(path)
            total += len(matches)
            for lineno, line in matches:
                if "--json" not in line:
                    bare.append(
                        f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}"
                    )
        self.assertGreater(total, 0, "expected at least one queue read example to pin")
        self.assertEqual(
            bare, [], f"bare queue read examples without --json:\n" + "\n".join(bare)
        )

    def test_charter_example_parses_as_json_invocation(self):
        """REQ-37-A1: generator snippets parse (shlex) with --json as a flag."""
        text = GENERATOR.read_text()
        snippets = SNIPPET.findall(text)
        read_snippets = [s for s in snippets if READ_OP.search(s)]
        self.assertGreater(
            len(read_snippets), 0, "generator must show a queue read example"
        )
        for snippet in read_snippets:
            argv = shlex.split(snippet)
            self.assertIn(
                "--json", argv, f"snippet lacks --json flag token: {snippet!r}"
            )

    def test_charter_states_never_retype_rule(self):
        """REQ-37-A1: the primer states the never-retype-ID rule."""
        text = GENERATOR.read_text()
        self.assertIn(
            "never retype",
            text.lower(),
            "generator must state the never-retype-ID rule",
        )

    def test_regen_carries_primer_into_rendered_leaves(self):
        """REQ-37-M1: every rendered startup/context.md carries the primer."""
        leaves = sorted(REPO_ROOT.glob("specs/**/startup/context.md")) + sorted(
            REPO_ROOT.glob("rigs/**/startup/context.md")
        )
        self.assertGreater(
            len(leaves), 0, "expected rendered startup/context.md leaves"
        )
        missing = [
            str(p.relative_to(REPO_ROOT))
            for p in leaves
            if "rig queue list --json" not in p.read_text()
        ]
        self.assertEqual(missing, [], f"leaves missing the --json primer: {missing}")


if __name__ == "__main__":
    unittest.main()
