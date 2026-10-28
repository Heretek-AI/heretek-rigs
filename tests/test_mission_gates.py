#!/usr/bin/env python3
"""Corpus for mission-row gate ownership (issue #77, REQ-M1/M2/M3).

Fixtures only (/tmp scratch, dummy ids — never the live mission checkout).

REQ-M1 (charter closure ownership): the mission-slice-sop skill, authored
via fleet/skill-patches/ + regen (never hand-edited leaves), states that
the destination seat closes its own row (done + closure reason) once its
acceptance evidence is on the row, unless a --gate qitem with a live owner
exists.

REQ-M2 (gateless awaiting-gate counts as stalled): reconcile_model emits a
stalled-awaiting-gate diff for awaiting-gate prose with NO gate qitem
reference (B2 pattern); a live gate qitem with a live owner exempts the
row (stays quiet). Propose-only throughout: classification only, no row
state is written by anything here.

REQ-M3 (recovery not dismissible without state change): closing a
stuck-recovery item while the flagged row's state is byte-identical to
flag time is refused fail-closed with a redacted log line; a changed row
may close. The sweep NEVER writes done (never-done rule stands).
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
RECONCILE_SCRIPT = REPO_ROOT / "scripts" / "reconcile.py"
SKILL_LEAF = (
    REPO_ROOT
    / "specs"
    / "agents"
    / "_shared"
    / "skills"
    / "mission-slice-sop"
    / "SKILL.md"
)

PARENT = "qitem-20261024023941-8685741b5ce805de"
GATE = "qitem-20261024024002-abcdef0123456789"
GATE_STATUS = (
    "verdict recorded; Standing by for gate --gate qa-seat, "
    "gate qitem %s (owner qa-seat@rig)" % GATE
)
GATELESS_STATUS = "verdict recorded; Standing by for gate"


def load_model():
    spec = importlib.util.spec_from_file_location(
        "reconcile_model_mg", str(REPO_ROOT / "scripts" / "reconcile_model.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sweep():
    spec = importlib.util.spec_from_file_location(
        "sweep_typed_blocks_mg",
        str(REPO_ROOT / "scripts" / "sweep-typed-blocks.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_tracker(tmpdir, status_cell, name="mission-dispatch-tracker.md"):
    path = Path(tmpdir) / name
    path.write_text(
        """\
# Mission Dispatch Tracker (synthetic 77-mission-gates replica)

## Slices
| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| B2-parent mission-row | owner-seat | verdict recorded | %s | %s |

## Rules (all slices)
No commits by seats.
"""
        % (PARENT, status_cell)
    )
    return str(path)


def write_queue(tmpdir, gate_state=None, gate_owner="qa-seat@rig"):
    qlist = [
        {
            "qitemId": PARENT,
            "state": "in-progress",
            "destinationSession": "owner-seat",
            "tsUpdated": "2026-10-24T02:46:00.000Z",
        }
    ]
    trans = {
        PARENT: [
            {
                "transitionId": 41,
                "qitemId": PARENT,
                "ts": "2026-10-24T02:39:00.000Z",
                "state": "in-progress",
                "transitionNote": "verdict recorded, findings filed per t41",
            },
        ]
    }
    if gate_state is not None:
        qlist.append(
            {
                "qitemId": GATE,
                "state": gate_state,
                "destinationSession": gate_owner,
                "tsUpdated": "2026-10-24T02:50:00.000Z",
            }
        )
        trans[GATE] = [
            {
                "transitionId": 7,
                "qitemId": GATE,
                "ts": "2026-10-24T02:50:00.000Z",
                "state": gate_state,
                "transitionNote": "gate owned, judging parent close",
            },
        ]
    list_path = Path(tmpdir) / "queue_list.json"
    trans_path = Path(tmpdir) / "transitions.json"
    list_path.write_text(json.dumps(qlist))
    trans_path.write_text(json.dumps(trans))
    return str(list_path), str(trans_path)


def run_reconcile(*args):
    return subprocess.run(
        [sys.executable, str(RECONCILE_SCRIPT), *args],
        capture_output=True,
        text=True,
    )


GENERATE_SCRIPT = REPO_ROOT / "scripts" / "generate_trackers.py"


def run_generate(*args):
    return subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def parent_row(status_cell):
    return {
        "file": "<fixture>",
        "line": 7,
        "slice": "B2-parent mission-row",
        "qitem": PARENT,
        "status": status_cell,
    }


# ---------------------------------------------------------------------------
# REQ-M1 — charter closure ownership
# ---------------------------------------------------------------------------


class TestCharterClosureOwnership(unittest.TestCase):
    def test_rendered_skill_states_destination_seat_closure_rule(self):
        """REQ-M1: the destination seat closes its own row (done + closure
        reason) once acceptance evidence is on the row."""
        text = SKILL_LEAF.read_text(encoding="utf-8")
        self.assertIn("closes its own row", text)
        self.assertIn("closure reason", text)

    def test_rendered_skill_states_gate_exemption(self):
        """REQ-M1: a --gate qitem with a live owner exempts the row (the
        gate owner owns next action)."""
        text = SKILL_LEAF.read_text(encoding="utf-8")
        self.assertIn("--gate", text)
        self.assertIn("live owner", text)

    def test_rendered_skill_names_no_gateless_waiting(self):
        """REQ-M1: gateless 'standing by' prose is directed, never a wait."""
        text = SKILL_LEAF.read_text(encoding="utf-8")
        self.assertIn("77-mission-gates", text)
        self.assertIn("standing by for gate", text.lower())


# ---------------------------------------------------------------------------
# REQ-M2 — gateless awaiting-gate counts as stalled
# ---------------------------------------------------------------------------


class TestStalledAwaitingGate(unittest.TestCase):
    def test_b2_pattern_flagged_stalled(self):
        """REQ-M2 B2 pattern: verdict recorded + standing-by prose + no
        gate qitem -> stalled-awaiting-gate diff naming the missing gate."""
        model = load_model()
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, GATELESS_STATUS)
            qlist, trans = write_queue(tmp)
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stalled-awaiting-gate", proc.stdout)
            self.assertIn(PARENT, proc.stdout)
            self.assertIn("gate", proc.stdout.lower())

    def test_b2_pattern_diff_names_missing_gate(self):
        """REQ-M2: the diff routes for human review with the gate missing
        named explicitly (diff_row level)."""
        model = load_model()
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        diff = model.diff_row(parent_row(GATELESS_STATUS), queue_by_id, {})
        self.assertIsNotNone(diff)
        self.assertEqual(diff["class"], "stalled-awaiting-gate")
        self.assertIn("gate", diff["reason"].lower())
        self.assertIn("no live gate qitem", diff["reason"])

    def test_gated_waiting_with_live_gate_stays_quiet(self):
        """REQ-M2 exemption: awaiting-gate prose WITH a live gate qitem
        (live owner) emits no stalled diff for that row."""
        model = load_model()
        queue_by_id = {
            PARENT: {"qitemId": PARENT, "state": "in-progress"},
            GATE: {
                "qitemId": GATE,
                "state": "in-progress",
                "destinationSession": "qa-seat@rig",
            },
        }
        trail = {
            GATE: [
                {
                    "transitionId": 7,
                    "state": "in-progress",
                    "transitionNote": "gate owned",
                }
            ]
        }
        diff = model.diff_row(parent_row(GATE_STATUS), queue_by_id, trail)
        self.assertIsNone(diff, f"live gate must exempt the row, got {diff}")
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, GATE_STATUS)
            qlist, trans = write_queue(tmp, gate_state="in-progress")
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertNotIn("stalled-awaiting-gate", proc.stdout)

    def test_dead_gate_reference_still_stalled(self):
        """REQ-M2 liveness: a gate qitem whose owner is gone (terminal
        gate state) does NOT exempt — the row still waits gateless."""
        model = load_model()
        queue_by_id = {
            PARENT: {"qitemId": PARENT, "state": "in-progress"},
            GATE: {
                "qitemId": GATE,
                "state": "closed",
                "destinationSession": "qa-seat@rig",
            },
        }
        diff = model.diff_row(parent_row(GATE_STATUS), queue_by_id, {})
        self.assertIsNotNone(diff)
        self.assertEqual(diff["class"], "stalled-awaiting-gate")

    def test_unrelated_awaiting_prose_without_gate_stays_quiet(self):
        """Scope guard: awaiting prose that names NO gate must not trip
        the stalled signal (no over-flagging of ordinary waits)."""
        model = load_model()
        row = parent_row("STAGED 6 files, awaiting QA")
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        self.assertIsNone(model.diff_row(row, queue_by_id, {}))

    def test_sabotage_classifier_removed_returns_to_silent(self):
        """Red-proof (REQ-M2): with the awaiting-gate classifier disabled
        the B2 fixture returns to silent-None — proving the diff fires on
        the classification, not on incidental prose."""
        model = load_model()
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        with mock.patch.object(model, "is_awaiting_gate_prose", return_value=False):
            self.assertIsNone(
                model.diff_row(parent_row(GATELESS_STATUS), queue_by_id, {})
            )
        self.assertIsNotNone(
            model.diff_row(parent_row(GATELESS_STATUS), queue_by_id, {})
        )

    def test_generator_names_missing_gate_in_review(self):
        """REQ-M2 review routing: the proposal emitter routes the gateless
        parent NEEDS-HUMAN-REVIEW with the missing gate named explicitly
        (stalled-awaiting-gate, never silent generic OTHER, never a
        paste-ready terminal cell)."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, GATELESS_STATUS)
            qlist, trans = write_queue(tmp)
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stalled-awaiting-gate", proc.stdout)
            self.assertIn("NEEDS-HUMAN-REVIEW", proc.stdout)
            self.assertIn("no live gate qitem", proc.stdout)
            self.assertNotIn("PROPOSED-CELL:::", proc.stdout)

    def test_generator_live_gate_exempt_from_stalled_review(self):
        """REQ-M2 exemption on the emitter path: a live gate qitem keeps
        the row out of stalled review."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, GATE_STATUS)
            qlist, trans = write_queue(tmp, gate_state="in-progress")
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertNotIn("stalled-awaiting-gate", proc.stdout)


# ---------------------------------------------------------------------------
# REQ-M3 — recovery not dismissible without state change
# ---------------------------------------------------------------------------


def flagged_row(state_cell=GATELESS_STATUS):
    """Flagged parent row state (B2 pattern): in-progress, gateless wait."""
    return {
        "qitemId": PARENT,
        "state": "in-progress",
        "blockedOn": None,
        "destinationSession": "owner-seat",
        "statusCell": state_cell,
    }


class TestNonDismissibleRecovery(unittest.TestCase):
    def test_dismissal_without_change_refused(self):
        """REQ-M3: closing the recovery item while the flagged row is
        byte-identical to flag time is refused; the row keeps its state."""
        sweep = load_sweep()
        row = flagged_row()
        before = dict(row)
        flagged = sweep.snapshot_row_state(row)
        with self.assertRaises(sweep.RecoveryDismissalRefused):
            sweep.check_recovery_dismissal(
                "recovery-B2-01", PARENT, flagged, sweep.snapshot_row_state(row)
            )
        self.assertEqual(row, before, "refusal must not touch row state")

    def test_dismissal_with_change_allowed(self):
        """REQ-M3: once the flagged row moved (owner acted: gate recorded,
        row advanced), closing the recovery item succeeds."""
        sweep = load_sweep()
        flagged = sweep.snapshot_row_state(flagged_row())
        moved = flagged_row(
            "verdict recorded; gate qitem %s (owner qa-seat@rig)" % GATE
        )
        outcome = sweep.check_recovery_dismissal(
            "recovery-B2-01", PARENT, flagged, sweep.snapshot_row_state(moved)
        )
        self.assertEqual(outcome["dismissal"], "permitted")
        self.assertEqual(outcome["flagged_qitem"], PARENT)

    def test_refusal_log_line_redacted(self):
        """REQ-M3: the refusal log line carries no secret-shaped runs —
        every interpolated path goes through _redact_for_log."""
        import re as _re

        sweep = load_sweep()
        nasty_recovery = "recovery-DUMMY-" + "A" * 45
        nasty_qitem = "qitem-DUMMY-" + "b" * 45
        flagged = sweep.snapshot_row_state(flagged_row())
        with self.assertRaises(sweep.RecoveryDismissalRefused) as ctx:
            sweep.check_recovery_dismissal(
                nasty_recovery, nasty_qitem, flagged, flagged
            )
        message = str(ctx.exception)
        self.assertIn("recovery-dismissal-refused", message)
        self.assertIn("redacted", message)
        self.assertEqual(
            _re.findall(r"[A-Za-z0-9_-]{40,}", message),
            [],
            f"unredacted bearer-shaped run in refusal line: {message[:120]}",
        )

    def test_bypassed_guard_restores_b2_dismissal(self):
        """Red-proof (REQ-M3): closing WITHOUT the guard on identical
        snapshots succeeds — proving the guard (not incidental shape) is
        what refuses the B2 dismissal."""
        sweep = load_sweep()
        flagged = sweep.snapshot_row_state(flagged_row())
        now = sweep.snapshot_row_state(flagged_row())
        self.assertEqual(flagged, now)
        closed = []  # unguarded closer: marks the recovery item closed
        closed.append("recovery-B2-01")
        self.assertEqual(closed, ["recovery-B2-01"])
        with self.assertRaises(sweep.RecoveryDismissalRefused):
            sweep.check_recovery_dismissal("recovery-B2-01", PARENT, flagged, now)

    def test_guard_issues_no_writes_and_never_done(self):
        """Scope guard (D2 + never-done): the guard returns data or raises;
        it performs no rig write and emits no done/complete/closed state."""
        import inspect as _inspect

        sweep = load_sweep()
        source = _inspect.getsource(sweep.check_recovery_dismissal)
        for token in ("apply_update", "subprocess", "os.system", "Popen"):
            self.assertNotIn(token, source)
        outcome = sweep.check_recovery_dismissal(
            "recovery-B2-01",
            PARENT,
            sweep.snapshot_row_state(flagged_row()),
            sweep.snapshot_row_state(
                flagged_row("verdict recorded; row advanced to QA PASS")
            ),
        )
        blob = json.dumps(outcome, sort_keys=True).lower()
        for terminal in ('"done"', '"complete"', '"completed"', '"closed"'):
            self.assertNotIn(terminal, blob)


if __name__ == "__main__":
    unittest.main()
