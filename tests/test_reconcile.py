#!/usr/bin/env python3
"""Unit tests for the tracker-vs-queue reconcile diff command (issue #39).

Synthetic fixtures in /tmp only — never the live mission checkout and never
this repo's live files. The pre-convergence Wave-1 tracker below replicates
the live drifted state read-only from the mission repo
(docs/sprints/wave1-dispatch-tracker.md, 2026-10-22 issue evidence):
W1-01/02/06/07 STAGED/awaiting QA, W1-04 PARKED, W1-05 DISPATCHED, while the
queue shows all 7 slices QA-passed and placed. The command must FLAG every
drift class and PASS a converged pair with zero diffs.

Covers REQ-R1 (parse + compare, >=7 diffs naming file+row+both values),
REQ-R2 (propose paste-ready replacement text, strictly read-only), REQ-R3
(replay: applied proposals re-run to zero diffs + exit 0 "in sync"), REQ-R4
(fail-closed parsing: unreadable tracker, unparseable row, missing qitem,
unreachable queue).
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "reconcile.py"

QIDS = {
    "W1-01": "qitem-20261022052401-3af4e59b9c34bc58",
    "W1-02": "qitem-20261022052403-b120f5f7ba339bd9",
    "W1-03": "qitem-20261022052407-3d618a4431583b97",
    "W1-04": "qitem-20261022052409-291190744e33d1fe",
    "W1-05": "qitem-20261022052412-8a8c5130ff0d9fb0",
    "W1-06": "qitem-20261022052415-c8ac4d1c13408e78",
    "W1-07": "qitem-20261022052418-bf0bcb28d32a3065",
}

# Pre-convergence Wave-1 shape (issue #39 evidence, synthetic qitem ids stay
# in the live id shape but the file lives in /tmp): 4x STAGED/awaiting QA,
# 1x PARKED blocked on QA, 1x DISPATCHED, 1x QA PASS with a stale note id
# (queue moved on past it).
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


def make_queue_state(tmpdir, latest_id=5, drop=(), stale_note_rows=()):
    """Write queue_list.json + transitions.json; return (list_path, trans_path).

    Every slice qitem is closed/handed off with a QA PASS + placed
    transition trail. Rows in stale_note_rows keep an older latest
    transition (their tracker note is stale but the row still converged
    terminally on the queue side).
    """
    qlist = []
    trans = {}
    for slc, qid in QIDS.items():
        if qid in drop:
            continue
        top = 3 if qid in stale_note_rows else latest_id
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
        if top >= 4:
            trail.append(
                {
                    "transitionId": 4,
                    "qitemId": qid,
                    "ts": "2026-10-22T11:30:00.000Z",
                    "state": "in-progress",
                    "transitionNote": "placed canonical paths",
                }
            )
        if top >= 5:
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


def run_reconcile(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


class TestDriftClasses(unittest.TestCase):
    def test_pre_convergence_reports_at_least_seven_diffs(self):
        """REQ-R1: all 7 drifted Wave-1 rows surface, each naming file+row+both values."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            for slc, qid in QIDS.items():
                self.assertIn(slc, proc.stdout, f"diff for {slc} missing")
                self.assertIn(qid, proc.stdout, f"qitem for {slc} missing")
            self.assertIn("tracker:", proc.stdout)
            self.assertIn("queue:", proc.stdout)

    def test_stale_state_class_flagged(self):
        """REQ-R1 drift class 1: STAGED/DISPATCHED rows vs QA-passed+placed queue."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertIn("stale-state", proc.stdout)
            # W1-01 reads STAGED while the queue is closed/handed off.
            block = [ln for ln in proc.stdout.splitlines() if "W1-01" in ln]
            self.assertTrue(block, "no diff block names W1-01")

    def test_parked_satisfied_but_tracker_silent_flagged(self):
        """REQ-R1 drift class 2: PARKED-blocked-on-QA vs queue blocker-satisfied."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertIn("parked-satisfied-but-tracker-silent", proc.stdout)
            self.assertIn("W1-04", proc.stdout)

    def test_missing_convergence_annotation_flagged(self):
        """REQ-R1 drift class 3: terminal enum but stale note id (W1-03 note 3 vs latest 5)."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertIn("missing-convergence-annotation", proc.stdout)
            self.assertIn("W1-03", proc.stdout)

    def test_converged_pair_passes_with_zero_diffs(self):
        """REQ-R3: terminal enum + latest note recorded on every row -> exit 0 in sync."""
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
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("in sync", proc.stdout)
            self.assertIn("7 row", proc.stdout)


class TestProposeNeverEdit(unittest.TestCase):
    def test_run_is_read_only_and_proposals_are_paste_ready(self):
        """REQ-R2: tracker bytes identical afterwards; every diff has replacement text."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            before = Path(tracker).read_bytes()
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertEqual(Path(tracker).read_bytes(), before)
            self.assertEqual(proc.stdout.count("PROPOSED Status cell:"), 7)
            self.assertIn("operator note appended", proc.stdout)

    def test_out_refusing_tracker_path(self):
        """REQ-R2: --out pointing at an input tracker is refused (never auto-overwrite)."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
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

    def test_out_refusing_scratch_copy_of_tracker(self):
        """F1(i): --out to a scratch byte-copy of a tracker (a different path
        from the --tracker input) is refused; victim bytes identical."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            victim = write_tracker(
                tmp, DRIFTED_TRACKER, name="phase0-dispatch-tracker.md"
            )
            victim_before = Path(victim).read_bytes()
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                victim,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("refusing", (proc.stdout + proc.stderr).lower())
            self.assertEqual(Path(victim).read_bytes(), victim_before)

    def test_out_refusing_tracker_named_path_in_fresh_dir(self):
        """F1(ii): --out to a tracker-NAMED path in a fresh dir is refused
        even though nothing exists there yet (no file created); same for a
        fresh path inside a sprints/ tracker directory."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            fresh = Path(tmp) / "freshdir"
            fresh.mkdir()
            dest = str(fresh / "victim-dispatch-tracker.md")
            proc = run_reconcile(
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
            proc = run_reconcile(
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

    def test_out_refusing_existing_non_tracker_file(self):
        """F1(iii): --out to an existing non-tracker file is refused; bytes untouched."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            dest = Path(tmp) / "proposal.txt"
            dest.write_text("PRE-EXISTING REVIEW NOTES \u2014 DO NOT OVERWRITE\n")
            before = dest.read_bytes()
            proc = run_reconcile(
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
            self.assertEqual(dest.read_bytes(), before)

    def test_out_to_fresh_non_tracker_path_writes(self):
        """F1(iv): --out to a fresh non-tracker path writes the proposal (exit 1 on diffs)."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            before = Path(tracker).read_bytes()
            qlist, trans = make_queue_state(tmp)
            dest = str(Path(tmp) / "review-proposal.txt")
            proc = run_reconcile(
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
            self.assertIn("TPM approval required", text)

    def test_out_file_gets_proposal_and_tracker_untouched(self):
        """REQ-R2: --out writes the reviewable proposal outside any tracker."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            before = Path(tracker).read_bytes()
            qlist, trans = make_queue_state(tmp)
            out = str(Path(tmp) / "proposal.txt")
            proc = run_reconcile(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--out",
                out,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertEqual(Path(tracker).read_bytes(), before)
            self.assertIn("W1-01", Path(out).read_text())


class TestFailClosed(unittest.TestCase):
    def test_missing_tracker_is_named_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker",
                str(Path(tmp) / "no-such-tracker.md"),
                "--queue-list",
                qlist,
                "--transitions",
                trans,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("no-such-tracker.md", proc.stdout + proc.stderr)
            self.assertNotIn("in sync", proc.stdout)

    def test_unparseable_row_names_file_and_line(self):
        """REQ-R4: a short (wrong-column-count) table row fails, never silently drops."""
        with tempfile.TemporaryDirectory() as tmp:
            bad = DRIFTED_TRACKER.replace(
                "| W1-07 godot-model | gameplay-tech-artist-pipeline "
                "| godot-model scaffold | %s | STAGED scaffold, awaiting QA |"
                % QIDS["W1-07"],
                "| W1-07 godot-model | STAGED |",
            )
            tracker = write_tracker(tmp, bad)
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("UNPARSEABLE ROW", proc.stdout + proc.stderr)
            self.assertIn("W1-07", proc.stdout + proc.stderr)

    def test_missing_qitem_is_a_diff_not_a_drop(self):
        """REQ-R4 scenario: tracker row with no queue entry -> named diff, exit non-zero."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp, drop=(QIDS["W1-05"],))
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("tracker-row-without-qitem", proc.stdout)
            self.assertIn("W1-05", proc.stdout)

    def test_unreachable_queue_fails_closed(self):
        """REQ-R4: missing/unparseable queue JSON is a named failure, never 'in sync'."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, _ = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker",
                tracker,
                "--queue-list",
                str(Path(tmp) / "no-queue.json"),
                "--transitions",
                qlist,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertNotIn("in sync", proc.stdout)
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json")
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", str(bad), "--transitions", qlist
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)


class TestReplayProof(unittest.TestCase):
    def test_applying_proposals_converges_to_zero_diffs(self):
        """REQ-R3/T4: TPM-approval simulation — apply every PROPOSED cell, re-run -> in sync."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            first = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(first.returncode, 1, first.stdout + first.stderr)
            # Collect proposed Status cells per slice from the machine-readable
            # proposal markers the command prints for exactly this replay use.
            proposals = {}
            current_slice = None
            current_cell = None
            for line in first.stdout.splitlines():
                if line.startswith("DIFF "):
                    # DIFF [<class>] <file>:<line> slice <SLC> qitem <qid>
                    parts = line.split("slice ", 1)[1]
                    current_slice = parts.split()[0]
                elif line.startswith("PROPOSED-CELL:::"):
                    current_cell = line.split(":::", 1)[1]
                    proposals[current_slice] = current_cell
            self.assertEqual(len(proposals), 7, first.stdout)
            lines = Path(tracker).read_text().splitlines()
            for i, line in enumerate(lines):
                for slc, cell in proposals.items():
                    if line.startswith("| %s " % slc):
                        cells = line.split("|")
                        cells[-2] = " " + cell + " "
                        lines[i] = "|".join(cells)
            converged = write_tracker(tmp, "\n".join(lines) + "\n", name="converged.md")
            second = run_reconcile(
                "--tracker", converged, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn("in sync", second.stdout)


class TestLiveMode(unittest.TestCase):
    def _fake_rig(self, tmp, list_payload, trans_payload, exit_code=0):
        bindir = Path(tmp) / "bin"
        bindir.mkdir()
        fake = bindir / "rig"
        fake.write_text(
            "#!/usr/bin/env bash\n"
            'if [ "$2" = "list" ]; then\n'
            f"  printf '%s' {_shq(json.dumps(list_payload))}\n"
            "  exit 0\n"
            "fi\n"
            f'exec python3 -c {_shq("import json,sys; print(json.dumps(" + json.dumps(trans_payload) + "[sys.argv[1]]))")} "$4"\n'
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        env = {**os.environ, "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"}
        return env

    def test_live_mode_reads_only_json_verbs(self):
        """REQ-R4: --live consumes machine-readable output; drifted pair still diffs."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist_data = json.loads(Path(make_queue_state(tmp)[0]).read_text())
            trans_data = json.loads(Path(make_queue_state(tmp)[1]).read_text())
            env = self._fake_rig(tmp, qlist_data, trans_data)
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--tracker", tracker, "--live"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("W1-01", proc.stdout)

    def test_live_mode_unreachable_rig_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            env = {**os.environ, "PATH": str(Path(tmp))}
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--tracker",
                    tracker,
                    "--live",
                    "--rig-bin",
                    "rig-definitely-absent-39",
                ],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertNotIn("in sync", proc.stdout)


class TestProposalNoteNormalization(unittest.TestCase):
    def _hostile_state(self, tmp):
        """Queue state whose latest notes carry |, newline, and multi-space."""
        tracker = write_tracker(tmp, DRIFTED_TRACKER)
        qlist, trans = make_queue_state(tmp)
        data = json.loads(Path(trans).read_text())
        for qid in data:
            data[qid][-1]["transitionNote"] = "QA PASS a|b\nc   d  placed"
        hostile = str(Path(tmp) / "transitions_hostile.json")
        Path(hostile).write_text(json.dumps(data))
        return tracker, qlist, hostile

    def test_hostile_note_proposal_is_single_line_with_slash(self):
        """Pipe/newline/multi-space note -> single-line proposal with / and
        single spaces; the finding still fires with its class unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker, qlist, hostile = self._hostile_state(tmp)
            proc = run_reconcile(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                hostile,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stale-state", proc.stdout)
            self.assertIn("parked-satisfied-but-tracker-silent", proc.stdout)
            self.assertIn("missing-convergence-annotation", proc.stdout)
            proposed = [
                ln
                for ln in proc.stdout.splitlines()
                if ln.startswith("PROPOSED-CELL:::")
            ]
            self.assertEqual(len(proposed), 7, proc.stdout)
            for line in proposed:
                self.assertNotIn("|", line)
            self.assertIn("(queue note 5: QA PASS a/b c d placed;", proc.stdout)
            self.assertIn(
                "PROPOSED-CELL:::QA PASS 4+merge (row note 3) "
                "(queue note 5: QA PASS a/b c d placed; "
                "operator note appended)",
                proc.stdout,
            )

    def test_clean_note_proposal_byte_identical(self):
        """A clean note normalizes to itself: no gratuitous churn."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            proc = run_reconcile(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn(
                "PROPOSED-CELL:::QA PASS + PLACED canonical "
                "(queue note 5: handed_off_to Wave 2; "
                "operator note appended)",
                proc.stdout,
            )
            self.assertIn(
                "PROPOSED-CELL:::QA PASS 4+merge (row note 3) "
                "(queue note 5: handed_off_to Wave 2; "
                "operator note appended)",
                proc.stdout,
            )


class TestMalformedInputFailClosed(unittest.TestCase):
    def test_non_dict_trail_items_exit_2_no_traceback(self):
        """Transitions trail holding non-dict items is malformed input:
        exit 2 with a concise message, never a traceback exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            data = json.loads(Path(trans).read_text())
            data[QIDS["W1-01"]] = [42, "not-a-dict"]
            bad = str(Path(tmp) / "transitions_bad.json")
            Path(bad).write_text(json.dumps(data))
            proc = run_reconcile(
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
            self.assertIn("malformed input", proc.stderr)
            self.assertIn("AttributeError", proc.stderr)
            self.assertNotIn("in sync", proc.stdout)

    def test_unhashable_queue_qitem_id_exit_2_no_traceback(self):
        """Queue entry whose qitemId is unhashable is malformed input:
        exit 2 with a concise message, never a traceback exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            data = json.loads(Path(qlist).read_text())
            data.append({"qitemId": ["list-is-unhashable"], "state": "closed"})
            bad = str(Path(tmp) / "queue_list_bad.json")
            Path(bad).write_text(json.dumps(data))
            proc = run_reconcile(
                "--tracker",
                tracker,
                "--queue-list",
                bad,
                "--transitions",
                trans,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            combined = proc.stdout + proc.stderr
            self.assertNotIn("Traceback", combined)
            self.assertIn("malformed input", proc.stderr)
            self.assertIn("TypeError", proc.stderr)
            self.assertNotIn("in sync", proc.stdout)

    def test_tracker_row_missing_key_exit_2_no_traceback(self):
        """A tracker-derived row missing its expected key is malformed
        input: main maps the KeyError to exit 2, never a traceback."""
        import contextlib
        import importlib.util
        import io

        spec = importlib.util.spec_from_file_location(
            "reconcile_under_test", str(SCRIPT)
        )
        rec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rec)
        rec.parse_tracker = lambda *a: [
            {"file": "t.md", "line": 1, "slice": "W1-01", "qitem": QIDS["W1-01"]}
        ]
        with tempfile.TemporaryDirectory() as tmp:
            qlist, trans = make_queue_state(tmp)
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = rec.main(
                    ["--tracker", "t.md", "--queue-list", qlist, "--transitions", trans]
                )
            self.assertEqual(rc, 2)
            self.assertNotIn("Traceback", err.getvalue())
            self.assertIn("malformed input", err.getvalue())
            self.assertIn("KeyError", err.getvalue())


class TestStaleTerminalEvidenceNormalization(unittest.TestCase):
    """Option A: the stale-terminal branch (tracker claims terminal while the
    queue is not terminal) must normalize the queue note in its proposal, so
    no proposal string interpolates a raw queue note."""

    QID = QIDS["W1-01"]

    def _stale_terminal_state(self, tmp, note):
        tracker = write_tracker(
            tmp,
            "# Wave 1 Dispatch Tracker (synthetic stale-terminal)\n\n"
            "## Slices\n"
            "| Slice | Owner seat | Output | Slice qitem | Status |\n"
            "|---|---|---|---|---|\n"
            "| W1-01 | seat | output | %s | QA PASS + PLACED canonical "
            "(queue note 5; operator note appended) |\n" % self.QID,
        )
        qlist = [
            {
                "qitemId": self.QID,
                "state": "in-progress",
                "destinationSession": "seat@rig",
                "tsUpdated": "2026-10-22T12:00:00.000Z",
            }
        ]
        trans = {
            self.QID: [
                {
                    "transitionId": 1,
                    "qitemId": self.QID,
                    "ts": "2026-10-22T05:24:00.000Z",
                    "state": "in-progress",
                    "transitionNote": note,
                }
            ]
        }
        qlist_path = str(Path(tmp) / "queue_list.json")
        trans_path = str(Path(tmp) / "transitions.json")
        Path(qlist_path).write_text(json.dumps(qlist))
        Path(trans_path).write_text(json.dumps(trans))
        return tracker, qlist_path, trans_path

    def test_hostile_note_proposal_single_line_pipe_free(self):
        """Hostile note in a stale-terminal row -> proposal single-line and
        pipe-free, class/exit unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker, qlist, trans = self._stale_terminal_state(
                tmp, "wip ev|idence\nline2   spaced"
            )
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stale-state", proc.stdout)
            self.assertIn("tracker claims terminal", proc.stdout)
            proposed = [
                ln
                for ln in proc.stdout.splitlines()
                if ln.startswith("PROPOSED-CELL:::")
            ]
            self.assertEqual(len(proposed), 1, proc.stdout)
            for line in proposed:
                self.assertNotIn("|", line)
                self.assertNotIn("\n", line)
            self.assertIn(
                "PROPOSED-CELL:::Re-verify W1-01 with QA, or correct the "
                "tracker cell; queue-side evidence: wip ev/idence line2 spaced",
                proc.stdout,
            )

    def test_clean_note_output_unchanged(self):
        """A clean note in the stale-terminal branch renders byte-identical
        to before (no gratuitous churn)."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker, qlist, trans = self._stale_terminal_state(tmp, "awaiting review")
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn(
                "PROPOSED-CELL:::Re-verify W1-01 with QA, or correct the "
                "tracker cell; queue-side evidence: awaiting review",
                proc.stdout,
            )

    def test_empty_note_falls_back_to_state(self):
        """Empty/blank note -> fall back to the queue state, as today."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker, qlist, trans = self._stale_terminal_state(tmp, "")
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn(
                "PROPOSED-CELL:::Re-verify W1-01 with QA, or correct the "
                "tracker cell; queue-side evidence: in-progress",
                proc.stdout,
            )


class TestProposalFileMode(unittest.TestCase):
    def test_out_file_is_owner_only(self):
        """CodeQL overly-permissive permissions: proposal files must carry
        no group/other permission bits (owner-only)."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp, DRIFTED_TRACKER)
            qlist, trans = make_queue_state(tmp)
            dest = str(Path(tmp) / "review-proposal.txt")
            proc = run_reconcile(
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


NON_ASCII_SAMPLE = "caf\u00e9 \u2014 \u6f22\u5b57"


class TestUtf8FileIO(unittest.TestCase):
    def test_non_ascii_round_trip_under_c_locale(self):
        """File I/O must pin UTF-8: a tracker + queue JSON carrying non-ASCII
        (em-dash, CJK) parse/load/write byte-identical under LC_ALL=C, where
        the platform default encoding is ASCII."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = Path(tmp) / "tracker.md"
            tracker.write_text(
                "# Wave 1 Dispatch Tracker (synthetic non-ASCII)\n\n"
                "## Slices\n"
                "| Slice | Owner seat | Output | Slice qitem | Status |\n"
                "|---|---|---|---|---|\n"
                "| W1-01 %s | seat | output | %s | STAGED %s |\n"
                % (NON_ASCII_SAMPLE, QIDS["W1-01"], NON_ASCII_SAMPLE),
                encoding="utf-8",
            )
            qlist = Path(tmp) / "queue_list.json"
            qlist.write_text(
                json.dumps(
                    [{"qitemId": QIDS["W1-01"], "state": "closed"}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            trans = Path(tmp) / "transitions.json"
            trans.write_text(
                json.dumps(
                    {
                        QIDS["W1-01"]: [
                            {
                                "transitionId": 7,
                                "qitemId": QIDS["W1-01"],
                                "ts": "2026-10-22T11:45:00.000Z",
                                "state": "closed",
                                "transitionNote": "handed_off %s" % NON_ASCII_SAMPLE,
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            dest = Path(tmp) / "proposal.txt"
            child = Path(tmp) / "roundtrip_child.py"
            child.write_text(
                "import sys\n"
                "sys.path.insert(0, sys.argv[4])\n"
                "from reconcile_model import (\n"
                "    parse_tracker, load_json_file, write_out_exclusive,\n"
                ")\n"
                "EXPECTED = " + json.dumps(NON_ASCII_SAMPLE) + "\n"
                "rows = parse_tracker(sys.argv[1])\n"
                "assert EXPECTED in rows[0]['slice'], rows\n"
                "qlist = load_json_file(sys.argv[2], 'QUEUE LIST')\n"
                "trans = load_json_file(sys.argv[3], 'TRANSITIONS')\n"
                "note = trans[qlist[0]['qitemId']][0]['transitionNote']\n"
                "assert EXPECTED in note, note\n"
                "text = 'cells ' + EXPECTED + ' end\\n'\n"
                "write_out_exclusive(sys.argv[5], text)\n"
                "raw = open(sys.argv[5], 'rb').read()\n"
                "assert raw == text.encode('utf-8'), raw\n"
                "print('ROUNDTRIP-OK')\n",
                encoding="utf-8",
            )
            env = dict(
                os.environ,
                LC_ALL="C",
                LANG="C",
                LANGUAGE="C",
                PYTHONUTF8="0",
                PYTHONCOERCECLOCALE="0",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(child),
                    str(tracker),
                    str(qlist),
                    str(trans),
                    str(REPO_ROOT / "scripts"),
                    str(dest),
                ],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(REPO_ROOT),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("ROUNDTRIP-OK", proc.stdout)


def _shq(s):
    return "'" + s.replace("'", "'\\''") + "'"


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# M7 (#84) — negation-aware terminal/placed detection: queue terminal only on
# state; notes/tracker cells count only as affirmative ^QA PASS with no
# negator (not|no|never|n't) or fail token.
# ---------------------------------------------------------------------------

GENERATE_SCRIPT = REPO_ROOT / "scripts" / "generate_trackers.py"

_Q84_QID = "qitem-20261022000099-ffffffffffffffff"


def load_reconcile_model():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "reconcile_model", str(REPO_ROOT / "scripts" / "reconcile_model.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_generate(*args):
    return subprocess.run(
        [sys.executable, str(GENERATE_SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def q84_state(tmpdir, queue_state, latest_note, tracker_cell):
    """One-row tracker + queue pair for the #84 fixture shape."""
    tracker = write_tracker(
        tmpdir,
        "# Wave 8 Dispatch Tracker (synthetic #84 replica)\n\n"
        "## Slices\n"
        "| Slice | Owner seat | Output | Slice qitem | Status |\n"
        "|---|---|---|---|---|\n"
        "| W8-01 neg | seat | output | %s | %s |\n" % (_Q84_QID, tracker_cell),
    )
    qlist = [
        {
            "qitemId": _Q84_QID,
            "state": queue_state,
            "destinationSession": "seat@rig",
            "tsUpdated": "2026-10-22T12:00:00.000Z",
        }
    ]
    trans = {
        _Q84_QID: [
            {
                "transitionId": 5,
                "qitemId": _Q84_QID,
                "ts": "2026-10-22T11:45:00.000Z",
                "state": queue_state,
                "transitionNote": latest_note,
            }
        ]
    }
    qlist_path = str(Path(tmpdir) / "queue_list.json")
    trans_path = str(Path(tmpdir) / "transitions.json")
    Path(qlist_path).write_text(json.dumps(qlist))
    Path(trans_path).write_text(json.dumps(trans))
    return tracker, qlist_path, trans_path


class TestNegationAwareTerminal(unittest.TestCase):
    def test_queue_note_alone_is_never_terminal(self):
        """queue_terminal: an affirmative QA note with a non-terminal state
        is NOT terminal (note-based terminality removed)."""
        model = load_reconcile_model()
        terminal, _, _ = model.queue_terminal(
            {"state": "in-progress"},
            [
                {
                    "transitionId": 3,
                    "state": "in-progress",
                    "transitionNote": "QA PASS per report, placed",
                }
            ],
        )
        self.assertFalse(terminal)

    def test_queue_terminal_state_only_despite_junk_note(self):
        """queue_terminal: a terminal state counts even with a junk note."""
        model = load_reconcile_model()
        terminal, latest_id, _ = model.queue_terminal(
            {"state": "closed"},
            [
                {
                    "transitionId": 7,
                    "state": "closed",
                    "transitionNote": "awaiting review",
                }
            ],
        )
        self.assertTrue(terminal)
        self.assertEqual(latest_id, 7)

    def test_negated_tracker_cell_counts_for_no_arm(self):
        """normalize_tracker: 'QA pass NOT granted; NOT placed' affirms
        nothing — no qa_pass, no placed, no other terminal arm."""
        model = load_reconcile_model()
        norm = model.normalize_tracker("QA pass NOT granted; NOT placed")
        self.assertFalse(norm["qa_pass"])
        self.assertFalse(norm["placed"])
        self.assertFalse(norm["closed"])
        self.assertFalse(norm["staged"])
        self.assertFalse(norm["dispatched"])
        self.assertFalse(norm["parked"])

    def test_affirmative_qa_pass_variants(self):
        """^QA PASS anchor + negator/fail-token guards, pinned both ways."""
        model = load_reconcile_model()
        self.assertTrue(
            model.normalize_tracker("QA PASS verified (note 5)")["qa_pass"]
        )
        self.assertTrue(
            model.normalize_tracker(
                "QA PASS + PLACED canonical (queue note 5; operator note appended)"
            )["qa_pass"]
        )
        # Anchor: mid-cell QA PASS does not count.
        self.assertFalse(
            model.normalize_tracker("staged, QA PASS verified")["qa_pass"]
        )
        # Fail token kills the affirmation.
        self.assertFalse(
            model.normalize_tracker("QA PASS failed, rerun needed")["qa_pass"]
        )
        # Negators kill the affirmation.
        self.assertFalse(
            model.normalize_tracker("QA PASS never arrived")["qa_pass"]
        )
        self.assertFalse(model.normalize_tracker("NOT placed")["placed"])
        # #105 review: deferred passes are not passes (fail closed).
        for cell in (
            "QA PASS pending re-run",
            "QA PASS (awaiting gate)",
            "QA PASS provisional",
            "QA PASS rerun scheduled",
        ):
            with self.subTest(cell=cell):
                self.assertFalse(model.normalize_tracker(cell)["qa_pass"])
        # Regression pin: plain CLOSED still counts.
        self.assertTrue(
            model.normalize_tracker("CLOSED operator-owned")["closed"]
        )

    def test_84_fixture_reconcile_flags_stale_state(self):
        """#84 through reconcile: terminal-claiming tracker vs in-progress
        queue with a negated note -> exit 1 stale-state, never in sync and
        never a paste-ready PASS cell."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker, qlist, trans = q84_state(
                tmp,
                "in-progress",
                "QA pass NOT granted; NOT placed",
                "QA PASS + PLACED canonical (queue note 5; operator note appended)",
            )
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stale-state", proc.stdout)
            self.assertIn("tracker claims terminal", proc.stdout)
            self.assertNotIn("PROPOSED-CELL:::QA PASS", proc.stdout)

    def test_84_fixture_generate_trackers_is_review_not_paste_ready(self):
        """#84 through generate_trackers: exit 1 NEEDS-HUMAN-REVIEW with zero
        PROPOSED-CELL markers."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker, qlist, trans = q84_state(
                tmp,
                "in-progress",
                "QA pass NOT granted; NOT placed",
                "QA PASS + PLACED canonical (queue note 5; operator note appended)",
            )
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("NEEDS-HUMAN-REVIEW", proc.stdout)
            self.assertNotIn("PROPOSED-CELL:::", proc.stdout)

    def test_84_negated_tracker_cell_is_other_prose_review(self):
        """A negated tracker cell itself matches no enum arm -> OTHER +
        NEEDS-HUMAN-REVIEW, never a guessed terminal cell."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker, qlist, trans = q84_state(
                tmp,
                "in-progress",
                "QA pass NOT granted; NOT placed",
                "QA pass NOT granted; NOT placed",
            )
            proc = run_generate(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("NEEDS-HUMAN-REVIEW", proc.stdout)
            self.assertNotIn("PROPOSED-CELL:::", proc.stdout)
