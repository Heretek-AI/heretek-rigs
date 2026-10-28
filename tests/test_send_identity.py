#!/usr/bin/env python3
"""Corpus tests for 09-send-identity S1: grant-bound sender attestation + relay verify.

Covers all four REQ-S2 forgery classes (spoofed --source ignored, replay
rejected, cross-rig impersonation impossible, bare-send bypass still denied)
plus the S1.1 issuance discipline (scope seat+rig, 0600 mkstemp+replace,
fail-closed parse, revoke-on-fail) and the REQ-S1 render rule (!cat
reference, never an inline secret).

No live daemon needed: the `rig` CLI is faked with a stateful python script in
/tmp scratch (0700 dirs, 0600 files, dummy tokens only); render tests use
synthetic --fleet/--charter fixtures plus the real committed catalog entry.
Secrets discipline: dummy keys only; every log assertion also asserts no
[A-Za-z0-9_-]{40,} bearer-shaped run leaks.
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
SEND_IDENTITY_SCRIPT = REPO_ROOT / "scripts/send_identity.py"
RENDER_SCRIPT = REPO_ROOT / "scripts/render-seat.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SEND_MOD = load_module("send_identity_09", SEND_IDENTITY_SCRIPT)
RENDER_MOD = load_module("render_seat_09", RENDER_SCRIPT)

BEARER_RUN_RE = re.compile(r"[A-Za-z0-9_-]{40,}")

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
    token = "fakesendidentitytoken%06d" % state["counter"]
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
    print(f"Revoked {name}.")
else:
    print("fake rig: unknown command", file=sys.stderr)
    sys.exit(2)
"""


class BindingNameRuleTests(unittest.TestCase):
    def test_binding_filename_embeds_session_with_key_suffix(self):
        fn = SEND_MOD.sender_binding_filename("blue-probe@test-rig")
        self.assertEqual(fn, "send-id-blue-probe@test-rig.key")

    def test_binding_filename_has_no_path_separators(self):
        for session in ("blue-probe@test-rig", "a-b@c"):
            fn = SEND_MOD.sender_binding_filename(session)
            self.assertNotIn("/", fn)
            self.assertNotIn("..", fn)

    def test_binding_filename_rejects_session_with_path_separator(self):
        for hostile in ("blue/probe@test-rig", "blue-probe@test/rig", "..@x"):
            with self.assertRaises(ValueError, msg=hostile):
                SEND_MOD.sender_binding_filename(hostile)

    def test_binding_grant_name_scopes_sender_with_suffix(self):
        name = SEND_MOD.sender_binding_grant_name("blue-probe@test-rig")
        self.assertEqual(name, "blue-probe@test-rig/send-identity")
        self.assertIn("blue-probe@test-rig", name)


class IssueSenderBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.secrets = self.root / "secrets"
        self.secrets.mkdir(mode=0o700)
        self.state = self.root / "fake-state.json"
        self.log = self.root / "fake-rig.log"
        self.state.write_text(json.dumps({"grants": {}, "counter": 0}))
        self.log.write_text("")
        self.fake_rig = self.root / "rig"
        self.fake_rig.write_text(FAKE_RIG_SRC)
        self.fake_rig.chmod(0o700)
        for key in ("FAKE_RIG_LEAK_ADD", "FAKE_RIG_FAIL_ADD"):
            os.environ.pop(key, None)
        self._old_env = dict(os.environ)
        os.environ["FAKE_RIG_STATE"] = str(self.state)
        os.environ["FAKE_RIG_LOG"] = str(self.log)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)

    def binding_path(self, session):
        return self.secrets / SEND_MOD.sender_binding_filename(session)

    def issue(self, session, rig="rig-y", **kw):
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            rc = SEND_MOD.issue_sender_binding(
                session, str(self.secrets), rig_bin=str(self.fake_rig), rig=rig, **kw
            )
        return rc, buf_out.getvalue(), buf_err.getvalue()

    def test_issue_mints_with_seat_and_rig_scope(self):
        rc, out, err = self.issue("blue-x@rig-y")
        self.assertEqual(rc, 0)
        body = self.binding_path("blue-x@rig-y").read_text()
        self.assertRegex(body, r"^fakesendidentitytoken\d{6}$")
        self.assertNotIn(body, out)
        self.assertNotIn(body, err)
        self.assertIsNone(BEARER_RUN_RE.search(out))
        self.assertIsNone(BEARER_RUN_RE.search(err))
        add_lines = [l for l in self.log.read_text().splitlines() if "token add" in l]
        self.assertEqual(len(add_lines), 1)
        self.assertIn("--seat blue-x@rig-y", add_lines[0])
        self.assertIn("--rig rig-y", add_lines[0])
        st = os.stat(self.binding_path("blue-x@rig-y"))
        self.assertTrue(stat.S_ISREG(st.st_mode))
        self.assertEqual(stat.S_IMODE(st.st_mode), 0o600)

    def test_issue_reuses_matching_grant_and_file(self):
        self.assertEqual(self.issue("blue-x@rig-y")[0], 0)
        first_body = self.binding_path("blue-x@rig-y").read_text()
        rc, out, _ = self.issue("blue-x@rig-y")
        self.assertEqual(rc, 0)
        self.assertIn("already issued", out)
        self.assertEqual(self.binding_path("blue-x@rig-y").read_text(), first_body)
        adds = [l for l in self.log.read_text().splitlines() if "token add" in l]
        self.assertEqual(len(adds), 1)

    def test_reuse_path_emits_no_token_material(self):
        # Rework-2 (CodeQL py/clear-text-logging-sensitive-data): the
        # "already issued" reuse path must emit neither the stored token
        # bytes nor any bearer-shaped run on stdout/stderr.
        self.assertEqual(self.issue("blue-x@rig-y")[0], 0)
        body = self.binding_path("blue-x@rig-y").read_text()
        self.assertTrue(body)
        rc, out, err = self.issue("blue-x@rig-y")
        self.assertEqual(rc, 0)
        self.assertIn("already issued", out)
        self.assertNotIn(body, out)
        self.assertNotIn(body, err)
        self.assertIsNone(BEARER_RUN_RE.search(out))
        self.assertIsNone(BEARER_RUN_RE.search(err))

    def test_scope_mismatch_heals_via_revoke_and_re_add(self):
        self.assertEqual(self.issue("blue-x@rig-y", rig="rig-y")[0], 0)
        first_body = self.binding_path("blue-x@rig-y").read_text()
        rc, _, _ = self.issue("blue-x@rig-y", rig="rig-other")
        self.assertEqual(rc, 0)
        second_body = self.binding_path("blue-x@rig-y").read_text()
        self.assertTrue(second_body)
        self.assertNotEqual(second_body, first_body)
        self.assertIn("token revoke blue-x@rig-y/send-identity", self.log.read_text())

    def test_unparseable_issuance_output_revokes_and_fails(self):
        os.environ["FAKE_RIG_LEAK_ADD"] = "1"
        rc, _, err = self.issue("blue-x@rig-y")
        self.assertNotEqual(rc, 0)
        self.assertFalse(self.binding_path("blue-x@rig-y").exists())
        self.assertIsNone(BEARER_RUN_RE.search(err))

    def test_existing_non_0600_store_refuses_pre_mint(self):
        target = self.binding_path("blue-x@rig-y")
        target.write_text("dummy")
        # Non-0600 on purpose (pre-mint refusal fixture): 0640 is group-
        # readable but NOT world-readable (CodeQL py/overly-permissive-file).
        os.chmod(target, 0o640)
        rc, _, err = self.issue("blue-x@rig-y")
        self.assertNotEqual(rc, 0)
        self.assertIn("0600", err)
        grants = json.loads(self.state.read_text())["grants"]
        self.assertNotIn("blue-x@rig-y/send-identity", grants)

    def test_reuse_path_refuses_non_0600_binding(self):
        # Reuse must apply the same 0600 regular-file gate as pre-mint:
        # seed once (0600, reuse reports success), chmod to 0640 externally,
        # re-run -> must FAIL loudly naming the file, not report reuse success.
        self.assertEqual(self.issue("blue-x@rig-y")[0], 0)
        rc, out, _ = self.issue("blue-x@rig-y")
        self.assertEqual(rc, 0)
        self.assertIn("already issued", out)
        target = self.binding_path("blue-x@rig-y")
        os.chmod(target, 0o640)
        rc, out, err = self.issue("blue-x@rig-y")
        self.assertNotEqual(rc, 0)
        self.assertNotIn("already issued", out)
        self.assertIn(target.name, err)
        self.assertIn("0600", err)

    def test_add_failure_is_fatal_in_strict_mode(self):
        os.environ["FAKE_RIG_FAIL_ADD"] = "1"
        rc, _, err = self.issue("blue-x@rig-y")
        self.assertNotEqual(rc, 0)
        self.assertFalse(self.binding_path("blue-x@rig-y").exists())
        self.assertIn("blue-x@rig-y", err)

    def test_add_failure_degrades_with_allow_missing_secrets(self):
        os.environ["FAKE_RIG_FAIL_ADD"] = "1"
        rc, _, err = self.issue("blue-x@rig-y", allow_missing_secrets=True)
        self.assertEqual(rc, 0)
        self.assertFalse(self.binding_path("blue-x@rig-y").exists())
        self.assertIn("warn", err)


class AttestationVerifyTests(unittest.TestCase):
    SECRET = "dummybindingsecret FOR-TEST-ONLY-0001"
    SENDER = "blue-probe@test-rig"
    RIG = "test-rig"

    def test_valid_fresh_attestation_records_attested_sender(self):
        seen = set()
        att = SEND_MOD.mint_attestation(self.SECRET, self.SENDER, self.RIG)
        res = SEND_MOD.verify_attestation(
            self.SECRET,
            att,
            expected_rig=self.RIG,
            expected_sender=self.SENDER,
            seen=seen,
        )
        self.assertEqual(res.status, "attested")
        self.assertEqual(res.sender, self.SENDER)

    def test_spoofed_claimed_source_is_ignored(self):
        seen = set()
        att = SEND_MOD.mint_attestation(self.SECRET, self.SENDER, self.RIG)
        res = SEND_MOD.verify_attestation(
            self.SECRET,
            att,
            expected_rig=self.RIG,
            expected_sender=self.SENDER,
            seen=seen,
            claimed_source="red-actor@other-rig",
        )
        self.assertEqual(res.status, "attested")
        self.assertEqual(res.sender, self.SENDER)
        self.assertNotEqual(res.sender, "red-actor@other-rig")

    def test_replay_of_valid_attestation_is_rejected(self):
        seen = set()
        att = SEND_MOD.mint_attestation(self.SECRET, self.SENDER, self.RIG)
        first = SEND_MOD.verify_attestation(
            self.SECRET,
            att,
            expected_rig=self.RIG,
            expected_sender=self.SENDER,
            seen=seen,
        )
        self.assertEqual(first.status, "attested")
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            second = SEND_MOD.verify_attestation(
                self.SECRET,
                att,
                expected_rig=self.RIG,
                expected_sender=self.SENDER,
                seen=seen,
            )
        self.assertEqual(second.status, "rejected")
        self.assertIsNone(second.sender)
        self.assertIsNone(BEARER_RUN_RE.search(buf.getvalue()))

    def test_cross_rig_presentation_fails_scope(self):
        seen = set()
        att = SEND_MOD.mint_attestation(self.SECRET, self.SENDER, self.RIG)
        res = SEND_MOD.verify_attestation(
            self.SECRET,
            att,
            expected_rig="other-rig",
            expected_sender=self.SENDER,
            seen=seen,
        )
        self.assertEqual(res.status, "unverified")
        self.assertIsNone(res.sender)

    def test_cross_seat_secret_cannot_authenticate_other_sender(self):
        # F5 hole, red-proven: seat A's secret mints an attestation naming
        # seat B with a valid MAC under A's secret. When seat A is the
        # expected sender, verification MUST fail — A's secret authenticates
        # A only, never B.
        seen = set()
        att = SEND_MOD.mint_attestation(self.SECRET, "seat-b@test-rig", self.RIG)
        res = SEND_MOD.verify_attestation(
            self.SECRET,
            att,
            expected_rig=self.RIG,
            expected_sender="seat-a@test-rig",
            seen=seen,
        )
        self.assertEqual(res.status, "unverified")
        self.assertIsNone(res.sender)

    def test_tampered_attestation_is_unverified(self):
        seen = set()
        att = SEND_MOD.mint_attestation(self.SECRET, self.SENDER, self.RIG)
        tampered = att[:-1] + ("0" if att[-1] != "0" else "1")
        res = SEND_MOD.verify_attestation(
            self.SECRET,
            tampered,
            expected_rig=self.RIG,
            expected_sender=self.SENDER,
            seen=seen,
        )
        self.assertEqual(res.status, "unverified")
        self.assertIsNone(res.sender)

    def test_wrong_binding_secret_is_unverified(self):
        seen = set()
        att = SEND_MOD.mint_attestation(self.SECRET, self.SENDER, self.RIG)
        res = SEND_MOD.verify_attestation(
            "anotherdummysecret FOR-TEST-ONLY-0002",
            att,
            expected_rig=self.RIG,
            expected_sender=self.SENDER,
            seen=seen,
        )
        self.assertEqual(res.status, "unverified")
        self.assertIsNone(res.sender)

    def test_missing_attestation_holds_unverified(self):
        res = SEND_MOD.verify_attestation(
            self.SECRET,
            None,
            expected_rig=self.RIG,
            expected_sender=self.SENDER,
            seen=set(),
        )
        self.assertEqual(res.status, "unverified")
        self.assertIsNone(res.sender)

    def test_malformed_attestation_is_unverified(self):
        seen = set()
        for bad in ("", "v1.short", "v9.a.b.c." + "0" * 64, "not-an-attestation"):
            res = SEND_MOD.verify_attestation(
                self.SECRET,
                bad,
                expected_rig=self.RIG,
                expected_sender=self.SENDER,
                seen=seen,
            )
            self.assertEqual(res.status, "unverified", bad)
            self.assertIsNone(res.sender, bad)


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


class RenderSenderBindingTests(unittest.TestCase):
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
        # probe-role also binds the seat-grant server, so its grant token
        # file must exist before render reaches the send-identity block.
        grant_file = self.secrets / RENDER_MOD.seat_grant_token_filename(
            "blue-probe-role@test-rig"
        )
        grant_file.write_text("dummybearer FOR-TEST-ONLY-0000")
        os.chmod(grant_file, 0o600)
        self.tools = self.root / "tools"
        pps = self.tools / "pi-packages/node_modules/@gotgenes/pi-permission-system"
        pps.mkdir(parents=True)
        (pps / "package.json").write_text(json.dumps({"version": "41.0.0"}))
        self.fleet_path, self.charter = _write_probe_fleet(str(self.root))
        self.env = {
            **os.environ,
            "HERETEK_SECRETS": str(self.secrets),
            "HERETEK_TOOLS": str(self.tools),
            "OPENRIG_HOME": "/tmp/hr-openrig-09send",
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

    def test_bound_role_renders_cat_reference_never_inline_secret(self):
        session = "blue-probe-role@test-rig"
        binding_file = self.secrets / SEND_MOD.sender_binding_filename(session)
        binding_file.write_text("dummybindingsecret FOR-TEST-ONLY-0003")
        os.chmod(binding_file, 0o600)
        proc = self.render("probe-role")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        entry = json.loads(proc.stdout)["send-identity.json"]
        self.assertEqual(entry["sender"], session)
        self.assertEqual(
            entry["binding"],
            f"!cat {binding_file}",
        )
        self.assertIsNone(BEARER_RUN_RE.search(json.dumps(entry)))

    def test_missing_binding_file_is_fatal_in_strict_mode(self):
        proc = self.render("probe-role")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("send-id-blue-probe-role@test-rig.key", proc.stderr)

    def test_missing_binding_file_degrades_with_allow_missing_secrets(self):
        proc = self.render("probe-role", "--allow-missing-secrets")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        entry = json.loads(proc.stdout)["send-identity.json"]
        self.assertEqual(entry["enabled"], False)

    def test_unbound_role_renders_no_binding(self):
        proc = self.render("plain-role", "--allow-missing-secrets")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("send-identity.json", json.loads(proc.stdout))


class BareSendDenyTests(unittest.TestCase):
    """REQ-S2 bare-send class: V22 triple intact in fleet + rendered leaves."""

    @classmethod
    def setUpClass(cls):
        import yaml

        cls.fleet = yaml.safe_load((REPO_ROOT / "fleet/fleet.yaml").read_text())
        cls.bare_mod = load_module(
            "bare_deny_helpers_09",
            REPO_ROOT / "tests/test_bare_queue_send_deny.py",
        )
        leaves = sorted(
            (REPO_ROOT / "specs/agents").rglob("runtime/pi-permission-config.json")
        )
        assert leaves, "no rendered permission leaves found"
        cls.leaves = leaves

    def test_fleet_declares_exact_bare_deny_triple(self):
        bad = []
        for rid, r in self.fleet["roles"].items():
            ba = (r.get("permissions") or {}).get("bash_allow") or []
            if any(str(b).startswith("rig queue") for b in ba):
                got = (r.get("permissions") or {}).get("bash_deny") or []
                if [str(x) for x in got] != [
                    "rig queue list",
                    "rig queue create",
                    "rig send",
                ]:
                    bad.append(rid)
        self.assertEqual(bad, [], f"roles missing exact bash_deny triple: {bad[:5]}")

    def test_rendered_maps_deny_bare_send_allow_addressed_send(self):
        pps_decide = self.bare_mod.pps_decide
        deny_bad, allow_bad, probed = [], [], 0
        for leaf in self.leaves:
            bash_map = (
                json.loads(leaf.read_text()).get("permission", {}).get("bash", {})
            )
            probed += 1
            if pps_decide(bash_map, "rig send") != "deny":
                deny_bad.append(leaf.parent.parent.name)
            if (
                pps_decide(
                    bash_map,
                    "rig send blue-appsec-engineer@defensive-sec-and-red-team hello",
                )
                != "allow"
            ):
                allow_bad.append(leaf.parent.parent.name)
        self.assertGreater(probed, 0)
        self.assertEqual(deny_bad, [], f"bare rig send allowed: {deny_bad[:6]}")
        self.assertEqual(allow_bad, [], f"addressed rig send denied: {allow_bad[:6]}")


if __name__ == "__main__":
    unittest.main()
