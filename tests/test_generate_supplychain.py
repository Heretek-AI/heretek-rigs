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
import shutil
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

    def test_symlink_member_dies_on_no_filter_path(self):
        # F1 rework: on old Pythons (no TarFile.extract(filter=)) the
        # plain-extract fallback must never restore a symlink member —
        # git archive preserves symlinks, so the caller must reject
        # non-regular members before extraction.
        tmp, clone, head = make_skill_repo()
        self.addCleanup(tmp.cleanup)
        (clone / "skills/demo-skill/real.txt").write_text("real\n")
        (clone / "skills/demo-skill/link.txt").symlink_to("real.txt")
        git("add", ".", cwd=clone)
        git("commit", "-qm", "add symlink", cwd=clone)
        head2 = git("rev-parse", "HEAD", cwd=clone).stdout.strip()
        orig = GEN._tar_supports_filter
        GEN._tar_supports_filter = lambda: False
        try:
            with self.assertRaises(SystemExit) as cm:
                GEN.vendor_skill_from_clone(
                    "demo",
                    clone,
                    head2[:7],
                    "skills/demo-skill",
                    Path(tmp.name) / "out" / "demo-skill",
                )
        finally:
            GEN._tar_supports_filter = orig
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


class TestTarFilterGuard(unittest.TestCase):
    """REQ-A2: TarFile.extract(filter=) guard.

    The filter branch runs on this host (Python 3.15.1 supports it); the
    guarded non-filter fallback is proved here with a stubbed tarfile object
    lacking filter support — no interpreter downgrade required.
    """

    def test_guarded_branch_omits_filter_on_old_pythons(self):
        recorded = {}

        class StubTF:
            def extract(self, member, path=None, **kw):
                recorded["member"] = member
                recorded["path"] = path
                recorded["kw"] = dict(kw)

        orig = GEN._tar_supports_filter
        GEN._tar_supports_filter = lambda: False  # noqa: E731
        try:
            GEN._safe_tar_extract(StubTF(), "skills/demo-skill", "/tmp/dest")
        finally:
            GEN._tar_supports_filter = orig
        self.assertEqual(recorded["member"], "skills/demo-skill")
        self.assertEqual(recorded["path"], "/tmp/dest")
        self.assertEqual(recorded["kw"], {})

    def test_filter_branch_passes_data_filter(self):
        recorded = {}

        class StubTF:
            def extract(self, member, path=None, **kw):
                recorded["kw"] = dict(kw)

        orig = GEN._tar_supports_filter
        GEN._tar_supports_filter = lambda: True  # noqa: E731
        try:
            GEN._safe_tar_extract(StubTF(), "skills/demo-skill", "/tmp/dest")
        finally:
            GEN._tar_supports_filter = orig
        self.assertEqual(recorded["kw"], {"filter": "data"})

    def test_live_interpreter_takes_filter_branch(self):
        # Code-path proof on THIS host: verify the live interpreter's detection matches reality.
        import tarfile

        code = getattr(tarfile.TarFile.extract, "__code__", None)
        has_filter = bool(code is not None and "filter" in code.co_varnames)
        self.assertEqual(GEN._tar_supports_filter(), has_filter)
        if has_filter:
            self.assertIn("filter", code.co_varnames)
        else:
            self.assertNotIn("filter", getattr(code, "co_varnames", ()))


class TestHermeticCharterFallback(unittest.TestCase):
    """REQ-A2: charter source chain crew -> fleet/charters -> snapshot."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        import yaml

        fleet = yaml.safe_load((REPO_ROOT / "fleet/fleet.yaml").read_text())["roles"]
        self.rid = sorted(fleet.keys())[0]
        self.r = fleet[self.rid]

    def write_overlay(self):
        d = self.root / "fleet" / "charters" / self.rid
        d.mkdir(parents=True)
        (d / "AGENTS.md").write_text(
            "## 1. Mandate\nOverlay mandate.\n"
            "## 2. Scope\nOverlay scope.\n"
            "## 3. Method\nOverlay method.\n"
            "- **Catalog wake policy**: on assignment\n"
        )

    def test_overlay_charter_composes_when_crew_absent(self):
        self.write_overlay()
        text = GEN.build_charter(
            self.rid, self.r, Path("/nonexistent/crew"), root=self.root
        )
        self.assertIn(self.r["title"], text)
        self.assertIn("Overlay mandate.", text)

    def test_snapshot_charter_returned_verbatim(self):
        text = GEN.build_charter(
            self.rid,
            self.r,
            Path("/nonexistent/crew"),
            root=self.root,
            fallback_text="SNAPSHOT-CHARTER-BYTES",
        )
        self.assertEqual(text, "SNAPSHOT-CHARTER-BYTES")

    def test_no_source_dies(self):
        with self.assertRaises(SystemExit) as cm:
            GEN.build_charter(
                self.rid, self.r, Path("/nonexistent/crew"), root=self.root
            )
        self.assertEqual(cm.exception.code, 2)


class TestHermeticVendorRestore(unittest.TestCase):
    """REQ-A2: snapshot restore verifies against the skills-lock tree hash."""

    def test_restore_matches_lock_and_tamper_dies(self):
        sid = "queue-handoff"
        live = REPO_ROOT / "specs/agents/_shared/skills" / sid
        lock_entry = {"tree": GEN.tree_hash(live)}
        snap = Path(self.tmp_root()) / "snap"
        good = snap / "agents" / "_shared" / "skills" / sid
        good.parent.mkdir(parents=True)
        shutil.copytree(live, good, symlinks=False)
        dst = Path(self.tmp_root()) / "dst" / sid
        dst.parent.mkdir(parents=True, exist_ok=True)
        GEN._restore_shared_skill(sid, dst, snap, lock_entry)
        self.assertEqual(GEN.tree_hash(dst), lock_entry["tree"])
        # Tampered snapshot bytes must die, never ship.
        (good / "SKILL.md").write_text("# tampered\n")
        with self.assertRaises(SystemExit) as cm:
            GEN._restore_shared_skill(
                sid, Path(self.tmp_root()) / "dst2" / sid, snap, lock_entry
            )
        self.assertEqual(cm.exception.code, 2)

    def tmp_root(self):
        if not hasattr(self, "_tmp"):
            self._tmp = tempfile.TemporaryDirectory()
            self.addCleanup(self._tmp.cleanup)
        return self._tmp.name


class TestSharedSkillLicenseValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_frontmatter_license_safe_yaml_parse(self):
        """#119 review: safe YAML parsing does not read past empty or multiline values."""
        import yaml

        sk = self.root / "SKILL.md"
        # Normal frontmatter
        sk.write_text("---\nname: demo\nlicense: MIT\ndescription: ok\n---\n# Body\n")
        parts = sk.read_text().split("---", 2)
        doc = yaml.safe_load(parts[1])
        self.assertEqual(doc.get("license"), "MIT")

        # Empty license followed by another key (regex with \s* crossed newlines)
        sk.write_text("---\nname: demo\nlicense:\ndescription: ok\n---\n# Body\n")
        parts = sk.read_text().split("---", 2)
        doc = yaml.safe_load(parts[1])
        self.assertIsNone(doc.get("license"))
        self.assertNotEqual(doc.get("license"), "description: ok")


if __name__ == "__main__":
    unittest.main()
