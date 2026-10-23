#!/usr/bin/env python3
"""Unit tests for the dispatch-tracker proposal generator (issue #57).

The generator (scripts/generate_trackers.py) emits paste-ready Status-cell
proposals from queue state WITHOUT mutating trackers or queue state
(REQ-G2). It consumes the shared reconcile row model
(scripts/reconcile_model.py: parse_tracker, normalize_tracker,
recorded_note_ids, queue_terminal, diff_row, propose_cell,
normalize_proposal_note, refuse_out_path, write_out_exclusive) and MUST NOT
own a parallel parser/normalizer/enum-mapping (REQ-G5).

Synthetic fixtures in /tmp only — never the live mission checkout and never
this repo's live files. Fixture shapes mirror tests/test_reconcile.py.

Covers REQ-G1 (7 paste-ready cells on the drifted Wave-1 pair, unchanged-row
listing, OTHER(<raw>)/orphan NEEDS-HUMAN-REVIEW with both-side evidence),
REQ-G2 (read-only + fresh-out guard incl. O_EXCL re-check), REQ-G3
(convergence replay of non-review cells to reconcile exit 0), REQ-G4
(fail-closed matrix incl. the EMPTY QUEUE LIST hard failure), REQ-G5
(shared-model imports, no forked parser).
"""

import hashlib
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
SCRIPT = REPO_ROOT / "scripts" / "generate_trackers.py"
MODEL = REPO_ROOT / "scripts" / "reconcile_model.py"
RECONCILE = REPO_ROOT / "scripts" / "reconcile.py"

QIDS = {
    "W1-01": "qitem-20261022052401-3af4e59b9c34bc58",
    "W1-02": "qitem-20261022052403-b120f5f7ba339bd9",
    "W1-03": "qitem-20261022052407-3d618a4431583b97",
    "W1-04": "qitem-20261022052409-291190744e33d1fe",
    "W1-05": "qitem-20261022052412-8a8c5130ff0d9fb0",
    "W1-06": "qitem-20261022052415-c8ac4d1c13408e78",
    "W1-07": "qitem-20261022052418-bf0bcb28d32a3065",
}

DRIFTED_TRACKER = """\
# Wave 1 Dispatch Tracker (synthetic pre-convergence replica)
Parent: qitem-20261022052237-f31eb9f55da995fb CLOSED done handed_off_to Wave 2 (transition 952).

## Slices (disjoint, one owner each)
| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| W1-01 workspace-root | build-ts-node-fullstack | root manifests, workspace configs | {q1} | STAGED 6 files, awaiting QA |
| W1-02 ts-configs | build-ts-node-fullstack | tsconfigs strict flags, eslint, prettier | {q2} | STAGED 9 files, awaiting QA |
| W1-03 rust-tauri | systems-rust-systems-spec | rustfmt/clippy, tauri conf | {q3} | QA PASS 4+merge (row note 3) |
| W1-04 ci-workflow | data-data-pipeline-eng | 4-job Actions workflow | {q4} | PARKED blocked on QA gate |
| W1-05 bff-protocol | build-go-backend-eng | bff + protocol scaffolds | {q5} | DISPATCHED pending |
| W1-06 web-tests | build-ts-node-fullstack | web + tests + e2e scaffolds | {q6} | STAGED 13 files, awaiting QA |
| W1-07 godot-model | gameplay-tech-artist-pipeline | godot-model scaffold | {q7} | STAGED scaffold, awaiting QA |

## Rules (all slices)
No commits by seats.
""".format(
    q1=QIDS["W1-01"],
    q2=QIDS["W1-02"],
    q3=QIDS["W1-03"],
    q4=QIDS["W1-04"],
    q5=QIDS["W1-05"],
    q6=QIDS["W1-06"],
    q7=QIDS["W1-07"],
)


def make_queue_state(tmpdir, latest_id=5, drop=()):
    """Write queue_list.json + transitions.json; return (list_path, trans_path).

    Every listed slice qitem is closed/handed off with a QA PASS + placed
    transition trail ending at latest_id.
    """
    qlist = []
    trans = {}
    for slc, qid in QIDS.items():
        if qid in drop:
            continue
        qlist.append(
            {
                "qitemId": qid,
                "state": "closed",
                "destinationSession": "seat@rig",
                "tsUpdated": "2026-10-22T12:00:00.000Z",
            }
        )
        trail = [
            {
                "transitionId": 1,
                "qitemId": qid,
                "ts": "2026-10-22T05:24:00.000Z",
                "state": "pending",
                "transitionNote": "created",
            },
            {
                "transitionId": 2,
                "qitemId": qid,
                "ts": "2026-10-22T05:30:00.000Z",
                "state": "in-progress",
                "transitionNote": "claimed",
            },
            {
                "transitionId": 3,
                "qitemId": qid,
                "ts": "2026-10-22T11:00:00.000Z",
                "state": "in-progress",
                "transitionNote": "QA PASS per wave1-qa-report",
            },
        ]
        if latest_id >= 4:
            trail.append(
                {
                    "transitionId": 4,
                    "qitemId": qid,
                    "ts": "2026-10-22T11:30:00.000Z",
                    "state": "in-progress",
                    "transitionNote": "placed canonical paths",
                }
            )
        if latest_id >= 5:
            trail.append(
                {
                    "transitionId": 5,
                    "qitemId": qid,
                    "ts": "2026-10-22T11:45:00.000Z",
                    "state": "closed",
                    "transitionNote": "handed_off_to Wave 2",
                }
            )
        trans[qid] = trail
    list_path = Path(tmpdir) / "queue_list.json"
    trans_path = Path(tmpdir) / "transitions.json"
    list_path.write_text(json.dumps(qlist))
    trans_path.write_text(json.dumps(trans))
    return str(list_path), str(trans_path)


def write_tracker(tmpdir, text, name="wave1-dispatch-tracker.md"):
    path = Path(tmpdir) / name
    path.write_text(text)
    return str(path)


def run_generate(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def run_reconcile(*args):
    return subprocess.run(
        [sys.executable, str(RECONCILE), *args],
        capture_output=True,
        text=True,
    )


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


class TestProposalCompleteness(unittest.TestCase):
    def test_drifted_wave1_emits_seven_paste_ready_cells(self):
        """REQ-G1: all 7 drifted rows yield full-replacement Status cells; exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            before = Path(tracker).read_bytes()
            qlist, trans = make_queue_state(tmp)
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            for slc, qid in QIDS.items():
                self.assertIn(slc, proc.stdout, f"proposal for {slc} missing")
                self.assertIn(qid, proc.stdout, f"qitem for {slc} missing")
            self.assertEqual(proc.stdout.count("PROPOSED-CELL:::"), 7, proc.stdout)
            self.assertIn("operator note appended", proc.stdout)
            self.assertEqual(Path(tracker).read_bytes(), before)

    def test_out_to_fresh_path_writes_proposal_tracker_untouched(self):
        """REQ-G1/G-T1 gate: --out emits paste-ready cells; git shows no mods."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            before = Path(tracker).read_bytes()
            qlist, trans = make_queue_state(tmp)
            dest = str(Path(tmp) / "wave1-proposal.txt")
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                dest,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertEqual(Path(tracker).read_bytes(), before)
            text = Path(dest).read_text()
            self.assertIn("W1-01", text)
            self.assertIn("PROPOSED-CELL:::", text)
            self.assertIn("TPM approval required", text)

    def test_converged_pair_lists_every_row_unchanged_and_exits_zero(self):
        """REQ-G1: agreeing rows are listed as unchanged (no partial-row silence)."""
        with tempfile.TemporaryDirectory() as tmp:
            rows = []
            for slc, qid in QIDS.items():
                rows.append(
                    "| %s | seat | output | %s | QA PASS + PLACED canonical "
                    "(queue note 5; operator note appended \u2014 "
                    "parked-on-QA blocker satisfied) |" % (slc, qid)
                )
            tracker = write_tracker(
                tmp,
                "# Wave 1 Dispatch Tracker (synthetic converged)\n\n"
                "## Slices\n"
                "| Slice | Owner seat | Output | Slice qitem | Status |\n"
                "|---|---|---|---|---|\n" + "\n".join(rows) + "\n",
            )
            qlist, trans = make_queue_state(tmp)
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("in sync", proc.stdout)
            for slc in QIDS:
                self.assertIn(slc, proc.stdout, f"{slc} not covered in summary")

    def test_unchanged_annotation_distinguishes_recorded_vs_non_terminal(self):
        """UNCHANGED lines must not claim a note is recorded when it is not."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(
                tmp,
                "# Wave 1 Dispatch Tracker (synthetic non-terminal pair)\n\n"
                "## Slices\n"
                "| Slice | Owner seat | Output | Slice qitem | Status |\n"
                "|---|---|---|---|---|\n"
                "| W1-01 | seat | output | %s | STAGED awaiting QA |\n" % QIDS["W1-01"],
            )
            qlist = [
                {
                    "qitemId": QIDS["W1-01"],
                    "state": "in-progress",
                    "destinationSession": "seat@rig",
                    "tsUpdated": "2026-10-22T12:00:00.000Z",
                }
            ]
            trans = {
                QIDS["W1-01"]: [
                    {
                        "transitionId": 2,
                        "qitemId": QIDS["W1-01"],
                        "ts": "2026-10-22T05:30:00.000Z",
                        "state": "in-progress",
                        "transitionNote": "claimed",
                    }
                ]
            }
            qlist_path = str(Path(tmp) / "queue_list.json")
            trans_path = str(Path(tmp) / "transitions.json")
            Path(qlist_path).write_text(json.dumps(qlist))
            Path(trans_path).write_text(json.dumps(trans))
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist_path,
                "--transitions",
                trans_path,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("UNCHANGED", proc.stdout)
            self.assertIn("no convergence note required", proc.stdout)
            self.assertNotIn("recorded)", proc.stdout)

    def test_note_append_only_on_newer_transition(self):
        """Design Q8: no churn — a cell already recording the latest note is unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(
                tmp,
                "# Wave 1 Dispatch Tracker (synthetic converged single)\n\n"
                "## Slices\n"
                "| Slice | Owner seat | Output | Slice qitem | Status |\n"
                "|---|---|---|---|---|\n"
                "| W1-01 | seat | output | %s | QA PASS + PLACED canonical "
                "(queue note 5: handed_off_to Wave 2; operator note appended) |\n"
                % QIDS["W1-01"],
            )
            qlist, trans = make_queue_state(tmp)
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("in sync", proc.stdout)
            self.assertNotIn("PROPOSED-CELL:::", proc.stdout)


class TestSharedRowModel(unittest.TestCase):
    def test_generator_imports_shared_model_no_fork(self):
        """REQ-G5: parsing/normalizing/terminal/diff resolve to reconcile_model."""
        spec = importlib.util.spec_from_file_location(
            "generate_trackers_under_test", str(SCRIPT)
        )
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        # The generator's `from reconcile_model import ...` binds the same
        # objects as the reconcile_model entry in sys.modules: identity with
        # that entry proves no forked implementation.
        model = sys.modules["reconcile_model"]
        for name in (
            "parse_tracker",
            "normalize_tracker",
            "recorded_note_ids",
            "queue_terminal",
            "diff_row",
            "propose_cell",
            "normalize_proposal_note",
            "refuse_out_path",
            "write_out_exclusive",
        ):
            self.assertIs(
                getattr(gen, name),
                getattr(model, name),
                f"generate_trackers.{name} must be the shared reconcile_model object",
            )
        source = Path(SCRIPT).read_text()
        for name in (
            "parse_tracker",
            "normalize_tracker",
            "recorded_note_ids",
            "queue_terminal",
            "diff_row",
        ):
            self.assertNotIn(
                f"def {name}",
                source,
                f"generate_trackers.py must not re-implement {name}",
            )


class TestOtherAndOrphan(unittest.TestCase):
    def _other_tracker(self, tmp):
        return write_tracker(
            tmp,
            "# Wave 1 Dispatch Tracker (synthetic OTHER prose)\n\n"
            "## Slices\n"
            "| Slice | Owner seat | Output | Slice qitem | Status |\n"
            "|---|---|---|---|---|\n"
            "| W1-01 | seat | output | %s | Awaiting triage by TPM |\n" % QIDS["W1-01"],
        )

    def test_unknown_prose_flagged_never_coerced(self):
        """REQ-G1: no-enum-arm prose -> OTHER(<raw>) + NEEDS-HUMAN-REVIEW, exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = self._other_tracker(tmp)
            qlist, trans = make_queue_state(tmp)
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            combined = proc.stdout + proc.stderr
            self.assertIn("OTHER(Awaiting triage by TPM)", combined)
            self.assertIn("NEEDS-HUMAN-REVIEW", combined)
            # Both-side evidence quoted: tracker raw cell and queue-side values.
            self.assertIn("Awaiting triage by TPM", combined)
            self.assertIn("state=closed", combined)
            # The status is NEVER guessed: no paste-ready canonical cell emitted.
            self.assertNotIn("PROPOSED-CELL:::", proc.stdout)

    def test_em_dash_row_is_review_diff_never_vanishes(self):
        """REQ-G1: row with no qitem -> tracker-row-without-qitem review marker."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(
                tmp,
                "# Wave 1 Dispatch Tracker (synthetic orphan)\n\n"
                "## Slices\n"
                "| Slice | Owner seat | Output | Slice qitem | Status |\n"
                "|---|---|---|---|---|\n"
                "| W1-09 operator-fix | seat | output | \u2014 | CLOSED operator-owned |\n",
            )
            qlist, trans = make_queue_state(tmp)
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("tracker-row-without-qitem", proc.stdout)
            self.assertIn("NEEDS-HUMAN-REVIEW", proc.stdout)
            self.assertIn("W1-09", proc.stdout)

    def test_qitem_without_queue_entry_is_review_diff(self):
        """REQ-G1: qitem with no queue entry -> review marker with both-side evidence."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp, drop=(QIDS["W1-05"],))
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("tracker-row-without-qitem", proc.stdout)
            self.assertIn("NEEDS-HUMAN-REVIEW", proc.stdout)
            self.assertIn("W1-05", proc.stdout)
            self.assertIn(QIDS["W1-05"], proc.stdout)

    def test_stale_terminal_carries_reverify_and_review_marker(self):
        """Design Q8: terminal tracker claim vs non-terminal queue -> re-verify + review."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(
                tmp,
                "# Wave 1 Dispatch Tracker (synthetic stale-terminal)\n\n"
                "## Slices\n"
                "| Slice | Owner seat | Output | Slice qitem | Status |\n"
                "|---|---|---|---|---|\n"
                "| W1-01 | seat | output | %s | QA PASS + PLACED canonical "
                "(queue note 5; operator note appended) |\n" % QIDS["W1-01"],
            )
            qlist = [
                {
                    "qitemId": QIDS["W1-01"],
                    "state": "in-progress",
                    "destinationSession": "seat@rig",
                    "tsUpdated": "2026-10-22T12:00:00.000Z",
                }
            ]
            trans = {
                QIDS["W1-01"]: [
                    {
                        "transitionId": 1,
                        "qitemId": QIDS["W1-01"],
                        "ts": "2026-10-22T05:24:00.000Z",
                        "state": "in-progress",
                        "transitionNote": "claimed",
                    }
                ]
            }
            qlist_path = str(Path(tmp) / "queue_list.json")
            trans_path = str(Path(tmp) / "transitions.json")
            Path(qlist_path).write_text(json.dumps(qlist))
            Path(trans_path).write_text(json.dumps(trans))
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist_path,
                "--transitions",
                trans_path,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("Re-verify W1-01 with QA", proc.stdout)
            self.assertIn("NEEDS-HUMAN-REVIEW", proc.stdout)


class TestReadOnlyAndFreshOut(unittest.TestCase):
    def test_run_leaves_tree_untouched_with_and_without_out(self):
        """REQ-G2: tracker + queue inputs byte-identical afterwards (md5 pre/post)."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            sums_before = {p: md5(p) for p in (tracker, qlist, trans)}
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            dest = str(Path(tmp) / "proposal.txt")
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                dest,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            for p, digest in sums_before.items():
                self.assertEqual(md5(p), digest, f"{p} modified by read-only run")

    def test_out_refusing_input_tracker(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            before = md5(tracker)
            qlist, trans = make_queue_state(tmp)
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                tracker,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("refusing", (proc.stdout + proc.stderr).lower())
            self.assertEqual(md5(tracker), before)

    def test_out_refusing_tracker_shaped_and_sprints_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            fresh = Path(tmp) / "freshdir"
            fresh.mkdir()
            dest = str(fresh / "victim-dispatch-tracker.md")
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                dest,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("refusing", (proc.stdout + proc.stderr).lower())
            self.assertFalse(Path(dest).exists())
            sprints_dir = fresh / "sprints"
            sprints_dir.mkdir()
            sprints_dest = str(sprints_dir / "review.txt")
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                sprints_dest,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("refusing", (proc.stdout + proc.stderr).lower())
            self.assertFalse(Path(sprints_dest).exists())

    def test_out_refusing_existing_file_bytes_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            dest = Path(tmp) / "proposal.txt"
            dest.write_text("PRE-EXISTING REVIEW NOTES \u2014 DO NOT OVERWRITE\n")
            before = md5(str(dest))
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                str(dest),
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("refusing", (proc.stdout + proc.stderr).lower())
            self.assertEqual(md5(str(dest)), before)

    def test_out_file_is_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            dest = str(Path(tmp) / "review-proposal.txt")
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                dest,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            mode = stat.S_IMODE(os.stat(dest).st_mode)
            self.assertEqual(mode & 0o077, 0, f"mode {oct(mode)} has group/other bits")


class TestFailClosed(unittest.TestCase):
    def test_missing_tracker_is_named_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            qlist, trans = make_queue_state(tmp)
            proc = run_generate(
                "--tracker",
                str(Path(tmp) / "no-such-tracker.md"),
                "--queue-list",
                qlist,
                "--transitions",
                trans,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            combined = proc.stdout + proc.stderr
            self.assertIn("UNREADABLE TRACKER", combined)
            self.assertIn("no-such-tracker.md", combined)
            self.assertNotIn("in sync", proc.stdout)

    def test_unparseable_row_names_file_and_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = DRIFTED_TRACKER.replace(
                "| W1-07 godot-model | gameplay-tech-artist-pipeline "
                "| godot-model scaffold | %s | STAGED scaffold, awaiting QA |"
                % QIDS["W1-07"],
                "| W1-07 godot-model | STAGED |",
            )
            tracker = write_tracker(tmp, bad)
            qlist, trans = make_queue_state(tmp)
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("UNPARSEABLE ROW", proc.stdout + proc.stderr)

    def test_missing_queue_json_is_named_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            _, trans = make_queue_state(tmp)
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                str(Path(tmp) / "no-queue.json"),
                "--transitions",
                trans,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("UNREADABLE QUEUE LIST", proc.stdout + proc.stderr)
            self.assertNotIn("in sync", proc.stdout)

    def test_invalid_queue_json_is_named_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json")
            proc = run_generate(
                "--tracker", tracker, "--queue-list", str(bad), "--transitions", trans
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("UNPARSEABLE QUEUE LIST", proc.stdout + proc.stderr)
            self.assertNotIn("in sync", proc.stdout)

    def test_wrong_shape_queue_list_is_named_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            _, trans = make_queue_state(tmp)
            shaped = Path(tmp) / "shaped.json"
            shaped.write_text(json.dumps({"qitemId": "not-a-list"}))
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                str(shaped),
                "--transitions",
                trans,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("UNPARSEABLE QUEUE LIST", proc.stdout + proc.stderr)

    def test_empty_queue_list_is_hard_failure_never_in_sync(self):
        """REQ-G4: a queue listing parsing to [] MUST fail exit 2, never agree."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            _, trans = make_queue_state(tmp)
            empty = Path(tmp) / "empty_list.json"
            empty.write_text("[]")
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                str(empty),
                "--transitions",
                trans,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            combined = proc.stdout + proc.stderr
            self.assertIn("EMPTY QUEUE LIST", combined)
            self.assertNotIn("in sync", proc.stdout)

    def test_unreachable_rig_binary_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            proc = run_generate(
                "--tracker",
                tracker,
                "--live",
                "--rig-bin",
                "rig-definitely-absent-57",
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("UNREACHABLE QUEUE", proc.stdout + proc.stderr)
            self.assertNotIn("in sync", proc.stdout)

    def test_non_dict_transition_items_exit_2_no_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            data = json.loads(Path(trans).read_text())
            data[QIDS["W1-01"]] = [42, "not-a-dict"]
            bad = str(Path(tmp) / "transitions_bad.json")
            Path(bad).write_text(json.dumps(data))
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                bad,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            combined = proc.stdout + proc.stderr
            self.assertNotIn("Traceback", combined)
            self.assertNotIn("in sync", proc.stdout)

    def test_hostile_note_proposal_is_single_line_pipe_free(self):
        """Design Q8: hostile queue notes normalize in proposals, raw in diagnostics."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(
                tmp,
                "# Wave 1 Dispatch Tracker (synthetic hostile)\n\n"
                "## Slices\n"
                "| Slice | Owner seat | Output | Slice qitem | Status |\n"
                "|---|---|---|---|---|\n"
                "| W1-01 | seat | output | %s | STAGED awaiting QA |\n" % QIDS["W1-01"],
            )
            qlist = [
                {
                    "qitemId": QIDS["W1-01"],
                    "state": "closed",
                    "destinationSession": "seat@rig",
                    "tsUpdated": "2026-10-22T12:00:00.000Z",
                }
            ]
            trans = {
                QIDS["W1-01"]: [
                    {
                        "transitionId": 9,
                        "qitemId": QIDS["W1-01"],
                        "ts": "2026-10-22T11:45:00.000Z",
                        "state": "closed",
                        "transitionNote": "QA PASS a|b\nc   d  placed",
                    }
                ]
            }
            qlist_path = str(Path(tmp) / "queue_list.json")
            trans_path = str(Path(tmp) / "transitions.json")
            Path(qlist_path).write_text(json.dumps(qlist))
            Path(trans_path).write_text(json.dumps(trans))
            proc = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist_path,
                "--transitions",
                trans_path,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            proposed = [
                ln
                for ln in proc.stdout.splitlines()
                if ln.startswith("PROPOSED-CELL:::")
            ]
            self.assertEqual(len(proposed), 1, proc.stdout)
            for line in proposed:
                self.assertNotIn("|", line)
            self.assertIn(
                "PROPOSED-CELL:::QA PASS + PLACED canonical "
                "(queue note 9: QA PASS a/b c d placed; "
                "operator note appended)",
                proc.stdout,
            )


class TestConvergenceReplay(unittest.TestCase):
    def test_applying_non_review_cells_converges_reconcile_to_zero_diffs(self):
        """REQ-G3: TPM-approval simulation — apply paste-ready cells, reconcile exits 0."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            first = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(first.returncode, 1, first.stdout + first.stderr)
            proposals = {}
            current_slice = None
            in_review = False
            for line in first.stdout.splitlines():
                if line.startswith("DIFF "):
                    parts = line.split("slice ", 1)[1]
                    current_slice = parts.split()[0]
                    in_review = False
                elif line.startswith("  NEEDS-HUMAN-REVIEW:"):
                    in_review = True
                    proposals.pop(current_slice, None)
                elif line.startswith("PROPOSED-CELL:::") and not in_review:
                    proposals[current_slice] = line.split(":::", 1)[1]
            # The drifted Wave-1 pair has zero review rows: every diff is paste-ready.
            self.assertEqual(len(proposals), 7, first.stdout)
            self.assertNotIn("  NEEDS-HUMAN-REVIEW:", first.stdout)
            lines = Path(tracker).read_text().splitlines()
            for i, line in enumerate(lines):
                for slc, cell in proposals.items():
                    if line.startswith("| %s " % slc):
                        cells = line.split("|")
                        cells[-2] = " " + cell + " "
                        lines[i] = "|".join(cells)
            # The TPM-approval simulation target is a scratch copy, and --out
            # MUST NOT target it: the refuse rule applies to generate too.
            scratch = write_tracker(tmp, "\n".join(lines) + "\n", name="scratch.md")
            refused = run_generate(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                scratch,
            )
            self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
            self.assertIn("refusing", (refused.stdout + refused.stderr).lower())
            second = run_reconcile(
                "--tracker", scratch, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn("in sync", second.stdout)


if __name__ == "__main__":
    unittest.main()
