#!/usr/bin/env python3
"""M1 (HR-F18) gate test: bare queue/send deny in seat maps.

Stage-time enforcement of REQ-C18 (openspec/changes/102-closeout): every
seat granting `rig queue *` must declare the exact fleet `bash_deny`
triple, every committed seat bash map must carry those denies after the
matching allows (pps last-match-wins), and under pps wildcard semantics
the bare forms must deny while the `--json` / `--json --verify` /
addressed-send forms still allow. Standalone (`python3 tests/...`);
V22 in scripts/verify-rigs.sh enforces the same property in `make verify`.
"""

import json
import os
import re
import unittest
from pathlib import Path

# HERETEK_TEST_ROOT override supports red-proof runs against a pristine
# checkout (e.g. the pre-fix base) without moving the test file.
ROOT = Path(os.environ.get("HERETEK_TEST_ROOT", Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

BARE_DENIES = ["rig queue list", "rig queue create", "rig send"]


def pps_translate(core: str) -> str:
    out = []
    for ch in core:
        if ch == "*":
            out.append(".*")
        elif ch == "?":
            out.append(".")
        else:
            out.append(re.escape(ch))
    return "".join(out)


def pps_match(pattern: str, value: str) -> bool:
    """Mirror of @gotgenes/pi-permission-system wildcard-matcher.ts.

    `*` matches any sequence (incl. empty), `?` one char, match anchored;
    a trailing " *" makes the space-and-arguments portion optional (so
    "rig queue *" also matches bare "rig queue").
    """
    if pattern.endswith(" *"):
        rx = "^" + pps_translate(pattern[:-2]) + r"( .*)?$"
    else:
        rx = "^" + pps_translate(pattern) + "$"
    return re.match(rx, value, re.DOTALL) is not None


def pps_decide(bash_map: dict, command: str) -> str:
    """Last matching pattern wins; no match -> deny (leading "*": deny)."""
    decision = "deny"
    for pat, verdict in bash_map.items():
        if pps_match(pat, command):
            decision = verdict
    return decision


class TestM1BareDeny(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROOT / "fleet/fleet.yaml") as f:
            cls.fleet = yaml.safe_load(f)
        leaves = sorted(
            (ROOT / "specs/agents").rglob("runtime/pi-permission-config.json")
        )
        assert leaves, "no rendered permission leaves found"
        cls.leaves = leaves

    def test_fleet_declares_bare_denies(self):
        """Every seat granting `rig queue *` must declare the 3 bare denies."""
        bad = []
        for rid, r in self.fleet["roles"].items():
            ba = (r.get("permissions") or {}).get("bash_allow") or []
            if any(str(b).startswith("rig queue") for b in ba):
                got = (r.get("permissions") or {}).get("bash_deny") or []
                if [str(x) for x in got] != BARE_DENIES:
                    bad.append(rid)
        self.assertEqual(
            bad, [], f"roles missing exact bash_deny {BARE_DENIES}: {bad[:5]}"
        )

    def test_rendered_maps_deny_bare_forms(self):
        """Committed seat maps deny the bare forms under pps semantics."""
        offenders = []
        for leaf in self.leaves:
            bash_map = (
                json.loads(leaf.read_text()).get("permission", {}).get("bash", {})
            )
            for cmd in BARE_DENIES:
                if pps_decide(bash_map, cmd) != "deny":
                    offenders.append(f"{leaf.parent.parent.name}: allows {cmd!r}")
        self.assertEqual(offenders, [], f"bare forms allowed: {offenders[:6]}")

    def test_rendered_maps_allow_disciplined_forms(self):
        """The --json / --json --verify / addressed-send forms must stay allowed."""
        probed = 0
        bad = []
        allowed_cmds = [
            "rig queue list --json",
            "rig queue list --json --destination delivery-tpm-scrum-lead@executive-and-architecture",
            "rig queue create --json --verify --source a --destination b --summary s --body-file f",
            'rig send delivery-tpm-scrum-lead@executive-and-architecture "hello"',
            "rig whoami",
            "rig queue show --json qitem-abc",
        ]
        for leaf in self.leaves:
            bash_map = (
                json.loads(leaf.read_text()).get("permission", {}).get("bash", {})
            )
            for cmd in allowed_cmds:
                probed += 1
                if pps_decide(bash_map, cmd) != "allow":
                    bad.append(f"{leaf.parent.parent.name}: denies {cmd!r}")
        self.assertGreater(probed, 0)
        self.assertEqual(bad, [], f"disciplined forms denied: {bad[:6]}")

    def test_denies_sit_after_allows(self):
        """Bare denies render after every allow matching the same command.

        (#91 gcc overlay allows sit after the terminal denies by design;
        they never match `rig ...` strings, so the property that matters
        is deny-after-matching-allow per bare command — true last-match-wins
        precedence — not deny-after-every-key.)
        """
        bad = []
        for leaf in self.leaves:
            bash_map = (
                json.loads(leaf.read_text()).get("permission", {}).get("bash", {})
            )
            keys = list(bash_map.keys())
            for d in BARE_DENIES:
                if d not in keys:
                    continue
                di = keys.index(d)
                for k in keys:
                    if (
                        bash_map[k] == "allow"
                        and pps_match(k, d)
                        and keys.index(k) > di
                    ):
                        bad.append(
                            f"{leaf.parent.parent.name}: allow {k!r} beats deny {d!r}"
                        )
        self.assertEqual(bad, [], f"allow-after-deny on same command: {bad[:6]}")


if __name__ == "__main__":
    unittest.main()
