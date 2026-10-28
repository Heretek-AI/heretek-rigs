#!/usr/bin/env python3
"""Corpus tests for 107-identity M1: seed-time per-seat grant issuance + render.

No live daemon needed: the `rig` CLI is faked with a stateful python script in
/tmp scratch (0700 dirs, 0600 files, dummy tokens only); render tests use
synthetic --fleet/--charter fixtures plus the real committed catalog entry.
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RENDER_SCRIPT = REPO_ROOT / "scripts/render-seat.py"
SEED_SCRIPT = REPO_ROOT / "scripts/seed-rig.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RENDER_MOD = load_module("render_seat_107m1", RENDER_SCRIPT)
SEED_MOD = load_module("seed_rig_107m1", SEED_SCRIPT)

FAKE_RIG_SRC = """#!/usr/bin/env python3
import json, os, sys
state_path = os.environ["FAKE_RIG_STATE"]
log_path = os.environ["FAKE_RIG_LOG"]
with open(log_path, "a") as fh:
    fh.write("rig " + " ".join(sys.argv[1:]) + "\\n")
try:
    with open(state_path) as fh:
        state = json.load(fh)
except FileNotFoundError:
    state = {"grants": {}, "counter": 0}
for _gname, _g in list(state.get("grants", {}).items()):
    if isinstance(_g, str):
        state["grants"][_gname] = {"seat": _g, "rigs": [], "roots": [],
                                    "workspace": False, "owner": False}
args = sys.argv[1:]
if args[:3] == ["mcp", "token", "list"]:
    print(json.dumps({
        "configured": True,
        "file": state_path,
        "grants": [
            {"name": n, "seat": g["seat"], "rigs": g["rigs"], "roots": g["roots"],
             "workspace": g["workspace"], "owner": g["owner"],
             "createdAt": "2026-10-27T00:00:00.000Z"}
            for n, g in sorted(state["grants"].items())
        ],
    }))
elif args[:3] == ["mcp", "token", "add"]:
    if os.environ.get("FAKE_RIG_LEAK_ADD") == "1":
        print("token add failed: internal error bearer " + "Q" * 47, file=sys.stderr)
        sys.exit(1)
    if os.environ.get("FAKE_RIG_FAIL_ADD") == "1":
        print("fake rig: add failed", file=sys.stderr)
        sys.exit(1)
    name = args[3]
    rest = args[4:]
    def flag_vals(key):
        return [rest[i + 1] for i, a in enumerate(rest)
                if a == key and i + 1 < len(rest)]
    seat_vals = flag_vals("--seat")
    seat = seat_vals[0] if seat_vals else ""
    rigs = flag_vals("--rig")
    roots = flag_vals("--root")
    workspace = "--workspace" in rest
    owner = "--owner" in rest
    if name in state["grants"]:
        print(f"'{name}' already has a grant; revoke it first to issue a new token")
        sys.exit(1)
    state["counter"] += 1
    token = "fakegrantsessiontoken%06d" % state["counter"]
    state["grants"][name] = {"seat": seat, "rigs": rigs, "roots": roots,
                             "workspace": workspace, "owner": owner}
    with open(state_path, "w") as fh:
        json.dump(state, fh)
    print(f"Token for {name}, shown once (only its hash is kept in {state_path}):")
    print(token)
    print(f"The client sends it as: Authorization: Bearer <token>. Revoke it with: rig mcp token revoke {name}")
elif args[:3] == ["mcp", "token", "revoke"]:
    name = args[3]
    if name not in state["grants"]:
        print(f"No grant named {name}.")
        sys.exit(1)
    del state["grants"][name]
    with open(state_path, "w") as fh:
        json.dump(state, fh)
    print(f"Revoked {name}: its next request is refused. Its rows and records stay.")
else:
    print("fake rig: unknown argv %r" % (args,), file=sys.stderr)
    sys.exit(2)
"""


class IssuanceHelperTests(unittest.TestCase):
    def test_token_filename_is_verbatim_session_with_key_suffix(self):
        self.assertEqual(
            RENDER_MOD.seat_grant_token_filename("blue-appsec@red-team"),
            "mcp-http-blue-appsec@red-team.key",
        )

    def test_parse_valid_once_printed_output(self):
        out = (
            "Token for blue-x@rig-y, shown once (only its hash is kept in /tmp/x.json):\n"
            "fakegrantsessiontoken000001\n"
            "The client sends it as: Authorization: Bearer <token>. "
            "Revoke it with: rig mcp token revoke blue-x@rig-y\n"
        )
        self.assertEqual(
            SEED_MOD.parse_issued_token(out, "blue-x@rig-y"),
            "fakegrantsessiontoken000001",
        )

    def test_parse_rejects_garbage(self):
        self.assertIsNone(SEED_MOD.parse_issued_token("", "blue-x@rig-y"))
        self.assertIsNone(
            SEED_MOD.parse_issued_token("some other output\n", "blue-x@rig-y")
        )
        self.assertIsNone(
            SEED_MOD.parse_issued_token(
                "Token for blue-x@rig-y, shown once:\nnot a token!!!\n", "blue-x@rig-y"
            )
        )

    def test_parse_rejects_wrong_grant_name(self):
        out = (
            "Token for evil-seat, shown once (only its hash is kept in /tmp/x.json):\n"
            "fakegrantsessiontoken000001\n"
            "The client sends it as: Authorization: Bearer <token>.\n"
        )
        self.assertIsNone(SEED_MOD.parse_issued_token(out, "blue-x@rig-y"))


class IssueSeatGrantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.secrets = self.root / "secrets"
        self.secrets.mkdir(mode=0o700)
        self.fake_rig = self.root / "fake-rig"
        self.fake_rig.write_text(FAKE_RIG_SRC)
        self.fake_rig.chmod(0o700)
        self.state = self.root / "token-state.json"
        self.log = self.root / "rig.log"
        self.env = {
            "FAKE_RIG_STATE": str(self.state),
            "FAKE_RIG_LOG": str(self.log),
        }
        self._old_env = dict(os.environ)
        os.environ.update(self.env)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)

    def issue(self, session, allow_missing=False, rig_bin=None, rig="rig-y"):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = SEED_MOD.issue_seat_grant(
                session,
                str(self.secrets),
                rig_bin=str(rig_bin or self.fake_rig),
                allow_missing_secrets=allow_missing,
                rig=rig,
            )
        return rc, out.getvalue(), err.getvalue()

    def token_path(self, session):
        return self.secrets / RENDER_MOD.seat_grant_token_filename(session)

    def test_fresh_add_stores_token_0600(self):
        rc, _, _ = self.issue("blue-x@rig-y")
        self.assertEqual(rc, 0)
        p = self.token_path("blue-x@rig-y")
        self.assertTrue(p.is_file())
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
        body = p.read_text()
        self.assertRegex(body, r"^[A-Za-z0-9_-]{16,}$")
        state = json.loads(self.state.read_text())
        grant = state["grants"].get("blue-x@rig-y")
        self.assertIsInstance(grant, dict)
        self.assertEqual(grant.get("seat"), "blue-x@rig-y")

    def test_add_scopes_grant_to_managed_rig(self):
        rc, _, _ = self.issue("blue-x@rig-y")
        self.assertEqual(rc, 0)
        log = self.log.read_text()
        self.assertIn("token add blue-x@rig-y --seat blue-x@rig-y --rig rig-y", log)
        state = json.loads(self.state.read_text())
        grant = state["grants"].get("blue-x@rig-y")
        self.assertEqual(grant.get("rigs"), ["rig-y"])
        self.assertEqual(grant.get("roots"), [])
        self.assertFalse(grant.get("workspace"))
        self.assertFalse(grant.get("owner"))

    def test_reuse_requires_matching_grant_metadata(self):
        self.state.write_text(
            json.dumps(
                {
                    "grants": {
                        "blue-x@rig-y": {
                            "seat": "evil@rig-y",
                            "rigs": [],
                            "roots": [],
                            "workspace": False,
                            "owner": False,
                        }
                    },
                    "counter": 0,
                }
            )
        )
        stale = self.token_path("blue-x@rig-y")
        stale.write_text("stalebearer FOR-TEST-ONLY-0001")
        os.chmod(stale, 0o600)
        rc, _, _ = self.issue("blue-x@rig-y")
        self.assertEqual(rc, 0)
        log = self.log.read_text()
        self.assertIn("token revoke blue-x@rig-y", log)
        self.assertIn("token add blue-x@rig-y --seat blue-x@rig-y --rig rig-y", log)
        fresh_body = self.token_path("blue-x@rig-y").read_text()
        self.assertNotEqual(fresh_body, "stalebearer FOR-TEST-ONLY-0001")
        state = json.loads(self.state.read_text())
        self.assertEqual(state["grants"]["blue-x@rig-y"]["seat"], "blue-x@rig-y")

    def test_reuse_rejects_scope_widened_grant(self):
        self.state.write_text(
            json.dumps(
                {
                    "grants": {
                        "blue-x@rig-y": {
                            "seat": "blue-x@rig-y",
                            "rigs": ["other-rig"],
                            "roots": [],
                            "workspace": False,
                            "owner": False,
                        }
                    },
                    "counter": 0,
                }
            )
        )
        self.token_path("blue-x@rig-y").write_text("stalebearer FOR-TEST-ONLY-0002")
        os.chmod(self.token_path("blue-x@rig-y"), 0o600)
        rc, _, _ = self.issue("blue-x@rig-y")
        self.assertEqual(rc, 0)
        log = self.log.read_text()
        self.assertIn("token revoke blue-x@rig-y", log)
        state = json.loads(self.state.read_text())
        self.assertEqual(state["grants"]["blue-x@rig-y"]["rigs"], ["rig-y"])

    def test_permissive_existing_file_is_rejected_before_add(self):
        p = self.token_path("blue-x@rig-y")
        p.write_text("attacker-planted FOR-TEST-ONLY-0003")
        os.chmod(p, 0o644)
        rc, _, err = self.issue("blue-x@rig-y")
        self.assertNotEqual(rc, 0)
        self.assertNotIn("token add", self.log.read_text())
        self.assertIn("blue-x@rig-y", err)
        self.assertEqual(p.read_text(), "attacker-planted FOR-TEST-ONLY-0003")
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o644)

    def test_permissive_existing_file_degrades_loudly_with_opt_out(self):
        p = self.token_path("blue-x@rig-y")
        p.write_text("attacker-planted FOR-TEST-ONLY-0004")
        os.chmod(p, 0o644)
        rc, _, err = self.issue("blue-x@rig-y", allow_missing=True)
        self.assertEqual(rc, 0)
        self.assertNotIn("token add", self.log.read_text())
        self.assertIn("warn", err)
        state = (
            json.loads(self.state.read_text())
            if self.state.exists()
            else {"grants": {}}
        )
        self.assertNotIn("blue-x@rig-y", state.get("grants", {}))

    def test_rerun_is_idempotent_without_re_add(self):
        self.assertEqual(self.issue("blue-x@rig-y")[0], 0)
        first_body = self.token_path("blue-x@rig-y").read_text()
        self.assertEqual(self.issue("blue-x@rig-y")[0], 0)
        self.assertEqual(self.token_path("blue-x@rig-y").read_text(), first_body)
        adds = [l for l in self.log.read_text().splitlines() if "token add" in l]
        self.assertEqual(len(adds), 1)

    def test_grant_without_file_heals_via_revoke_and_re_add(self):
        self.assertEqual(self.issue("blue-x@rig-y")[0], 0)
        first_body = self.token_path("blue-x@rig-y").read_text()
        self.token_path("blue-x@rig-y").unlink()
        rc, _, _ = self.issue("blue-x@rig-y")
        self.assertEqual(rc, 0)
        second_body = self.token_path("blue-x@rig-y").read_text()
        self.assertTrue(second_body)
        self.assertNotEqual(second_body, first_body)
        log = self.log.read_text()
        self.assertIn("token revoke blue-x@rig-y", log)

    def test_add_failure_output_bearer_is_redacted_in_log(self):
        os.environ["FAKE_RIG_LEAK_ADD"] = "1"
        rc, _, err = self.issue("blue-x@rig-y")
        self.assertNotEqual(rc, 0)
        self.assertIn("token add failed", err)
        self.assertNotRegex(err, r"[A-Za-z0-9_-]{40,}")
        self.assertFalse(self.token_path("blue-x@rig-y").exists())

    def test_add_failure_output_bearer_redacted_when_degraded(self):
        os.environ["FAKE_RIG_LEAK_ADD"] = "1"
        rc, _, err = self.issue("blue-x@rig-y", allow_missing=True)
        self.assertEqual(rc, 0)
        self.assertIn("warn", err)
        self.assertIn("token add failed", err)
        self.assertNotRegex(err, r"[A-Za-z0-9_-]{40,}")
        self.assertFalse(self.token_path("blue-x@rig-y").exists())

    def test_add_failure_is_fatal_in_strict_mode(self):
        os.environ["FAKE_RIG_FAIL_ADD"] = "1"
        rc, _, err = self.issue("blue-x@rig-y")
        self.assertNotEqual(rc, 0)
        self.assertFalse(self.token_path("blue-x@rig-y").exists())
        self.assertIn("blue-x@rig-y", err)

    def test_add_failure_degrades_with_allow_missing_secrets(self):
        os.environ["FAKE_RIG_FAIL_ADD"] = "1"
        rc, _, err = self.issue("blue-x@rig-y", allow_missing=True)
        self.assertEqual(rc, 0)
        self.assertFalse(self.token_path("blue-x@rig-y").exists())
        self.assertIn("warn", err)

    def test_missing_rig_binary_fails_closed_or_degrades(self):
        rc, _, _ = self.issue("blue-x@rig-y", rig_bin="/nonexistent/rig-107")
        self.assertNotEqual(rc, 0)
        rc, _, err = self.issue(
            "blue-x@rig-y", allow_missing=True, rig_bin="/nonexistent/rig-107"
        )
        self.assertEqual(rc, 0)
        self.assertIn("warn", err)


class SeatNeedsGrantTests(unittest.TestCase):
    CATALOG = {
        "rig-mcp-http": {"transport": "http", "seat_grant": True},
        "memory": {"transport": "stdio"},
    }

    def test_bound_role_needs_grant(self):
        role = {"mcp": [{"server": "rig-mcp-http"}, {"server": "memory"}]}
        self.assertTrue(SEED_MOD.seat_needs_grant(role, self.CATALOG))

    def test_unbound_role_needs_no_grant(self):
        role = {"mcp": [{"server": "memory"}]}
        self.assertFalse(SEED_MOD.seat_needs_grant(role, self.CATALOG))
        self.assertFalse(SEED_MOD.seat_needs_grant({"mcp": []}, self.CATALOG))
        self.assertFalse(SEED_MOD.seat_needs_grant({}, self.CATALOG))
        self.assertFalse(SEED_MOD.seat_needs_grant(None, self.CATALOG))

    def test_explicit_opt_in_issues_without_binding(self):
        role = {"mcp": [{"server": "memory"}]}
        self.assertTrue(SEED_MOD.seat_needs_grant(role, self.CATALOG, opt_in=True))
        self.assertFalse(SEED_MOD.seat_needs_grant(role, self.CATALOG, opt_in=False))


def _write_probe_fleet(tmpdir):
    fleet = {
        "model": {
            "api": "openai-responses",
            "base_url": "https://opencode.ai/inference/go/v1",
            "context_window": 1048576,
            "max_tokens": 131072,
        },
        "rigs": [{"id": "test-rig", "pods": [{"id": "blue"}]}],
        "roles": {
            "probe-role": {
                "thinking": "high",
                "permission_policy": "builtin:standard",
                "permissions": {
                    "path_write": ["tests/*"],
                    "bash_allow": ["rig queue list --json*"],
                },
                "mcp": [{"server": "rig-mcp-http"}],
            },
            "plain-role": {
                "thinking": "high",
                "permission_policy": "builtin:standard",
                "permissions": {
                    "path_write": ["tests/*"],
                    "bash_allow": ["rig queue list --json*"],
                },
                "mcp": [],
            },
        },
    }
    fleet_path = Path(tmpdir) / "fleet.yaml"
    import yaml

    fleet_path.write_text(yaml.safe_dump(fleet))
    charter = Path(tmpdir) / "charter.md"
    charter.write_text("# probe charter\n")
    return fleet_path, charter


class RenderSeatGrantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.secrets = self.root / "secrets"
        self.secrets.mkdir(mode=0o700)
        key_file = self.secrets / "opencode-go.key"
        key_file.write_text("dummy")
        os.chmod(key_file, 0o600)
        # 09-send-identity S1: bound roles also render send-identity.json, so
        # the fixture secrets dir carries a sender binding alongside the
        # grant token (both seed-issued under the same gate).
        import importlib.util as _ilu09

        _spec09 = _ilu09.spec_from_file_location(
            "send_identity_fixture_09",
            Path(__file__).resolve().parent.parent / "scripts/send_identity.py",
        )
        _mod09 = _ilu09.module_from_spec(_spec09)
        _spec09.loader.exec_module(_mod09)
        binding_file = self.secrets / _mod09.sender_binding_filename(
            "blue-probe-role@test-rig"
        )
        binding_file.write_text("dummybindingsecret FOR-TEST-ONLY-107M1")
        os.chmod(binding_file, 0o600)
        self.tools = self.root / "tools"
        pps = self.tools / "pi-packages/node_modules/@gotgenes/pi-permission-system"
        pps.mkdir(parents=True)
        (pps / "package.json").write_text(json.dumps({"version": "41.0.0"}))
        self.fleet_path, self.charter = _write_probe_fleet(str(self.root))
        self.env = {
            **os.environ,
            "HERETEK_SECRETS": str(self.secrets),
            "HERETEK_TOOLS": str(self.tools),
            "OPENRIG_HOME": "/tmp/hr-openrig-107m1",
        }

    def render(self, role, *extra):
        return subprocess.run(
            [
                sys.executable,
                str(RENDER_SCRIPT),
                "--role",
                role,
                "--rig",
                "test-rig",
                "--pod",
                "blue",
                "--fleet",
                str(self.fleet_path),
                "--mcp",
                str(REPO_ROOT / "fleet/mcp-servers.yaml"),
                "--charter",
                str(self.charter),
                "--dry-run",
                *extra,
            ],
            cwd=str(REPO_ROOT),
            env=self.env,
            capture_output=True,
            text=True,
        )

    def test_bound_role_renders_bearer_header_from_token_file(self):
        session = "blue-probe-role@test-rig"
        token_file = self.secrets / RENDER_MOD.seat_grant_token_filename(session)
        token_file.write_text("dummybearer FOR-TEST-ONLY-0001")
        os.chmod(token_file, 0o600)
        proc = self.render("probe-role")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        entry = json.loads(proc.stdout)["mcp.json"]["mcpServers"]["rig-mcp-http"]
        self.assertEqual(entry["url"], "http://127.0.0.1:7437/mcp")
        self.assertEqual(
            entry["headers"],
            {"Authorization": f"!echo Bearer $(cat {token_file})"},
        )
        self.assertNotIn("enabled", entry)

    def test_missing_token_file_is_fatal_in_strict_mode(self):
        proc = self.render("probe-role")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("mcp-http-blue-probe-role@test-rig.key", proc.stderr)

    def test_missing_token_file_degrades_with_allow_missing_secrets(self):
        proc = self.render("probe-role", "--allow-missing-secrets")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        entry = json.loads(proc.stdout)["mcp.json"]["mcpServers"]["rig-mcp-http"]
        self.assertEqual(entry["enabled"], False)

    def test_unbound_role_renders_no_grant_server(self):
        proc = self.render("plain-role", "--allow-missing-secrets")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["mcp.json"], {"mcpServers": {}})


class CatalogStructureTests(unittest.TestCase):
    def test_grant_server_catalog_shape_and_opt_in_default(self):
        import yaml

        catalog = yaml.safe_load((REPO_ROOT / "fleet/mcp-servers.yaml").read_text())[
            "servers"
        ]
        entry = catalog.get("rig-mcp-http")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.get("transport"), "http")
        self.assertEqual(entry.get("url_template"), "http://127.0.0.1:7437/mcp")
        self.assertTrue(entry.get("seat_grant"))
        self.assertNotIn("latest", str(entry.get("pin", "")))
        self.assertNotIn("env", entry)
        self.assertNotIn("headers", entry)
        self.assertEqual(entry.get("exposure"), "deferred")
        fleet = yaml.safe_load((REPO_ROOT / "fleet/fleet.yaml").read_text())
        bound = [
            rid
            for rid, r in fleet.get("roles", {}).items()
            for b in (r.get("mcp") or [])
            if b.get("server") == "rig-mcp-http"
        ]
        self.assertEqual(bound, [])


class RotationRunbookStep3Tests(unittest.TestCase):
    RUNBOOK = REPO_ROOT / "docs/evidence/107-identity-rotation.md"

    def step3_region(self):
        lines = self.RUNBOOK.read_text().splitlines()
        start = next(
            (i for i, l in enumerate(lines) if l.startswith("3. Mint the replacement")),
            None,
        )
        end = next(
            (i for i, l in enumerate(lines) if l.startswith("4. Redistribute")),
            None,
        )
        self.assertIsNotNone(start, "runbook step-3 anchor missing")
        self.assertIsNotNone(end, "runbook step-4 anchor missing")
        self.assertLess(start, end, "runbook step anchors out of order")
        return "\n".join(lines[start:end])

    def test_step3_mints_with_rig_scope_and_no_rigless_form(self):
        step3 = self.step3_region()
        cmds = re.findall(r"`rig mcp token add[^`]*`", step3)
        self.assertTrue(
            any("--seat" in c and "--rig" in c for c in cmds),
            "runbook step 3 must mint with --seat AND --rig (rig-scoped replacement)",
        )
        for c in cmds:
            self.assertIn(
                "--rig",
                c,
                f"runbook step 3 must not carry a rig-less mint form (got {c!r})",
            )


if __name__ == "__main__":
    unittest.main()
