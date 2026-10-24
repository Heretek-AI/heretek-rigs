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
from unittest import mock

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

    def __init__(self, rows, transitions_by_id, unreachable=(), fail_updates=()):
        self._rows = rows
        self._transitions = transitions_by_id
        self._unreachable = set(unreachable)
        self._fail_updates = set(fail_updates)
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
        for qid in self._fail_updates:
            if qid in argv:
                raise sweep.DataSourceError(f"daemon refused update for {qid}")
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


def _bt(qid, tid, state, note, actor="owner@fleet"):
    return {
        "transitionId": tid,
        "qitemId": qid,
        "ts": f"2026-10-22T06:{tid % 60:02d}:00.000Z",
        "state": state,
        "transitionNote": note,
        "actorSession": actor,
    }


def parked_with_verdict_blocker():
    """Parked row whose predicate names a verdict qitem (REQ-BU2 leg (b))."""
    row = {
        "qitemId": "qitem-PARKED",
        "state": "blocked",
        "blockedOn": "external:qa-operator-gate-verdict",
        "destinationSession": "owner@fleet",
        "summary": "parked awaiting verdict qitem",
    }
    parked = [
        _bt(
            "qitem-PARKED",
            1,
            "blocked",
            "SATISFY-WHEN: QA PASS verdict VIA qitem-V1 verdict row; "
            "parked on external:qa-operator-gate-verdict, awaiting verdict",
            "owner@fleet",
        ),
    ]
    blocker = [
        _bt("qitem-V1", 1, "in-progress", "verdict row opened", "qa@fleet"),
        _bt(
            "qitem-V1", 2, "in-progress", "evidence gathered, deliberating", "qa@fleet"
        ),
    ]
    verdict_row = {"qitemId": "qitem-V1", "state": "in-progress", "blockedOn": None}
    return row, parked, blocker, verdict_row


class TestBlockerSideTrigger(unittest.TestCase):
    def test_blocker_only_transition_triggers_reevaluation_and_unparks(self):
        # Parked row quiet after the first sweep; a satisfying verdict lands
        # ONLY on the referenced blocker qitem -> must still unpark (leg (b)).
        row, parked, blocker, verdict_row = parked_with_verdict_blocker()
        by_id = {row["qitemId"]: parked, verdict_row["qitemId"]: blocker}
        client = FakeClient([row, verdict_row], by_id)
        first = sweep.run_sweep(client, cursor={}, dry_run=False)
        self.assertEqual(client.updates, [])
        self.assertIn(row["qitemId"], first["stay_blocked"])
        blocker.append(
            _bt(
                "qitem-V1",
                3,
                "in-progress",
                "QA verdict PASS per wave1-qa-report; gate satisfied, verdict recorded",
                "qa@fleet",
            )
        )
        logs = []
        second = sweep.run_sweep(
            client, cursor=first["cursor"], dry_run=False, log_lines=logs
        )
        self.assertEqual(second["unparked"], [row["qitemId"]])
        self.assertEqual(len(client.updates), 1)
        argv = client.updates[0]
        note = argv[argv.index("--note") + 1]
        self.assertIn("qitem-V1", note)
        self.assertIn("wave1-qa-report", note)

    def test_unrelated_blocker_transition_stays_blocked(self):
        # A new transition on the referenced blocker that carries no
        # satisfaction must trigger re-evaluation yet stay blocked.
        row, parked, blocker, verdict_row = parked_with_verdict_blocker()
        by_id = {row["qitemId"]: parked, verdict_row["qitemId"]: blocker}
        client = FakeClient([row, verdict_row], by_id)
        first = sweep.run_sweep(client, cursor={}, dry_run=False)
        self.assertIn(row["qitemId"], first["stay_blocked"])
        blocker.append(
            _bt(
                "qitem-V1",
                3,
                "in-progress",
                "housekeeping: rotated logs, still deliberating",
                "qa@fleet",
            )
        )
        logs = []
        second = sweep.run_sweep(
            client, cursor=first["cursor"], dry_run=False, log_lines=logs
        )
        self.assertIn(row["qitemId"], second["evaluated"])
        self.assertIn(row["qitemId"], second["stay_blocked"])
        self.assertEqual(second["unparked"], [])
        self.assertEqual(client.updates, [])


class TestSweepFaultIsolation(unittest.TestCase):
    def test_apply_update_failure_leaves_row_blocked_and_continues(self):
        row_a, trans_a = satisfy_shape()
        row_b, trans_b = w103_shape()
        client = FakeClient(
            [row_a, row_b],
            {row_a["qitemId"]: trans_a, row_b["qitemId"]: trans_b},
            fail_updates=(row_a["qitemId"],),
        )
        logs = []
        report = sweep.run_sweep(client, cursor={}, dry_run=False, log_lines=logs)
        self.assertIn(row_a["qitemId"], report["stay_blocked"])
        self.assertNotIn(row_a["qitemId"], report["unparked"])
        self.assertIn(row_b["qitemId"], report["unparked"])
        self.assertEqual(len(client.updates), 1)
        self.assertTrue(
            any("unpark" in line.lower() and "fail" in line.lower() for line in logs),
            logs,
        )

    def test_unreadable_blocker_stays_blocked_cursor_frozen_and_continues(self):
        row_bad = {
            "qitemId": "qitem-R1",
            "state": "blocked",
            "blockedOn": "external:qa-operator-gate-verdict",
        }
        trans_bad = [
            _bt(
                "qitem-R1",
                1,
                "blocked",
                "SATISFY-WHEN: QA PASS verdict VIA qitem-BAD verdict row; "
                "parked, awaiting verdict",
                "owner@fleet",
            )
        ]
        row_ok, trans_ok = satisfy_shape()
        client = FakeClient(
            [row_bad, row_ok],
            {
                row_bad["qitemId"]: trans_bad,
                row_ok["qitemId"]: trans_ok,
                "qitem-BAD": [],
            },
            unreachable=("qitem-BAD",),
        )
        logs = []
        report = sweep.run_sweep(client, cursor={}, dry_run=False, log_lines=logs)
        self.assertIn(row_bad["qitemId"], report["stay_blocked"])
        self.assertNotIn(row_bad["qitemId"], report["cursor"])
        self.assertNotIn(row_bad["qitemId"], report["unparked"])
        self.assertIn(row_ok["qitemId"], report["unparked"])
        self.assertTrue(any("qitem-BAD" in line for line in logs), logs)


class TestParkArgvSafety(unittest.TestCase):
    def test_plan_results_carry_parsed_dry_run(self):
        typed = [
            "qitem-X",
            "--on",
            "external:qa-gate-verdict",
            "--predicate",
            "SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report",
            "--note",
            "parked",
            "--sweep-covered",
        ]
        self.assertTrue(park.plan(["--dry-run", *typed])["dry_run"])
        self.assertFalse(park.plan(typed)["dry_run"])
        live = ["qitem-Y", "--on", "operator@fleet", "--note", "hi"]
        self.assertTrue(park.plan(["--dry-run", *live])["dry_run"])
        self.assertFalse(park.plan(live)["dry_run"])

    def test_abbreviated_dry_run_cannot_trigger_live_write(self):
        argv = [
            "qitem-X",
            "--on",
            "external:qa-gate-verdict",
            "--predicate",
            "SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report",
            "--note",
            "parked",
            "--sweep-covered",
            "--dry-ru",
        ]
        with mock.patch.object(park.subprocess, "run") as run_mock:
            run_mock.side_effect = AssertionError("live rig invocation attempted")
            with self.assertRaises(SystemExit) as cm:
                park.main(argv)
        self.assertEqual(cm.exception.code, 2)
        run_mock.assert_not_called()

    def test_empty_wake_watchdog_is_not_a_live_wake(self):
        result = park.plan(
            [
                "qitem-X",
                "--on",
                "external:qa-gate-verdict",
                "--predicate",
                "SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report",
                "--wake-watchdog",
                "",
            ]
        )
        self.assertNotEqual(result["exit"], 0)
        self.assertIn("wake", result["stderr"].lower())
        self.assertIsNone(result["argv"])

    def test_continuation_merged_singly_with_sweep_covered(self):
        result = park.plan(
            [
                "qitem-X",
                "--on",
                "external:qa-gate-verdict",
                "--predicate",
                "SATISFY-WHEN: QA PASS verdict VIA wave1-qa-report",
                "--continuation",
                "keep me",
                "--sweep-covered",
            ]
        )
        self.assertEqual(result["exit"], 0)
        argv = result["argv"]
        self.assertEqual(argv.count("--continuation"), 1)
        value = argv[argv.index("--continuation") + 1]
        self.assertIn("keep me", value)
        self.assertIn("sweep-covered", value)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# M7 (#83) — auth: parks need operator/TPM actor, exact blocker string, and a
# resolvable evidence qitem. Non-auth: blockers keep existing matching.
# ---------------------------------------------------------------------------

AUTH_BLOCKER = "auth:wave2-tpm-release"


def auth_shape(actor="operator@fleet", evidence="qitem-V9 QA PASS placed",
               blocker=AUTH_BLOCKER):
    """Parked auth: row + a SATISFIED: note from the given actor."""
    row = {
        "qitemId": "qitem-AUTH",
        "state": "blocked",
        "blockedOn": AUTH_BLOCKER,
        "destinationSession": "owner@fleet",
        "summary": "auth-gated release",
    }
    transitions = [
        _bt(
            "qitem-AUTH",
            1,
            "blocked",
            "SATISFY-WHEN: TPM release VIA qitem-V9 verdict row; "
            "parked on auth:wave2-tpm-release",
            "owner@fleet",
        ),
        _bt(
            "qitem-AUTH",
            2,
            "blocked",
            f"SATISFIED: {blocker} {evidence}",
            actor,
        ),
    ]
    return row, transitions


class TestAuthBlockerHardening(unittest.TestCase):
    def test_tpm_seat_set_loads_from_fleet(self):
        """The verifier set is fleet-derived, not hardcoded: it must contain
        the TPM role and its bound session."""
        ids = sweep.load_tpm_seat_ids()
        self.assertIn("tpm-scrum-lead", ids)
        self.assertIn(
            "delivery-tpm-scrum-lead@executive-and-architecture", ids
        )

    def test_auth_self_written_satisfy_stays_blocked(self):
        """#83 case A: the parked seat writes its own SATISFIED: note."""
        row, transitions = auth_shape(actor="owner@fleet")
        verdict = sweep.evaluate_row(
            row,
            transitions,
            fetch_blocker_transitions=lambda ref: [],
            authorized_actors={"tpm-scrum-lead"},
        )
        self.assertEqual(verdict["verdict"], "stay-blocked")

    def test_auth_operator_exact_satisfy_with_evidence_unparks(self):
        """Control: operator-authored exact SATISFIED: with evidence still unparks."""
        row, transitions = auth_shape(actor="operator@fleet")
        verdict = sweep.evaluate_row(
            row,
            transitions,
            fetch_blocker_transitions=lambda ref: [],
            authorized_actors={"tpm-scrum-lead"},
        )
        self.assertEqual(verdict["verdict"], "unpark")

    def test_auth_tpm_seat_satisfy_unparks_via_fleet_default(self):
        """Control: a TPM-seat-authored SATISFIED: unparks using the default
        fleet-derived verifier set (no explicit pass-through)."""
        row, transitions = auth_shape(
            actor="delivery-tpm-scrum-lead@executive-and-architecture"
        )
        verdict = sweep.evaluate_row(
            row, transitions, fetch_blocker_transitions=lambda ref: []
        )
        self.assertEqual(verdict["verdict"], "unpark")

    def test_auth_token_overlap_blocker_stays_blocked(self):
        """#83 case B: SATISFIED: naming auth:wave2-tpm (overlap, not equal)."""
        row, transitions = auth_shape(
            actor="operator@fleet", blocker="auth:wave2-tpm"
        )
        overlap = sweep.blocker_key_tokens(
            "auth:wave2-tpm"
        ) & sweep.blocker_key_tokens(AUTH_BLOCKER)
        self.assertTrue(
            overlap,
            "fixture must genuinely token-overlap (else the test is vacuous)",
        )
        verdict = sweep.evaluate_row(
            row,
            transitions,
            fetch_blocker_transitions=lambda ref: [],
            authorized_actors={"tpm-scrum-lead"},
        )
        self.assertEqual(verdict["verdict"], "stay-blocked")

    def test_auth_legacy_overlap_note_stays_blocked(self):
        """#83 case B (legacy path): overlapping tokens without the full
        blocker string must not satisfy an auth: park."""
        row = {
            "qitemId": "qitem-AL",
            "state": "blocked",
            "blockedOn": AUTH_BLOCKER,
            "destinationSession": "owner@fleet",
            "summary": "auth-gated release",
        }
        transitions = [
            _bt(
                "qitem-AL",
                1,
                "blocked",
                "parked on auth:wave2-tpm-release awaiting TPM release",
                "owner@fleet",
            ),
            _bt(
                "qitem-AL",
                2,
                "blocked",
                "wave2 TPM release PASS per wave1-qa-report, notes attached",
                "operator@fleet",
            ),
        ]
        verdict = sweep.evaluate_row(
            row, transitions, authorized_actors={"tpm-scrum-lead"}
        )
        self.assertEqual(verdict["verdict"], "stay-blocked")

    def test_auth_legacy_full_string_note_needs_authority(self):
        """A legacy note naming the full auth: string unparks only from an
        authoritative actor (TPM seat), never from the parked seat itself."""
        row = {
            "qitemId": "qitem-AF",
            "state": "blocked",
            "blockedOn": AUTH_BLOCKER,
            "destinationSession": "owner@fleet",
            "summary": "auth-gated release",
        }
        note = "auth:wave2-tpm-release QA PASS placed, verdict recorded"
        park = _bt(
            "qitem-AF",
            1,
            "blocked",
            "parked on auth:wave2-tpm-release awaiting TPM release",
            "owner@fleet",
        )
        tpm_verdict = sweep.evaluate_row(
            row,
            [park, _bt("qitem-AF", 2, "blocked", note,
                       "delivery-tpm-scrum-lead@executive-and-architecture")],
            authorized_actors=sweep.load_tpm_seat_ids(),
        )
        self.assertEqual(tpm_verdict["verdict"], "unpark")
        seat_verdict = sweep.evaluate_row(
            row,
            [park, _bt("qitem-AF", 2, "blocked", note, "owner@fleet")],
            authorized_actors=sweep.load_tpm_seat_ids(),
        )
        self.assertEqual(seat_verdict["verdict"], "stay-blocked")

    def test_auth_evidence_without_qitem_ref_stays_blocked(self):
        """auth: requires a resolvable evidence qitem: an operator SATISFIED:
        with no qitem ref in the evidence stays blocked."""
        row, transitions = auth_shape(
            actor="operator@fleet", evidence="per wave1-qa-report QA PASS"
        )
        verdict = sweep.evaluate_row(
            row,
            transitions,
            fetch_blocker_transitions=lambda ref: [],
            authorized_actors={"tpm-scrum-lead"},
        )
        self.assertEqual(verdict["verdict"], "stay-blocked")

    def test_auth_dangling_qitem_ref_stays_blocked_and_names_ref(self):
        """auth: evidence qitem that cannot be resolved stays blocked."""
        row, transitions = auth_shape(
            actor="operator@fleet", evidence="qitem-GONE-1 QA PASS"
        )

        def fetch_missing(ref):
            raise sweep.DataSourceError(f"no such qitem: {ref}")

        verdict = sweep.evaluate_row(
            row,
            transitions,
            fetch_blocker_transitions=fetch_missing,
            authorized_actors={"tpm-scrum-lead"},
        )
        self.assertEqual(verdict["verdict"], "stay-blocked")
        self.assertIn("qitem-GONE-1", verdict["reason"])

    def test_empty_verifier_set_leaves_operator_only(self):
        """Fail-closed catalog: with no resolvable TPM set, a TPM actor is
        not authoritative but the operator still is."""
        row, transitions = auth_shape(
            actor="delivery-tpm-scrum-lead@executive-and-architecture"
        )
        verdict = sweep.evaluate_row(
            row,
            transitions,
            fetch_blocker_transitions=lambda ref: [],
            authorized_actors=set(),
        )
        self.assertEqual(verdict["verdict"], "stay-blocked")

    def test_non_auth_overlap_still_unparks(self):
        """Scope guard: exact-equality is auth:-only. An external: SATISFIED:
        naming an overlapping (non-equal) blocker still unparks."""
        row = {
            "qitemId": "qitem-OV",
            "state": "blocked",
            "blockedOn": "external:wave2-tpm-release",
            "destinationSession": "owner@fleet",
            "summary": "external overlap",
        }
        transitions = [
            _bt(
                "qitem-OV",
                1,
                "blocked",
                "SATISFY-WHEN: release VIA wave2-tpm-report; parked",
                "owner@fleet",
            ),
            _bt(
                "qitem-OV",
                2,
                "blocked",
                "SATISFIED: external:wave2-tpm qitem-V9 QA PASS",
                "operator@fleet",
            ),
        ]
        overlap = sweep.blocker_key_tokens(
            "external:wave2-tpm"
        ) & sweep.blocker_key_tokens("external:wave2-tpm-release")
        self.assertTrue(overlap, "fixture must genuinely token-overlap")
        verdict = sweep.evaluate_row(row, transitions)
        self.assertEqual(verdict["verdict"], "unpark")
