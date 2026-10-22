#!/usr/bin/env python3
"""Unit + red-proof tests for scripts/sweep-typed-blocks.py and
scripts/park-typed-block.py (remediate-38-unblock, REQ-BU1..BU7).

No daemon, no network, no live-queue mutation: the sweep is driven through a
FakeClient, and the park wrapper is exercised in --dry-run mode only. Live
evidence enters solely as read-only recorded transcripts (T1 baseline).
"""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SWEEP_SCRIPT = REPO_ROOT / "scripts" / "sweep-typed-blocks.py"
PARK_SCRIPT = REPO_ROOT / "scripts" / "park-typed-block.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sweep = load_module("sweep_typed_blocks", SWEEP_SCRIPT)
park = load_module("park_typed_block", PARK_SCRIPT)


# ---------------------------------------------------------------------------
# Fixture builders: faithful W1-03/W1-04 shape
# (park on typed-external verdict gate, verdict PASS + placements landed,
# operator unblock note, trailing stale watchdog restatements)
# ---------------------------------------------------------------------------


def _t(tid, state, note, actor="seat@fleet"):
    return {
        "transitionId": tid,
        "qitemId": "qitem-W103",
        "ts": f"2026-10-22T06:{tid % 60:02d}:00.000Z",
        "state": state,
        "transitionNote": note,
        "actorSession": actor,
    }


def w103_shape(extra_trailing=()):
    """Recorded-shape replay: satisfaction asserted, then stale restatements."""
    transitions = [
        _t(1, "pending", "created", "delivery@fleet"),
        _t(2, "in-progress", "claimed", "owner@fleet"),
        _t(
            3,
            "in-progress",
            "staged and conformed, ready for operator placement and QA gate",
            "owner@fleet",
        ),
        _t(
            4,
            "blocked",
            "SATISFY-WHEN: QA PASS verdict on wave1-qa-report VIA operator placement log; "
            "parked on external:operator-placement-qa-gate-verdict, awaiting operator placement and QA verdict",
            "owner@fleet",
        ),
        _t(
            5,
            "blocked",
            "OPERATOR: W1-03 QA PASS content per wave1-qa-report "
            "(rustfmt/clippy/tauri conf GREEN, least-privilege verified). "
            "Placed 4 files + cargo-lints merged. Parked-on-QA-verdict blocker now satisfied. "
            "Row work complete; closure awaits TPM Wave-2 handoff.",
            "operator@fleet",
        ),
        _t(
            6,
            "blocked",
            "parked-owner wake reserved: owner@fleet|abc#1",
            "watchdog@system",
        ),
        _t(
            7,
            "blocked",
            "Watchdog review, still staged awaiting operator placement and QA verdict, "
            "no seat action available, blocker stands",
            "watchdog@system",
        ),
        _t(
            8,
            "blocked",
            "parked-owner wake delivered: owner@fleet|abc#1",
            "watchdog@system",
        ),
    ]
    transitions.extend(extra_trailing)
    row = {
        "qitemId": "qitem-W103",
        "state": "blocked",
        "blockedOn": "external:operator-placement-qa-gate-verdict",
        "destinationSession": "owner@fleet",
        "summary": "W1-03 Rust Tauri config",
    }
    return row, transitions


def satisfy_shape():
    """Well-formed SATISFIED: convention note."""
    row = {
        "qitemId": "qitem-SAT",
        "state": "blocked",
        "blockedOn": "external:qa-operator-gate-verdict",
        "destinationSession": "owner@fleet",
        "summary": "W1-04 CI workflow",
    }
    transitions = [
        _t(
            1,
            "blocked",
            "SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report; parked on verdict",
            "owner@fleet",
        ),
        _t(
            2,
            "blocked",
            "SATISFIED: external:qa-operator-gate-verdict wave1-qa-report t928 QA PASS placed",
            "operator@fleet",
        ),
    ]
    for t in transitions:
        t["qitemId"] = "qitem-SAT"
    return row, transitions


class FakeClient:
    """In-memory rig surface; records every update call (live writes)."""

    def __init__(self, rows, transitions_by_id, unreachable=()):
        self._rows = rows
        self._transitions = transitions_by_id
        self._unreachable = set(unreachable)
        self.updates = []

    def fetch_list(self):
        if "list" in self._unreachable:
            raise sweep.DataSourceError("daemon unreachable (list)")
        return self._rows

    def fetch_transitions(self, qitem_id):
        if qitem_id in self._unreachable:
            raise sweep.DataSourceError(f"daemon unreachable (transitions {qitem_id})")
        return self._transitions.get(qitem_id, [])

    def apply_update(self, argv):
        self.updates.append(list(argv))
        return {"ok": True}


# ---------------------------------------------------------------------------
# T1 — baseline: note-without-state never unparks (the stuck shape)
# ---------------------------------------------------------------------------


class TestBaselineStuckShape(unittest.TestCase):
    def test_recorded_w103_baseline_ends_blocked_despite_unblock_note(self):
        # Read-only incident transcript: t5 asserts satisfaction, yet the row
        # is still blocked and no later transition changes state. This pins
        # the pre-fix shape `update`-without-`--state` cannot escape.
        row, transitions = w103_shape()
        self.assertEqual(row["state"], "blocked")
        satisfaction_landed = any(
            "blocker now satisfied" in (t["transitionNote"] or "") for t in transitions
        )
        self.assertTrue(satisfaction_landed, "fixture must contain the unblock note")
        state_changes_after_note = [
            t for t in transitions[5:] if t["state"] != "blocked"
        ]
        self.assertEqual(
            state_changes_after_note,
            [],
            "baseline: no unpark transition follows the unblock note",
        )
        # And the evaluation layer, fed only pre-sweep evidence rules, must
        # NOT have unparked on its own: without the sweep there is no actor.
        # (The sweep test in TestReplay proves the sweep is that actor.)


# ---------------------------------------------------------------------------
# Sweep pure-function unit tests
# ---------------------------------------------------------------------------


class TestBlockerRecognition(unittest.TestCase):
    def test_typed_external_prefixes_recognised(self):
        for blocker in ("external:qa-gate", "fold:wave-2", "auth:operator-approval"):
            self.assertTrue(sweep.is_typed_blocker(blocker), blocker)

    def test_live_qitem_and_human_seats_are_not_typed(self):
        self.assertFalse(
            sweep.is_typed_blocker("qitem-20261022052407-3d618a4431583b97")
        )
        self.assertFalse(sweep.is_typed_blocker("operator@heretek-omni-fleet"))
        self.assertFalse(sweep.is_typed_blocker(None))
        self.assertFalse(sweep.is_typed_blocker(""))

    def test_key_tokens_split_suffix(self):
        tokens = sweep.blocker_key_tokens("external:operator-placement-qa-gate-verdict")
        self.assertIn("qa", tokens)
        self.assertIn("verdict", tokens)
        self.assertIn("placement", tokens)


class TestSatisfyConvention(unittest.TestCase):
    def test_wellformed_satisfy_parses(self):
        kind = sweep.parse_satisfy_note(
            "SATISFIED: external:qa-operator-gate-verdict wave1-qa-report t928"
        )
        self.assertIsNotNone(kind)
        status, blocker, evidence = kind
        self.assertEqual(status, "ok")
        self.assertEqual(blocker, "external:qa-operator-gate-verdict")
        self.assertIn("wave1-qa-report", evidence)

    def test_malformed_satisfy_missing_evidence(self):
        kind = sweep.parse_satisfy_note("SATISFIED: external:qa-gate")
        self.assertIsNotNone(kind)
        self.assertEqual(kind[0], "malformed")

    def test_malformed_satisfy_bare_marker(self):
        kind = sweep.parse_satisfy_note("SATISFIED:")
        self.assertIsNotNone(kind)
        self.assertEqual(kind[0], "malformed")

    def test_ordinary_note_is_not_satisfy(self):
        self.assertIsNone(sweep.parse_satisfy_note("QA PASS per report, looks good"))
        self.assertIsNone(sweep.parse_satisfy_note("still awaiting verdict"))


class TestEvaluation(unittest.TestCase):
    def test_satisfy_note_marks_predicate_met(self):
        row, transitions = satisfy_shape()
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "unpark")
        self.assertIn("wave1-qa-report", verdict["evidence_citation"])

    def test_legacy_operator_unblock_note_marks_predicate_met(self):
        row, transitions = w103_shape()
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "unpark")
        self.assertIn("wave1-qa-report", verdict["evidence_citation"])

    def test_stale_watchdog_restatement_does_not_override_satisfaction(self):
        # The exact incident bug: post-satisfaction "blocker stands" boilerplate
        # cites no new evidence, so the predicate stays met.
        row, transitions = w103_shape()
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "unpark")

    def test_sabotage_note_without_satisfaction_tokens_stays_blocked(self):
        # Red-proof: an unblock-shaped note with the evidence language removed
        # must NOT unpark (proves the unpark fires on satisfying evidence).
        row, transitions = w103_shape()
        transitions[4]["transitionNote"] = (
            "OPERATOR: W1-03 looked at per wave1-qa-report. "
            "Parked-on-QA-verdict item noted. Row work complete; closure awaits TPM Wave-2 handoff."
        )
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "stay-blocked")
        self.assertIn("missing", verdict["reason"].lower())

    def test_sabotage_rework_note_rearms_block(self):
        # Red-proof: a later note citing new failure/rework re-arms the block.
        row, transitions = w103_shape()
        transitions.append(
            _t(
                9,
                "blocked",
                "QA recheck: job2 failed on windows runner, rework requested "
                "before verdict can stand",
                "qa@fleet",
            )
        )
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "stay-blocked")
        self.assertIn("9", verdict["reason"])

    def test_negated_rework_does_not_rearm(self):
        # "zero rework owed" must not count as a re-arming note.
        row, transitions = w103_shape()
        transitions.append(
            _t(
                9,
                "blocked",
                "Wake consumed: QA PASS plus placed per t5 noted, "
                "zero rework owed, closure awaiting TPM handoff, park stands",
                "owner@fleet",
            )
        )
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "unpark")

    def test_ambiguous_evidence_stays_blocked_and_names_gap(self):
        row = {
            "qitemId": "qitem-AMB",
            "state": "blocked",
            "blockedOn": "external:qa-operator-gate-verdict",
        }
        transitions = [
            _t(
                1,
                "blocked",
                "SATISFY-WHEN: QA PASS VIA wave1-qa-report; parked",
                "owner@fleet",
            ),
            _t(2, "blocked", "QA is looking at the workflow today", "qa@fleet"),
        ]
        for t in transitions:
            t["qitemId"] = "qitem-AMB"
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "stay-blocked")
        self.assertTrue(verdict["missing"] or "missing" in verdict["reason"].lower())

    def test_malformed_satisfy_stays_blocked_with_recorded_evaluation(self):
        row = {
            "qitemId": "qitem-MAL",
            "state": "blocked",
            "blockedOn": "external:qa-operator-gate-verdict",
        }
        transitions = [
            _t(
                1,
                "blocked",
                "SATISFY-WHEN: QA PASS VIA wave1-qa-report; parked",
                "owner@fleet",
            ),
            _t(2, "blocked", "SATISFIED:", "operator@fleet"),
        ]
        for t in transitions:
            t["qitemId"] = "qitem-MAL"
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "stay-blocked")
        self.assertIn("malformed", verdict["reason"].lower())

    def test_non_blocked_rows_are_out_of_scope(self):
        row = {"qitemId": "qitem-OPEN", "state": "in-progress", "blockedOn": None}
        verdict = sweep.evaluate_row(row, [])
        self.assertEqual(verdict["verdict"], "skip")

    def test_non_typed_blockers_are_out_of_scope(self):
        row = {
            "qitemId": "qitem-H",
            "state": "blocked",
            "blockedOn": "operator@heretek-omni-fleet",
        }
        verdict = sweep.evaluate_row(row, [])
        self.assertEqual(verdict["verdict"], "skip")

    def test_dangling_verdict_qitem_ref_stays_blocked_and_names_ref(self):
        row = {
            "qitemId": "qitem-DAN",
            "state": "blocked",
            "blockedOn": "external:qa-operator-gate-verdict",
        }
        transitions = [
            _t(
                1,
                "blocked",
                "SATISFY-WHEN: QA PASS VIA wave1-qa-report; parked",
                "owner@fleet",
            ),
            _t(
                2,
                "blocked",
                "SATISFIED: external:qa-operator-gate-verdict "
                "qitem-DELETED-111 QA PASS",
                "operator@fleet",
            ),
        ]
        for t in transitions:
            t["qitemId"] = "qitem-DAN"

        def fetch_missing(qitem_id):
            raise sweep.DataSourceError(f"no such qitem: {qitem_id}")

        verdict = sweep.evaluate_row(
            row, transitions, fetch_blocker_transitions=fetch_missing
        )
        self.assertEqual(verdict["verdict"], "stay-blocked")
        self.assertIn("qitem-DELETED-111", verdict["reason"])

    def test_pending_pass_assertion_stays_blocked(self):
        # Live W2-06 shape (transition 1194): "runner pass still pending"
        # names the blocker and contains "pass", but pending-state negation
        # plus no evidence citation must keep the row parked.
        row = {
            "qitemId": "qitem-W206",
            "state": "blocked",
            "blockedOn": "external:w2-01-operator-runner-pass",
        }
        transitions = [
            _t(1, "blocked", "parked awaiting runner pass", "owner@fleet"),
            _t(
                2,
                "blocked",
                "Watchdog review, scaffold staged but placement "
                "and runner pass still pending, no seat action available, "
                "blocker stands",
                "owner@fleet",
            ),
        ]
        for t in transitions:
            t["qitemId"] = "qitem-W206"
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "stay-blocked")

    def test_bare_seat_assertion_without_citation_stays_blocked(self):
        # A seat note with a SAT token but no evidence citation and no
        # verdict authority is not actionable (fail-closed).
        row = {
            "qitemId": "qitem-BARE",
            "state": "blocked",
            "blockedOn": "external:qa-operator-gate-verdict",
        }
        transitions = [
            _t(1, "blocked", "parked awaiting QA verdict", "owner@fleet"),
            _t(2, "blocked", "QA verdict PASS, all good from here", "owner@fleet"),
        ]
        for t in transitions:
            t["qitemId"] = "qitem-BARE"
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "stay-blocked")

    def test_operator_verdict_without_citation_unparks(self):
        # Live W1-08 shape (transition 1101): the operator IS the verdict
        # authority, so an operator SAT note needs no separate citation.
        row = {
            "qitemId": "qitem-W108",
            "state": "blocked",
            "blockedOn": "external:operator-placement-qa-gate",
        }
        transitions = [
            _t(1, "blocked", "parked awaiting placement and QA", "owner@fleet"),
            _t(
                2,
                "blocked",
                "OPERATOR W1-08 CLOSED: placed 3/3 EXACT, "
                "agency-qa PASS-with-observations. Row complete.",
                "operator@fleet",
            ),
        ]
        for t in transitions:
            t["qitemId"] = "qitem-W108"
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "unpark")

    def test_park_predicate_alone_never_self_satisfies(self):
        # A park note describing future satisfaction ("SATISFY-WHEN: QA
        # PASS ...") must not count as landed evidence on its own.
        row = {
            "qitemId": "qitem-PARK",
            "state": "blocked",
            "blockedOn": "external:qa-operator-gate-verdict",
        }
        transitions = [
            _t(
                1,
                "blocked",
                "SATISFY-WHEN: QA PASS verdict VIA "
                "wave1-qa-report; parked awaiting QA verdict",
                "owner@fleet",
            ),
        ]
        for t in transitions:
            t["qitemId"] = "qitem-PARK"
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "stay-blocked")


# ---------------------------------------------------------------------------
# Sweep run-level tests: unpark route, dry-run, idempotency, fail-closed
# ---------------------------------------------------------------------------


class TestSweepRun(unittest.TestCase):
    def test_replay_w103_shape_unparks_with_spec_route(self):
        row, transitions = w103_shape()
        client = FakeClient([row], {row["qitemId"]: transitions})
        report = sweep.run_sweep(client, cursor={}, dry_run=False)
        self.assertEqual(len(client.updates), 1)
        argv = client.updates[0]
        # Exact spec route: update --state in-progress --reopen + audit note.
        self.assertEqual(argv[:2], ["queue", "update"])
        self.assertIn(row["qitemId"], argv)
        self.assertIn("--state", argv)
        self.assertEqual(argv[argv.index("--state") + 1], "in-progress")
        self.assertIn("--reopen", argv)
        self.assertIn("--note", argv)
        note = argv[argv.index("--note") + 1]
        self.assertIn("external:operator-placement-qa-gate-verdict", note)
        self.assertIn("wave1-qa-report", note)
        self.assertEqual(report["unparked"], [row["qitemId"]])

    def test_rerun_is_idempotent_no_duplicate_unpark(self):
        row, transitions = w103_shape()
        client = FakeClient([row], {row["qitemId"]: transitions})
        first = sweep.run_sweep(client, cursor={}, dry_run=False)
        self.assertEqual(len(client.updates), 1)
        second = sweep.run_sweep(client, cursor=first["cursor"], dry_run=False)
        self.assertEqual(len(client.updates), 1, "rerun must not duplicate the unpark")
        self.assertEqual(second["unparked"], [])

    def test_dry_run_reports_but_mutates_nothing(self):
        row, transitions = w103_shape()
        client = FakeClient([row], {row["qitemId"]: transitions})
        report = sweep.run_sweep(client, cursor={}, dry_run=True)
        self.assertEqual(report["would_unpark"], [row["qitemId"]])
        self.assertEqual(client.updates, [], "dry-run must not issue any update")

    def test_sweep_never_emits_done(self):
        shapes = [w103_shape(), satisfy_shape()]
        rows = [r for r, _ in shapes]
        by_id = {r["qitemId"]: t for r, t in shapes}
        client = FakeClient(rows, by_id)
        sweep.run_sweep(client, cursor={}, dry_run=False)
        for argv in client.updates:
            self.assertNotIn("done", argv, f"sweep must never close rows: {argv}")

    def test_daemon_unreachable_claims_no_evaluations(self):
        client = FakeClient([], {}, unreachable=("list",))
        with self.assertRaises(sweep.DataSourceError):
            sweep.run_sweep(client, cursor={}, dry_run=False)
        self.assertEqual(client.updates, [])

    def test_in_progress_rows_are_not_touched(self):
        row = {"qitemId": "qitem-OPEN", "state": "in-progress", "blockedOn": None}
        client = FakeClient([row], {})
        report = sweep.run_sweep(client, cursor={}, dry_run=False)
        self.assertEqual(client.updates, [])
        self.assertEqual(report["evaluated"], [])


# ---------------------------------------------------------------------------
# Park wrapper tests (all --dry-run: no live queue mutation)
# ---------------------------------------------------------------------------


class TestParkWrapper(unittest.TestCase):
    def run_park(self, *args):
        return park.plan(["--dry-run", *args])

    def test_predicate_less_typed_park_rejected(self):
        proc = self.run_park(
            "qitem-X",
            "--on",
            "external:qa-gate-verdict",
            "--note",
            "parked awaiting verdict",
        )
        self.assertNotEqual(proc["exit"], 0)
        self.assertIn("predicate", proc["stderr"].lower())
        self.assertEqual(proc["argv"], None, "rejected park must build no rig argv")

    def test_malformed_predicate_rejected(self):
        proc = self.run_park(
            "qitem-X",
            "--on",
            "external:qa-gate-verdict",
            "--predicate",
            "qa will pass soon",
            "--note",
            "parked",
            "--wake-watchdog",
            "WD1",
        )
        self.assertNotEqual(proc["exit"], 0)
        self.assertIn("SATISFY-WHEN", proc["stderr"])

    def test_timer_only_typed_park_rejected(self):
        proc = self.run_park(
            "qitem-X",
            "--on",
            "external:qa-gate-verdict",
            "--predicate",
            "SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report",
            "--note",
            "parked",
            "--wake-after",
            "2h",
        )
        self.assertNotEqual(proc["exit"], 0)
        self.assertIn("wake", proc["stderr"].lower())

    def test_watchdog_backed_typed_park_accepted(self):
        proc = self.run_park(
            "qitem-X",
            "--on",
            "external:qa-gate-verdict",
            "--predicate",
            "SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report",
            "--note",
            "parked",
            "--wake-watchdog",
            "WD1",
        )
        self.assertEqual(proc["exit"], 0)
        self.assertIn("queue", proc["argv"])
        self.assertIn("block", proc["argv"])
        joined = " ".join(proc["argv"])
        self.assertIn("SATISFY-WHEN", joined, "predicate must travel in the park note")

    def test_sweep_covered_typed_park_accepted(self):
        proc = self.run_park(
            "qitem-X",
            "--on",
            "external:qa-gate-verdict",
            "--predicate",
            "SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report",
            "--note",
            "parked",
            "--sweep-covered",
        )
        self.assertEqual(proc["exit"], 0)

    def test_dry_run_executes_nothing(self):
        # --dry-run must never spawn rig: run via subprocess and assert no
        # queue mutation is possible (argv printed, exit 0, no daemon needed).
        result = subprocess.run(
            [
                sys.executable,
                str(PARK_SCRIPT),
                "--dry-run",
                "qitem-X",
                "--on",
                "external:qa-gate-verdict",
                "--predicate",
                "SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report",
                "--note",
                "parked",
                "--sweep-covered",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("rig queue block", result.stdout)


if __name__ == "__main__":
    unittest.main()
