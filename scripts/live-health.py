#!/usr/bin/env python3
"""Warn-first live-fleet health gate (remediate-45-live-health, REQ-LH1..LH9).

Read-only against the daemon: this script ONLY runs
  rig queue list | overdue | undelivered | show | transitions  (always --json)
  rig ps --nodes  (always --json --no-cleanup)
  rig daemon status
anything else is refused by check_allowed() (fail-closed, REQ-LH8).

Sub-checks report PASS / WARN / FAIL / SKIP. SKIP is never PASS (REQ-LH2):
any unreachable or unconfigured data source is named in the summary, and a
run with any SKIP MUST NOT print the healthy banner. Advisory default:
exit 0 on WARN/SKIP; --strict promotes WARN breaches to FAIL + exit 2.

Thresholds (all tunable via flags or env; every run prints effective values):
  T_pickup       claim -> first-transition latency     flag --t-pickup-min       env LH_T_PICKUP_MIN       default 15 (min)
  T_stuck        overdue age past closure_required_at  flag --t-stuck-min        env LH_T_STUCK_MIN        default 30 (min)
  T_undelivered  undelivered-nudge age                 flag --t-undelivered-min  env LH_T_UNDELIVERED_MIN  default 15 (min)
  T_hb           heartbeat freshness = hb_mult x role heartbeat_sec
                                                       flag --hb-mult           env LH_HB_MULT            default 3 (x)

Seat-idleness definition (REQ-LH9): a seat is idle-at-prompt while holding
work when agentActivity.state (case/separator-insensitive) is one of
{idle, idle-at-prompt, waiting, waiting-for-input} AND the seat holds >=1
claimed (in-progress) queue row. States {running, active, busy, working} count
as active. Any other/missing state resolves to SKIP for that seat, never healthy.

Overdue histogram buckets (REQ-LH5): `<=T_stuck` (grace), `T_stuck-2xT_stuck`,
`>2xT_stuck`, measured as age past closure_required_at (fallback: tsUpdated).

Promotion policy (REQ-LH7): breaches WARN + exit 0 until thresholds are
calibrated against a baseline distribution of pickup latency / stuck-row age
collected from warn-first runs, and a human approves the flip to --strict in
CI. Warn-first MUST NOT rot into report-only: if calibration evidence has not
been reviewed within 30 days of landing, the owning team either promotes or
records a dated deferral. Post-promotion, WARN becomes FAIL + nonzero exit.

Unparseable threshold config dies with a usage error (fail-closed on config,
distinct from fleet state). Unparseable CLI output resolves the affected
sub-check to SKIP + WARN naming the verb, never to healthy.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FLEET_FILE = REPO_ROOT / "fleet" / "fleet.yaml"
RIG_BIN = os.environ.get("RIG_PATH", "rig")

DEFAULT_T_PICKUP_MIN = 15.0
DEFAULT_T_STUCK_MIN = 30.0
DEFAULT_T_UNDELIVERED_MIN = 15.0
DEFAULT_HB_MULT = 3.0
FETCH_LIMIT = 100

IDLE_STATES = {"idle", "idleatprompt", "waiting", "waitingforinput"}
ACTIVE_STATES = {"running", "active", "busy", "working"}

# provisioning-gate-74 (#74, REQ-P3/P4): host tool artifacts the gate
# resolves read-only (shutil.which + path-exists, no installs/pulls/
# network). Bash-grant leading binaries with no catalog command.
PROVISIONING_BASH_BINARIES = ("r2", "rabin2", "tshark")


class DataSourceError(Exception):
    """A live data source is unreachable, errored, or unparseable."""


# ---------------------------------------------------------------------------
# Read-only enforcement (REQ-LH8)
# ---------------------------------------------------------------------------


def check_allowed(argv):
    """Refuse anything that is not a known read-only observation verb."""
    if not argv:
        raise RuntimeError("refusing empty rig invocation")
    if argv[0] == "daemon" and argv[1:] == ["status"]:
        return
    if argv[0] == "ps":
        if "--nodes" in argv and "--json" in argv and "--no-cleanup" in argv:
            return
        raise RuntimeError(
            f"refusing ps invocation without pinned read-only flags "
            f"(--nodes --json --no-cleanup): {argv}"
        )
    if (
        argv[0] == "queue"
        and len(argv) > 1
        and argv[1] in ("list", "overdue", "undelivered", "show", "transitions")
    ):
        if "--json" not in argv:
            raise RuntimeError(
                f"refusing {argv}: queue/ps verbs must use --json "
                "(pinned parseable combo, #44)"
            )
        return
    raise RuntimeError(f"refusing non-read-only rig invocation: {argv}")


def run_rig(args, timeout=60):
    """Run one allowlisted rig command, return parsed JSON (or raw text)."""
    check_allowed(args)
    try:
        proc = subprocess.run(
            [RIG_BIN, *args], capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise DataSourceError(f"rig binary not found at {RIG_BIN}: {exc}")
    except subprocess.TimeoutExpired:
        raise DataSourceError(f"rig {' '.join(args)} timed out")
    if proc.returncode != 0:
        raise DataSourceError(
            f"rig {' '.join(args)} exited {proc.returncode}: "
            f"{proc.stderr.strip()[:300]}"
        )
    if args[0] == "daemon":
        return {"status_text": proc.stdout.strip()}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise DataSourceError(f"rig {' '.join(args)} output unparseable as JSON: {exc}")


class RigClient:
    """Live read-only client over the rig CLI."""

    def __init__(self, rig_scope_all=True, rig_name=None, limit=FETCH_LIMIT):
        self.scope = (
            ["-A"]
            if rig_scope_all and not rig_name
            else (["--rig", rig_name] if rig_name else [])
        )

        self.limit = limit

    def _q(self, verb, extra=None):
        args = ["queue", verb, "--json", *self.scope, "--limit", str(self.limit)]
        if extra:
            args.extend(extra)
        result = run_rig(args)
        if not isinstance(result, list):
            raise DataSourceError(f"rig queue {verb}: expected a JSON list")
        if len(result) >= self.limit:
            raise DataSourceError(
                f"rig queue {verb}: {len(result)} rows hit the fetch cap "
                f"({self.limit}); results may be truncated, "
                "refusing to report healthy"
            )
        return result

    def fetch_list(self):
        return self._q("list")

    def fetch_overdue(self):
        return self._q("overdue")

    def fetch_undelivered(self):
        return self._q("undelivered")

    def fetch_transitions(self, qitem_id):
        result = run_rig(["queue", "transitions", "--json", qitem_id])
        if not isinstance(result, list):
            raise DataSourceError(
                f"rig queue transitions {qitem_id}: expected a JSON list"
            )
        return result

    def fetch_ps_nodes(self):
        args = ["ps", "--nodes", "--json", "--no-cleanup", *self.scope]
        result = run_rig(args)
        if not isinstance(result, list):
            raise DataSourceError("rig ps --nodes: expected a JSON list")
        return result

    def fetch_tool_status(self):
        """provisioning-gate-74 (#74, REQ-P3): live host tool resolution."""
        return live_tool_status()


class FixtureClient:
    """Deterministic replay client over saved JSON fixtures (QA red-proofs)."""

    def __init__(self, fixture_dir):
        self.root = Path(fixture_dir)

    def _load(self, name, default=None):
        path = self.root / name
        if not path.exists():
            if default is not None:
                return default
            raise DataSourceError(f"fixture {name} missing in {self.root}")
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            raise DataSourceError(f"fixture {name} unreadable: {exc}")

    def fetch_list(self):
        return self._load("queue_list.json")

    def fetch_overdue(self):
        return self._load("queue_overdue.json", default=[])

    def fetch_undelivered(self):
        return self._load("queue_undelivered.json", default=[])

    def fetch_ps_nodes(self):
        return self._load("ps_nodes.json", default=[])

    def fetch_transitions(self, qitem_id):
        return self._load("transitions.json", default={}).get(qitem_id, [])

    def fetch_fleet_heartbeat(self):
        return self._load("fleet_heartbeat.json", default=None)

    def fetch_tool_status(self):
        """provisioning-gate-74 (#74, REQ-P3): replayed tool status, or an
        unassessed marker (SKIP, never healthy) when the fixture ships none."""
        status = self._load(
            "tool_provisioning.json", default={"missing": [], "total": 0}
        )
        if status is None:
            return {"missing": [], "total": 0}
        return status


# ---------------------------------------------------------------------------
# Pure evaluation helpers (unit-tested, no I/O)
# ---------------------------------------------------------------------------


def parse_iso_ts(value):
    if not value or not isinstance(value, str):
        return None
    try:
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        moment = datetime.fromisoformat(text)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        return moment
    except (ValueError, OverflowError):
        return None


def age_minutes(since, now):
    moment = parse_iso_ts(since)
    if moment is None:
        return None
    return (now - moment).total_seconds() / 60.0


def _fmt_age(age_min):
    if age_min is None:
        return "age-unknown"
    if age_min < 60:
        return f"{age_min:.0f}m"
    return f"{age_min / 60.0:.1f}h"


class GateOpts:
    def __init__(
        self,
        t_pickup_min=DEFAULT_T_PICKUP_MIN,
        t_stuck_min=DEFAULT_T_STUCK_MIN,
        t_undelivered_min=DEFAULT_T_UNDELIVERED_MIN,
        hb_mult=DEFAULT_HB_MULT,
        strict=False,
        rig_scope_all=True,
        rig_name=None,
        limit=FETCH_LIMIT,
    ):
        self.t_pickup_min = t_pickup_min
        self.t_stuck_min = t_stuck_min
        self.t_undelivered_min = t_undelivered_min
        self.hb_mult = hb_mult
        self.strict = strict
        self.rig_scope_all = rig_scope_all
        self.rig_name = rig_name
        self.limit = limit


def effective_values(opts):
    return {
        "T_pickup_min": opts.t_pickup_min,
        "T_stuck_min": opts.t_stuck_min,
        "T_undelivered_min": opts.t_undelivered_min,
        "T_hb_mult": opts.hb_mult,
    }


def _promote(status, strict):
    if status == "WARN" and strict:
        return "FAIL"
    return status


def evaluate_pickup(rows, get_transitions, now, t_pickup_min):
    """REQ-LH4: claim -> first-transition latency per claimed row."""
    breached, unknown = [], []
    for row in rows:
        qid = row.get("qitemId", "?")
        claimed_at = row.get("claimedAt")
        if row.get("state") != "in-progress" or not claimed_at:
            continue
        claim_ts = parse_iso_ts(claimed_at)
        if claim_ts is None:
            unknown.append(qid)
            continue
        try:
            transitions = get_transitions(qid) or []
        except Exception:
            unknown.append(qid)
            continue
        first_post_claim = None
        for t in transitions:
            if not isinstance(t, dict):
                continue
            ts = parse_iso_ts(t.get("ts"))
            if ts is not None and ts > claim_ts:
                if first_post_claim is None or ts < first_post_claim:
                    first_post_claim = ts
        if first_post_claim is not None:
            latency = (first_post_claim - claim_ts).total_seconds() / 60.0
            if latency > t_pickup_min:
                breached.append({"id": qid, "age_min": latency})
            continue
        age = (now - claim_ts).total_seconds() / 60.0
        if age > t_pickup_min:
            breached.append({"id": qid, "age_min": age})
    if breached:
        detail = (
            "claimed rows whose first post-claim transition exceeded "
            f"T_pickup={t_pickup_min:g}m (or never arrived): "
            + ", ".join(f"{b['id']} ({_fmt_age(b['age_min'])})" for b in breached)
        )
        if unknown:
            detail += f"; transitions-unreadable: {', '.join(unknown)}"
        return {
            "name": "pickup",
            "status": "WARN",
            "detail": detail,
            "breached": breached,
        }
    if unknown:
        return {
            "name": "pickup",
            "status": "SKIP",
            "detail": "transitions unreadable for: " + ", ".join(unknown),
            "breached": [],
        }
    return {
        "name": "pickup",
        "status": "PASS",
        "detail": f"all claimed rows progressed within T_pickup={t_pickup_min:g}m",
        "breached": [],
    }


def evaluate_overdue(rows, now, t_stuck_min):
    """REQ-LH5: stuck-row age past closure_required_at + histogram."""
    buckets = {
        f"<=T_stuck({t_stuck_min:g}m)": 0,
        f"T_stuck-2xT({t_stuck_min:g}m-{2 * t_stuck_min:g}m)": 0,
        f">2xT(>{2 * t_stuck_min:g}m)": 0,
    }
    breached, unknown = [], []
    keys = list(buckets.keys())
    for row in rows:
        qid = row.get("qitemId", "?")
        age = age_minutes(row.get("closureRequiredAt"), now)
        if age is None:
            age = age_minutes(row.get("tsUpdated"), now)
        if age is None:
            unknown.append(qid)
            continue
        if age <= t_stuck_min:
            buckets[keys[0]] += 1
        elif age <= 2 * t_stuck_min:
            buckets[keys[1]] += 1
        else:
            buckets[keys[2]] += 1
        if age > t_stuck_min:
            breached.append({"id": qid, "age_min": age})
    hist = ", ".join(f"{k}={v}" for k, v in buckets.items())
    if breached:
        detail = (
            f"overdue rows past grace T_stuck={t_stuck_min:g}m: "
            + ", ".join(
                f"{b['id']} ({_fmt_age(b['age_min'])} past deadline)" for b in breached
            )
            + f" | histogram: {hist}"
        )
        if unknown:
            detail += f"; age-unknown: {', '.join(unknown)}"
        return {
            "name": "stuck-overdue",
            "status": "WARN",
            "detail": detail,
            "breached": breached,
            "histogram": buckets,
        }
    if unknown:
        return {
            "name": "stuck-overdue",
            "status": "SKIP",
            "detail": f"overdue ages unparseable for: "
            f"{', '.join(unknown)} | histogram: {hist}",
            "breached": [],
            "histogram": buckets,
        }
    return {
        "name": "stuck-overdue",
        "status": "PASS",
        "detail": f"no overdue rows past grace "
        f"T_stuck={t_stuck_min:g}m | histogram: {hist}",
        "breached": [],
        "histogram": buckets,
    }


def evaluate_undelivered(rows, now, t_undelivered_min):
    """REQ-LH6: PENDING rows whose create-path nudge FAILED."""
    breached, unknown = [], []
    for row in rows:
        qid = row.get("qitemId", "?")
        age = age_minutes(row.get("lastNudgeAttempt"), now)
        if age is None:
            age = age_minutes(row.get("tsCreated"), now)
        if age is None:
            unknown.append(qid)
            continue
        if age > t_undelivered_min:
            breached.append({"id": qid, "age_min": age})
    if breached:
        detail = (
            "undelivered rows beyond grace "
            f"T_undelivered={t_undelivered_min:g}m: "
            + ", ".join(f"{b['id']} ({_fmt_age(b['age_min'])})" for b in breached)
        )
        if unknown:
            detail += f"; age-unknown: {', '.join(unknown)}"
        return {
            "name": "undelivered",
            "status": "WARN",
            "detail": detail,
            "breached": breached,
        }
    if unknown:
        return {
            "name": "undelivered",
            "status": "SKIP",
            "detail": "undelivered ages unparseable for: " + ", ".join(unknown),
            "breached": [],
        }
    return {
        "name": "undelivered",
        "status": "PASS",
        "detail": "no undelivered rows beyond grace "
        f"T_undelivered={t_undelivered_min:g}m",
        "breached": [],
    }


def evaluate_heartbeat(assessed, unconfigured, now, hb_mult):
    """REQ-LH3: heartbeat freshness; UNCONFIGURED roles cap at WARN."""
    stale = []
    for entry in assessed:
        interval = entry.get("interval_sec") or 0
        if interval <= 0:
            continue
        age = age_minutes(entry.get("last_hb"), now)
        if age is None or age > hb_mult * interval / 60.0:
            stale.append(entry)
    unc = sorted(set(unconfigured or []))
    if unc:
        detail = f"UNCONFIGURED heartbeat roles ({len(unc)}): " + ", ".join(unc)
        if stale:
            detail += "; stale/missing heartbeat: " + ", ".join(
                f"{e['session']} ({_fmt_age(age_minutes(e.get('last_hb'), now))})"
                for e in stale
            )
        return {"name": "heartbeat", "status": "WARN", "detail": detail, "breached": []}
    if stale:
        detail = "stale/missing heartbeat: " + ", ".join(
            f"{e['session']} ({_fmt_age(age_minutes(e.get('last_hb'), now))})"
            for e in stale
        )
        return {"name": "heartbeat", "status": "WARN", "detail": detail, "breached": []}
    if not assessed:
        return {
            "name": "heartbeat",
            "status": "SKIP",
            "detail": "no claimed-row sessions to assess heartbeat for",
            "breached": [],
        }
    return {
        "name": "heartbeat",
        "status": "PASS",
        "detail": f"all {len(assessed)} assessed session(s) fresh "
        f"within {hb_mult:g}x role interval",
        "breached": [],
    }


def _norm_activity(state):
    if not isinstance(state, str):
        return ""
    return state.strip().lower().replace("-", "").replace("_", "").replace(" ", "")


def evaluate_seat_idleness(nodes, holders):
    """REQ-LH9: idle-at-prompt seats holding claimed rows are named."""
    by_session = {}
    for node in nodes:
        session = node.get("canonicalSessionName")
        if session:
            by_session[session] = node
    idle, skipped = [], []
    for session in sorted(holders):
        node = by_session.get(session)
        if node is None:
            skipped.append(f"{session} (no ps row)")
            continue
        activity = (node.get("agentActivity") or {}).get("state")
        norm = _norm_activity(activity)
        if norm in IDLE_STATES:
            idle.append(session)
        elif norm in ACTIVE_STATES:
            continue
        else:
            skipped.append(f"{session} (activity={activity!r})")
    if idle:
        detail = "idle-at-prompt holders of claimed rows: " + ", ".join(idle)
        if skipped:
            detail += "; activity-unknown (SKIP, not healthy): " + ", ".join(skipped)
        return {
            "name": "seat-idleness",
            "status": "WARN",
            "detail": detail,
            "breached": [],
        }
    if skipped:
        return {
            "name": "seat-idleness",
            "status": "SKIP",
            "detail": "activity state unparseable/unknown (never healthy): "
            + ", ".join(skipped),
            "breached": [],
        }
    return {
        "name": "seat-idleness",
        "status": "PASS",
        "detail": "no idle-at-prompt holders of claimed rows",
        "breached": [],
    }


def load_heartbeat_map(fleet_path):
    """Parse role -> heartbeat_sec from the fleet catalog (read-only).

    Returns (role_map, unconfigured_roles). Raises DataSourceError when the
    catalog cannot be read or contains no roles.
    """
    try:
        import yaml

        with open(fleet_path) as handle:
            data = yaml.safe_load(handle)
    except Exception as exc:
        raise DataSourceError(f"fleet catalog unreadable: {exc}")
    roles = {}
    if isinstance(data, dict):
        roles = data.get("roles", {}) or {}
        if not roles:
            for key, value in data.items():
                if isinstance(value, dict) and "heartbeat_sec" in value:
                    roles[key] = value
    if not roles:
        raise DataSourceError(f"no roles found in {fleet_path}")
    role_map, unconfigured = {}, []
    for role, config in roles.items():
        try:
            seconds = int((config or {}).get("heartbeat_sec", 0))
        except (TypeError, ValueError):
            seconds = 0
        role_map[role] = seconds
        if seconds <= 0:
            unconfigured.append(role)
    return role_map, sorted(unconfigured)


def session_role(session):
    """Map a canonical session to its fleet role (pod prefix stripped)."""
    local = (session or "").split("@", 1)[0]
    if "-" not in local:
        return local
    return local.split("-", 1)[1]


def live_tool_status(tools_dir=None, catalog_path=None):
    """Resolve every catalog stdio command + bash-grant binaries read-only.

    Returns {"missing": [...], "total": N}. Absolute @TOOLS@ paths must
    exist on disk; bare names (uvx, docker) must resolve via shutil.which.
    Remote-http servers (github) carry no command and are excluded.
    Raises DataSourceError when the catalog is unreadable.
    """
    import shutil as _shutil

    tools = tools_dir or os.environ.get(
        "HERETEK_TOOLS", str(Path.home() / ".local/share/heretek-rigs/tools")
    )
    catalog = catalog_path or (REPO_ROOT / "fleet" / "mcp-servers.yaml")
    try:
        import yaml

        with open(catalog) as handle:
            servers = (yaml.safe_load(handle) or {}).get("servers", {})
    except Exception as exc:
        raise DataSourceError(f"mcp catalog unreadable: {exc}")
    missing, total = [], 0
    for name in sorted(servers):
        server = servers[name] or {}
        if server.get("transport") == "http" or "command" not in server:
            continue
        total += 1
        raw = str(server["command"]).replace("@TOOLS@", tools)
        first = raw.strip()
        if not first:
            missing.append(f"{name}:<empty-command>")
            continue
        if first.startswith("/") or "/" in first:
            ok = _shutil.which(first) is not None
        else:
            ok = _shutil.which(first) is not None
        if not ok:
            missing.append(f"{name}:{first}")
    for binary in PROVISIONING_BASH_BINARIES:
        total += 1
        if _shutil.which(binary) is None:
            missing.append(binary)
    return {"missing": sorted(missing), "total": total}


def evaluate_tool_provisioning(status):
    """provisioning-gate-74 (#74, REQ-P3): WARN-first "0 missing tools"
    sub-check. Missing artifacts WARN (warn-first REQ-LH7, never a
    runtime hard fail); zero missing PASSes with the "0 missing tools"
    banner. Unassessed/unreadable sources SKIP, never healthy."""
    if not isinstance(status, dict):
        return {
            "name": "tool-provisioning",
            "status": "SKIP",
            "detail": f"tool status unparseable: {status!r}",
            "breached": [],
        }
    if status.get("error"):
        return {
            "name": "tool-provisioning",
            "status": "SKIP",
            "detail": f"tool source unreachable: {status['error']}",
            "breached": [],
        }
    missing = status.get("missing", [])
    total = status.get("total", 0)
    if missing:
        return {
            "name": "tool-provisioning",
            "status": "WARN",
            "detail": f"{len(missing)} missing host tool artifact(s) of "
            f"{total} checked: " + ", ".join(sorted(str(m) for m in missing)),
            "breached": [],
        }
    if not total:
        return {
            "name": "tool-provisioning",
            "status": "SKIP",
            "detail": "no tool artifacts assessed (never healthy)",
            "breached": [],
        }
    return {
        "name": "tool-provisioning",
        "status": "PASS",
        "detail": f"0 missing tools ({total} host tool artifacts resolve)",
        "breached": [],
    }


def run_gate(client, fleet_map, unconfigured, opts, now, tool_status=None):
    """Run all sub-checks; any DataSourceError degrades to SKIP (REQ-LH2)."""
    fleet_error = None
    if isinstance(unconfigured, Exception):
        fleet_error = str(unconfigured)
        unconfigured = []

    try:
        rows = client.fetch_list()
    except Exception as exc:
        skip = lambda name: {
            "name": name,
            "status": "SKIP",  # noqa: E731
            "detail": f"data source unreachable: {exc}",
            "breached": [],
        }
        checks = [
            skip("pickup"),
            skip("stuck-overdue"),
            skip("undelivered"),
            skip("heartbeat"),
            skip("seat-idleness"),
            skip("tool-provisioning"),
        ]
        return finalize(checks, opts)

    def safe(evaluate, *args):
        try:
            return evaluate(*args)
        except DataSourceError as exc:
            return {
                "name": getattr(evaluate, "__name__", "sub-check"),
                "status": "SKIP",
                "detail": f"data source unreachable: {exc}",
                "breached": [],
            }

    claimed = [
        r
        for r in rows
        if isinstance(r, dict)
        and r.get("state") == "in-progress"
        and r.get("claimedAt")
    ]
    holders = {
        r.get("destinationSession") for r in claimed if r.get("destinationSession")
    }

    pickup = safe(
        evaluate_pickup, claimed, client.fetch_transitions, now, opts.t_pickup_min
    )
    pickup["name"] = "pickup"

    try:
        overdue_rows = client.fetch_overdue()
    except Exception as exc:
        overdue_rows = DataSourceError(str(exc))
    overdue = (
        {
            "name": "stuck-overdue",
            "status": "SKIP",
            "detail": f"data source unreachable: {overdue_rows}",
            "breached": [],
        }
        if isinstance(overdue_rows, DataSourceError)
        else safe(evaluate_overdue, overdue_rows, now, opts.t_stuck_min)
    )
    overdue["name"] = "stuck-overdue"

    try:
        undelivered_rows = client.fetch_undelivered()
    except Exception as exc:
        undelivered_rows = DataSourceError(str(exc))
    undelivered = (
        {
            "name": "undelivered",
            "status": "SKIP",
            "detail": f"data source unreachable: {undelivered_rows}",
            "breached": [],
        }
        if isinstance(undelivered_rows, DataSourceError)
        else safe(evaluate_undelivered, undelivered_rows, now, opts.t_undelivered_min)
    )
    undelivered["name"] = "undelivered"

    if fleet_error is not None:
        heartbeat = {
            "name": "heartbeat",
            "status": "SKIP",
            "detail": f"fleet catalog unreadable: {fleet_error}",
            "breached": [],
        }
    else:
        latest_hb = {}
        for row in claimed:
            session = row.get("destinationSession")
            if not session:
                continue
            stamp = row.get("lastHeartbeat")
            if stamp is None:
                latest_hb.setdefault(session, None)
                continue
            if (
                session not in latest_hb
                or latest_hb[session] is None
                or (parse_iso_ts(stamp) or datetime.min.replace(tzinfo=timezone.utc))
                > (
                    parse_iso_ts(latest_hb[session])
                    or datetime.min.replace(tzinfo=timezone.utc)
                )
            ):
                latest_hb[session] = stamp
        assessed, hb_unknown = [], []
        for session, stamp in sorted(latest_hb.items()):
            role = session_role(session)
            if role not in fleet_map:
                hb_unknown.append(f"{session} (role mapping unknown)")
                continue
            assessed.append(
                {
                    "session": session,
                    "role": role,
                    "interval_sec": fleet_map[role],
                    "last_hb": stamp,
                }
            )
        heartbeat = safe(evaluate_heartbeat, assessed, unconfigured, now, opts.hb_mult)
        heartbeat["name"] = "heartbeat"
        if hb_unknown:
            heartbeat["detail"] += (
                "; role-mapping unknown (SKIP, not healthy): " + ", ".join(hb_unknown)
            )
            if heartbeat["status"] == "PASS":
                heartbeat["status"] = "SKIP"

    try:
        nodes = client.fetch_ps_nodes()
    except Exception as exc:
        nodes = DataSourceError(str(exc))
    if isinstance(nodes, DataSourceError):
        idleness = {
            "name": "seat-idleness",
            "status": "SKIP",
            "detail": f"data source unreachable: {nodes}",
            "breached": [],
        }
    else:
        idleness = safe(evaluate_seat_idleness, nodes, holders)
        idleness["name"] = "seat-idleness"

    # provisioning-gate-74 (#74, REQ-P3): WARN-first tool-provisioning
    # sub-check. Explicit tool_status (QA replay) wins; fixture clients may
    # serve tool_provisioning.json; live clients resolve the host read-only.
    if tool_status is None:
        fetch_tools = getattr(client, "fetch_tool_status", None)
        if callable(fetch_tools):
            try:
                tool_status = fetch_tools()
            except Exception as exc:
                tool_status = {"missing": [], "total": 0, "error": str(exc)}
        else:
            try:
                tool_status = live_tool_status()
            except Exception as exc:
                tool_status = {"missing": [], "total": 0, "error": str(exc)}
    tools_check = safe(evaluate_tool_provisioning, tool_status)
    tools_check["name"] = "tool-provisioning"

    return finalize(
        [pickup, overdue, undelivered, heartbeat, idleness, tools_check], opts
    )


def finalize(checks, opts):
    for check in checks:
        check["status"] = _promote(check["status"], opts.strict)
    sources_skipped = sum(1 for c in checks if c["status"] == "SKIP")
    sources_ok = len(checks) - sources_skipped
    if any(c["status"] == "FAIL" for c in checks):
        overall = "FAIL"
    elif any(c["status"] == "WARN" for c in checks):
        overall = "WARN"
    elif sources_skipped:
        overall = "SKIP"
    else:
        overall = "PASS"
    return {
        "checks": checks,
        "sources_ok": sources_ok,
        "sources_skipped": sources_skipped,
        "overall": overall,
    }


def render_text(report, effective):
    lines = []
    overall = report["overall"]
    if overall == "PASS":
        lines.append("LIVE-HEALTH PASS: all sub-checks PASS")
    elif overall == "FAIL":
        lines.append(
            "LIVE-HEALTH FAIL: breaching rows/seats listed below "
            "(promotion policy: thresholds calibrated, failing)"
        )
    elif overall == "WARN":
        lines.append(
            "LIVE-HEALTH WARN (advisory, exit 0): breaching rows/seats "
            "listed below; warn-first, not yet failing"
        )
    else:
        lines.append(
            "LIVE-HEALTH SKIP: sources unreachable or unconfigured - "
            "fleet state unknown, investigate (no passing signal)"
        )
    lines.append(
        "effective thresholds: "
        + ", ".join(f"{key}={value:g}" for key, value in effective.items())
    )
    for check in report["checks"]:
        lines.append(f"[{check['status']}] {check['name']}: {check['detail']}")
    lines.append(
        f"sources: {report['sources_ok']} ok, {report['sources_skipped']} skipped"
    )
    return "\n".join(lines) + "\n"


def overall_exit(report, strict):
    if strict and report["overall"] in ("WARN", "FAIL"):
        return 2
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _resolve_number(flag_value, env_name, default, label):
    raw = flag_value if flag_value is not None else os.environ.get(env_name)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return float(default)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(
            f"error: {label} unparseable: {raw!r} "
            f"(flag or ${env_name}); refusing to run on bad config"
        )
    if value <= 0:
        raise ValueError(f"error: {label} must be > 0, got {raw!r}; refusing to run")
    return value


def build_parser():
    parser = argparse.ArgumentParser(
        description="Warn-first live-fleet health gate (read-only). "
        "Exit 0 advisory; --strict promotes WARN to FAIL (exit 2)."
    )
    parser.add_argument(
        "--t-pickup-min",
        default=None,
        help="claim->transition breach age in minutes "
        f"(env LH_T_PICKUP_MIN, default {DEFAULT_T_PICKUP_MIN:g})",
    )
    parser.add_argument(
        "--t-stuck-min",
        default=None,
        help="overdue grace past deadline in minutes "
        f"(env LH_T_STUCK_MIN, default {DEFAULT_T_STUCK_MIN:g})",
    )
    parser.add_argument(
        "--t-undelivered-min",
        default=None,
        help="undelivered-nudge breach age in minutes "
        f"(env LH_T_UNDELIVERED_MIN, default {DEFAULT_T_UNDELIVERED_MIN:g})",
    )
    parser.add_argument(
        "--hb-mult",
        default=None,
        help="heartbeat freshness multiple of role interval "
        f"(env LH_HB_MULT, default {DEFAULT_HB_MULT:g})",
    )
    parser.add_argument(
        "--strict",
        "--fail-on-warn",
        action="store_true",
        help="promote WARN breaches to FAIL (exit 2)",
    )
    parser.add_argument(
        "--rig", default=None, help="scope to one rig (default: all rigs via -A)"
    )
    parser.add_argument(
        "--no-all-rigs",
        action="store_true",
        help="do not pass -A (current-rig scope only)",
    )
    parser.add_argument(
        "--limit",
        default=FETCH_LIMIT,
        type=int,
        help=f"per-verb row cap (default {FETCH_LIMIT})",
    )
    parser.add_argument(
        "--fixture-dir",
        default=None,
        help="replay saved JSON fixtures instead of the daemon "
        "(queue_list.json, queue_overdue.json, "
        "queue_undelivered.json, ps_nodes.json, "
        "transitions.json, fleet_heartbeat.json)",
    )
    parser.add_argument(
        "--fleet-file",
        default=str(DEFAULT_FLEET_FILE),
        help=f"fleet catalog for heartbeat_sec (default {DEFAULT_FLEET_FILE})",
    )
    parser.add_argument(
        "--now", default=None, help="override clock (ISO-8601, QA replay only)"
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        opts = GateOpts(
            t_pickup_min=_resolve_number(
                args.t_pickup_min, "LH_T_PICKUP_MIN", DEFAULT_T_PICKUP_MIN, "T_pickup"
            ),
            t_stuck_min=_resolve_number(
                args.t_stuck_min, "LH_T_STUCK_MIN", DEFAULT_T_STUCK_MIN, "T_stuck"
            ),
            t_undelivered_min=_resolve_number(
                args.t_undelivered_min,
                "LH_T_UNDELIVERED_MIN",
                DEFAULT_T_UNDELIVERED_MIN,
                "T_undelivered",
            ),
            hb_mult=_resolve_number(
                args.hb_mult, "LH_HB_MULT", DEFAULT_HB_MULT, "T_hb multiplier"
            ),
            strict=args.strict,
            rig_scope_all=not args.no_all_rigs and not args.rig,
            rig_name=args.rig,
            limit=args.limit,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    now = parse_iso_ts(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        print(f"error: --now unparseable: {args.now!r}", file=sys.stderr)
        return 2

    if args.fixture_dir:
        client = FixtureClient(args.fixture_dir)
        try:
            fleet_raw = client.fetch_fleet_heartbeat()
        except DataSourceError:
            fleet_raw = None
        if isinstance(fleet_raw, dict):
            fleet_map = {k: int(v) for k, v in fleet_raw.items()}
            unconfigured = sorted(k for k, v in fleet_map.items() if v <= 0)
        else:
            fleet_map, unconfigured = _fleet_or_skip(args.fleet_file)
    else:
        client = RigClient(
            rig_scope_all=opts.rig_scope_all, rig_name=opts.rig_name, limit=opts.limit
        )
        fleet_map, unconfigured = _fleet_or_skip(args.fleet_file)

    report = run_gate(client, fleet_map, unconfigured, opts, now)
    sys.stdout.write(render_text(report, effective_values(opts)))
    return overall_exit(report, opts.strict)


def _fleet_or_skip(fleet_file):
    try:
        return load_heartbeat_map(fleet_file)
    except DataSourceError as exc:
        return {}, exc


if __name__ == "__main__":
    sys.exit(main())
