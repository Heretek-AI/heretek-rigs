#!/usr/bin/env python3
"""Unit tests for M9 supply-chain generator behavior (issues #85, #97, #99).

Synthetic git trees in /tmp only — never the live checkout, never the real
vendor clones. Covers:
  - vendor_skill_from_clone: git-archive vendoring byte-equals the source
    tree, and dies fail-closed on dirty clones / unknown SHAs / missing
    SKILL.md.
  - resolve_run_attestation: real run records ground a "tested" claim;
    absent/malformed records yield "not_tested" with zero record ids.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "scripts/generate-rigs.py"


def load_gen():
    spec = importlib.util.spec_from_file_location("gen_supplychain", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GEN = load_gen()


def git(*args, cwd, env=None):
    base = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(Path(cwd).parent),
    }
    if env:
        base.update(env)
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=base,
    )


def make_skill_repo(skills=("demo-skill",), extra_files=()):
    """Build a synthetic vendor clone: git repo with skills/<id>/SKILL.md."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name) / "clone"
    root.mkdir()
    git("init", "-q", cwd=root)
    git("config", "user.email", "qa@example.test", cwd=root)
    git("config", "user.name", "supplychain-qa", cwd=root)
    for sid in skills:
        sdir = root / "skills" / sid
        sdir.mkdir(parents=True)
        (sdir / "SKILL.md").write_text(f"# {sid}\n\nVendored test skill.\n")
        (sdir / "helper.sh").write_text("#!/bin/sh\necho hi\n")
    for rel, content in extra_files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    git("add", ".", cwd=root)
    git("commit", "-qm", "seed", cwd=root)
    head = git("rev-parse", "HEAD", cwd=root).stdout.strip()
    return tmp, root, head


class TestVendorSkillFromClone(unittest.TestCase):
    def test_archived_skill_bytes_equal_source_tree(self):
        tmp, clone, head = make_skill_repo()
        self.addCleanup(tmp.cleanup)
        dst_parent = Path(tmp.name) / "out"
        dst_parent.mkdir()
        dst = dst_parent / "demo-skill"
        GEN.vendor_skill_from_clone("demo", clone, head[:7], "skills/demo-skill", dst)
        self.assertTrue((dst / "SKILL.md").is_file())
        self.assertEqual(
            (dst / "SKILL.md").read_bytes(),
            (clone / "skills/demo-skill/SKILL.md").read_bytes(),
        )
        self.assertEqual(
            (dst / "helper.sh").read_bytes(),
            (clone / "skills/demo-skill/helper.sh").read_bytes(),
        )

    def test_dirty_clone_dies(self):
        tmp, clone, head = make_skill_repo()
        self.addCleanup(tmp.cleanup)
        (clone / "skills/demo-skill/SKILL.md").write_text("# tampered\n")
        with self.assertRaises(SystemExit) as cm:
            GEN.vendor_skill_from_clone(
                "demo",
                clone,
                head[:7],
                "skills/demo-skill",
                Path(tmp.name) / "out" / "demo-skill",
            )
        self.assertEqual(cm.exception.code, 2)

    def test_unknown_sha_dies(self):
        tmp, clone, head = make_skill_repo()
        self.addCleanup(tmp.cleanup)
        with self.assertRaises(SystemExit) as cm:
            GEN.vendor_skill_from_clone(
                "demo",
                clone,
                "0" * 40,
                "skills/demo-skill",
                Path(tmp.name) / "out" / "demo-skill",
            )
        self.assertEqual(cm.exception.code, 2)

    def test_missing_skill_path_dies(self):
        tmp, clone, head = make_skill_repo()
        self.addCleanup(tmp.cleanup)
        with self.assertRaises(SystemExit) as cm:
            GEN.vendor_skill_from_clone(
                "demo",
                clone,
                head[:7],
                "skills/no-such-skill",
                Path(tmp.name) / "out" / "no-such-skill",
            )
        self.assertEqual(cm.exception.code, 2)


class TestResolveRunAttestation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write_records(self, doc):
        p = self.root / "docs/evidence/run-records.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(doc))

    def test_absent_records_yield_not_tested(self):
        label, ids = GEN.resolve_run_attestation(self.root)
        self.assertEqual(label, "not_tested")
        self.assertEqual(ids, [])

    def test_malformed_records_yield_not_tested(self):
        p = self.root / "docs/evidence/run-records.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{not json")
        label, ids = GEN.resolve_run_attestation(self.root)
        self.assertEqual(label, "not_tested")
        self.assertEqual(ids, [])

    def test_empty_ids_yield_not_tested(self):
        self.write_records({"recordIds": []})
        label, ids = GEN.resolve_run_attestation(self.root)
        self.assertEqual(label, "not_tested")
        self.assertEqual(ids, [])

    def test_real_records_ground_tested_claim(self):
        self.write_records({"recordIds": ["rr-local-001"]})
        label, ids = GEN.resolve_run_attestation(self.root)
        self.assertEqual(label, "tested")
        self.assertEqual(ids, ["rr-local-001"])


if __name__ == "__main__":
    unittest.main()
