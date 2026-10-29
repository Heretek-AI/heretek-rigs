#!/usr/bin/env python3
"""Corpus for seat idle-park + daemon source (issue #81, REQ-I1/I2/I3 + S2.1).

Fixtures only (/tmp scratch, dummy ids — never the live mission checkout).

REQ-I1 (charter claim+first-action is one turn): the queue-handoff skill,
authored via fleet/skill-patches/ + regen (never hand-edited leaves),
states that claiming a qitem and the first work action are one turn — a
seat holding an open obligation MUST NOT end its turn right after the claim.

REQ-I2 (claim-then-park counts as stalled with latency attribution):
reconcile_model emits a stalled-idle-park diff for claim recorded + no work
action + parked-at-prompt while holding an open obligation (Mission-A
pattern), routing for human review with park-to-wake vs work attribution
attached. Obligation-free idle and live-gate waiting stay quiet.
Propose-only throughout: classification + report only, no row state is
written by anything here.

REQ-I3 (daemon handoffs carry a distinct source, never operator):
send_identity exposes the daemon-source rule (daemon:stuck-sweep); a daemon
handoff presenting as operator is relabeled to the daemon source with a
redacted log line, never recorded as an operator relay. Genuine operator
relays via send-authenticated.sh are untouched (wave-9 attestation intact).

S2.1 (non-dismissible idle-park recovery): closing an idle-park recovery
item while the flagged row's state is byte-identical to flag time is
refused fail-closed with a redacted log line; a changed row may close.
The guard never writes done.

Refs #81 (never Closes #81 — the issue stays open for the live-fleet proof).
"""

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
RECONCILE_SCRIPT = REPO_ROOT / "scripts" / "reconcile.py"
SKILL_LEAF = (
    REPO_ROOT / "specs" / "agents" / "_shared" / "skills" / "queue-handoff" / "SKILL.md"
)

PARENT = "qitem-20261023213329-7ad896bfc962330d"
RECOVERY_DAEMON = "qitem-recovery-3b06228ed0da95e8"
IDLE_STATUS = (
    "claimed, 1 open obligation; Handoff received \u2014 pulling the queue item; "
    "parked (arbitrated: idle at prompt)"
)
CLAIM_TS = "2026-10-23T21:33:29.000Z"
HANDOFF_TS = "2026-10-23T21:33:37.000Z"
PARK_TS = "2026-10-23T21:34:00.000Z"
WAKE_TS = "2026-10-23T21:34:53.000Z"
WATCHDOG_NOTE = (
    "[OpenRig watchdog scheduler \u00b7 policy: parked-owner-consumer \u2026] "
    "You are parked (arbitrated: idle at prompt) while holding 1 open obligation"
)


def load_model():
    spec = importlib.util.spec_from_file_location(
        "reconcile_model_idle", str(REPO_ROOT / "scripts" / "reconcile_model.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_send_identity():
    spec = importlib.util.spec_from_file_location(
        "send_identity_idle", str(REPO_ROOT / "scripts" / "send_identity.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sweep():
    spec = importlib.util.spec_from_file_location(
        "sweep_typed_blocks_idle",
        str(REPO_ROOT / "scripts" / "sweep-typed-blocks.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def idle_trail(work_note=None, park_last=True):
    trail = [
        {
            "transitionId": 11,
            "qitemId": PARENT,
            "ts": CLAIM_TS,
            "state": "in-progress",
            "transitionNote": "claimed",
        },
        {
            "transitionId": 12,
            "qitemId": PARENT,
            "ts": HANDOFF_TS,
            "state": "in-progress",
            "transitionNote": "Handoff received \u2014 pulling the queue item",
        },
    ]
    if work_note is not None:
        trail.append(
            {
                "transitionId": 13,
                "qitemId": PARENT,
                "ts": PARK_TS,
                "state": "in-progress",
                "transitionNote": work_note,
            }
        )
    if park_last:
        trail.append(
            {
                "transitionId": 14,
                "qitemId": PARENT,
                "ts": PARK_TS,
                "state": "in-progress",
                "transitionNote": WATCHDOG_NOTE,
            }
        )
    return trail


def write_tracker(tmpdir, status_cell, name="mission-dispatch-tracker.md"):
    path = Path(tmpdir) / name
    path.write_text(
        """\
# Mission Dispatch Tracker (synthetic 81-seat-idle replica)

## Slices
| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| A-parent seat-row | owner-seat | claim recorded | %s | %s |

## Rules (all slices)
No commits by seats.
"""
        % (PARENT, status_cell)
    )
    return str(path)


def write_queue(tmpdir, trail):
    qlist = [
        {
            "qitemId": PARENT,
            "state": "in-progress",
            "destinationSession": "owner-seat",
            "tsUpdated": PARK_TS,
        }
    ]
    trans = {PARENT: trail}
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


def parent_row(status_cell):
    return {
        "file": "<fixture>",
        "line": 7,
        "slice": "A-parent seat-row",
        "qitem": PARENT,
        "status": status_cell,
    }


def idle_queue_by_id(state="in-progress"):
    return {PARENT: {"qitemId": PARENT, "state": state}}


# ---------------------------------------------------------------------------
# REQ-I1 — charter claim+first-action is one turn
# ---------------------------------------------------------------------------


class TestCharterClaimFirstAction(unittest.TestCase):
    def test_patch_input_exists_with_replacements(self):
        """REQ-I1: the rule rides the generator (fleet/skill-patches/ +
        regen), never a hand-edited leaf."""
        patch_path = REPO_ROOT / "fleet" / "skill-patches" / "queue-handoff.yaml"
        self.assertTrue(patch_path.is_file(), f"missing {patch_path}")
        import yaml

        patch = yaml.safe_load(patch_path.read_text(encoding="utf-8"))
        self.assertEqual(patch.get("skill"), "queue-handoff")
        self.assertIn("81", str(patch.get("reason")))
        replacements = patch.get("replacements") or []
        self.assertTrue(replacements, "patch needs a non-empty replacements list")
        self.assertTrue(
            any("first work action" in r.get("new", "") for r in replacements),
            "patch must add the claim+first-action rule",
        )

    def test_rendered_skill_states_one_turn_rule(self):
        """REQ-I1: claiming a qitem and the first work action are one turn —
        no park-at-prompt after claim while holding an open obligation."""
        text = SKILL_LEAF.read_text(encoding="utf-8")
        self.assertIn("first work action", text)
        self.assertIn("one turn", text)
        self.assertIn("open obligation", text)

    def test_rendered_skill_names_idle_park_change(self):
        """REQ-I1: the rendered rule carries the 81-seat-idle change tag so
        the V30 gate can pin it."""
        text = SKILL_LEAF.read_text(encoding="utf-8")
        self.assertIn("81-seat-idle", text)

    def test_all_nine_leaves_carry_rule(self):
        """REQ-I1: every rendered queue-handoff leaf (specs + 8 rigs)
        carries the rule — zero hand-edited leaves, generator-applied."""
        leaves = [SKILL_LEAF] + sorted(
            (REPO_ROOT / "rigs").glob("*/agents/_shared/skills/queue-handoff/SKILL.md")
        )
        self.assertEqual(len(leaves), 9, f"expected 9 leaves, got {len(leaves)}")
        for leaf in leaves:
            text = leaf.read_text(encoding="utf-8")
            for marker in ("first work action", "one turn", "81-seat-idle"):
                self.assertIn(
                    marker, text, f"leaf {leaf.relative_to(REPO_ROOT)} lost {marker!r}"
                )


# ---------------------------------------------------------------------------
# REQ-I2 — claim-then-park counts as stalled with latency attribution
# ---------------------------------------------------------------------------


class TestStalledIdlePark(unittest.TestCase):
    def test_mission_a_pattern_flagged_stalled(self):
        """REQ-I2 Mission-A pattern: claim + handoff receipt + parked-at-
        prompt watchdog holding 1 open obligation, no work action ->
        stalled-idle-park diff naming the parked obligation."""
        model = load_model()
        diff = model.stalled_idle_park_diff(
            parent_row(IDLE_STATUS), idle_queue_by_id(), {PARENT: idle_trail()}
        )
        self.assertIsNotNone(diff)
        self.assertEqual(diff["class"], "stalled-idle-park")
        self.assertIn("open obligation", diff["reason"])
        self.assertIn("parked", diff["reason"].lower())

    def test_flagged_diff_routes_human_review_with_attribution(self):
        """REQ-I2: the diff routes for human review with park-to-wake vs
        work attribution attached (report-only, never state writes)."""
        model = load_model()
        diff = model.stalled_idle_park_diff(
            parent_row(IDLE_STATUS), idle_queue_by_id(), {PARENT: idle_trail()}
        )
        self.assertIn("review", diff["proposal"].lower())
        self.assertIn("park-to-wake", diff["proposal"])
        self.assertIn("attribution", diff)
        self.assertIn("park-to-wake", json.dumps(diff["attribution"]))

    def test_reconcile_cli_flags_idle_park(self):
        """REQ-I2 end to end: the Mission-A fixture exits 1 with the
        stalled-idle-park signal and attribution lines on stdout."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, IDLE_STATUS)
            qlist, trans = write_queue(tmp, idle_trail())
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stalled-idle-park", proc.stdout)
            self.assertIn(PARENT, proc.stdout)
            self.assertIn("park-to-wake", proc.stdout)

    def test_obligation_free_idle_stays_quiet(self):
        """REQ-I2 scope guard: parked-at-prompt prose with NO open
        obligation emits no idle-park diff."""
        model = load_model()
        quiet_status = "parked (arbitrated: idle at prompt); queue exhausted"
        diff = model.stalled_idle_park_diff(
            parent_row(quiet_status), idle_queue_by_id(), {PARENT: idle_trail()}
        )
        self.assertIsNone(diff, f"obligation-free idle must stay quiet, got {diff}")
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, quiet_status)
            qlist, trans = write_queue(tmp, idle_trail())
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertNotIn("stalled-idle-park", proc.stdout)

    def test_live_gate_waiting_stays_quiet(self):
        """REQ-I2 scope guard: live-gate waiting (live owner named, no open
        obligation) emits no idle-park diff."""
        model = load_model()
        gate = "qitem-20261024024002-abcdef0123456789"
        waiting = (
            "Standing by for gate --gate qa-seat, gate qitem %s "
            "(owner qa-seat@rig); parked, gate owner owns next action" % gate
        )
        queue_by_id = {
            PARENT: {"qitemId": PARENT, "state": "in-progress"},
            gate: {
                "qitemId": gate,
                "state": "in-progress",
                "destinationSession": "qa-seat@rig",
            },
        }
        diff = model.stalled_idle_park_diff(
            parent_row(waiting), queue_by_id, {PARENT: idle_trail()}
        )
        self.assertIsNone(diff, f"live-gate waiting must stay quiet, got {diff}")

    def test_work_action_present_stays_quiet(self):
        """REQ-I2 scope guard: a recorded first work action (verdict filed)
        means the seat did not park right after the claim — quiet."""
        model = load_model()
        trail = idle_trail(
            work_note="verdict recorded, findings filed per t13", park_last=False
        )
        diff = model.stalled_idle_park_diff(
            parent_row("claimed; verdict recorded, findings filed"),
            idle_queue_by_id(),
            {PARENT: trail},
        )
        self.assertIsNone(diff, f"worked row must stay quiet, got {diff}")

    def test_attribution_reports_park_to_wake_vs_work(self):
        """REQ-I2 attribution: claim/park/wake timestamps yield the
        park-to-wake share vs work share (inputs for #15/#17)."""
        model = load_model()
        trail = idle_trail() + [
            {
                "transitionId": 15,
                "qitemId": PARENT,
                "ts": WAKE_TS,
                "state": "in-progress",
                "transitionNote": "watchdog release: owner woken, obligation still open",
            }
        ]
        attribution = model.attribute_idle_latency(trail)
        self.assertEqual(attribution["claim_ts"], CLAIM_TS)
        self.assertEqual(attribution["park_ts"], PARK_TS)
        self.assertIsNone(attribution["work_ts"])
        self.assertEqual(attribution["work_s"], 0)
        self.assertGreater(attribution["park_to_wake_s"], 0)
        self.assertIn("park-to-wake", attribution["note"])

    def test_attribution_is_report_only(self):
        """REQ-I2 propose-only: attribution performs no rig write and the
        diff path writes no tracker or queue state."""
        import inspect as _inspect

        model = load_model()
        for fn in (
            model.attribute_idle_latency,
            model.stalled_idle_park_diff,
            model.diff_row,
        ):
            source = _inspect.getsource(fn)
            for token in (
                "apply_update",
                "subprocess",
                "os.system",
                "Popen",
                "write_out_exclusive",
                "open(",
            ):
                self.assertNotIn(
                    token, source, f"{fn.__name__} must not touch state ({token})"
                )

    def test_sabotage_classifier_removed_returns_to_silent(self):
        """Red-proof S1a (REQ-I2): with the idle-park classification
        disabled the Mission-A fixture returns to silent-None — proving the
        diff fires on the classification, not on incidental prose."""
        model = load_model()
        queue_by_id = idle_queue_by_id()
        with mock.patch.object(model, "is_idle_park_prose", return_value=False):
            self.assertIsNone(
                model.stalled_idle_park_diff(
                    parent_row(IDLE_STATUS), queue_by_id, {PARENT: idle_trail()}
                )
            )
        self.assertIsNotNone(
            model.stalled_idle_park_diff(
                parent_row(IDLE_STATUS), queue_by_id, {PARENT: idle_trail()}
            )
        )

    def test_obligation_free_quiet_both_ways(self):
        """Red-proof S1b (REQ-I2): obligation-free idle stays quiet with
        the classifier on and off (no over-flagging either way)."""
        model = load_model()
        quiet_status = "parked (arbitrated: idle at prompt); queue exhausted"
        queue_by_id = idle_queue_by_id()
        self.assertIsNone(
            model.stalled_idle_park_diff(
                parent_row(quiet_status), queue_by_id, {PARENT: idle_trail()}
            )
        )
        with mock.patch.object(model, "is_idle_park_prose", return_value=False):
            self.assertIsNone(
                model.stalled_idle_park_diff(
                    parent_row(quiet_status), queue_by_id, {PARENT: idle_trail()}
                )
            )

    def test_live_gate_quiet_both_ways(self):
        """Red-proof S1c (REQ-I2): live-gate waiting stays quiet with the
        classifier on and off."""
        model = load_model()
        gate = "qitem-20261024024002-abcdef0123456789"
        waiting = (
            "Standing by for gate --gate qa-seat, gate qitem %s "
            "(owner qa-seat@rig); parked, gate owner owns next action" % gate
        )
        queue_by_id = {
            PARENT: {"qitemId": PARENT, "state": "in-progress"},
            gate: {
                "qitemId": gate,
                "state": "in-progress",
                "destinationSession": "qa-seat@rig",
            },
        }
        self.assertIsNone(
            model.stalled_idle_park_diff(
                parent_row(waiting), queue_by_id, {PARENT: idle_trail()}
            )
        )
        with mock.patch.object(model, "is_idle_park_prose", return_value=False):
            self.assertIsNone(
                model.stalled_idle_park_diff(
                    parent_row(waiting), queue_by_id, {PARENT: idle_trail()}
                )
            )


# ---------------------------------------------------------------------------
# REQ-I3 — daemon handoffs carry a distinct source, never operator
# ---------------------------------------------------------------------------


class TestDaemonSource(unittest.TestCase):
    def test_operator_labeled_daemon_handoff_relabeled(self):
        """REQ-I3: a stuck-sweep recovery handoff of daemon origin labeled
        `From: operator` is relabeled to the distinct daemon source — never
        recorded as an operator relay."""
        si = load_send_identity()
        outcome = si.validate_handoff_source(
            origin="daemon:stuck-sweep", presented_from="operator"
        )
        self.assertEqual(outcome["source"], "daemon:stuck-sweep")
        self.assertEqual(outcome["action"], "relabeled")
        self.assertNotEqual(outcome["source"], "operator")

    def test_daemon_labeled_daemon_source_persists(self):
        """REQ-I3: a correctly labeled daemon handoff persists with the
        distinct source (no refusal of honest labels)."""
        si = load_send_identity()
        outcome = si.validate_handoff_source(
            origin="daemon:stuck-sweep", presented_from="daemon:stuck-sweep"
        )
        self.assertEqual(outcome["source"], "daemon:stuck-sweep")
        self.assertEqual(outcome["action"], "persisted")

    def test_genuine_operator_relay_untouched(self):
        """REQ-I3: an operator-origin relay keeps the operator source and
        wave-9 attestation handling is unchanged
        (attested/unverified/rejected preserved)."""
        si = load_send_identity()
        outcome = si.validate_handoff_source(
            origin="operator", presented_from="operator"
        )
        self.assertEqual(outcome["source"], "operator")
        self.assertTrue(hasattr(si, "mint_attestation"))
        self.assertTrue(hasattr(si, "verify_attestation"))
        binding = "dummy-binding-secret-for-81-seat-idle"
        seen: set = set()
        attestation = si.mint_attestation(binding, "a@r", "r")
        result = si.verify_attestation(
            binding, attestation, expected_rig="r", expected_sender="a@r", seen=seen
        )
        self.assertEqual(result.status, "attested")
        replayed = si.verify_attestation(
            binding, attestation, expected_rig="r", expected_sender="a@r", seen=seen
        )
        self.assertEqual(replayed.status, "rejected")

    def test_relabel_log_line_redacted(self):
        """REQ-I3: the relabel log line carries no secret-shaped runs —
        every interpolated path goes through _redact_for_log."""
        import io
        from contextlib import redirect_stderr

        si = load_send_identity()
        nasty_origin = "daemon:stuck-sweep-" + "A" * 45
        buf = io.StringIO()
        with redirect_stderr(buf):
            outcome = si.validate_handoff_source(
                origin=nasty_origin, presented_from="operator"
            )
        logged = buf.getvalue()
        self.assertEqual(outcome["source"], "daemon:stuck-sweep")
        self.assertIn("daemon-source", logged)
        self.assertIn("redacted", logged)
        self.assertEqual(
            re.findall(r"[A-Za-z0-9_-]{40,}", logged),
            [],
            f"unredacted bearer-shaped run in relabel line: {logged[:120]}",
        )

    def test_sabotage_allow_operator_restores_collision(self):
        """Red-proof S1d (REQ-I3): allowing the operator label for daemon
        origin restores the #81/#9 collision — proving the validator (not
        incidental shape) is what enforces the distinct source."""
        si = load_send_identity()
        with mock.patch.object(
            si,
            "validate_handoff_source",
            return_value={"source": "operator", "action": "persisted"},
        ):
            outcome = si.validate_handoff_source(
                origin="daemon:stuck-sweep", presented_from="operator"
            )
            self.assertEqual(
                outcome["source"],
                "operator",
                "bypassed validator restores the operator-label collision",
            )
        outcome = si.validate_handoff_source(
            origin="daemon:stuck-sweep", presented_from="operator"
        )
        self.assertEqual(outcome["source"], "daemon:stuck-sweep")


# ---------------------------------------------------------------------------
# S2.1 — non-dismissible idle-park recovery
# ---------------------------------------------------------------------------


def idle_flagged_row(state_cell=IDLE_STATUS):
    """Flagged idle-park parent row state (Mission-A pattern)."""
    return {
        "qitemId": PARENT,
        "state": "in-progress",
        "blockedOn": None,
        "destinationSession": "owner-seat",
        "statusCell": state_cell,
    }


class TestIdleParkNonDismissibleRecovery(unittest.TestCase):
    def test_dismissal_without_change_refused(self):
        """S2.1: closing the idle-park recovery item while the flagged row
        is byte-identical to flag time is refused; the row keeps its state."""
        sweep = load_sweep()
        row = idle_flagged_row()
        before = dict(row)
        flagged = sweep.snapshot_row_state(row)
        with self.assertRaises(sweep.RecoveryDismissalRefused):
            sweep.check_recovery_dismissal(
                "recovery-idle-park-01", PARENT, flagged, sweep.snapshot_row_state(row)
            )
        self.assertEqual(row, before, "refusal must not touch row state")

    def test_dismissal_with_change_permitted(self):
        """S2.1: once the flagged row moved (owner acted: first work action
        recorded), closing the idle-park recovery item succeeds."""
        sweep = load_sweep()
        flagged = sweep.snapshot_row_state(idle_flagged_row())
        moved = idle_flagged_row("claimed; verdict recorded, findings filed per t15")
        outcome = sweep.check_recovery_dismissal(
            "recovery-idle-park-01", PARENT, flagged, sweep.snapshot_row_state(moved)
        )
        self.assertEqual(outcome["dismissal"], "permitted")
        self.assertEqual(outcome["flagged_qitem"], PARENT)

    def test_refusal_log_line_redacted(self):
        """S2.1: the refusal log line carries no secret-shaped runs."""
        sweep = load_sweep()
        nasty_recovery = "recovery-idle-park-" + "A" * 45
        nasty_qitem = "qitem-IDLE-" + "b" * 45
        flagged = sweep.snapshot_row_state(idle_flagged_row())
        with self.assertRaises(sweep.RecoveryDismissalRefused) as ctx:
            sweep.check_recovery_dismissal(
                nasty_recovery, nasty_qitem, flagged, flagged
            )
        message = str(ctx.exception)
        self.assertIn("recovery-dismissal-refused", message)
        self.assertIn("redacted", message)
        self.assertEqual(
            re.findall(r"[A-Za-z0-9_-]{40,}", message),
            [],
            f"unredacted bearer-shaped run in refusal line: {message[:120]}",
        )

    def test_guard_issues_no_writes_and_never_done(self):
        """Scope guard: the guard returns data or raises; it performs no rig
        write and emits no done/complete/closed state."""
        import inspect as _inspect

        sweep = load_sweep()
        source = _inspect.getsource(sweep.check_recovery_dismissal)
        for token in ("apply_update", "subprocess", "os.system", "Popen"):
            self.assertNotIn(token, source)
        outcome = sweep.check_recovery_dismissal(
            "recovery-idle-park-01",
            PARENT,
            sweep.snapshot_row_state(idle_flagged_row()),
            sweep.snapshot_row_state(
                idle_flagged_row("claimed; verdict recorded, findings filed per t15")
            ),
        )
        blob = json.dumps(outcome, sort_keys=True).lower()
        for terminal in ('"done"', '"complete"', '"completed"', '"closed"'):
            self.assertNotIn(terminal, blob)


if __name__ == "__main__":
    unittest.main()
