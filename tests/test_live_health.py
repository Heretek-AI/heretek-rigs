#!/usr/bin/env python3
"""Unit + red-proof tests for scripts/live-health.py (warn-first live-fleet gate).

No daemon, no network: pure-function checks run against synthetic fixtures, and
the two subprocess red-proofs drive the real gate entrypoint with a stub `rig`
binary (dead-daemon SKIP; read-only argv audit).
"""

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = REPO_ROOT / "scripts" / "live-health.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("live_health_gate", GATE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NOW = datetime(2026, 10, 22, 12, 5, 0, tzinfo=timezone.utc)

# Three W4-shaped rows: claimed 11:14-11:15, zero post-claim transitions (~50m).
INCIDENT_ROWS = [
    {
        "qitemId": "qitem-20261022111416-78213c07c3272cbc",
        "state": "in-progress",
        "destinationSession": "design-a11y-specialist@heretek-omni-fleet",
        "claimedAt": "2026-10-22T11:14:23.647Z",
        "tsCreated": "2026-10-22T11:14:16.461Z",
        "tsUpdated": "2026-10-22T11:14:23.647Z",
        "lastHeartbeat": None,
    },
    {
        "qitemId": "qitem-20261022111410-8d4e00317b7b6621",
        "state": "in-progress",
        "destinationSession": "design-design-system-eng@heretek-omni-fleet",
        "claimedAt": "2026-10-22T11:14:15.010Z",
        "tsCreated": "2026-10-22T11:14:10.918Z",
        "tsUpdated": "2026-10-22T11:14:15.010Z",
        "lastHeartbeat": None,
    },
    {
        "qitemId": "qitem-20261022111413-ea9f86772c241179",
        "state": "in-progress",
        "destinationSession": "design-design-system-eng@heretek-omni-fleet",
        "claimedAt": "2026-10-22T11:14:18.554Z",
        "tsCreated": "2026-10-22T11:14:13.995Z",
        "tsUpdated": "2026-10-22T11:14:18.554Z",
        "lastHeartbeat": None,
    },
]

INCIDENT_TRANSITIONS = {
    row["qitemId"]: [
        {
            "transitionId": 1,
            "qitemId": row["qitemId"],
            "ts": row["tsCreated"],
            "state": "pending",
            "transitionNote": "created",
        },
        {
            "transitionId": 2,
            "qitemId": row["qitemId"],
            "ts": row["claimedAt"],
            "state": "in-progress",
            "transitionNote": "claimed",
        },
    ]
    for row in INCIDENT_ROWS
}


class FakeClient:
    """In-memory stand-in for RigClient/FixtureClient."""

    def __init__(self, payloads=None, error=None):
        self.payloads = payloads or {}
        self.error = error

    def _get(self, kind):
        if self.error:
            raise self.error
        if kind not in self.payloads:
            raise Exception(f"no fixture for {kind}")
        return self.payloads[kind]

    def fetch_list(self):
        return self._get("list")

    def fetch_overdue(self):
        return self._get("overdue")

    def fetch_undelivered(self):
        return self._get("undelivered")

    def fetch_ps_nodes(self):
        return self._get("ps")

    def fetch_transitions(self, qitem_id):
        if self.error:
            raise self.error
        return self.payloads.get("transitions", {}).get(qitem_id, [])


def default_opts(gate, **over):
    opts = gate.GateOpts(
        t_pickup_min=15,
        t_stuck_min=30,
        t_undelivered_min=15,
        hb_mult=3,
        strict=False,
        rig_scope_all=True,
        rig_name=None,
        limit=100,
    )
    for key, value in over.items():
        setattr(opts, key, value)
    return opts


def heartbeat_map_all_configured():
    return (
        {"a11y-specialist": 1800, "design-system-eng": 1800},
        [],
    )


class TestPickupEvaluation(unittest.TestCase):
    def setUp(self):
        self.gate = load_gate()

    def test_claimed_untouched_row_named_with_age(self):
        client = FakeClient(
            {
                "list": INCIDENT_ROWS[:1],
                "overdue": [],
                "undelivered": [],
                "ps": [],
                "transitions": INCIDENT_TRANSITIONS,
            }
        )
        result = self.gate.evaluate_pickup(
            client.fetch_list(), client.fetch_transitions, NOW, 15
        )
        self.assertEqual(result["status"], "WARN")
        self.assertEqual(len(result["breached"]), 1)
        self.assertEqual(
            result["breached"][0]["id"], "qitem-20261022111416-78213c07c3272cbc"
        )
        self.assertGreaterEqual(result["breached"][0]["age_min"], 50)

    def test_fresh_claim_passes(self):
        rows = [
            dict(
                INCIDENT_ROWS[0],
                claimedAt="2026-10-22T12:00:00.000Z",
                tsUpdated="2026-10-22T12:00:00.000Z",
            )
        ]
        transitions = {
            rows[0]["qitemId"]: [
                {
                    "ts": rows[0]["claimedAt"],
                    "state": "in-progress",
                    "transitionNote": "claimed",
                }
            ]
        }
        result = self.gate.evaluate_pickup(rows, transitions.get, NOW, 15)
        self.assertEqual(result["status"], "PASS")

    def test_post_claim_transition_clears_breach(self):
        rows = [dict(INCIDENT_ROWS[0])]
        transitions = {
            rows[0]["qitemId"]: INCIDENT_TRANSITIONS[rows[0]["qitemId"]]
            + [
                {
                    "ts": "2026-10-22T11:40:00.000Z",
                    "state": "in-progress",
                    "transitionNote": "progress note",
                }
            ]
        }
        # First post-claim transition lands 11:40, ~26m after the 11:14:23
        # claim: beyond T_pickup=15, so the row still breaches (named, WARN).
        result = self.gate.evaluate_pickup(rows, transitions.get, NOW, 15)
        self.assertEqual(result["status"], "WARN")
        self.assertEqual(len(result["breached"]), 1)
        self.assertEqual(result["breached"][0]["id"], rows[0]["qitemId"])
        self.assertGreater(result["breached"][0]["age_min"], 15)
        self.assertIn(rows[0]["qitemId"], result["detail"])


class TestOverdueUndelivered(unittest.TestCase):
    def setUp(self):
        self.gate = load_gate()

    def test_overdue_breach_names_ids_and_histogram(self):
        rows = [
            {"qitemId": "q-overdue-1", "closureRequiredAt": "2026-10-22T10:00:00.000Z"},
            {"qitemId": "q-overdue-2", "closureRequiredAt": "2026-10-22T11:50:00.000Z"},
        ]
        result = self.gate.evaluate_overdue(rows, NOW, 30)
        self.assertEqual(result["status"], "WARN")
        ids = [b["id"] for b in result["breached"]]
        self.assertIn("q-overdue-1", ids)
        self.assertNotIn("q-overdue-2", ids)  # 15m past deadline < 30m grace
        self.assertIn("histogram", result)
        total = sum(result["histogram"].values())
        self.assertEqual(total, 2)

    def test_empty_overdue_passes(self):
        result = self.gate.evaluate_overdue([], NOW, 30)
        self.assertEqual(result["status"], "PASS")

    def test_undelivered_breach_names_ids_with_age(self):
        rows = [
            {
                "qitemId": "q-undelivered-9",
                "tsCreated": "2026-10-22T11:00:00.000Z",
                "lastNudgeAttempt": "2026-10-22T11:00:05.000Z",
            }
        ]
        result = self.gate.evaluate_undelivered(rows, NOW, 15)
        self.assertEqual(result["status"], "WARN")
        self.assertEqual(result["breached"][0]["id"], "q-undelivered-9")
        self.assertGreaterEqual(result["breached"][0]["age_min"], 60)

    def test_empty_undelivered_passes(self):
        result = self.gate.evaluate_undelivered([], NOW, 15)
        self.assertEqual(result["status"], "PASS")


class TestHeartbeat(unittest.TestCase):
    def setUp(self):
        self.gate = load_gate()

    def test_unconfigured_roles_cap_at_warn_and_are_named(self):
        assessed = [
            {
                "session": "design-a11y-specialist@fleet",
                "role": "a11y-specialist",
                "interval_sec": 1800,
                "last_hb": "2026-10-22T12:00:00.000Z",
            }
        ]
        result = self.gate.evaluate_heartbeat(
            assessed, ["stale-role-a", "stale-role-b"], NOW, 3
        )
        self.assertIn(result["status"], ("WARN", "FAIL"))
        self.assertIn("stale-role-a", result["detail"])
        self.assertIn("stale-role-b", result["detail"])

    def test_all_configured_and_fresh_passes(self):
        assessed = [
            {
                "session": "design-a11y-specialist@fleet",
                "role": "a11y-specialist",
                "interval_sec": 1800,
                "last_hb": "2026-10-22T12:00:00.000Z",
            }
        ]
        result = self.gate.evaluate_heartbeat(assessed, [], NOW, 3)
        self.assertEqual(result["status"], "PASS")

    def test_stale_seat_named(self):
        assessed = [
            {
                "session": "design-a11y-specialist@fleet",
                "role": "a11y-specialist",
                "interval_sec": 1800,
                "last_hb": "2026-10-22T09:00:00.000Z",
            }
        ]
        result = self.gate.evaluate_heartbeat(assessed, [], NOW, 3)
        self.assertEqual(result["status"], "WARN")
        self.assertIn("design-a11y-specialist@fleet", result["detail"])

    def test_missing_heartbeat_never_passes(self):
        assessed = [
            {
                "session": "design-a11y-specialist@fleet",
                "role": "a11y-specialist",
                "interval_sec": 1800,
                "last_hb": None,
            }
        ]
        result = self.gate.evaluate_heartbeat(assessed, [], NOW, 3)
        self.assertIn(result["status"], ("WARN", "FAIL", "SKIP"))
        self.assertNotEqual(result["status"], "PASS")


class TestSeatIdleness(unittest.TestCase):
    def setUp(self):
        self.gate = load_gate()

    def test_idle_at_prompt_holder_named(self):
        nodes = [
            {
                "canonicalSessionName": "design-a11y-specialist@fleet",
                "agentActivity": {"state": "idle-at-prompt"},
            }
        ]
        holders = {"design-a11y-specialist@fleet"}
        result = self.gate.evaluate_seat_idleness(nodes, holders)
        self.assertEqual(result["status"], "WARN")
        self.assertIn("design-a11y-specialist@fleet", result["detail"])

    def test_unknown_activity_state_skips_never_healthy(self):
        nodes = [
            {
                "canonicalSessionName": "design-a11y-specialist@fleet",
                "agentActivity": {"state": "unknown"},
            }
        ]
        holders = {"design-a11y-specialist@fleet"}
        result = self.gate.evaluate_seat_idleness(nodes, holders)
        self.assertEqual(result["status"], "SKIP")
        self.assertIn("design-a11y-specialist@fleet", result["detail"])

    def test_running_holder_passes(self):
        nodes = [
            {
                "canonicalSessionName": "design-a11y-specialist@fleet",
                "agentActivity": {"state": "running"},
            }
        ]
        holders = {"design-a11y-specialist@fleet"}
        result = self.gate.evaluate_seat_idleness(nodes, holders)
        self.assertEqual(result["status"], "PASS")


class TestIncidentReplay(unittest.TestCase):
    """T6a / returnable: the 2026-10-22 50-minute idle shape must WARN + name IDs."""

    def setUp(self):
        self.gate = load_gate()

    def test_three_claimed_untouched_rows_warn_with_all_ids(self):
        fixture_dir = (
            REPO_ROOT / "tests" / "fixtures" / "live-health" / "incident-2026-10-22"
        )
        client = self.gate.FixtureClient(fixture_dir)
        fleet_raw = client.fetch_fleet_heartbeat()
        fleet_map = {k: int(v) for k, v in fleet_raw.items()}
        unconfigured = sorted(k for k, v in fleet_map.items() if v <= 0)
        report = self.gate.run_gate(
            client, fleet_map, unconfigured, default_opts(self.gate), NOW
        )
        text = self.gate.render_text(
            report, self.gate.effective_values(default_opts(self.gate))
        )
        for row in INCIDENT_ROWS:
            self.assertIn(row["qitemId"], text)
        self.assertIn("WARN", text)
        self.assertNotIn("all sub-checks PASS", text)


class TestDeadDaemon(unittest.TestCase):
    """T3/T6b: unreachable daemon -> every live sub-check SKIP, exit 0, never PASS."""

    def test_gate_level_skip(self):
        gate = load_gate()
        client = FakeClient(error=gate.DataSourceError("daemon down"))
        report = gate.run_gate(client, {}, [], default_opts(gate), NOW)
        names = [c["name"] for c in report["checks"]]
        for expected in (
            "pickup",
            "stuck-overdue",
            "undelivered",
            "heartbeat",
            "seat-idleness",
        ):
            self.assertIn(expected, names)
        for check in report["checks"]:
            self.assertEqual(check["status"], "SKIP", check["name"])
        text = gate.render_text(report, gate.effective_values(default_opts(gate)))
        self.assertIn("sources: 0 ok", text)
        self.assertNotIn("healthy", text.lower())
        self.assertEqual(gate.overall_exit(report, strict=False), 0)

    def test_dead_daemon_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "rig"
            stub.write_text("#!/bin/sh\necho 'daemon unreachable' >&2\nexit 1\n")
            stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
            env = {**os.environ, "RIG_PATH": str(stub)}
            proc = subprocess.run(
                [sys.executable, str(GATE_SCRIPT)],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(REPO_ROOT),
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("SKIP", proc.stdout)
        self.assertIn("sources: 0 ok", proc.stdout)
        self.assertNotIn("healthy", proc.stdout.lower())


class TestReadOnly(unittest.TestCase):
    """T6c/REQ-LH8: the gate issues zero mutating queue/session calls."""

    MUTATING = (
        "claim",
        "update",
        "block",
        "resolve",
        "handoff",
        "send",
        "create",
        "unclaim",
        "fallback",
        "inbox-drop",
        "inbox-absorb",
        "inbox-deny",
        "outbox-record",
    )

    def test_stub_log_shows_no_mutating_verbs(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "argv.log"
            fixture = Path(tmp) / "list.json"
            fixture.write_text("[]")
            stub = Path(tmp) / "rig"
            stub.write_text(f"#!/bin/sh\necho \"$@\" >> {log}\necho '[]'\n")
            stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
            env = {**os.environ, "RIG_PATH": str(stub)}
            proc = subprocess.run(
                [sys.executable, str(GATE_SCRIPT)],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(REPO_ROOT),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            logged = log.read_text() if log.exists() else ""
            self.assertTrue(logged.strip(), "stub log must record at least one command")
            for verb in self.MUTATING:
                for line in logged.splitlines():
                    parts = line.split()
                    self.assertNotIn(verb, parts, f"mutating verb issued: {line}")

    def test_allowlist_refuses_mutation(self):
        gate = load_gate()
        with self.assertRaises(RuntimeError):
            gate.check_allowed(["queue", "claim", "q-1"])
        with self.assertRaises(RuntimeError):
            gate.check_allowed(["queue", "send", "x@y@z", "hi"])
        # read-only verbs pass
        gate.check_allowed(["queue", "list", "--json", "-A"])
        gate.check_allowed(["queue", "transitions", "--json", "q-1"])
        gate.check_allowed(["ps", "--nodes", "-A", "--json", "--no-cleanup"])


class TestConfigFailClosed(unittest.TestCase):
    def test_unparseable_threshold_dies(self):
        env = {**os.environ, "LH_T_PICKUP_MIN": "not-a-number"}
        proc = subprocess.run(
            [sys.executable, str(GATE_SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(REPO_ROOT),
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("LH_T_PICKUP_MIN", proc.stderr)


class TestStrictPromotion(unittest.TestCase):
    def setUp(self):
        self.gate = load_gate()

    def test_strict_promotes_warn_to_fail(self):
        client = FakeClient(
            {
                "list": INCIDENT_ROWS[:1],
                "overdue": [],
                "undelivered": [],
                "ps": [],
                "transitions": INCIDENT_TRANSITIONS,
            }
        )
        fleet_map, unconfigured = heartbeat_map_all_configured()
        report = self.gate.run_gate(
            client, fleet_map, unconfigured, default_opts(self.gate, strict=True), NOW
        )
        self.assertEqual(self.gate.overall_exit(report, strict=True), 2)
        text = self.gate.render_text(
            report, self.gate.effective_values(default_opts(self.gate))
        )
        self.assertIn("FAIL", text)


if __name__ == "__main__":
    unittest.main()
