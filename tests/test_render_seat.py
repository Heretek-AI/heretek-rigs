#!/usr/bin/env python3
"""Unit tests for scripts/render-seat.py output contract (no daemon, no network)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDER_SCRIPT = REPO_ROOT / "scripts/render-seat.py"


class TestRenderSeat(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.secrets = Path(self.tmp_dir.name) / "secrets"
        self.secrets.mkdir(mode=0o700)
        key_file = self.secrets / "opencode-go.key"
        key_file.write_text("dummy")
        os.chmod(key_file, 0o600)
        # M2 (#67): the permission extension is mandatory — the fixture tools
        # dir carries the pinned pps package.json so renders pass the
        # fail-closed guard (missing/drifted pps is covered by the M2 tests).
        self.tools = Path(self.tmp_dir.name) / "tools"
        pps = self.tools / "pi-packages/node_modules/@gotgenes/pi-permission-system"
        pps.mkdir(parents=True)
        (pps / "package.json").write_text(json.dumps({"version": "41.0.0"}))
        self.env = {
            **os.environ,
            "HERETEK_SECRETS": str(self.secrets),
            "HERETEK_TOOLS": str(self.tools),
            "OPENRIG_HOME": "/tmp/hr-openrig",
        }

    def tearDown(self):
        self.tmp_dir.cleanup()

    def render(self, *args):
        proc = subprocess.run(
            [
                sys.executable,
                str(RENDER_SCRIPT),
                *args,
                "--dry-run",
                "--allow-missing-secrets",
            ],
            cwd=str(REPO_ROOT),
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(proc.stdout)

    def test_appsec_auth_is_command_backed_key(self):
        f = self.render(
            "--role",
            "appsec-engineer",
            "--rig",
            "defensive-sec-and-red-team",
            "--pod",
            "blue",
        )
        self.assertEqual(
            f["auth.json"],
            {
                "opencode-go": {
                    "type": "api_key",
                    "key": f"!cat {self.secrets / 'opencode-go.key'}",
                }
            },
        )

    def test_appsec_settings_pin_model_thinking_and_permission_package(self):
        s = self.render(
            "--role",
            "appsec-engineer",
            "--rig",
            "defensive-sec-and-red-team",
            "--pod",
            "blue",
        )["settings.json"]
        self.assertEqual(s["defaultProvider"], "opencode-go")
        self.assertEqual(s["defaultModel"], "muse-spark-1.3-contributor")
        self.assertEqual(s["defaultThinkingLevel"], "high")
        self.assertEqual(
            s["packages"],
            [
                str(
                    self.tools
                    / "pi-packages/node_modules/@gotgenes/pi-permission-system"
                )
            ],
        )
        self.assertIn("tool_search", s["defaultTools"])

    def test_settings_shellpath_routes_through_seat_sandbox(self):
        s = self.render(
            "--role",
            "sabotage-qa-tester",
            "--rig",
            "qa-and-verification-gauntlet",
            "--pod",
            "qa",
        )["settings.json"]
        self.assertTrue(s["shellPath"].endswith("scripts/seat-sandbox.sh"))
        self.assertTrue(Path(s["shellPath"]).is_file())
        self.assertTrue(os.access(s["shellPath"], os.X_OK))

    def test_sandbox_env_carries_normalized_write_roots_and_secret_store(self):
        f = self.render(
            "--role",
            "sabotage-qa-tester",
            "--rig",
            "qa-and-verification-gauntlet",
            "--pod",
            "qa",
        )
        env_lines = dict(
            line.split("=", 1) for line in f["sandbox.env"].strip().splitlines()
        )
        # Bind-normalized: trailing /* stripped to literal jail dirs.
        self.assertEqual(env_lines["HERETEK_SANDBOX_WRITE"], "tests/chaos:docs/qa")
        self.assertEqual(env_lines["HERETEK_SECRET_STORE"], str(self.secrets))

    def test_appsec_permission_config_fails_closed_and_ends_path_write_with_dot_dot_guard(
        self,
    ):
        c = self.render(
            "--role",
            "appsec-engineer",
            "--rig",
            "defensive-sec-and-red-team",
            "--pod",
            "blue",
        )["extensions/pi-permission-system/config.json"]
        self.assertEqual(c["permission"]["*"], "deny")
        self.assertEqual(c["permission"]["bash"]["*"], "deny")
        # HR-5.5-prefix-escape: terminal bash denies must be present LAST so
        # live --output/chaining suffixes cannot escape an allowed prefix.
        # HR-5.5-enforcement-gap: `&`/backtick/`$`/parens denies added.
        # HR-5.5-git-patch-read-bypass: patch-output flag denies added (`-p`,
        # `--patch`, `--full-diff`, `--textconv`) so `git log -p` / `git show
        # --patch` past a `fleet/*` read-deny are denied even on allowed
        # git prefixes.
        for _td in (
            "*--output*",
            "*;*",
            "*|*",
            "*>*",
            "*<*",
            "*&*",
            "*`*",
            "*$*",
            "*(*",
            "*)*",
            "* -p*",
            "*\t-p*",
            "*--patch*",
            "*--full-diff*",
            "*--textconv*",
            # M5 (#69) git-diff read-bypass family + (#72) env-forgery forms.
            "* -u*",
            "*\t-u*",
            "* -U*",
            "*\t-U*",
            "*--unified*",
            "*--cc*",
            "* -c *",
            "* -m *",
            "* -W*",
            "*--function-context*",
            "*--word-diff*",
            "*--color-words*",
            "*--binary*",
            "*--raw*",
            "*OPENRIG_SESSION_NAME=*",
            "*OPENRIG_URL=*",
        ):
            self.assertEqual(c["permission"]["bash"][_td], "deny")
        self.assertEqual(c["permission"]["external_directory"], "deny")
        self.assertEqual(c["promptTimeoutMs"], 60000)
        keys = list(c["permission"]["path_write"].keys())
        self.assertEqual(keys[0], "*")
        self.assertEqual(keys[-1], "*..*")
        self.assertEqual(
            keys,
            [
                "*",
                "docs/security/advisories/*",
                ".git/*",
                "*/.git/*",
                "AGENTS.md",
                "*/AGENTS.md",
                ".pi/*",
                "*/.pi/*",
                ".agents/*",
                "*/.agents/*",
                "fleet/*",
                "scripts/*",
                "*..*",
            ],
        )
        self.assertEqual(
            c["permission"]["path_write"]["docs/security/advisories/*"], "allow"
        )
        self.assertEqual(
            c["permission"]["mcp"],
            {"*": "deny", "semgrep": "allow", "codebase-memory": "allow"},
        )
        self.assertEqual(c["permission"]["ast_grep"], "allow")
        self.assertEqual(c["permission"]["code_rewrite"], "deny")
        self.assertEqual(c["permission"]["lsp_rename"], "deny")
        self.assertEqual(c["permission"]["lsp_code_actions"], "deny")
        # HR-5.3: credential-bearing URL/user suffixes must be denied too.
        self.assertEqual(c["permission"]["path"]["*.url"], "deny")
        self.assertEqual(c["permission"]["path"]["*.user"], "deny")
        # HR-5.2: the read map carries the same guard block as path_write.
        self.assertEqual(
            list(c["permission"]["path"].keys()),
            [
                "*",
                "*.env",
                "*.env.*",
                "*.env.example",
                "*.pem",
                "*.key",
                "*id_rsa*",
                "*kubeconfig*",
                "*/secrets/*",
                ".git/*",
                "*/.git/*",
                "AGENTS.md",
                "*/AGENTS.md",
                ".pi/*",
                "*/.pi/*",
                ".agents/*",
                "*/.agents/*",
                "fleet/*",
                "scripts/*",
                "*.pat",
                "*.uri",
                "*.profile",
                "*.region",
                "*.host",
                "*.password",
                "*.credentials",
                "*.config",
                "*.url",
                "*.user",
                "*..*",
            ],
        )
        self.assertNotIn('"ask"', json.dumps(c))

    def test_product_director_github_readonly_and_disabled_without_pat(self):
        m = self.render(
            "--role",
            "product-director",
            "--rig",
            "executive-and-architecture",
            "--pod",
            "exec",
        )["mcp.json"]["mcpServers"]
        self.assertEqual(
            m["github"]["url"], "https://api.githubcopilot.com/mcp/x/issues/readonly"
        )
        self.assertEqual(m["github"]["enabled"], False)
        self.assertRegex(
            m["github"]["headers"]["Authorization"],
            r"^!echo Bearer \$\(cat .*github\.pat\)$",
        )

    def test_missing_secret_without_allow_missing_secrets_is_hard_error(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(RENDER_SCRIPT),
                "--role",
                "product-director",
                "--rig",
                "executive-and-architecture",
                "--pod",
                "exec",
                "--dry-run",
            ],
            cwd=str(REPO_ROOT),
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertRegex(proc.stderr, r"github needs .*github\.pat")

    def test_world_readable_key_file_is_refused(self):
        key_file = self.secrets / "opencode-go.key"
        os.chmod(key_file, 0o644)
        proc = subprocess.run(
            [
                sys.executable,
                str(RENDER_SCRIPT),
                "--role",
                "appsec-engineer",
                "--rig",
                "defensive-sec-and-red-team",
                "--pod",
                "blue",
                "--dry-run",
            ],
            cwd=str(REPO_ROOT),
            env=self.env,
            capture_output=True,
            text=True,
        )
        os.chmod(key_file, 0o600)
        self.assertEqual(proc.returncode, 2)
        self.assertRegex(proc.stderr, r"is mode 644; run: chmod 600")

    def test_ids_with_dots_are_refused(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(RENDER_SCRIPT),
                "--role",
                "appsec-engineer",
                "--rig",
                "x",
                "--pod",
                "blue.team",
                "--dry-run",
            ],
            cwd=str(REPO_ROOT),
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertRegex(proc.stderr, r"must not contain")

    def test_missing_pps_is_hard_error_despite_allow_missing_secrets(self):
        env = {**self.env, "HERETEK_TOOLS": "/nonexistent-hr-tools"}
        proc = subprocess.run(
            [
                sys.executable,
                str(RENDER_SCRIPT),
                "--role",
                "exec-director",
                "--rig",
                "executive-and-architecture",
                "--pod",
                "exec",
                "--dry-run",
                "--allow-missing-secrets",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertRegex(proc.stderr, r"@gotgenes/pi-permission-system is mandatory")

    def test_drifted_pps_version_is_hard_error(self):
        pps_pkg = (
            self.tools
            / "pi-packages/node_modules/@gotgenes/pi-permission-system/package.json"
        )
        pps_pkg.write_text(json.dumps({"version": "40.0.0"}))
        proc = subprocess.run(
            [
                sys.executable,
                str(RENDER_SCRIPT),
                "--role",
                "exec-director",
                "--rig",
                "executive-and-architecture",
                "--pod",
                "exec",
                "--dry-run",
                "--allow-missing-secrets",
            ],
            cwd=str(REPO_ROOT),
            env=self.env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertRegex(proc.stderr, r"version 40\.0\.0, need 41\.0\.0")


if __name__ == "__main__":
    unittest.main()
