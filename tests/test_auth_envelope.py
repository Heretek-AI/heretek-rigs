#!/usr/bin/env python3
"""Corpus for pre-authorization envelopes (issue #15, REQ-E1/E2/E3).

Fixtures only (/tmp scratch, dummy ids and dummy 16-hex diff hashes —
never the live mission checkout, never real bearer material).

REQ-E2 (premise drift counts as stalled with premise-age attribution):
reconcile_model emits a stalled-premise-drift diff for a landing diff that
drifted from its authorized premise (or an open authorization with no
matching landing record), routing for human review with premise-age
attribution attached. Clean premises (landing identical to premise) stay
quiet. Propose-only throughout: classification + report only, no row state
is written by anything here.

REQ-E1 (standing envelopes bind premise to landing): auth_envelope
mint/validate binds the diff hash + scope paths + mandatory expiry +
single-use nonce (HMAC-bound, wave-9 nonce discipline reused). Clean
envelopes validate; drifted/scope-breached/expired/replayed envelopes are
refused fail-closed with a redacted log. Envelopes never self-execute and
never auto-commit (REQ-E3): validation is a pure check, refusal leaves the
row byte-identical, and recovery dismissal requires a row state change.

Refs #15 (never Closes #15 — the issue stays open for the live-fleet proof).
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

# #15-pattern fixture ids (dummy; 16-hex hashes stay under the 40+ secret
# floor so evidence greps stay empty).
PARENT = "qitem-20261020100001-a1b2c3d4e5f60718"
PREMISE_HASH = "aaaaaaaaaaaaaaaa"
LANDING_HASH = "bbbbbbbbbbbbbbbb"
PREMISE_TS = "2026-10-20T10:00:00.000Z"
VERIFY_TS = "2026-10-20T10:05:00.000Z"
LANDING_TS = "2026-10-20T10:12:00.000Z"
SECRET = "dummy-binding-secret-for-tests-only"

PREMISE_STATUS = (
    "authorized premise %s scope src/include/hash.h; "
    "premise at %s; verified at %s; TPM verified"
    % (PREMISE_HASH, PREMISE_TS, VERIFY_TS)
)


def landing_note(diff_hash=LANDING_HASH, paths="src/include/hash.h,src/extra/eleven.c"):
    return "landing diff %s paths %s at %s" % (diff_hash, paths, LANDING_TS)


def load_model():
    spec = importlib.util.spec_from_file_location(
        "reconcile_model_auth", str(REPO_ROOT / "scripts" / "reconcile_model.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_envelope():
    spec = importlib.util.spec_from_file_location(
        "auth_envelope", str(REPO_ROOT / "scripts" / "auth_envelope.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_sweep():
    spec = importlib.util.spec_from_file_location(
        "sweep_typed_blocks_auth",
        str(REPO_ROOT / "scripts" / "sweep-typed-blocks.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_tracker(
    tmpdir, status_cell=PREMISE_STATUS, name="mission-dispatch-tracker.md"
):
    path = Path(tmpdir) / name
    path.write_text(
        """\
# Mission Dispatch Tracker (synthetic 15-auth-envelope replica)

## Slices
| Slice | Owner seat | Output | Slice qitem | Status |
|---|---|---|---|---|
| S02 landing slice | owner-seat | hash.h one-liner | %s | %s |

## Rules (all slices)
No commits by seats.
"""
        % (PARENT, status_cell)
    )
    return str(path)


def write_queue(tmpdir, latest_note, state="in-progress"):
    qlist = [
        {
            "qitemId": PARENT,
            "state": state,
            "destinationSession": "owner-seat",
            "tsUpdated": LANDING_TS,
        }
    ]
    trans = {
        PARENT: [
            {
                "transitionId": 61,
                "qitemId": PARENT,
                "ts": PREMISE_TS,
                "state": "in-progress",
                "transitionNote": "claimed",
            },
            {
                "transitionId": 62,
                "qitemId": PARENT,
                "ts": LANDING_TS,
                "state": state,
                "transitionNote": latest_note,
            },
        ]
    }
    qlist_path = str(Path(tmpdir) / "queue_list.json")
    trans_path = str(Path(tmpdir) / "transitions.json")
    Path(qlist_path).write_text(json.dumps(qlist))
    Path(trans_path).write_text(json.dumps(trans))
    return qlist_path, trans_path


def run_reconcile(*args):
    return subprocess.run(
        [sys.executable, str(RECONCILE_SCRIPT), *args],
        capture_output=True,
        text=True,
    )


class TestPremiseDriftClassification(unittest.TestCase):
    def test_drifted_premise_flagged_stalled(self):
        """REQ-E2: landing hash differs from the premise hash -> stalled."""
        model = load_model()
        row = {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": PREMISE_STATUS,
        }
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        trans = {
            PARENT: [
                {
                    "transitionId": 61,
                    "state": "in-progress",
                    "transitionNote": "claimed",
                },
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(),
                    "ts": LANDING_TS,
                },
            ]
        }
        diff = model.stalled_premise_drift_diff(row, queue_by_id, trans)
        self.assertIsNotNone(diff)
        self.assertEqual(diff["class"], "stalled-premise-drift")
        self.assertIn("src/extra/eleven.c", diff["reason"])

    def test_premise_age_attribution_attached(self):
        """REQ-E2: the drift diff carries premise-age attribution (720s)."""
        model = load_model()
        row = {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": PREMISE_STATUS,
        }
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        trans = {
            PARENT: [
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(),
                    "ts": LANDING_TS,
                },
            ]
        }
        diff = model.stalled_premise_drift_diff(row, queue_by_id, trans)
        attribution = diff["attribution"]
        self.assertEqual(attribution["premise_age_s"], 720)
        self.assertEqual(attribution["verify_to_landing_s"], 420)
        self.assertIn("premise age", attribution["note"])

    def test_clean_premise_stays_quiet(self):
        """REQ-E2: landing identical to premise within scope -> no diff."""
        model = load_model()
        row = {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": PREMISE_STATUS,
        }
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        trans = {
            PARENT: [
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(
                        diff_hash=PREMISE_HASH, paths="src/include/hash.h"
                    ),
                    "ts": LANDING_TS,
                },
            ]
        }
        self.assertIsNone(model.stalled_premise_drift_diff(row, queue_by_id, trans))

    def test_row_without_premise_stays_quiet(self):
        """REQ-E2: rows declaring no premise never match (no over-flagging)."""
        model = load_model()
        row = {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": "STAGED awaiting QA",
        }
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        trans = {
            PARENT: [
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(),
                    "ts": LANDING_TS,
                },
            ]
        }
        self.assertIsNone(model.stalled_premise_drift_diff(row, queue_by_id, trans))

    def test_open_authorization_without_landing_is_stalled(self):
        """REQ-E2: open authorization with no matching landing record stalls."""
        model = load_model()
        row = {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": PREMISE_STATUS,
        }
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        trans = {
            PARENT: [
                {
                    "transitionId": 61,
                    "state": "in-progress",
                    "transitionNote": "claimed",
                },
            ]
        }
        diff = model.stalled_premise_drift_diff(row, queue_by_id, trans)
        self.assertIsNotNone(diff)
        self.assertEqual(diff["class"], "stalled-premise-drift")
        self.assertIn("no matching landing", diff["reason"])

    def test_scope_breach_flagged_same_hash(self):
        """REQ-E2: identical hash but landing outside scope still stalls."""
        model = load_model()
        row = {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": PREMISE_STATUS,
        }
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        trans = {
            PARENT: [
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(
                        diff_hash=PREMISE_HASH,
                        paths="src/include/hash.h,fleet/fleet.yaml",
                    ),
                    "ts": LANDING_TS,
                },
            ]
        }
        diff = model.stalled_premise_drift_diff(row, queue_by_id, trans)
        self.assertIsNotNone(diff)
        self.assertEqual(diff["class"], "stalled-premise-drift")
        self.assertIn("fleet/fleet.yaml", diff["reason"])

    def test_premise_scope_rejects_dotdot_traversal(self):
        """Pinning (r1-F7): a landing path with a .. segment never counts
        as scope-covered, even when it shares the scope directory prefix
        (prefix checks alone would bind it inside the scope it escapes)."""
        model = load_model()
        uncovered = model._scope_covers(
            ["src/extra/"], ["src/extra/../fleet/fleet.yaml"]
        )
        self.assertEqual(uncovered, ["src/extra/../fleet/fleet.yaml"])
        self.assertEqual(
            model._scope_covers(["src/extra/"], ["src/extra/eleven.c"]), []
        )

    def test_landing_found_when_followed_by_non_landing_note(self):
        """Pinning (r1-F8): the classifier scans the trail newest-to-oldest
        and binds the first recognized landing — a clean landing followed
        by a non-landing note stays quiet (the landing is still found)."""
        model = load_model()
        row = {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": PREMISE_STATUS,
        }
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        trans = {
            PARENT: [
                {
                    "transitionId": 61,
                    "state": "in-progress",
                    "transitionNote": "claimed",
                },
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(
                        diff_hash=PREMISE_HASH, paths="src/include/hash.h"
                    ),
                    "ts": LANDING_TS,
                },
                {
                    "transitionId": 63,
                    "state": "in-progress",
                    "transitionNote": "owner comment: waiting on TPM ruling",
                    "ts": LANDING_TS,
                },
            ]
        }
        self.assertIsNone(model.stalled_premise_drift_diff(row, queue_by_id, trans))

    def test_drifted_landing_still_flagged_when_followed_by_note(self):
        """Pinning (r1-F8, other direction): a drifted landing followed by
        a non-landing note still routes for human review with the drift
        reason (the scan finds the earlier landing, it does not go silent)."""
        model = load_model()
        row = {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": PREMISE_STATUS,
        }
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        trans = {
            PARENT: [
                {
                    "transitionId": 61,
                    "state": "in-progress",
                    "transitionNote": "claimed",
                },
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(),
                    "ts": LANDING_TS,
                },
                {
                    "transitionId": 63,
                    "state": "in-progress",
                    "transitionNote": "owner comment: waiting on TPM ruling",
                    "ts": LANDING_TS,
                },
            ]
        }
        diff = model.stalled_premise_drift_diff(row, queue_by_id, trans)
        self.assertIsNotNone(diff)
        self.assertEqual(diff["class"], "stalled-premise-drift")
        self.assertIn("drifted", diff["reason"])

    def test_attribution_is_report_only(self):
        """REQ-E2: attribution computes from fixture timestamps, writes nothing."""
        model = load_model()
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp)
            before = Path(tracker).read_bytes()
            qlist, trans = write_queue(tmp, landing_note())
            qlist_before = Path(qlist).read_bytes()
            trans_before = Path(trans).read_bytes()
            attribution = model.attribute_premise_age(PREMISE_TS, VERIFY_TS, LANDING_TS)
            self.assertEqual(attribution["premise_age_s"], 720)
            self.assertEqual(Path(tracker).read_bytes(), before)
            self.assertEqual(Path(qlist).read_bytes(), qlist_before)
            self.assertEqual(Path(trans).read_bytes(), trans_before)

    def test_reconcile_end_to_end_flags_drift(self):
        """REQ-E2 through reconcile: exit 1 naming stalled-premise-drift."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp)
            qlist, trans = write_queue(tmp, landing_note())
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stalled-premise-drift", proc.stdout)
            self.assertIn("premise age", proc.stdout)
            self.assertIn("NEEDS-HUMAN-REVIEW", proc.stdout)
            self.assertNotIn("PROPOSED-CELL:::", proc.stdout)

    def test_reconcile_end_to_end_clean_quiet(self):
        """REQ-E2 through reconcile: clean premise reconciles silent."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp)
            qlist, trans = write_queue(
                tmp, landing_note(diff_hash=PREMISE_HASH, paths="src/include/hash.h")
            )
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("in sync", proc.stdout)

    def test_classifier_removal_is_silent(self):
        """Pinning (wave-81 lesson): killing the classifier restores silence.

        Proves the suite is non-vacuous: if diff_row ever stops delegating
        to stalled_premise_drift_diff, this test (and the end-to-end above)
        flips — sabotage cannot outrun the corpus.
        """
        model = load_model()
        row = {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": PREMISE_STATUS,
        }
        queue_by_id = {PARENT: {"qitemId": PARENT, "state": "in-progress"}}
        trans = {
            PARENT: [
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(),
                    "ts": LANDING_TS,
                },
            ]
        }
        with mock.patch.object(model, "stalled_premise_drift_diff", return_value=None):
            self.assertIsNone(
                model.diff_row(row, queue_by_id, trans),
                "with the classifier disabled the drifted row must go silent "
                "(RED direction of the S1a red-proof)",
            )
        self.assertIsNotNone(model.diff_row(row, queue_by_id, trans))


class TestEnvelopeMintValidate(unittest.TestCase):
    def test_clean_envelope_validates(self):
        """REQ-E1: matching hash, in-scope paths, live, fresh nonce -> authorized."""
        env = load_envelope()
        seen = set()
        envelope = env.mint_envelope(
            SECRET,
            PREMISE_HASH,
            ["src/include/hash.h"],
            expires_at=1780000000,
            nonce="fresh-nonce-00000001",
        )
        result = env.validate_envelope(
            SECRET,
            envelope,
            PREMISE_HASH,
            ["src/include/hash.h"],
            now=1779999999,
            seen=seen,
        )
        self.assertEqual(result.status, "authorized")
        self.assertIn("fresh-nonce-00000001", seen)

    def test_drifted_landing_refused(self):
        """REQ-E1: landing hash differs by even one line -> refused."""
        env = load_envelope()
        seen = set()
        envelope = env.mint_envelope(
            SECRET,
            PREMISE_HASH,
            ["src/include/hash.h", "src/extra/"],
            expires_at=1780000000,
            nonce="drifted-nonce-000001",
        )
        result = env.validate_envelope(
            SECRET,
            envelope,
            LANDING_HASH,
            ["src/include/hash.h", "src/extra/eleven.c"],
            now=1779999999,
            seen=seen,
        )
        self.assertEqual(result.status, "refused")
        self.assertNotIn("drifted-nonce-000001", seen)

    def test_scope_breach_refused(self):
        """REQ-E1: landing file-set outside scope paths -> refused."""
        env = load_envelope()
        seen = set()
        envelope = env.mint_envelope(
            SECRET,
            PREMISE_HASH,
            ["src/include/hash.h"],
            expires_at=1780000000,
            nonce="scope-nonce-00000002",
        )
        result = env.validate_envelope(
            SECRET,
            envelope,
            PREMISE_HASH,
            ["src/include/hash.h", "fleet/fleet.yaml"],
            now=1779999999,
            seen=seen,
        )
        self.assertEqual(result.status, "refused")

    def test_expired_envelope_refused(self):
        """REQ-E1: past the expiry window -> refused."""
        env = load_envelope()
        seen = set()
        envelope = env.mint_envelope(
            SECRET,
            PREMISE_HASH,
            ["src/include/hash.h"],
            expires_at=1780000000,
            nonce="expired-nonce-0000003",
        )
        result = env.validate_envelope(
            SECRET,
            envelope,
            PREMISE_HASH,
            ["src/include/hash.h"],
            now=1780000001,
            seen=seen,
        )
        self.assertEqual(result.status, "refused")

    def test_replayed_nonce_refused(self):
        """REQ-E1: a consumed nonce presented again -> refused, never rewound."""
        env = load_envelope()
        seen = set()
        envelope = env.mint_envelope(
            SECRET,
            PREMISE_HASH,
            ["src/include/hash.h"],
            expires_at=1780000000,
            nonce="replay-nonce-00000004",
        )
        first = env.validate_envelope(
            SECRET,
            envelope,
            PREMISE_HASH,
            ["src/include/hash.h"],
            now=1779999999,
            seen=seen,
        )
        self.assertEqual(first.status, "authorized")
        second = env.validate_envelope(
            SECRET,
            envelope,
            PREMISE_HASH,
            ["src/include/hash.h"],
            now=1779999999,
            seen=seen,
        )
        self.assertEqual(second.status, "refused")
        self.assertIn("replay", (second.reason or "").lower())

    def test_mint_rejects_comma_in_scope_entry(self):
        """Pinning (r1-F5): a comma inside one scope entry never mints.

        Scope travels as comma-joined CSV inside the envelope; minting an
        entry containing a comma would let validate split it into several
        scopes. Fail closed at mint time instead.
        """
        env = load_envelope()
        with self.assertRaises(ValueError):
            env.mint_envelope(
                SECRET,
                PREMISE_HASH,
                ["src/include/hash.h,src/extra/eleven.c"],
                expires_at=1780000000,
                nonce="comma-nonce-00000009",
            )

    def test_scope_covers_rejects_suspicious_landing_paths(self):
        """Pinning (r1-F6): non-string, empty, absolute, and dot-segment
        landing paths never count as covered; uncovered stays join-safe
        (no TypeError) and canonical coverage is preserved."""
        env = load_envelope()
        scope_csv = "src/extra/"
        suspicious = [
            None,
            123,
            "",
            "/abs/path.c",
            "src/extra/../fleet/fleet.yaml",
            "src/./eleven.c",
            "src//eleven.c",
            "..",
        ]
        uncovered = env._scope_covers(scope_csv, suspicious)
        for path in suspicious:
            self.assertIn(str(path), uncovered)
        self.assertEqual(env._scope_covers(scope_csv, ["src/extra/eleven.c"]), [])
        self.assertEqual(
            env._scope_covers(scope_csv, ["fleet/fleet.yaml"]),
            ["fleet/fleet.yaml"],
        )

    def test_bad_mac_refused(self):
        """Pinning: an envelope MAC'd under another secret never authorizes."""
        env = load_envelope()
        seen = set()
        envelope = env.mint_envelope(
            "another-dummy-secret-value",
            PREMISE_HASH,
            ["src/include/hash.h"],
            expires_at=1780000000,
            nonce="mac-nonce-0000000005",
        )
        result = env.validate_envelope(
            SECRET,
            envelope,
            PREMISE_HASH,
            ["src/include/hash.h"],
            now=1779999999,
            seen=seen,
        )
        self.assertEqual(result.status, "refused")

    def test_tampered_expiry_and_hash_refused_for_mac(self):
        """Pinning (r1-F9, alongside bad-MAC): re-signing-free tampering
        with the expiry or the diff hash is refused for a MAC-related
        reason and never consumes the nonce."""
        env = load_envelope()
        seen = set()
        envelope = env.mint_envelope(
            SECRET,
            PREMISE_HASH,
            ["src/include/hash.h"],
            expires_at=1780000000,
            nonce="tamper-nonce-00000010",
        )
        parts = envelope.split(".")
        self.assertEqual(len(parts), 6)
        tampered_expiry = ".".join(parts[:3] + ["1880000000"] + parts[4:])
        tampered_hash = ".".join([parts[0], LANDING_HASH] + parts[2:])
        for tampered in (tampered_expiry, tampered_hash):
            result = env.validate_envelope(
                SECRET,
                tampered,
                PREMISE_HASH,
                ["src/include/hash.h"],
                now=1779999999,
                seen=seen,
            )
            self.assertEqual(result.status, "refused")
            self.assertIn("mac", (result.reason or "").lower())
        self.assertEqual(seen, set())

    def test_missing_replay_set_fails_closed(self):
        """Pinning: a verifier without a seen-set cannot run (fail closed)."""
        env = load_envelope()
        envelope = env.mint_envelope(
            SECRET,
            PREMISE_HASH,
            ["src/include/hash.h"],
            expires_at=1780000000,
            nonce="noset-nonce-00000006",
        )
        result = env.validate_envelope(
            SECRET,
            envelope,
            PREMISE_HASH,
            ["src/include/hash.h"],
            now=1779999999,
            seen=None,
        )
        self.assertEqual(result.status, "refused")

    def test_refused_landing_leaves_row_untouched(self):
        """REQ-E3: a refused landing keeps the row byte-identical; nothing committed."""
        env = load_envelope()
        seen = set()
        envelope = env.mint_envelope(
            SECRET,
            PREMISE_HASH,
            ["src/include/hash.h"],
            expires_at=1780000000,
            nonce="untouched-nonce-00007",
        )
        row = {"qitemId": PARENT, "state": "in-progress", "statusCell": PREMISE_STATUS}
        before = json.dumps(row, sort_keys=True)
        result = env.validate_envelope(
            SECRET,
            envelope,
            LANDING_HASH,
            ["src/extra/eleven.c"],
            now=1779999999,
            seen=seen,
        )
        self.assertEqual(result.status, "refused")
        self.assertEqual(json.dumps(row, sort_keys=True), before)

    def test_refusal_log_is_redacted(self):
        """Pinning: secret-shaped runs never reach the refusal log line."""
        env = load_envelope()
        import contextlib
        import io

        seen = set()
        long_secret = "dummy-" + "z9" * 30 + "-binding-secret"
        envelope = env.mint_envelope(
            long_secret,
            PREMISE_HASH,
            ["src/include/hash.h"],
            expires_at=1780000000,
            nonce="redact-nonce-00000008",
        )
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            result = env.validate_envelope(
                long_secret,
                envelope,
                LANDING_HASH,
                ["src/extra/eleven.c"],
                now=1779999999,
                seen=seen,
            )
        self.assertEqual(result.status, "refused")
        self.assertIsNone(re.search(r"[A-Za-z0-9_-]{40,}", err.getvalue()))

    def test_no_self_execution_surface(self):
        """REQ-E3 pinning: the envelope module owns no executor or committer.

        The never-self-execute / never-auto-commit constraint is documented
        prose AND structurally enforced: stripping docstrings/comments must
        leave no executor, shell, or commit call behind.
        """
        source = (REPO_ROOT / "scripts" / "auth_envelope.py").read_text()
        code = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
        code = "\n".join(line.split("#", 1)[0] for line in code.splitlines())
        for marker in (
            "subprocess",
            "os.system",
            "os.exec",
            "os.popen",
            "check_output",
            ".commit(",
            "auto-commit",
            "self-execut",
        ):
            self.assertNotIn(marker, code)
        self.assertIn("never", source.lower())

    def test_recovery_needs_row_state_change(self):
        """REQ-E3: identical-snapshot dismissal refused; changed permitted."""
        sweep = load_sweep()
        flagged = sweep.snapshot_row_state(
            {"qitemId": PARENT, "state": "in-progress", "statusCell": PREMISE_STATUS}
        )
        with self.assertRaises(sweep.RecoveryDismissalRefused):
            sweep.check_recovery_dismissal(
                "recovery-premise-01", PARENT, flagged, flagged
            )
        moved = sweep.snapshot_row_state(
            {
                "qitemId": PARENT,
                "state": "in-progress",
                "statusCell": "authorized premise %s scope src/include/hash.h; "
                "fresh premise re-verified" % LANDING_HASH,
            }
        )
        outcome = sweep.check_recovery_dismissal(
            "recovery-premise-01", PARENT, flagged, moved
        )
        self.assertEqual(outcome.get("dismissal"), "permitted")


class TestEnvelopePresenceGating(unittest.TestCase):
    """REQ-E5: opt-in envelope-presence gating on a consulted registry.

    A clean landing (hash identical, paths in scope) stalls with the
    stalled-envelope-absence class IFF a populated envelope lookup holds
    no envelope matching the row's premise. Absent/empty lookup and a
    matching envelope stay quiet (REQ-E2 clean-quiet preserved). Fixtures
    only: dummy ids, dummy 16-hex hashes, /tmp scratch.
    """

    def clean_row(self):
        return {
            "file": "t.md",
            "line": 1,
            "slice": "S02",
            "qitem": PARENT,
            "status": PREMISE_STATUS,
        }

    def clean_queue(self):
        return {PARENT: {"qitemId": PARENT, "state": "in-progress"}}

    def clean_trans(self):
        return {
            PARENT: [
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(
                        diff_hash=PREMISE_HASH, paths="src/include/hash.h"
                    ),
                    "ts": LANDING_TS,
                },
            ]
        }

    def test_clean_landing_without_envelope_stalls_when_lookup_populated(
        self,
    ):
        """REQ-E5 fires: clean landing, populated lookup, no envelope -> stalled."""
        model = load_model()
        lookup = {
            "qitem-20261020100009-ffffffffffffffff": {"premise_hash": PREMISE_HASH}
        }
        diff = model.stalled_premise_drift_diff(
            self.clean_row(),
            self.clean_queue(),
            self.clean_trans(),
            envelope_by_id=lookup,
        )
        self.assertIsNotNone(diff)
        self.assertEqual(diff["class"], "stalled-envelope-absence")
        self.assertIn("envelope", diff["reason"])
        self.assertIn("premise age", diff["attribution"]["note"])
        self.assertEqual(diff["attribution"]["premise_age_s"], 720)

    def test_quiet_when_lookup_absent(self):
        """REQ-E5 quiet: no lookup passed -> default preserves clean-quiet."""
        model = load_model()
        self.assertIsNone(
            model.stalled_premise_drift_diff(
                self.clean_row(), self.clean_queue(), self.clean_trans()
            )
        )

    def test_quiet_when_lookup_empty(self):
        """REQ-E5 quiet: an empty (unconfigured) lookup never gates."""
        model = load_model()
        self.assertIsNone(
            model.stalled_premise_drift_diff(
                self.clean_row(),
                self.clean_queue(),
                self.clean_trans(),
                envelope_by_id={},
            )
        )

    def test_quiet_when_matching_envelope_present(self):
        """REQ-E5 quiet: lookup holds an envelope bound to the premise hash."""
        model = load_model()
        for record in (
            {"premise_hash": PREMISE_HASH},
            {"diff_hash": PREMISE_HASH},
            {"nonce": "dummy-nonce-00000001"},
        ):
            with self.subTest(record=record):
                self.assertIsNone(
                    model.stalled_premise_drift_diff(
                        self.clean_row(),
                        self.clean_queue(),
                        self.clean_trans(),
                        envelope_by_id={PARENT: record},
                    )
                )

    def test_mismatched_binding_fires(self):
        """REQ-E5 fires: lookup entry bound to another premise is no envelope."""
        model = load_model()
        diff = model.stalled_premise_drift_diff(
            self.clean_row(),
            self.clean_queue(),
            self.clean_trans(),
            envelope_by_id={PARENT: {"premise_hash": LANDING_HASH}},
        )
        self.assertIsNotNone(diff)
        self.assertEqual(diff["class"], "stalled-envelope-absence")

    def test_drifted_row_keeps_e2_class_without_lookup(self):
        """REQ-E5 changes nothing for drift: E2 stall stands, lookup or not."""
        model = load_model()
        row = self.clean_row()
        queue_by_id = self.clean_queue()
        trans = {
            PARENT: [
                {
                    "transitionId": 62,
                    "state": "in-progress",
                    "transitionNote": landing_note(),
                    "ts": LANDING_TS,
                },
            ]
        }
        for lookup in (None, {}, {"other": {"premise_hash": PREMISE_HASH}}):
            with self.subTest(lookup=lookup):
                kwargs = {} if lookup is None else {"envelope_by_id": lookup}
                diff = model.stalled_premise_drift_diff(
                    row, queue_by_id, trans, **kwargs
                )
                self.assertIsNotNone(diff)
                self.assertEqual(diff["class"], "stalled-premise-drift")

    def test_envelope_absence_attribution_is_report_only(self):
        """REQ-E5: gating computes attribution from fixtures, writes nothing."""
        model = load_model()
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp)
            before = Path(tracker).read_bytes()
            qlist, trans = write_queue(
                tmp, landing_note(diff_hash=PREMISE_HASH, paths="src/include/hash.h")
            )
            qlist_before = Path(qlist).read_bytes()
            trans_before = Path(trans).read_bytes()
            lookup = {
                "qitem-20261020100009-ffffffffffffffff": {"premise_hash": PREMISE_HASH}
            }
            diff = model.stalled_premise_drift_diff(
                self.clean_row(),
                self.clean_queue(),
                self.clean_trans(),
                envelope_by_id=lookup,
            )
            self.assertIsNotNone(diff)
            self.assertEqual(diff["attribution"]["premise_age_s"], 720)
            self.assertEqual(Path(tracker).read_bytes(), before)
            self.assertEqual(Path(qlist).read_bytes(), qlist_before)
            self.assertEqual(Path(trans).read_bytes(), trans_before)

    def test_reconcile_end_to_end_envelopes_flag(self):
        """REQ-E5 through reconcile: --envelopes without a match -> exit 1."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp)
            qlist, trans = write_queue(
                tmp, landing_note(diff_hash=PREMISE_HASH, paths="src/include/hash.h")
            )
            env_path = str(Path(tmp) / "envelopes.json")
            Path(env_path).write_text(
                json.dumps(
                    {
                        "qitem-20261020100009-ffffffffffffffff": {
                            "premise_hash": PREMISE_HASH
                        }
                    }
                )
            )
            proc = run_reconcile(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--envelopes",
                env_path,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stalled-envelope-absence", proc.stdout)
            self.assertIn("NEEDS-HUMAN-REVIEW", proc.stdout)
            self.assertNotIn("PROPOSED-CELL:::", proc.stdout)
            # Same fixtures without the flag stay quiet (E2 clean-quiet).
            proc = run_reconcile(
                "--tracker", tracker, "--queue-list", qlist, "--transitions", trans
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("in sync", proc.stdout)

    def test_reconcile_end_to_end_matching_envelope_quiet(self):
        """REQ-E5 through reconcile: --envelopes with a match -> exit 0."""
        with tempfile.TemporaryDirectory() as tmp:
            tracker = write_tracker(tmp)
            qlist, trans = write_queue(
                tmp, landing_note(diff_hash=PREMISE_HASH, paths="src/include/hash.h")
            )
            env_path = str(Path(tmp) / "envelopes.json")
            Path(env_path).write_text(
                json.dumps({PARENT: {"premise_hash": PREMISE_HASH}})
            )
            proc = run_reconcile(
                "--tracker",
                tracker,
                "--queue-list",
                qlist,
                "--transitions",
                trans,
                "--envelopes",
                env_path,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("in sync", proc.stdout)

    def test_presence_check_removal_is_silent(self):
        """Anti-vacuity pin: killing the presence check restores silence.

        Proves the suite is non-vacuous: if the classifier ever stops
        consulting the envelope lookup, this test (and the end-to-end
        above) flips — sabotage cannot outrun the corpus.
        """
        model = load_model()
        lookup = {
            "qitem-20261020100009-ffffffffffffffff": {"premise_hash": PREMISE_HASH}
        }
        with mock.patch.object(
            model, "stalled_envelope_absence_diff", return_value=None
        ):
            self.assertIsNone(
                model.diff_row(
                    self.clean_row(),
                    self.clean_queue(),
                    self.clean_trans(),
                    envelope_by_id=lookup,
                ),
                "with the presence check disabled the clean unenveloped row "
                "must go silent (RED direction of the R1 red-proof)",
            )
        self.assertIsNotNone(
            model.diff_row(
                self.clean_row(),
                self.clean_queue(),
                self.clean_trans(),
                envelope_by_id=lookup,
            )
        )

    def test_no_commit_surface_in_presence_path(self):
        """REQ-E3 pinning: the presence path owns no executor or committer.

        Scoped to the NEW presence helper (the module's pre-existing
        `run_rig` read-only queue fetcher is allow-listed to
        `queue list/transitions --json` and untouched by this change):
        stripping docstrings/comments from the helper source must leave
        no executor, shell, or commit call behind.
        """
        import inspect

        model = load_model()
        source = inspect.getsource(model.stalled_envelope_absence_diff)
        code = re.sub(r'""".*?"""', "", source, flags=re.DOTALL)
        code = "\n".join(line.split("#", 1)[0] for line in code.splitlines())
        for marker in (
            "subprocess",
            "os.system",
            "os.exec",
            "os.popen",
            "check_output",
            ".commit(",
            "auto-commit",
            "self-execut",
        ):
            self.assertNotIn(marker, code)
        self.assertIn("never", source.lower())


if __name__ == "__main__":
    unittest.main()
