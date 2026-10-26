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

EXPECTED_42_DENIES = (
    "*--output=*",
    "*--output *",
    "*--output\t*",
    "*--output-junit*",
    "*--output-log*",
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
    def test_terminal_bash_denies_narrowed_42_ordered(self):
        mod = load_render_seat()
        self.assertEqual(tuple(mod.TERMINAL_BASH_DENIES), EXPECTED_42_DENIES)


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


class TestScopedPathValue(unittest.TestCase):
    """REQ-A1: shared flag-value path check (realpath containment + token
    hygiene, no existence requirement). Mirrors pps enforcement posture."""

    def test_in_scope_relative_allows(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            verdict, _ = mod.classify_scoped_path_value(
                "src/foo.c", cwd=ws, path_write=["src/*"]
            )
            self.assertEqual(verdict, "allow-effect")

    def test_dot_and_build_dir_allow(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            for raw in (".", "build", "./sub"):
                with self.subTest(raw=raw):
                    verdict, reason = mod.classify_scoped_path_value(
                        raw, cwd=ws, path_write=["src/*"]
                    )
                    self.assertEqual(verdict, "allow-effect")
                    self.assertTrue(reason)

    def test_deny_directions_hold(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            outsider = Path(ws).parent / "outsider91.txt"
            outsider.write_text("x")
            self.addCleanup(lambda: outsider.unlink(missing_ok=True))
            for raw in [
                "",
                "/etc/passwd",
                "/tmp/abs-escape",
                "../../etc/passwd",
                "sub/../../escape",
                "a;b",
                "x$y",
                "a`b",
                "x$(id)",
                "a\nb",
                "OPENRIG_SESSION_NAME=e",
                str(outsider),
            ]:
                with self.subTest(raw=raw):
                    verdict, reason = mod.classify_scoped_path_value(
                        raw, cwd=ws, path_write=["src/*"]
                    )
                    self.assertEqual(verdict, "deny")
                    self.assertTrue(reason)

    def test_symlink_escape_denies(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            link = Path(ws) / "link.c"
            try:
                link.symlink_to("/etc/hostname")
            except OSError:
                self.skipTest("symlinks unavailable")
            verdict, reason = mod.classify_scoped_path_value(
                "link.c", cwd=ws, path_write=["src/*"]
            )
            self.assertEqual(verdict, "deny")
            self.assertTrue(reason)


class TestGoPackageArg(unittest.TestCase):
    """REQ-A1: Go `...` package-pattern branch — patterns within scope
    allow, never as literal paths; any `..` traversal denies first."""

    def test_package_patterns_allow(self):
        mod = load_render_seat()
        for arg in ("./...", "./pkg/...", "pkg/...", "..."):
            with self.subTest(arg=arg):
                verdict, reason = mod.classify_go_package_arg(arg)
                self.assertEqual(verdict, "allow-effect")
                self.assertTrue(reason)

    def test_traversal_and_absolute_deny(self):
        mod = load_render_seat()
        for arg in (
            "../../etc/...",
            "../...",
            "/abs/...",
            "./a/../b/...",
            "",
            "pkg/...;evil",
            "pkg/...$(id)",
        ):
            with self.subTest(arg=arg):
                verdict, reason = mod.classify_go_package_arg(arg)
                self.assertEqual(verdict, "deny")
                self.assertTrue(reason)

    def test_plain_path_is_not_a_package_pattern(self):
        mod = load_render_seat()
        verdict, _ = mod.classify_go_package_arg("./pkg/foo")
        self.assertEqual(verdict, "not-a-pattern")


class TestCmakePairing(unittest.TestCase):
    """REQ-A1: cmake -S/-B flag-value pairing; values resolved against
    scope roots like any path operand."""

    def test_verbatim_configure_pairs_allow(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            pairs = mod.pair_cmake_flag_values(["cmake", "-S", ".", "-B", "build"])
            self.assertEqual(pairs, [("-S", "."), ("-B", "build")])
            for _flag, value in pairs:
                verdict, _ = mod.classify_scoped_path_value(
                    value, cwd=ws, path_write=["src/engine/*"]
                )
                self.assertEqual(verdict, "allow-effect")

    def test_escape_values_deny(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            for argv in (
                ["cmake", "-S", "../../etc", "-B", "build"],
                ["cmake", "-S", ".", "-B", "/tmp/evil"],
                ["cmake", "-S", ".", "-B", "build;evil"],
            ):
                with self.subTest(argv=argv):
                    pairs = mod.pair_cmake_flag_values(argv)
                    verdicts = [
                        mod.classify_scoped_path_value(
                            v, cwd=ws, path_write=["src/engine/*"]
                        )[0]
                        for _, v in pairs
                    ]
                    self.assertIn("deny", verdicts)

    def test_dangling_flag_denies(self):
        mod = load_render_seat()
        pairs = mod.pair_cmake_flag_values(["cmake", "-S"])
        self.assertEqual(pairs, [("-S", None)])


class TestGccCommand(unittest.TestCase):
    """REQ-A1/A2: gcc -c + source pairing; -o stays in scope; warning
    flags coexist without touching the terminal denies."""

    def test_verbatim_compile_classifies(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            src = Path(ws) / "src" / "foo.c"
            src.parent.mkdir(parents=True)
            src.write_text("int main(void){return 0;}\n")
            verdict, detail = mod.classify_gcc_command(
                ["gcc", "-c", "src/foo.c"], cwd=ws, path_write=["src/*"]
            )
            self.assertEqual(verdict, "allow-effect")
            self.assertIn("src/foo.c", detail)

    def test_wall_coexists_and_o_in_scope_allows(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            verdict, _ = mod.classify_gcc_command(
                ["gcc", "-Wall", "-Wextra", "-c", "src/foo.c", "-o", "src/foo.o"],
                cwd=ws,
                path_write=["src/*"],
            )
            self.assertEqual(verdict, "allow-effect")

    def test_deny_directions_hold(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            for argv in (
                ["gcc", "-c", "../../evil.c"],
                ["gcc", "-c", "/etc/hostname"],
                ["gcc", "-c", "src/foo.c", "-o", "/tmp/evil.o"],
                ["gcc", "-c", "src/foo.c;evil"],
                ["sh", "-c", "evil"],
            ):
                with self.subTest(argv=argv):
                    verdict, reason = mod.classify_gcc_command(
                        argv, cwd=ws, path_write=["src/*"]
                    )
                    self.assertEqual(verdict, "deny")
                    self.assertTrue(reason)

    def test_missing_source_denies(self):
        mod = load_render_seat()
        with tempfile.TemporaryDirectory() as ws:
            verdict, _ = mod.classify_gcc_command(
                ["gcc", "-c"], cwd=ws, path_write=["src/*"]
            )
            self.assertEqual(verdict, "deny")


class TestNativeMapBuilder(unittest.TestCase):
    """REQ-A1: native-map declarations (the M0 winner) per held verbs."""

    def test_pytest_role_declares_read(self):
        mod = load_render_seat()
        m = mod.build_command_effects_map(["pytest tests/rag*", "git status*"])
        self.assertEqual(m, {"pytest": {"effects": "read"}})

    def test_go_role_declares_build_test_with_o_guard(self):
        mod = load_render_seat()
        m = mod.build_command_effects_map(["go build*", "go test*"])
        self.assertEqual(
            m,
            {
                "go": {
                    "unlessOption": ["-o"],
                    "subcommands": {"build": "read", "test": "read"},
                }
            },
        )

    def test_engine_role_declares_cmake_gcc(self):
        mod = load_render_seat()
        m = mod.build_command_effects_map(
            ["cmake -S *", "cmake --build*", "gcc *", "g++ *"]
        )
        self.assertEqual(
            m,
            {
                "cmake": {"effects": "read"},
                "gcc": {"effects": "read", "unlessOption": ["-o"]},
                "g++": {"effects": "read", "unlessOption": ["-o"]},
            },
        )

    def test_ctest_role_declares_read_with_script_guard(self):
        mod = load_render_seat()
        m = mod.build_command_effects_map(["ctest*", "ctest -R physics*"])
        self.assertEqual(
            m,
            {
                "ctest": {
                    "effects": "read",
                    "unlessOption": ["-S", "--script", "--script-new-process"],
                }
            },
        )

    def test_unrelated_verbs_declare_nothing(self):
        mod = load_render_seat()
        self.assertEqual(
            mod.build_command_effects_map(["git status*", "ninja*", "date +%s"]), {}
        )
        self.assertEqual(mod.build_command_effects_map([]), {})


class TestDescriptorsWithVerbs(unittest.TestCase):
    """REQ-A1/A4: audit descriptor list gains per-tool stanzas only for
    held verbs; note/body stay first and byte-identical in shape."""

    def test_empty_verbs_keep_note_body_only(self):
        mod = load_render_seat()
        ids = [e.get("id") for e in mod.build_command_effects([])]
        self.assertEqual(ids, ["note-effect", "body-file-effect"])

    def test_engine_verbs_append_cmake_gcc_descriptors(self):
        mod = load_render_seat()
        descs = mod.build_command_effects(
            ["src/engine/*"], ["cmake -S *", "gcc *", "g++ *", "ctest*"]
        )
        ids = [e.get("id") for e in descs]
        self.assertEqual(
            ids,
            [
                "note-effect",
                "body-file-effect",
                "cmake-effect",
                "gcc-effect",
                "ctest-effect",
            ],
        )
        by_id = {e.get("id"): e for e in descs}
        self.assertNotIn('"ask"', json.dumps(descs))
        self.assertEqual(by_id["gcc-effect"]["overlay"], "after-terminal-denies")

    def test_go_verbs_append_go_descriptor(self):
        mod = load_render_seat()
        ids = [e.get("id") for e in mod.build_command_effects(["pkg/*"], ["go build*"])]
        self.assertEqual(ids, ["note-effect", "body-file-effect", "go-effect"])

    def test_pytest_verbs_append_pytest_descriptor(self):
        mod = load_render_seat()
        ids = [
            e.get("id")
            for e in mod.build_command_effects(["tests/rag/*"], ["pytest tests/rag*"])
        ]
        self.assertEqual(ids, ["note-effect", "body-file-effect", "pytest-effect"])


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
        # #91 migration (deliberate): config.json commandEffects is the
        # native MAP (M0 winner); audit descriptors ride in the sidecar.
        import yaml

        fleet = yaml.safe_load((REPO_ROOT / "fleet/fleet.yaml").read_text())
        checked = 0
        for rid, role in sorted(fleet["roles"].items()):
            allows = role.get("permissions", {}).get("bash_allow", [])
            if not any(str(a).startswith("rig queue") for a in allows):
                continue
            with self.subTest(role=rid):
                rendered = self.render(
                    "--role", rid, "--rig", role["rig"], "--pod", role["pod"]
                )
                cfg = rendered["extensions/pi-permission-system/config.json"]
                effects = cfg.get("commandEffects")
                self.assertIsInstance(effects, dict)
                sidecar = rendered[
                    "extensions/pi-permission-system/command-effects.descriptors.json"
                ]
                self.assertIsInstance(sidecar, list)
                by_id = {e.get("id"): e for e in sidecar}
                note = by_id.get("note-effect")
                body = by_id.get("body-file-effect")
                self.assertIsNotNone(note)
                self.assertIsNotNone(body)
                self.assertEqual(note["match"]["pattern"], "^[A-Za-z0-9 _\\-/.:|]+$")
                self.assertEqual(note["match"]["execModel"], "argv-not-shell")
                self.assertEqual(body["constraints"]["maxBytes"], 262144)
                self.assertTrue(body["constraints"]["regularFileOnly"])
                self.assertTrue(body["constraints"]["noSymlinkEscape"])
                self.assertTrue(body["constraints"]["noDotDotEscape"])
                self.assertTrue(body["constraints"]["noAbsoluteTmp"])
                checked += 1
        self.assertGreater(checked, 0)

    def test_command_effects_carry_no_ask_rule(self):
        rendered = self.render(
            "--role",
            "appsec-engineer",
            "--rig",
            "defensive-sec-and-red-team",
            "--pod",
            "blue",
        )
        cfg = rendered["extensions/pi-permission-system/config.json"]
        sidecar = rendered[
            "extensions/pi-permission-system/command-effects.descriptors.json"
        ]
        self.assertNotIn('"ask"', json.dumps(cfg.get("commandEffects", {})))
        self.assertNotIn('"ask"', json.dumps(sidecar))

    def test_native_map_keys_match_held_verbs(self):
        import yaml

        fleet = yaml.safe_load((REPO_ROOT / "fleet/fleet.yaml").read_text())
        for rid, tools in (
            ("vector-rag-spec", {"pytest"}),
            ("go-backend-eng", {"go"}),
            ("cpp-lowlevel-eng", {"cmake", "gcc", "g++", "ctest"}),
            ("engine-systems-eng", {"cmake", "gcc", "g++", "ctest"}),
            ("appsec-engineer", set()),
        ):
            with self.subTest(role=rid):
                role = fleet["roles"][rid]
                cfg = self.render(
                    "--role", rid, "--rig", role["rig"], "--pod", role["pod"]
                )["extensions/pi-permission-system/config.json"]
                self.assertEqual(set(cfg.get("commandEffects", {}).keys()), tools)

    def test_gcc_overlay_renders_after_terminal_denies(self):
        import yaml

        fleet = yaml.safe_load((REPO_ROOT / "fleet/fleet.yaml").read_text())
        for rid in ("cpp-lowlevel-eng", "engine-systems-eng"):
            with self.subTest(role=rid):
                role = fleet["roles"][rid]
                cfg = self.render(
                    "--role", rid, "--rig", role["rig"], "--pod", role["pod"]
                )["extensions/pi-permission-system/config.json"]
                keys = list(cfg["permission"]["bash"].keys())
                terms = [k for k in keys if k in EXPECTED_42_DENIES]
                self.assertEqual(len(terms), 42)
                for pat in ("gcc *", "g++ *"):
                    self.assertEqual(cfg["permission"]["bash"][pat], "allow")
                    self.assertGreater(keys.index(pat), keys.index(terms[-1]))

    def test_go_path_read_exception_scoped_to_go_roles(self):
        import yaml

        fleet = yaml.safe_load((REPO_ROOT / "fleet/fleet.yaml").read_text())
        role = fleet["roles"]["go-backend-eng"]
        cfg = self.render(
            "--role", "go-backend-eng", "--rig", role["rig"], "--pod", role["pod"]
        )["extensions/pi-permission-system/config.json"]
        self.assertEqual(cfg["permission"].get("path_read"), {"*/...": "allow"})
        role = fleet["roles"]["appsec-engineer"]
        cfg = self.render(
            "--role", "appsec-engineer", "--rig", role["rig"], "--pod", role["pod"]
        )["extensions/pi-permission-system/config.json"]
        self.assertNotIn("path_read", cfg["permission"])


if __name__ == "__main__":
    unittest.main()
