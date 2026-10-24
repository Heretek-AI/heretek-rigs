#!/usr/bin/env python3
"""Corpus tests for #106 commandEffects overlay (REQ-C1/C2/C3, REQ-G1/G2).

New coverage lives in this file alongside — tests/test_render_seat.py
(31-entry corpus) is NOT edited in this change (drift belongs to #102).
"""

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDER_SCRIPT = REPO_ROOT / "scripts/render-seat.py"

EXPECTED_38_DENIES = (
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
    "* -u*",
    "*\t-u*",
    "* -U*",
    "*\t-U*",
    "*--unified*",
    "*--cc*",
    "* -c *",
    "*\t-c *",
    "* -c\t*",
    "*\t-c\t*",
    "* -m *",
    "*\t-m *",
    "* -m\t*",
    "*\t-m\t*",
    "* -W*",
    "*\t-W*",
    "*--function-context*",
    "*--word-diff*",
    "*--color-words*",
    "*--binary*",
    "*--raw*",
    "*OPENRIG_SESSION_NAME=*",
    "*OPENRIG_URL=*",
)

NOTE_ALLOW_SAMPLES = (
    "a/b | c",
    "hello world",
    "v1.0: fix x-y_z",
    "Q3 review / notes | draft staging",
)

NOTE_DENY_SAMPLES = (
    "a;b",
    "price $5",
    "run `id`",
    "x$(id)",
    "line1\nline2",
    "line1\rline2",
    "OPENRIG_SESSION_NAME=evil",
    "OPENRIG_URL=https://evil.example",
    "",
)


def load_render_seat():
    spec = importlib.util.spec_from_file_location("render_seat_ce", RENDER_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCommandEffectsFrozenDenies(unittest.TestCase):
    def test_terminal_bash_denies_still_38_ordered(self):
        mod = load_render_seat()
        self.assertEqual(tuple(mod.TERMINAL_BASH_DENIES), EXPECTED_38_DENIES)


class TestNoteValueEffect(unittest.TestCase):
    def test_allow_pattern_matches_expected_values(self):
        mod = load_render_seat()
        for sample in NOTE_ALLOW_SAMPLES:
            with self.subTest(sample=sample):
                self.assertTrue(mod.is_note_value_allowed(sample))

    def test_deny_directions_hold(self):
        mod = load_render_seat()
        for sample in NOTE_DENY_SAMPLES:
            with self.subTest(sample=sample):
                self.assertFalse(mod.is_note_value_allowed(sample))

    def test_non_string_and_empty_deny(self):
        mod = load_render_seat()
        self.assertFalse(mod.is_note_value_allowed(""))
        self.assertFalse(mod.is_note_value_allowed(None))
        self.assertFalse(mod.is_note_value_allowed(123))


class TestBodyFileEffect(unittest.TestCase):
    def test_pure_classifier_allows_in_scope_regular_sized(self):
        mod = load_render_seat()
        verdict, _ = mod.classify_body_file(
            "notes/body.md",
            cwd_resolved="/seat/ws",
            expanded_roots=["/seat/ws"],
            is_regular_file=True,
            size_bytes=100,
            resolved_path="/seat/ws/notes/body.md",
        )
        self.assertEqual(verdict, "allow-effect")

    def test_pure_classifier_deny_directions(self):
        mod = load_render_seat()
        cases = [
            # (raw, roots, regular, size, resolved)
            ("/etc/passwd", ["/seat/ws"], True, 100, "/etc/passwd"),
            ("prod.env", ["/seat/ws"], True, 100, "/seat/prod.env"),
            ("../../etc/passwd", ["/seat/ws"], True, 100, "/etc/passwd"),
            ("notes/big.md", ["/seat/ws"], True, 262145, "/seat/ws/notes/big.md"),
            ("notes/big.md", ["/seat/ws"], True, None, "/seat/ws/notes/big.md"),
            ("notes/dir", ["/seat/ws"], False, 100, "/seat/ws/notes/dir"),
            ("notes/missing.md", ["/seat/ws"], True, 100, None),
            ("/tmp/escape.md", ["/seat/ws"], True, 100, "/tmp/escape.md"),
            ("/var/tmp/other.md", ["/seat/ws"], True, 100, "/var/tmp/other.md"),
            (
                "notes/link.md",
                ["/seat/ws"],
                True,
                100,
                "/etc/link-target.md",
            ),
        ]
        for raw, roots, regular, size, resolved in cases:
            with self.subTest(raw=raw, resolved=resolved):
                verdict, reason = mod.classify_body_file(
                    raw,
                    cwd_resolved="/seat/ws",
                    expanded_roots=roots,
                    is_regular_file=regular,
                    size_bytes=size,
                    resolved_path=resolved,
                )
                self.assertEqual(verdict, "deny")
                self.assertTrue(reason)

    def test_pid_scratch_root_allows(self):
        mod = load_render_seat()
        verdict, _ = mod.classify_body_file(
            "/var/tmp/seatjail.12345/body.md",
            cwd_resolved="/seat/ws",
            expanded_roots=["/seat/ws", "/var/tmp/seatjail.12345"],
            is_regular_file=True,
            size_bytes=10,
            resolved_path="/var/tmp/seatjail.12345/body.md",
        )
        self.assertEqual(verdict, "allow-effect")

    def test_filesystem_check_in_scope_file_allows(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            target = Path(ws) / "body.md"
            target.write_text("hello")
            verdict, _ = mod.check_body_file_path(
                str(target), cwd=ws, path_write=["docs/*"]
            )
            self.assertEqual(verdict, "allow-effect")

    def test_filesystem_check_deny_directions(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            outsider = Path(ws).parent / "outsider.md"
            outsider.write_text("x")
            self.addCleanup(lambda: outsider.unlink(missing_ok=True))
            cases = [
                "/etc/passwd",
                str(outsider),
                str(Path(ws) / "missing.md"),
                "/tmp/abs-escape.md",
            ]
            link = Path(ws) / "link.md"
            try:
                link.symlink_to("/etc/hostname")
                cases.append(str(link))
            except OSError:
                pass
            big = Path(ws) / "big.md"
            big.write_bytes(b"x" * (262144 + 1))
            cases.append(str(big))
            for raw in cases:
                with self.subTest(raw=raw):
                    verdict, reason = mod.check_body_file_path(
                        raw, cwd=ws, path_write=["docs/*"]
                    )
                    self.assertEqual(verdict, "deny")
                    self.assertTrue(reason)


class TestCommandEffectsRendered(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.secrets = Path(self.tmp_dir.name) / "secrets"
        self.secrets.mkdir(mode=0o700)
        key_file = self.secrets / "opencode-go.key"
        key_file.write_text("dummy")
        os.chmod(key_file, 0o600)
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

    def test_every_queue_capable_role_carries_both_effects(self):
        import yaml

        fleet = yaml.safe_load((REPO_ROOT / "fleet/fleet.yaml").read_text())
        checked = 0
        for rid, role in sorted(fleet["roles"].items()):
            allows = role.get("permissions", {}).get("bash_allow", [])
            if not any(str(a).startswith("rig queue") for a in allows):
                continue
            with self.subTest(role=rid):
                cfg = self.render(
                    "--role", rid, "--rig", role["rig"], "--pod", role["pod"]
                )["extensions/pi-permission-system/config.json"]
                effects = cfg.get("commandEffects")
                self.assertIsInstance(effects, list)
                by_id = {e.get("id"): e for e in effects}
                note = by_id.get("note-effect")
                body = by_id.get("body-file-effect")
                self.assertIsNotNone(note)
                self.assertIsNotNone(body)
                self.assertEqual(note["match"]["pattern"], "^[A-Za-z0-9 _\\-/.:|]+$")
                self.assertEqual(note["match"]["execModel"], "argv-not-shell")
                self.assertEqual(body["constraints"]["maxBytes"], 262144)
                self.assertTrue(body["constraints"]["regularFileOnly"])
                self.assertTrue(body["constraints"]["noSymlinkEscape"])
                checked += 1
        self.assertGreater(checked, 0)

    def test_command_effects_carry_no_ask_rule(self):
        cfg = self.render(
            "--role",
            "appsec-engineer",
            "--rig",
            "defensive-sec-and-red-team",
            "--pod",
            "blue",
        )["extensions/pi-permission-system/config.json"]
        self.assertNotIn('"ask"', json.dumps(cfg.get("commandEffects", [])))


if __name__ == "__main__":
    unittest.main()
