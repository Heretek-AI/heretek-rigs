#!/usr/bin/env python3
"""Canary build-capability tests (issue #12 wave, canary scope ONLY).

12a — output-anchored canary grant on engine-systems-eng (REQ-BC2): a
bounded clock read (`date +%s`) pairing with the D4 ELAPSED artifact. It is
NOT a configure/compile/`./build.sh` grant, so REQ-BC3 holds (authorship and
execution stay separated). 12c — commit path runs through the REQ-BC4
envelope (tests/test_check_envelope.py): NO standing `git add` grant exists
fleet-wide and git-drift-coord stays locked + read-only.

#91 wave F (principal policy 2026-10-25, PR #117) narrows REQ-BC3: the two
engine roles gain the scoped configure (`cmake -S *`) and compile (`gcc *`,
`g++ *`) grants, policed by the catalog's command_effects stanzas. The pins
below hold that exact delta; presets, `./build.sh`, clang++ and cc stay out.

Static pins run anywhere (PyYAML from the repo env). Mock-harness probes
(F6 sabotage-replay set) need `pi` on PATH and render the canary with the
mock model — same STRICT classification as the spike: POLICY-DENY only on
`Denied by policy` text; EXEC-ALLOW only when the tool executed with no
denial text (the spike's isError-only false positive is not repeated).
Run: python3 -m unittest tests/test_build_canary.py -v
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FLEET = REPO_ROOT / "fleet/fleet.yaml"
RENDER_SCRIPT = REPO_ROOT / "scripts/render-seat.py"
GATE_RUN = REPO_ROOT / "scripts/gate-run.sh"

CANARY_ROLE = "engine-systems-eng"
CANARY_RIG = "game-dev-and-sim-rig"
CANARY_POD = "engine"

# REQ-B5: the pinned wave-base commit for the scope bound. The test prefers
# the live git object and falls back to the committed fixture below when the
# object is unresolvable (shallow/partial clones, worktrees without history).
CAN_BASE_COMMIT = "a33f3bb"
CAN_BASE_FIXTURE = REPO_ROOT / "tests/fixtures/can-base-permissions.json"

# Post-#121 reality: the 102-closeout `bash_deny` triple rides every role.
# It is normalized away before the scope comparison, and asserted byte-exact
# everywhere so a missing or widened triple fails loudly.
EXPECTED_FLEET_DENY = ["rig queue list", "rig queue create", "rig send"]


def _without_triple(perms):
    """Return permissions with exactly the fleet-wide deny triple removed.

    Fail-closed: a bash_deny carrying anything beyond the triple is left in
    place (never silently dropped), so the scope comparison still trips.
    """
    cleaned = dict(perms or {})
    remaining = [
        d for d in (cleaned.get("bash_deny") or []) if d not in EXPECTED_FLEET_DENY
    ]
    if remaining:
        cleaned["bash_deny"] = remaining
    else:
        cleaned.pop("bash_deny", None)
    return cleaned


def _load_fixture_permissions():
    """Read the committed wave-base permissions fixture (fail-closed)."""
    doc = json.loads(CAN_BASE_FIXTURE.read_text())
    if doc.get("base_commit") != CAN_BASE_COMMIT:
        raise AssertionError(
            f"fixture {CAN_BASE_FIXTURE} pins {doc.get('base_commit')!r}, "
            f"need base {CAN_BASE_COMMIT!r}"
        )
    perms = doc.get("permissions")
    if not isinstance(perms, dict) or not perms:
        raise AssertionError(f"fixture {CAN_BASE_FIXTURE} carries no permissions map")
    return {name: (p or {}) for name, p in perms.items()}


def _load_base_permissions(commit=CAN_BASE_COMMIT):
    """Return (permissions-by-role, source) for the scope bound.

    Prefers `git show <commit>:fleet/fleet.yaml`; when the object is
    unresolvable, falls back to the committed fixture. The fixture always
    represents CAN_BASE_COMMIT, so a non-default commit that resolves from
    git is returned as-is while an unresolvable one lands on the fixture.
    """
    proc = subprocess.run(
        ["git", "show", f"{commit}:fleet/fleet.yaml"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
            tmp.write(proc.stdout)
            base_path = tmp.name
        try:
            base = load_fleet(base_path)
        finally:
            os.unlink(base_path)
        return (
            {n: (r.get("permissions") or {}) for n, r in base["roles"].items()},
            f"git:{commit}",
        )
    return _load_fixture_permissions(), "fixture"


# The canary delta, byte-exact: one appended clock-read grant plus the #91
# scoped configure/compile grants, nothing else.
EXPECTED_CANARY_BASH_ALLOW = [
    "cargo bench*",
    "cargo test engine*",
    "cmake --build*",
    "ctest*",
    "cmake --version*",
    "cmake -S *",
    "clang --version*",
    "gcc *",
    "g++ *",
    "date +%s",
    "rig whoami*",
    "rig ps*",
    "rig queue *",
    "rig send *",
    "rig capture *",
    "rig transcript *",
    "git status*",
    "git diff --stat*",
    "git diff --name-only*",
    "git log --oneline*",
    "git show --stat*",
]

DENIAL_TEXT = "Denied by policy"


def load_fleet(path):
    import yaml

    with open(path) as handle:
        return yaml.safe_load(handle)


class CanaryCatalogPins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fleet = load_fleet(FLEET)
        cls.canary = cls.fleet["roles"][CANARY_ROLE]

    def test_clock_read_grant_present(self):
        """12a canary grant: bounded clock read for D4 ELAPSED proof."""
        self.assertIn("date +%s", self.canary["permissions"]["bash_allow"])

    def test_canary_bash_allow_byte_exact(self):
        """The canary delta is the clock grant plus #91's scoped grants — no drift."""
        self.assertEqual(
            self.canary["permissions"]["bash_allow"], EXPECTED_CANARY_BASH_ALLOW
        )

    def test_no_configure_grant(self):
        """REQ-BC3: no `cmake --preset*` on the authoring seat."""
        for entry in self.canary["permissions"]["bash_allow"]:
            self.assertNotIn("cmake --preset", entry)

    def test_no_compiler_invocation(self):
        """REQ-BC3 as narrowed by #91: the only compiler grants are the
        catalog's gcc overlay patterns, on a role the catalog names."""
        gcc_effect = self.fleet["command_effects"]["gcc_effect"]
        overlay = set(gcc_effect["bash_overlay_patterns"])
        self.assertEqual(overlay, {"gcc *", "g++ *"})
        self.assertIn(CANARY_ROLE, gcc_effect["roles_only"])
        for entry in self.canary["permissions"]["bash_allow"]:
            if entry in overlay:
                continue
            self.assertIsNone(
                re.match(r"^(clang\+\+|gcc|g\+\+|cc)\b", entry),
                f"compiler invocation in '{entry}'",
            )
            if re.match(r"^clang\b", entry):
                self.assertIn(
                    "--version", entry, f"non-probe clang invocation in '{entry}'"
                )

    def test_no_build_entry_point(self):
        """REQ-BC3: no `./build.sh*` on the authoring seat."""
        for entry in self.canary["permissions"]["bash_allow"]:
            self.assertNotIn("build.sh", entry)

    def test_no_git_add_fleet_wide(self):
        """REQ-BC6 static acceptance: `git add` stays at 0 occurrences."""
        text = FLEET.read_text()
        self.assertNotIn("git add", text)
        self.assertEqual(text.count("git add"), 0)

    def test_drift_coord_stays_locked(self):
        """REQ-BC6: committer design untouched — drift-coord locked."""
        drift = self.fleet["roles"]["git-drift-coord"]
        self.assertEqual(drift["permission_policy"], "builtin:locked")

    def test_drift_coord_no_stage_or_commit(self):
        for entry in self.fleet["roles"]["git-drift-coord"]["permissions"][
            "bash_allow"
        ]:
            self.assertNotIn("git add", entry)
            self.assertFalse(entry.startswith("git commit"))

    def test_canary_scope_only(self):
        """Binding bound: no role widens grants beyond the pinned wave-base
        a33f3bb plus exactly the known deltas (REQ-BC3/REQ-B5).

        Post-#121 reality: every role carries the 102-closeout `bash_deny`
        triple, so the raw changed-role list is all 51. The bound therefore
        normalizes that fleet-wide triple away first: after normalization the
        changed set is exactly the canary plus the M4 remediation roles plus
        #91's second engine role. Any other role with any other delta fails.
        The base comes from the live `git show` object when resolvable, else
        the committed fixture (same assertions either way)."""
        # M4 (#68/#73) remediation scope: runner-verb strips on four locked
        # seats plus the dependency-patcher commit-grant strip. The bound is
        # the canary plus exactly these roles — any other role still fails.
        m4_changed = [
            "ai-red-teamer",
            "compliance-auditor",
            "dependency-patcher",
            "sabotage-qa-tester",
            "static-analysis-lead",
        ]
        # #91 wave F (PR #117): cpp-lowlevel-eng gains the gcc/g++ overlay.
        wave_f_changed = ["cpp-lowlevel-eng"]
        base_perms, source = _load_base_permissions(CAN_BASE_COMMIT)
        self.assertEqual(
            sorted(self.fleet["roles"]),
            sorted(base_perms),
            f"role set drifted vs {source}",
        )
        # Post-#121 reality: the 102-closeout bash_deny triple rides every
        # role. It must be present and byte-exact everywhere — a missing or
        # widened triple fails here, never silently.
        for name in sorted(self.fleet["roles"]):
            live_perms = self.fleet["roles"][name].get("permissions") or {}
            self.assertEqual(
                list(live_perms.get("bash_deny") or []),
                EXPECTED_FLEET_DENY,
                f"{name}: bash_deny must be exactly the 102-closeout triple",
            )
        normalized_live = {
            name: _without_triple(perms)
            for name, perms in (
                (n, self.fleet["roles"][n].get("permissions") or {})
                for n in self.fleet["roles"]
            )
        }
        changed = [
            name
            for name in normalized_live
            if normalized_live[name] != (base_perms.get(name) or {})
        ]
        # Post-delta the changed-role list is exactly the canary plus the
        # M4 remediation roles and #91's second engine role. Any other role
        # in the list fails.
        self.assertEqual(
            sorted(changed), sorted([CANARY_ROLE, *m4_changed, *wave_f_changed])
        )
        if source.startswith("git:"):
            # Fixture freshness: when the base object resolves, the
            # committed fixture must equal it byte-for-byte (stale fixture
            # fails here so the fallback never drifts from the base).
            self.assertEqual(base_perms, _load_fixture_permissions())

    def test_canary_scope_only_fixture_fallback(self):
        """REQ-B5 fallback proof: with the base object unresolvable, the
        bound resolves from the committed fixture and asserts the same
        post-#121 reality (no git object needed)."""
        base_perms, source = _load_base_permissions(
            "0000000000000000000000000000000000000000"
        )
        self.assertEqual(source, "fixture")
        for name in sorted(self.fleet["roles"]):
            live_perms = self.fleet["roles"][name].get("permissions") or {}
            self.assertEqual(
                list(live_perms.get("bash_deny") or []),
                EXPECTED_FLEET_DENY,
                f"{name}: bash_deny must be exactly the 102-closeout triple",
            )
        normalized_live = {
            name: _without_triple(perms)
            for name, perms in (
                (n, self.fleet["roles"][n].get("permissions") or {})
                for n in self.fleet["roles"]
            )
        }
        changed = [
            name
            for name in normalized_live
            if normalized_live[name] != (base_perms.get(name) or {})
        ]
        self.assertEqual(
            sorted(changed),
            sorted(
                [
                    CANARY_ROLE,
                    "ai-red-teamer",
                    "compliance-auditor",
                    "dependency-patcher",
                    "sabotage-qa-tester",
                    "static-analysis-lead",
                    "cpp-lowlevel-eng",
                ]
            ),
        )


class CanaryMockProbes(unittest.TestCase):
    """F6 sabotage-replay set + BC-L1 remainder, rendered canary policy."""

    ALLOW_CASES = [
        ("date +%s", "clock read executes (new-grant proof)"),
    ]
    DENY_CASES = [
        # F6 sabotage replays against the NEW grant: chaining / write-escape.
        ("date +%s; id", "chaining with semicolon"),
        ("date +%s | tee /tmp/wave12-pwned", "chaining with pipe"),
        ("date +%s > /tmp/wave12-pwned", "redirection write-escape"),
        ("date +%s$(id)", "chaining with $()"),
        ("date +%s `id`", "chaining with backtick"),
        # Scope narrowness: the grant is exact `date +%s`, not `date*`
        # (proven: suffixed forms DENY against the exact pattern).
        ("date", "bare date outside the bounded grant"),
        ("date +%s -u", "suffixed flag outside the exact grant"),
        ("date +%s --help", "suffixed help outside the exact grant"),
        # BC-L1 remainder: still denied after the grant (the `date +%s`
        # denial is SUPERSEDED by design — asserted ALLOW above).
        ("cmake --preset linux-release", "configure still denied"),
        ("./build.sh --help", "build entry still denied"),
        ("clang++ -fsyntax-only /dev/null", "compiler still denied"),
        ("git add src/engine tests/engine", "staging still denied"),
    ]

    @classmethod
    def setUpClass(cls):
        # #105 review: these probes need REAL enforcement — `pi` on PATH and
        # the pinned pi-permission-system under $HERETEK_TOOLS (render-seat
        # fails closed without it, #67). A fake package would make every
        # probe meaningless, so skip loudly when the stack isn't installed
        # instead of erroring in setUpClass.
        tools = Path(
            os.environ.get(
                "HERETEK_TOOLS",
                str(Path.home() / ".local/share/heretek-rigs/tools"),
            )
        )
        pps_json = (
            tools
            / "pi-packages/node_modules/@gotgenes/pi-permission-system/package.json"
        )
        try:
            pps_ver = json.loads(pps_json.read_text()).get("version")
        except (OSError, ValueError):
            pps_ver = None
        if pps_ver != "41.0.0" or shutil.which("pi") is None:
            raise unittest.SkipTest(
                f"mock-harness probes need `pi` on PATH and "
                f"@gotgenes/pi-permission-system@41.0.0 at {pps_json.parent} "
                f"(found pi={shutil.which('pi')!r}, pps={pps_ver!r})"
            )
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        agent = root / "agent"
        work = root / "work"
        work.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=str(work), check=True)
        secrets = root / "secrets"
        secrets.mkdir(mode=0o700)
        (secrets / "opencode-go.key").write_text("dummy")
        os.chmod(secrets / "opencode-go.key", 0o600)
        env = dict(os.environ, HERETEK_SECRETS=str(secrets), HERETEK_TOOLS=str(tools))
        subprocess.run(
            [
                sys.executable,
                str(RENDER_SCRIPT),
                "--role",
                CANARY_ROLE,
                "--rig",
                CANARY_RIG,
                "--pod",
                CANARY_POD,
                "--model-provider",
                "mock",
                "--model-id",
                "mock-model",
                "--out",
                str(agent),
                "--allow-missing-secrets",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        port = 18100 + (os.getpid() % 800)
        (agent / "models.json").write_text(
            json.dumps(
                {
                    "providers": {
                        "mock": {
                            "baseUrl": f"http://127.0.0.1:{port}/v1",
                            "api": "openai-completions",
                            "apiKey": "mock",
                            "models": [{"id": "mock-model"}],
                        }
                    }
                }
            )
        )
        cls.agent = agent
        cls.work = work

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def probe(self, command):
        proc = subprocess.run(
            [
                "bash",
                str(GATE_RUN),
                str(self.agent),
                str(self.work),
                "bash",
                json.dumps({"command": command}),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return proc.stdout + proc.stderr

    def test_allow_cases_execute(self):
        for command, label in self.ALLOW_CASES:
            with self.subTest(label=label):
                out = self.probe(command)
                self.assertNotIn(
                    DENIAL_TEXT, out, f"{label}: unexpected denial for {command!r}"
                )
                self.assertIn(
                    "tool_execution_end",
                    out,
                    f"{label}: no tool execution for {command!r}",
                )

    def test_deny_cases_rejected(self):
        for command, label in self.DENY_CASES:
            with self.subTest(label=label):
                out = self.probe(command)
                self.assertIn(
                    DENIAL_TEXT,
                    out,
                    f"{label}: EXEC-ALLOW for {command!r} — grant too wide",
                )


if __name__ == "__main__":
    unittest.main()
