#!/usr/bin/env python3
"""Unit tests for scripts/seed-rig.py stage-time existence gate (#74, REQ-P2).

Read-only: the gate resolves bound MCP commands + bash-grant leading
binaries with shutil.which/path-exists (no installs, no pulls, no network)
and degrades loudly with the same warn shape as the render gate (REQ-P1).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed-rig.py"


class TestSeedStageGate74(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.secrets = Path(self.tmp_dir.name) / "secrets"
        self.secrets.mkdir(mode=0o700)
        key_file = self.secrets / "opencode-go.key"
        key_file.write_text("dummy")
        os.chmod(key_file, 0o600)
        self.tools = Path(self.tmp_dir.name) / "tools"
        pps = self.tools / "pi-packages/node_modules/@gotgenes/pi-permission-system"
        pps.mkdir(parents=True)
        (pps / "package.json").write_text(json.dumps({"version": "41.0.0"}))
        self.empty_bin = Path(self.tmp_dir.name) / "emptybin"
        self.empty_bin.mkdir()
        self.member = Path(self.tmp_dir.name) / "member.yaml"
        self.member.write_text(
            json.dumps({"id": "m1", "agent_ref": "local:roles/binary-reverse-eng"})
        )
        self.base_env = {
            **os.environ,
            "HERETEK_SECRETS": str(self.secrets),
            "HERETEK_TOOLS": str(self.tools),
            "OPENRIG_HOME": "/tmp/hr-openrig",
            "PATH": str(self.empty_bin),
        }

    def seed_proc(self, extra_env=None):
        env = dict(self.base_env)
        env.update(extra_env or {})
        return subprocess.run(
            [
                sys.executable,
                str(SEED_SCRIPT),
                str(self.member),
                "--rig",
                "defensive-sec-and-red-team",
                "--pod",
                "red",
                "--dry-run",
                "--allow-missing-secrets",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_stage_time_missing_tool_warns_with_render_shape(self):
        # Stripped PATH + empty tools dir: r2mcp (radare2) and r2/rabin2
        # must warn naming the seat, the server/grant, and the artifact.
        proc = self.seed_proc()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(
            proc.stderr,
            r"warn: red-m1@defensive-sec-and-red-team: "
            r"radare2.*missing tool artifact.*r2mcp",
        )
        self.assertRegex(
            proc.stderr,
            r"warn: red-m1@defensive-sec-and-red-team: "
            r"bash grant .*missing tool artifact: r2",
        )

    def test_stage_time_present_tool_is_silent(self):
        for binary in ("r2", "rabin2", "tshark"):
            stub = self.empty_bin / binary
            stub.write_text("#!/bin/sh\n")
            stub.chmod(0o755)
        r2mcp_dir = self.tools / "bin"
        r2mcp_dir.mkdir(parents=True)
        (r2mcp_dir / "r2mcp").write_text("#!/bin/sh\n")
        (r2mcp_dir / "r2mcp").chmod(0o755)
        proc = self.seed_proc()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("missing tool artifact: r2", proc.stderr)
        self.assertNotIn("missing tool artifact: rabin2", proc.stderr)
        self.assertNotIn("missing tool artifact: tshark", proc.stderr)
        self.assertNotIn("radare2", proc.stderr)


if __name__ == "__main__":
    unittest.main()
