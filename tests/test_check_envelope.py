#!/usr/bin/env python3
"""Binary fail-closed tests for the PRE-AUTH envelope verifier (issue #12 wave, 12b).

REQ-BC4 (review criterion N2): NO envelope-validating code existed in this
worktree, so this suite pins the verifier field-by-field — an envelope
missing/invalid in path scope, owning seats, enumerated actions, TPM gating,
expiry, revocation, or any of the 3 audit links MUST be refused (operator
holds, no execution); exactly one fully-populated envelope MUST be accepted.
Existing receipt-parsing + never-raw-`rig-send` coverage
(tests/test_queue_json_discipline.py) stays unchanged.

Hermetic: envelopes are inline strings staged to /tmp; the verifier is
invoked as a subprocess with --at pinning reference time. No daemon, no
network, no live checkout.
Run: python3 -m unittest tests/test_check_envelope.py -v
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "scripts/check-envelope.py"

NOW = "2026-10-23 19:00Z"

VALID_ENVELOPE = """\
PRE-AUTH ENVELOPE WAVE12-CANARY-001
Slice class: engine-canary-elapsed-proof
Issued by: wave-12-operator
Issued at (UTC): 2026-10-23 19:00Z
Expiry: expires 2026-10-24 19:00Z
Path scope (exact repo paths):
src/engine/
tests/engine/
CMakeLists.txt
build.sh
Owning seats: engine-systems-eng, cpp-lowlevel-eng
Permitted operator actions:
COMMIT
FILE-QUEUE-ITEM ops-log
TPM verification gate:
1. WHAT: seat close-out doc + CTest log + tree SHA
2. BY WHOM: TPM
3. ARTIFACTS: queue item qitem-20261023000000-aaaaaaaaaaaaaaaa + attached log paths
Revocation: issuer or any senior human operator, via signed queue item to the operator channel or direct session order
Audit trail:
1. This envelope filed as queue item qitem-20261023000000-bbbbbbbbbbbbbbbb
2. The TPM verification record qitem-20261023000000-cccccccccccccccc
3. The execution record commit SHA + executor + timestamp in the ops log
OPTIONAL notes: canary scope only; engine-systems-eng clock-read grant verification
"""

# Template-verbatim wrapped header forms (docs/sprints/PRE-AUTH-ENVELOPES.md
# section 2 renders `Permitted operator` / `actions:`, `TPM verification` /
# `gate:` and `Path scope` / `(exact repo paths):` across two lines).
WRAPPED_ENVELOPE = """\
PRE-AUTH ENVELOPE WAVE12-CANARY-002
Slice class: engine-canary-elapsed-proof
Issued by: wave-12-operator
Issued at (UTC): 2026-10-23 19:00Z
Expiry: single-slice: void after first execution attempt (success or failure)
Path scope
(exact repo paths): src/engine/, tests/engine/
Owning seats: engine-systems-eng
Permitted operator
actions: COMMIT
TPM verification
gate:
1. WHAT: seat close-out doc + tree SHA
2. BY WHOM: TPM
3. ARTIFACTS: queue item qitem-20261023000000-dddddddddddddddd
Revocation: issuer, via signed queue item to the operator channel
Audit trail:
1. This envelope filed as queue item qitem-20261023000000-eeeeeeeeeeeeeeee
2. The TPM verification record qitem-20261023000000-ffffffffffffffff
3. The execution record commit SHA + executor + timestamp in the ops log
"""


def run_checker(text=None, path=None, *extra):
    """Invoke the checker; text staged to /tmp unless an explicit path wins."""
    if path is None:
        staged = Path(tempfile.mkdtemp()) / "envelope.txt"
        staged.write_text(text if text is not None else VALID_ENVELOPE)
        path = str(staged)
    proc = subprocess.run(
        [sys.executable, str(CHECKER), "--envelope", path, "--at", NOW, *extra],
        capture_output=True,
        text=True,
    )
    return proc


def mutate(base, old, new):
    assert old in base, f"mutation anchor missing: {old!r}"
    return base.replace(old, new, 1)


def drop_line(base, prefix):
    kept = [ln for ln in base.splitlines() if not ln.startswith(prefix)]
    assert len(kept) < len(base.splitlines()), f"drop anchor missing: {prefix!r}"
    return "\n".join(kept) + "\n"


class EnvelopeAcceptTests(unittest.TestCase):
    def test_fully_populated_envelope_accepted(self):
        """N2 green: exactly one fully-populated envelope MUST be accepted."""
        proc = run_checker(VALID_ENVELOPE)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ACCEPT", proc.stdout)

    def test_template_wrapped_headers_accepted(self):
        """Template-verbatim wrapped header forms parse identically."""
        proc = run_checker(WRAPPED_ENVELOPE)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ACCEPT", proc.stdout)


class EnvelopeIdentityTests(unittest.TestCase):
    def test_missing_envelope_id_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "PRE-AUTH ENVELOPE"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("ENVELOPE", proc.stdout + proc.stderr)

    def test_missing_slice_class_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "Slice class:"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Slice", proc.stdout + proc.stderr)

    def test_missing_issued_by_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "Issued by:"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Issued by", proc.stdout + proc.stderr)

    def test_missing_issued_at_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "Issued at"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Issued at", proc.stdout + proc.stderr)

    def test_malformed_issued_at_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "2026-10-23 19:00Z", "tomorrow"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Issued at", proc.stdout + proc.stderr)


class EnvelopeExpiryTests(unittest.TestCase):
    def test_missing_expiry_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "Expiry:"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Expiry", proc.stdout + proc.stderr)

    def test_open_ended_expiry_refused(self):
        proc = run_checker(
            mutate(VALID_ENVELOPE, "expires 2026-10-24 19:00Z", "open-ended")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Expiry", proc.stdout + proc.stderr)

    def test_never_expiry_refused(self):
        proc = run_checker(
            mutate(VALID_ENVELOPE, "expires 2026-10-24 19:00Z", "never expires")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Expiry", proc.stdout + proc.stderr)

    def test_expired_deadline_refused(self):
        proc = run_checker(
            mutate(
                VALID_ENVELOPE, "expires 2026-10-24 19:00Z", "expires 2026-10-22 19:00Z"
            )
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Expiry", proc.stdout + proc.stderr)

    def test_combined_single_slice_and_deadline_refused(self):
        """Expiry is XOR: single-slice AND an explicit deadline is refused."""
        proc = run_checker(
            mutate(
                VALID_ENVELOPE,
                "Expiry: expires 2026-10-24 19:00Z",
                "Expiry: single-slice: void after first execution attempt; "
                "expires 2026-10-24 19:00Z",
            )
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Expiry", proc.stdout + proc.stderr)

    def test_single_slice_consumed_refused(self):
        """Single-slice envelopes are void after the first attempt."""
        proc = run_checker(WRAPPED_ENVELOPE, None, "--consumed")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("VOID", proc.stdout + proc.stderr)

    def test_revoked_envelope_refused(self):
        proc = run_checker(VALID_ENVELOPE, None, "--revoked")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("VOID", proc.stdout + proc.stderr)


class EnvelopeScopeTests(unittest.TestCase):
    def test_missing_path_scope_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "Path scope"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Path scope", proc.stdout + proc.stderr)

    def test_absolute_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "/etc/passwd"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Path scope", proc.stdout + proc.stderr)

    def test_parent_traversal_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "../evil"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Path scope", proc.stdout + proc.stderr)

    def test_root_alias_dot_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "."))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Path scope", proc.stdout + proc.stderr)

    def test_root_alias_dot_slash_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "./"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Path scope", proc.stdout + proc.stderr)

    def test_home_prefixed_entry_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "~/evil"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Path scope", proc.stdout + proc.stderr)

    def test_glob_star_entry_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "src/*"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Path scope", proc.stdout + proc.stderr)

    def test_glob_bracket_entry_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "src/[a-z]"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Path scope", proc.stdout + proc.stderr)

    def test_missing_owning_seats_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "Owning seats:"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Owning seats", proc.stdout + proc.stderr)

    def test_malformed_seat_token_refused(self):
        proc = run_checker(
            mutate(
                VALID_ENVELOPE,
                "engine-systems-eng, cpp-lowlevel-eng",
                "Engine Systems!",
            )
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Owning seats", proc.stdout + proc.stderr)


class EnvelopeActionTests(unittest.TestCase):
    def test_missing_actions_refused(self):
        text = VALID_ENVELOPE.replace(
            "Permitted operator actions:\nCOMMIT\nFILE-QUEUE-ITEM ops-log\n", ""
        )
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("action", proc.stdout + proc.stderr)

    def test_forbidden_verb_rebase_refused(self):
        proc = run_checker(VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "REBASE"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("action", proc.stdout + proc.stderr)

    def test_forbidden_verb_seed_refused(self):
        proc = run_checker(VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "SEED"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("action", proc.stdout + proc.stderr)

    def test_bare_push_without_branch_refused(self):
        proc = run_checker(VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "PUSH"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("action", proc.stdout + proc.stderr)

    def test_commit_with_flags_refused(self):
        proc = run_checker(VALID_ENVELOPE.replace("COMMIT\n", "COMMIT --amend\n"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("action", proc.stdout + proc.stderr)

    def test_bare_file_queue_item_refused(self):
        proc = run_checker(
            VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "FILE-QUEUE-ITEM")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("action", proc.stdout + proc.stderr)

    def test_duplicate_actions_sections_refused(self):
        """A second Permitted-actions section must not be silently ignored."""
        text = VALID_ENVELOPE + "Permitted operator actions:\nREBASE\n"
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("AMBIGUOUS", proc.stdout + proc.stderr)

    def test_push_force_refspec_refused(self):
        proc = run_checker(
            VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "PUSH +main")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("action", proc.stdout + proc.stderr)

    def test_push_colon_refspec_refused(self):
        proc = run_checker(
            VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "PUSH :main")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("action", proc.stdout + proc.stderr)

    def test_push_head_refspec_refused(self):
        proc = run_checker(
            VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "PUSH HEAD:main")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("action", proc.stdout + proc.stderr)

    def test_push_bare_main_refused(self):
        """M8 (#92): PUSH to trunk refs (main/master/HEAD) is refused — exact
        branch form or not, trunk pushes are never envelope work."""
        text = VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "PUSH main")
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("trunk", proc.stdout + proc.stderr)

    def test_explicit_push_with_branch_accepted(self):
        """PUSH is permitted ONLY with the exact branch named."""
        text = VALID_ENVELOPE.replace(
            "FILE-QUEUE-ITEM ops-log", "PUSH feat/wave-12-canary"
        )
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("ACCEPT", proc.stdout)


class EnvelopeTpmTests(unittest.TestCase):
    def test_missing_tpm_gate_refused(self):
        text = VALID_ENVELOPE.replace(
            "TPM verification gate:\n"
            "1. WHAT: seat close-out doc + CTest log + tree SHA\n"
            "2. BY WHOM: TPM\n"
            "3. ARTIFACTS: queue item qitem-20261023000000-aaaaaaaaaaaaaaaa + attached log paths\n",
            "",
        )
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("TPM", proc.stdout + proc.stderr)

    def test_missing_what_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "1. WHAT:"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("TPM", proc.stdout + proc.stderr)

    def test_missing_artifacts_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "3. ARTIFACTS:"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("TPM", proc.stdout + proc.stderr)

    def test_embedded_what_marker_does_not_satisfy(self):
        """Marker text embedded mid-record must NOT satisfy presence."""
        text = mutate(
            VALID_ENVELOPE,
            "1. WHAT: seat close-out doc + CTest log + tree SHA",
            "1. scope note: whatever the seat produced is attached",
        )
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("WHAT", proc.stdout + proc.stderr)

    def test_empty_what_value_refused(self):
        text = mutate(
            VALID_ENVELOPE,
            "1. WHAT: seat close-out doc + CTest log + tree SHA",
            "1. WHAT:",
        )
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("TPM", proc.stdout + proc.stderr)

    def test_owning_seat_as_verifier_refused(self):
        """The verifier must not be an owning seat for its own work."""
        proc = run_checker(
            mutate(VALID_ENVELOPE, "2. BY WHOM: TPM", "2. BY WHOM: engine-systems-eng")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("TPM", proc.stdout + proc.stderr)


class EnvelopeRevocationAuditTests(unittest.TestCase):
    def test_missing_revocation_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "Revocation:"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Revocation", proc.stdout + proc.stderr)

    def test_none_revocation_refused(self):
        proc = run_checker(
            mutate(
                VALID_ENVELOPE,
                "issuer or any senior human operator, via signed queue item to the operator channel or direct session order",
                "none",
            )
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Revocation", proc.stdout + proc.stderr)

    def test_missing_audit_trail_refused(self):
        proc = run_checker(drop_line(VALID_ENVELOPE, "Audit trail:"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Audit", proc.stdout + proc.stderr)

    def test_two_link_audit_refused(self):
        """Missing any of the 3 audit links = incomplete execution."""
        proc = run_checker(drop_line(VALID_ENVELOPE, "3. The execution record"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("Audit", proc.stdout + proc.stderr)


class EnvelopeRobustnessTests(unittest.TestCase):
    def test_unreadable_envelope_fails_closed(self):
        proc = run_checker(None, "/tmp/does-not-exist-wave12-envelope.txt")
        self.assertNotEqual(proc.returncode, 0)

    def test_unknown_top_level_section_refused(self):
        text = VALID_ENVELOPE.replace("OPTIONAL notes:", "Extra grants:")
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("unknown section", proc.stdout + proc.stderr)

    def test_usage_error_without_envelope(self):
        proc = subprocess.run(
            [sys.executable, str(CHECKER), "--at", NOW],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()


class TestEnvelopeSemanticsM8(unittest.TestCase):
    """M8 (#92): path-scope, PUSH-branch, time-ordering, seat/marker/link
    semantics. Every row here must REFUSE (rc=1)."""

    def test_dotgit_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", ".git/hooks/x"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_dotpi_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", ".pi/agent/x"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_dotagents_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", ".agents/y"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_fleet_dir_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "fleet/fleet.yaml"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_scripts_dir_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "scripts/run.sh"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_agents_md_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "AGENTS.md"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "docs/AGENTS.md"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_leading_dash_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "-evil"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_colon_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "src/a:b"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_non_ascii_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "src/caf\u00e9/"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_percent_path_refused(self):
        proc = run_checker(mutate(VALID_ENVELOPE, "src/engine/", "src/100%x/"))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_push_main_refused(self):
        proc = run_checker(
            VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "PUSH main")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_push_master_refused(self):
        proc = run_checker(
            VALID_ENVELOPE.replace("FILE-QUEUE-ITEM ops-log", "PUSH master")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_far_future_expiry_refused(self):
        """A 9999 deadline exceeds the issued+14d window."""
        proc = run_checker(
            mutate(
                VALID_ENVELOPE, "expires 2026-10-24 19:00Z", "expires 9999-01-01 00:00Z"
            )
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_issued_after_expiry_refused(self):
        """Issued (10-24) after the deadline (10-23 20:00Z), now pinned 10-23."""
        text = mutate(VALID_ENVELOPE, "2026-10-23 19:00Z", "2026-10-24 19:00Z")
        text = mutate(text, "expires 2026-10-24 19:00Z", "expires 2026-10-23 20:00Z")
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_future_issued_refused(self):
        """An envelope issued after --at is not yet live."""
        text = mutate(VALID_ENVELOPE, "2026-10-23 19:00Z", "2026-10-25 19:00Z")
        text = mutate(text, "expires 2026-10-24 19:00Z", "expires 2026-10-26 19:00Z")
        proc = run_checker(text)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_multiple_deadlines_governed_by_min(self):
        """A live first deadline plus an expired second one is expired."""
        proc = run_checker(
            mutate(
                VALID_ENVELOPE,
                "Expiry: expires 2026-10-24 19:00Z",
                "Expiry: expires 2026-10-24 19:00Z; extended, expires 2026-10-22 19:00Z",
            )
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_unknown_owning_seat_refused(self):
        proc = run_checker(
            mutate(
                VALID_ENVELOPE,
                "engine-systems-eng, cpp-lowlevel-eng",
                "engine-systems-eng, not-a-real-seat",
            )
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_by_whom_nobody_refused(self):
        proc = run_checker(
            mutate(VALID_ENVELOPE, "2. BY WHOM: TPM", "2. BY WHOM: nobody")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_by_whom_non_tpm_seat_refused(self):
        proc = run_checker(
            mutate(VALID_ENVELOPE, "2. BY WHOM: TPM", "2. BY WHOM: go-backend-eng")
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_unlinked_audit_record_refused(self):
        proc = run_checker(
            mutate(
                VALID_ENVELOPE,
                "1. This envelope filed as queue item qitem-20261023000000-bbbbbbbbbbbbbbbb",
                "1. This envelope filed in the usual place",
            )
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
