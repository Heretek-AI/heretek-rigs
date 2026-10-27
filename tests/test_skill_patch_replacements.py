#!/usr/bin/env python3
"""Unit tests for fleet-side skill body-replacement patches (issue #102).

Synthetic fixtures in /tmp only — never the live checkout. Covers the
`replacements:` extension to fleet/skill-patches/ (REQ-CWS): the loader
accepts the new shape, the applier edits vendored sibling docs
exactly-once, and every fail-closed guard (escapes, missing files,
no-ops, unknown keys) dies instead of half-applying. A frontmatter-only
(#101 legacy shape) regression test pins the existing behavior.
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "scripts/generate-rigs.py"


def load_gen():
    spec = importlib.util.spec_from_file_location("gen_rigs_repl", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GEN = load_gen()

SKILL_MD = """\
---
name: probe-skill
description: probe fixture
---

# Probe
"""

DOC_WITH_REF = """\
# Writing Good Tests

Documents that instruct agents are tested by the consuming
agent's behavior (superpowers:writing-skills); prose for humans earns no
test at all.
"""


def make_skill_dir(base: Path, doc_text: str = DOC_WITH_REF) -> Path:
    sdir = base / "probe-skill"
    sdir.mkdir(parents=True)
    (sdir / "SKILL.md").write_text(SKILL_MD)
    (sdir / "writing-good-tests.md").write_text(doc_text)
    return sdir


def write_patch_file(patch_dir: Path, stem: str, body: str) -> None:
    patch_dir.mkdir(parents=True, exist_ok=True)
    (patch_dir / f"{stem}.yaml").write_text(body)


class TestSkillPatchReplacements(unittest.TestCase):
    def test_loader_accepts_replacements_shape(self):
        with tempfile.TemporaryDirectory(prefix="heretek-patch-red-") as tmp:
            root = Path(tmp)
            write_patch_file(
                root / "fleet" / "skill-patches",
                "probe-skill",
                """\
skill: probe-skill
reason: "drop a dangling ref (#102)"
replacements:
  - file: writing-good-tests.md
    old: "behavior (superpowers:writing-skills); prose"
    new: "behavior; prose"
""",
            )
            patches = GEN.load_skill_patches(root)
            self.assertIn("probe-skill", patches)
            rep = patches["probe-skill"]["replacements"]
            self.assertEqual(len(rep), 1)
            self.assertEqual(rep[0]["file"], "writing-good-tests.md")

    def test_apply_replacement_to_sibling_doc(self):
        with tempfile.TemporaryDirectory(prefix="heretek-patch-red-") as tmp:
            sdir = make_skill_dir(Path(tmp))
            GEN.apply_skill_patch(
                "probe-skill",
                sdir,
                {
                    "frontmatter": None,
                    "replacements": [
                        {
                            "file": "writing-good-tests.md",
                            "old": "behavior (superpowers:writing-skills); prose",
                            "new": "behavior; prose",
                        }
                    ],
                },
            )
            text = (sdir / "writing-good-tests.md").read_text()
            self.assertNotIn("superpowers:writing-skills", text)
            self.assertIn("behavior; prose", text)

    def test_double_occurrence_dies(self):
        with tempfile.TemporaryDirectory(prefix="heretek-patch-red-") as tmp:
            sdir = make_skill_dir(
                Path(tmp), DOC_WITH_REF + "\nagain (superpowers:writing-skills).\n"
            )
            with self.assertRaises(SystemExit):
                GEN.apply_skill_patch(
                    "probe-skill",
                    sdir,
                    {
                        "frontmatter": None,
                        "replacements": [
                            {
                                "file": "writing-good-tests.md",
                                "old": "superpowers:writing-skills",
                                "new": "writing-skills-removed",
                            }
                        ],
                    },
                )

    def test_path_escape_dies(self):
        for evil in ("../evil.md", "/abs/evil.md", "sub/../../evil.md", ""):
            with tempfile.TemporaryDirectory(prefix="heretek-patch-red-") as tmp:
                sdir = make_skill_dir(Path(tmp))
                with self.assertRaises(SystemExit, msg=f"escape {evil!r} survived"):
                    GEN.apply_skill_patch(
                        "probe-skill",
                        sdir,
                        {
                            "frontmatter": None,
                            "replacements": [
                                {"file": evil or "x", "old": "a", "new": "b"}
                                if evil
                                else {"file": "", "old": "a", "new": "b"},
                            ],
                        },
                    )

    def test_missing_file_dies(self):
        with tempfile.TemporaryDirectory(prefix="heretek-patch-red-") as tmp:
            sdir = make_skill_dir(Path(tmp))
            with self.assertRaises(SystemExit):
                GEN.apply_skill_patch(
                    "probe-skill",
                    sdir,
                    {
                        "frontmatter": None,
                        "replacements": [
                            {"file": "no-such-doc.md", "old": "a", "new": "b"}
                        ],
                    },
                )

    def test_noop_replacement_dies(self):
        with tempfile.TemporaryDirectory(prefix="heretek-patch-red-") as tmp:
            sdir = make_skill_dir(Path(tmp))
            with self.assertRaises(SystemExit):
                GEN.apply_skill_patch(
                    "probe-skill",
                    sdir,
                    {
                        "frontmatter": None,
                        "replacements": [
                            {
                                "file": "writing-good-tests.md",
                                "old": "behavior",
                                "new": "behavior",
                            }
                        ],
                    },
                )

    def test_unknown_top_level_key_dies(self):
        with tempfile.TemporaryDirectory(prefix="heretek-patch-red-") as tmp:
            root = Path(tmp)
            write_patch_file(
                root / "fleet" / "skill-patches",
                "probe-skill",
                """\
skill: probe-skill
reason: "x"
bogus_key:
  - 1
""",
            )
            with self.assertRaises(SystemExit):
                GEN.load_skill_patches(root)

    def test_frontmatter_only_patch_still_works(self):
        # #101 legacy shape: frontmatter repair of SKILL.md, unchanged.
        with tempfile.TemporaryDirectory(prefix="heretek-patch-red-") as tmp:
            root = Path(tmp)
            write_patch_file(
                root / "fleet" / "skill-patches",
                "probe-skill",
                """\
skill: probe-skill
reason: "quote the description (#101)"
frontmatter:
  description: "probed description"
""",
            )
            patches = GEN.load_skill_patches(root)
            self.assertEqual(
                patches["probe-skill"]["frontmatter"],
                {"description": "probed description"},
            )
            sdir = make_skill_dir(root / "skills")
            GEN.apply_skill_patch("probe-skill", sdir, patches["probe-skill"])
            self.assertIn(
                'description: "probed description"',
                (sdir / "SKILL.md").read_text(),
            )


if __name__ == "__main__":
    unittest.main()
