#!/usr/bin/env python3
"""Unit tests for the regen-gate sanctioned-untracked allowlist (issue #43).

Synthetic git trees in /tmp only — never the live checkout. Covers REQ-RG1
(classified dirt check), REQ-RG2 (allowlist coverage incl. tracked-override)
and REQ-RG3 (classified refusal message), plus the ALLOW_DIRTY escape hatch.
"""

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR = REPO_ROOT / "scripts/generate-rigs.py"

# Every sanctioned stray the gate must ignore (untracked-only).
SANCTIONED_STRAYS = [
    "docs/evidence/session-note.md",
    "docs/reports/stage-report.md",
    ".agents/scratch.json",
    ".claude/state.json",
    ".opencode/loop-transcript.json",
    ".lane/trees/probe/notes.md",
    "openspec/changes/probe-scratch/proposal.md",
    "skills-lock.json",
    "PROMPT_REVIEW.md",
]


def load_gate():
    spec = importlib.util.spec_from_file_location("regen_gate", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GATE = load_gate()


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


class TestRegenGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        git("init", "-q", cwd=self.root)
        git("config", "user.email", "qa@example.test", cwd=self.root)
        git("config", "user.name", "regen-gate-qa", cwd=self.root)
        (self.root / "fleet").mkdir()
        (self.root / "fleet/fleet.yaml").write_text("roles: {}\n")
        # Seed tracked parents so fixtures mirror the real steady state:
        # docs/ and openspec/changes/ are tracked, so strays beneath them
        # surface as collapsed `?? docs/evidence/`-style entries; .agents/,
        # .claude/, .opencode/ and .lane/ stay wholly untracked to exercise
        # the collapsed-dir (`?? .agents/`) matching form.
        (self.root / "docs").mkdir()
        (self.root / "docs/index.md").write_text("seed\n")
        (self.root / "scripts").mkdir()
        (self.root / "scripts/.keep").write_text("seed\n")
        (self.root / "openspec/changes").mkdir(parents=True)
        (self.root / "openspec/changes/.keep").write_text("seed\n")
        git("add", ".", cwd=self.root)
        git("commit", "-qm", "seed", cwd=self.root)
        self.head = git("rev-parse", "HEAD", cwd=self.root).stdout.strip()
        self.assertRegex(self.head, r"^[0-9a-f]{40}$")

    def tearDown(self):
        self.tmp.cleanup()

    def resolve(self, **env):
        old = dict(os.environ)
        os.environ.update({k: v for k, v in env.items() if v is not None})
        for k in env:
            if env[k] is None and k in os.environ:
                del os.environ[k]
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                sha = GATE.resolve_heretek_commit(self.root)
            return sha, out.getvalue(), err.getvalue(), None
        except SystemExit as e:  # noqa: BLE001 - die() exits
            return None, out.getvalue(), err.getvalue(), e.code
        finally:
            os.environ.clear()
            os.environ.update(old)

    def write_strays(self, rels):
        for rel in rels:
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("session scratch\n")

    # REQ-RG1: sanctioned-only dirt resolves.
    def test_sanctioned_strays_only_resolves(self):
        self.write_strays(SANCTIONED_STRAYS)
        sha, out, err, code = self.resolve()
        self.assertEqual(code, None)
        self.assertEqual(sha, self.head)

    # REQ-RG1: tracked modification refuses with exit 2.
    def test_tracked_modification_refuses(self):
        self.write_strays(SANCTIONED_STRAYS)
        (self.root / "fleet/fleet.yaml").write_text("roles: {changed: true}\n")
        sha, out, err, code = self.resolve()
        self.assertEqual(code, 2)
        self.assertIsNone(sha)

    # REQ-RG3 verbatim fidelity: a FIRST-line unstaged modification keeps its
    # leading status space in the refusal (whole-output .strip() would turn
    # ` M ...` into staged-looking `M ...`).
    def test_unstaged_first_line_keeps_leading_space_verbatim(self):
        (self.root / "fleet/fleet.yaml").write_text("roles: {changed: true}\n")
        sha, out, err, code = self.resolve()
        self.assertEqual(code, 2)
        self.assertIsNone(sha)
        lines = err.splitlines()
        matches = [l for l in lines if l.endswith("fleet/fleet.yaml")]
        self.assertEqual(len(matches), 1)
        # 2-space refusal indent + verbatim ` M ` porcelain code (3 spaces
        # before M). A whole-output .strip() would yield `  M ...` (staged).
        self.assertEqual(matches[0], "   M fleet/fleet.yaml")

    # REQ-RG1: non-allowlisted untracked path refuses with exit 2.
    def test_non_allowlisted_untracked_refuses(self):
        self.write_strays(SANCTIONED_STRAYS)
        self.write_strays(["scripts/evil-new-helper.py"])
        sha, out, err, code = self.resolve()
        self.assertEqual(code, 2)
        self.assertIsNone(sha)

    # REQ-RG2 tracked-override: committed-then-edited allowlisted path is dirt.
    def test_committed_allowlisted_path_edit_is_dirt(self):
        (self.root / "docs/evidence").mkdir(parents=True)
        (self.root / "docs/evidence/kept.md").write_text("v1\n")
        git("add", ".", cwd=self.root)
        git("commit", "-qm", "commit evidence", cwd=self.root)
        (self.root / "docs/evidence/kept.md").write_text("v2\n")
        sha, out, err, code = self.resolve()
        self.assertEqual(code, 2)
        self.assertIsNone(sha)

    # REQ-RG3: refusal names blocking lines verbatim + ignored section.
    def test_refusal_classifies_both_sections(self):
        self.write_strays(["docs/evidence/session-note.md"])
        self.write_strays(["scripts/evil-new-helper.py"])
        (self.root / "fleet/fleet.yaml").write_text("roles: {changed: true}\n")
        sha, out, err, code = self.resolve()
        self.assertEqual(code, 2)
        self.assertIn("M fleet/fleet.yaml", err)
        self.assertIn("scripts/evil-new-helper.py", err)
        self.assertIn("docs/evidence", err)
        ignored = err.split("ignored sanctioned")[1]
        self.assertIn("docs/evidence", ignored)
        blocking = err.split("ignored sanctioned")[0]
        self.assertNotIn("docs/evidence", blocking)

    # REQ-RG3: happy path stays silent about dirt.
    def test_clean_run_emits_no_dirt_output(self):
        self.write_strays(SANCTIONED_STRAYS)
        sha, out, err, code = self.resolve()
        self.assertEqual(code, None)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    # Escape hatch unchanged: ALLOW_DIRTY proceeds and records the real SHA.
    def test_allow_dirty_bypass_records_real_sha(self):
        (self.root / "fleet/fleet.yaml").write_text("roles: {changed: true}\n")
        self.write_strays(["scripts/evil-new-helper.py"])
        sha, out, err, code = self.resolve(HERETEK_RIGS_ALLOW_DIRTY="1")
        self.assertEqual(code, None)
        self.assertEqual(sha, self.head)

    # HANDOFF.md-style tracked edit refuses without the escape hatch.
    def test_tracked_handoff_style_edit_refuses(self):
        (self.root / "HANDOFF.md").write_text("live handoff\n")
        git("add", ".", cwd=self.root)
        git("commit", "-qm", "handoff", cwd=self.root)
        (self.root / "HANDOFF.md").write_text("live handoff updated\n")
        self.write_strays(SANCTIONED_STRAYS)
        sha, out, err, code = self.resolve()
        self.assertEqual(code, 2)
        self.assertIn("HANDOFF.md", err)


if __name__ == "__main__":
    unittest.main()
