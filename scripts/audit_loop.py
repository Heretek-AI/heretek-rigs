#!/usr/bin/env python3
"""audit_loop.py — Automated Adversarial Fleet Audit & Remediation Runner for heretek-rigs.

Executes the OpenCode (Muse Spark 1.3 Contributor via OpenCode Go) implementation,
adversarial triad audit (Alpha / Beta / Gamma), and fail-closed remediation loop
until 3 consecutive `STATUS: NO_FINDINGS` passes (with zero P0/P1/P2/P3 defects AND
`./scripts/verify-rigs.sh` exiting 0) are achieved.

Features:
  - Enforces pre-audit and post-remediation deterministic gate (`./scripts/verify-rigs.sh`).
  - Parses both `AUDIT_REPORT_FINDINGS.md` and agent stdout for the canonical
    `STATUS: NO_FINDINGS` vs `STATUS: FINDINGS_DETECTED` sentinel.
  - Rejects false-positive `STATUS: NO_FINDINGS` claims if `verify-rigs.sh` fails, if
    the report contains any open `HR-` finding header (any ATX depth, with or
    without trailing colon), if any table cell carries a BROKEN/PARTIAL token
    (after stripping `*_~` and emoji), if any Defect-Matrix body cell carries
    a P0–P3 grade, or if any Sabotage-table body row has a last cell other
    than `yes`.
  - Resets consecutive pass counter to 0 whenever any finding or gate failure occurs.
  - Supports `--self-test` / `--dry-run` for CI verification without invoking live LLM calls.

Usage:
  python3 scripts/audit_loop.py [--required-passes 3] [--max-iterations 15] [--model opencode-go/muse-spark-1.3-contributor] [--self-test]
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple

DEFAULT_MODEL = "opencode-go/muse-spark-1.3-contributor"
AUDIT_PROMPT_FILE = "PROMPT_ADVERSARIAL_FLEET_AUDIT.md"
# Live operator prompt (M7 overhaul-c): single live brief drives the
# implementation phase and the remediation phase. The pre-#122 spoonfeeder
# upload and the remediation protocol are archived under archive/ (reference
# only) and must never be referenced as live inputs — run_self_test enforces
# this fail-closed.
REMEDIATION_PROMPT_FILE = "docs/IMPLEMENTATION_PROMPT.md"
IMPLEMENTATION_PROMPT_FILE = "docs/IMPLEMENTATION_PROMPT.md"
REPORT_FILE = "AUDIT_REPORT_FINDINGS.md"
STATUS_NO_FINDINGS = "STATUS: NO_FINDINGS"
STATUS_FINDINGS_DETECTED = "STATUS: FINDINGS_DETECTED"

# M6 (#79): finding-header shapes. Any ATX heading (levels 1-6) opening an
# HR-<id> finding section counts, with or without a trailing colon — a
# `## HR-…:` or `#### HR-…` header hiding behind a NO_FINDINGS sentinel is a
# lie, not a shallower report.
HR_HEADER_RE = re.compile(r"^#{1,6}\s*HR-[\w.-]+", flags=re.MULTILINE)
# #105 review: a bold finding line (`**HR-4.1: ...**`) is a finding header
# too, even when it isn't an ATX heading.
HR_BOLD_RE = re.compile(r"^\s*(?:[-*]\s+)?\*\*\s*HR-[\w.-]+", flags=re.MULTILINE)

# M6 (#79): cell-decoration stripping for the ledger scan. Bold/italic/
# strikethrough/code ticks (`*_~``) and emoji (❌, ✅, …) must not launder a
# BROKEN/PARTIAL token: `**BROKEN**`, `BROKEN ❌`, `BROKEN (see notes)` all
# count as findings.
_CELL_DECORATION_RE = re.compile(r"[*_~`]+")
_EMOJI_RE = re.compile(
    "[\U0001f300-\U0001faff\u2600-\u2bff\ufe00-\ufe0f\u200d\U0001f1e6-\U0001f1ff]"
)
_LEDGER_TOKEN_RE = re.compile(r"\b(BROKEN|PARTIAL)\b", flags=re.IGNORECASE)
# #105 review: ledger verdicts. Only the Status/Verdict cell is read (the
# Evidence column routinely says "fail-closed", "verify FAILED as expected").
# Claim Ledger: anything other than VERIFIED / UNVERIFIABLE is a finding.
# Regression Ledger: STILL OPEN / REGRESSED are findings.
_CLAIM_OK_VERDICTS = ("VERIFIED", "UNVERIFIABLE")
_REGRESSION_OPEN_RE = re.compile(r"^(STILL\s+OPEN|REGRESSED)\b", re.IGNORECASE)

# M6 (#79): any P0–P3 token in a Defect-Matrix table body cell counts as a
# finding (case-insensitive: `p1` launders nothing).
_PGRADE_RE = re.compile(r"\bP[0-3]\b", flags=re.IGNORECASE)

_TABLE_SEPARATOR_RE = re.compile(r"^:?-+:?$")


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_verify_gate(repo_root: Path) -> Tuple[bool, str]:
    """Run ./scripts/verify-rigs.sh and return (passed, output)."""
    verify_script = repo_root / "scripts" / "verify-rigs.sh"
    if not verify_script.exists():
        return False, f"Missing verification gate: {verify_script}"
    proc = subprocess.run(
        ["bash", str(verify_script), "--check-only"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    combined = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode == 0, combined.strip()


def _table_cells(line):
    """Split a markdown table line into stripped cells."""
    cells = line.strip().split("|")
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return [c.strip() for c in cells]


def _is_separator_cells(cells):
    return bool(cells) and all(_TABLE_SEPARATOR_RE.match(c or "") for c in cells)


def _strip_cell_decorations(cell):
    """Remove `*_~`` runs and emoji so decorated tokens stay detectable."""
    return _EMOJI_RE.sub("", _CELL_DECORATION_RE.sub("", cell))


def _scan_report_tables(combined):
    """Fail-closed table scan. Returns (ledger, matrix, sabotage) hit counts.

    - ledger: any pipe-delimited line with a BROKEN/PARTIAL token in any
      cell after decoration-stripping (Claim Ledger, fenced or bare,
      decorated or plain).
    - matrix: a P0–P3 token in a body cell of a Defect-Matrix table — a
      table under a "defect matrix" heading or whose header row names a
      "Priority" column. Header and separator rows are never evidence.
    - sabotage: a body row of a Sabotage table (under a "sabotage"
      heading or with a "Caught?" column) whose last cell is not `yes`
      (`no`, `NOT RUN`, `UNVERIFIABLE`, … all count as open).
    """
    ledger = matrix = sabotage = 0
    current_heading = ""
    run_header = None
    in_run = False
    for line in combined.splitlines():
        stripped = line.strip()
        heading = re.match(r"^#{1,6}\s+(.*)$", stripped)
        if heading:
            current_heading = heading.group(1)
            in_run = False
            run_header = None
            continue
        if "|" not in stripped:
            in_run = False
            run_header = None
            continue
        cells = _table_cells(stripped)
        if not cells:
            in_run = False
            run_header = None
            continue
        for cell in cells:
            if _LEDGER_TOKEN_RE.search(_strip_cell_decorations(cell)):
                ledger += 1
                break
        if _is_separator_cells(cells):
            continue
        if not in_run:
            run_header = cells
            in_run = True
            continue
        header_ci = [c.lower() for c in run_header]
        is_matrix = ("defect matrix" in current_heading.lower()) or (
            "priority" in header_ci
        )
        is_sabotage = ("sabotage" in current_heading.lower()) or (
            "caught?" in header_ci
        )
        heading_ci = current_heading.lower()
        verdict_col = next(
            (i for i, h in enumerate(header_ci) if h in ("status", "verdict")), None
        )
        if not is_sabotage and verdict_col is not None and verdict_col < len(cells):
            verdict = _strip_cell_decorations(cells[verdict_col]).strip().upper()
            if "regression ledger" in heading_ci:
                if _REGRESSION_OPEN_RE.search(verdict):
                    ledger += 1
            elif "claim ledger" in heading_ci or (
                header_ci and header_ci[0] == "claim"
            ):
                if not _LEDGER_TOKEN_RE.search(verdict) and not verdict.startswith(
                    _CLAIM_OK_VERDICTS
                ):
                    ledger += 1
        if is_matrix:
            for cell in cells:
                if _PGRADE_RE.search(_strip_cell_decorations(cell)):
                    matrix += 1
                    break
        if is_sabotage and cells:
            last = _strip_cell_decorations(cells[-1]).strip().lower()
            if last != "yes":
                sabotage += 1
    return ledger, matrix, sabotage


def evaluate_audit_status(
    report_text: str, agent_output: str, gate_passed: bool
) -> Tuple[str, str]:
    """Deterministically classify audit outcome (fail-closed)."""
    if not gate_passed:
        return STATUS_FINDINGS_DETECTED, "verify-rigs.sh gate failed"

    combined = f"{report_text}\n{agent_output}"
    if STATUS_FINDINGS_DETECTED in combined:
        return (
            STATUS_FINDINGS_DETECTED,
            "Explicit STATUS: FINDINGS_DETECTED sentinel present",
        )

    # HR-8.3 + M6 (#79): scan the combined report+agent output (not
    # report_text alone) for open finding headers, and match ledger
    # BROKEN/PARTIAL rows with or without numeric claim IDs on the
    # UNSTRIPPED text so fenced-only rows still trip. M6 widens the header
    # to any ATX depth with or without a trailing colon.
    open_finding_headers = HR_HEADER_RE.findall(combined) + HR_BOLD_RE.findall(combined)
    if open_finding_headers:
        return (
            STATUS_FINDINGS_DETECTED,
            f"Report contains {len(open_finding_headers)} finding section(s)",
        )

    # M6 (#79): decorated ledger tokens, Defect-Matrix P-grades, and open
    # Sabotage rows are findings even under a NO_FINDINGS sentinel.
    ledger_hits, matrix_hits, sabotage_open = _scan_report_tables(combined)
    if ledger_hits:
        return (
            STATUS_FINDINGS_DETECTED,
            f"Claim Ledger contains {ledger_hits} BROKEN/PARTIAL claim(s)",
        )
    if matrix_hits:
        return (
            STATUS_FINDINGS_DETECTED,
            f"Defect Matrix contains {matrix_hits} P0-P3 graded row(s)",
        )
    if sabotage_open:
        return (
            STATUS_FINDINGS_DETECTED,
            f"Sabotage table contains {sabotage_open} uncaught row(s)",
        )

    if STATUS_NO_FINDINGS in combined:
        return (
            STATUS_NO_FINDINGS,
            "Verified STATUS: NO_FINDINGS with 0 open findings and green verify-rigs.sh",
        )

    return (
        STATUS_FINDINGS_DETECTED,
        "Missing deterministic STATUS: NO_FINDINGS sentinel (fail-closed)",
    )


def invoke_opencode_agent(
    repo_root: Path,
    prompt_file: Path,
    instruction: str,
    model: str,
    log_path: Path,
    timeout_sec: int = 1800,
) -> Tuple[int, str]:
    """Invoke OpenCode CLI (`opencode run`) in non-interactive mode with Muse 1.3 Contributor."""
    opencode_bin = shutil.which("opencode")
    if not opencode_bin:
        raise RuntimeError(
            "OpenCode CLI ('opencode') not found on PATH. Install @opencode/cli or run with --self-test."
        )
    full_prompt = (
        f"Read {prompt_file.name} in full and execute all instructions strictly. "
        f"{instruction}"
    )
    cmd = [opencode_bin, "run", "--model", model, full_prompt]
    env = os.environ.copy()
    if "OPENCODE_GO_API_KEY" in env and "OPENCODE_API_KEY" not in env:
        env["OPENCODE_API_KEY"] = env["OPENCODE_GO_API_KEY"]

    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output)
    return proc.returncode, output


def run_self_test(repo_root: Path) -> int:
    """Verify prompt presence, evaluator fail-closed invariants, and verify-rigs.sh gate."""
    print(f"[{utc_now()}] Running audit_loop.py --self-test in {repo_root}...")
    for req in [
        IMPLEMENTATION_PROMPT_FILE,
        AUDIT_PROMPT_FILE,
        REMEDIATION_PROMPT_FILE,
        "fleet/fleet.yaml",
        "fleet/mcp-servers.yaml",
    ]:
        p = repo_root / req
        if "archive" in p.resolve().parts:
            print(
                f"  [FAIL] Archived path referenced as live input: {req}",
                file=sys.stderr,
            )
            return 1
        if not p.exists() or p.stat().st_size < 500:
            print(f"  [FAIL] Missing or stub file: {p}", file=sys.stderr)
            return 1
        print(f"  [PASS] Found {req} ({p.stat().st_size} bytes)")

    verify_script = repo_root / "scripts" / "verify-rigs.sh"
    if verify_script.exists():
        gate_ok, gate_out = run_verify_gate(repo_root)
        if not gate_ok:
            print(f"  [FAIL] verify-rigs.sh failed:\n{gate_out}", file=sys.stderr)
            return 1
        print(
            "  [PASS] ./scripts/verify-rigs.sh passed all static, schema, digest, and security checks"
        )
    else:
        print(
            "  [INFO] ./scripts/verify-rigs.sh not yet generated (pre-implementation state); verifying evaluator invariants"
        )

    clean_report = (
        "# AUDIT_REPORT_FINDINGS: heretek-rigs\n"
        "## Claim Ledger\n| Claim 1.1 | VERIFIED | scripts/verify-rigs.sh |\n"
        f"\n{STATUS_NO_FINDINGS}\n"
    )
    status, reason = evaluate_audit_status(clean_report, "", True)
    assert status == STATUS_NO_FINDINGS, f"Expected NO_FINDINGS, got {status}: {reason}"

    dirty_report_lie = (
        "# AUDIT_REPORT_FINDINGS: heretek-rigs\n"
        "### HR-1.1-broken-rig: Broken rig\n"
        f"\n{STATUS_NO_FINDINGS}\n"
    )
    status_lie, _ = evaluate_audit_status(dirty_report_lie, "", True)
    assert status_lie == STATUS_FINDINGS_DETECTED, (
        "Parser failed to catch false NO_FINDINGS with ### HR- header!"
    )

    broken_claim_lie = (
        "# AUDIT_REPORT_FINDINGS: heretek-rigs\n"
        "| Claim 2.1 [A] | BROKEN | finding |\n"
        f"\n{STATUS_NO_FINDINGS}\n"
    )
    status_broken, _ = evaluate_audit_status(broken_claim_lie, "", True)
    assert status_broken == STATUS_FINDINGS_DETECTED, (
        "Parser failed to catch BROKEN claim in ledger!"
    )

    # HR-8.3: bare "| 2.1 | broken |" rows and fenced rows must also trip the evaluator.
    for extra in (
        "# R\n| 2.1 | BROKEN | x |\nSTATUS: NO_FINDINGS\n",
        "# R\n| 2.1 | broken | x |\nSTATUS: NO_FINDINGS\n",
        "# R\n```\n| 2.1 | BROKEN | x |\n```\nSTATUS: NO_FINDINGS\n",
    ):
        s, _ = evaluate_audit_status(extra, "", True)
        assert s == STATUS_FINDINGS_DETECTED, f"Parser missed ledger row: {extra!r}"

    # M6 (#79): the 8 report-format variants. Each hides a finding behind a
    # NO_FINDINGS sentinel using a shape the old evaluator missed (header
    # depth/colon, decorated ledger cell, Defect-Matrix P-grade, open
    # Sabotage row). Each must return FINDINGS_DETECTED.
    m6_vectors = (
        # V1: depth-2 finding header with colon (old: exactly ### only).
        "## HR-4.1: Depth-two header with colon\nSTATUS: NO_FINDINGS\n",
        # V2: depth-3 finding header WITHOUT trailing colon.
        "### HR-4.2 header without trailing colon\nSTATUS: NO_FINDINGS\n",
        # V3: depth-4 finding header.
        "#### HR-4.3 deep header\nSTATUS: NO_FINDINGS\n",
        # V4: bold-decorated BROKEN cell.
        "| Claim 9.1 | **BROKEN** | x |\nSTATUS: NO_FINDINGS\n",
        # V5: emoji-decorated BROKEN cell.
        "| Claim 9.2 | BROKEN \u274c | x |\nSTATUS: NO_FINDINGS\n",
        # V6: parenthetical BROKEN cell.
        "| Claim 9.3 | BROKEN (see notes) | x |\nSTATUS: NO_FINDINGS\n",
        # V7: Defect-Matrix row carrying a P-grade.
        "## Prioritized Defect Matrix\n"
        "| ID | Priority | Claim | Location | Summary |\n"
        "|----|----------|-------|----------|---------|\n"
        "| DM-1 | P1 | widget frobnicator | foo.py:12 | broke |\n"
        "STATUS: NO_FINDINGS\n",
        # V8: Sabotage row whose last cell is not yes.
        "## Sabotage Results\n"
        "| Invariant | One-line sabotage (file:line, before -> after) "
        "| Suite result | Caught? |\n"
        "|-----------|----------|--------------|---------|\n"
        "| 5.1 yolo | builtin:locked -> builtin:yolo | NOT RUN | no |\n"
        "STATUS: NO_FINDINGS\n",
        # V9-V11 (#105 review): FAIL / PARTIALLY HOLDS ledger verdicts and a
        # bold (non-heading) finding line.
        "## Claim Ledger\n| Claim | Verdict | Evidence |\n|---|---|---|\n"
        "| 3.1 | FAIL | x |\nSTATUS: NO_FINDINGS\n",
        "## Claim Ledger\n| Claim | Verdict | Evidence |\n|---|---|---|\n"
        "| 3.2 | PARTIALLY HOLDS | x |\nSTATUS: NO_FINDINGS\n",
        "## Claim Ledger\n| Claim | Status | Evidence |\n|---|---|---|\n"
        "| 3.3 | FAIL | x |\nSTATUS: NO_FINDINGS\n",
        "## Regression Ledger\n| Finding | Status | Evidence |\n|---|---|---|\n"
        "| #68 | STILL OPEN | x |\nSTATUS: NO_FINDINGS\n",
        "**HR-7.1: bold finding line**\nSTATUS: NO_FINDINGS\n",
    )
    for i, vector in enumerate(m6_vectors, start=1):
        s, reason = evaluate_audit_status(vector, "", True)
        assert s == STATUS_FINDINGS_DETECTED, (
            f"M6 vector V{i} missed (returned {s}: {reason}): {vector!r}"
        )

    # Control: a caught sabotage row saying the gate FAILED is not a finding.
    caught = (
        "## Sabotage Results\n| Invariant | Sabotage | Suite result | Caught? |\n"
        "|---|---|---|---|\n| 5.1 | x -> y | verify FAILED | yes |\n"
        "STATUS: NO_FINDINGS\n"
    )
    s, reason = evaluate_audit_status(caught, "", True)
    assert s == STATUS_NO_FINDINGS, f"caught-sabotage control misread: {reason}"
    # Controls: "fail" in a VERIFIED row's Evidence or Claim cell is not a
    # finding, and FIXED regression rows are clean.
    for clean_row in (
        "| 2.1 | VERIFIED | fail-closed render holds |",
        "| 4.2 Render fails closed | VERIFIED | ok |",
        "| 5.1 | UNVERIFIABLE | needs live fleet |",
    ):
        s, reason = evaluate_audit_status(
            "## Claim Ledger\n| Claim | Status | Evidence |\n|---|---|---|\n"
            + clean_row
            + "\nSTATUS: NO_FINDINGS\n",
            "",
            True,
        )
        assert s == STATUS_NO_FINDINGS, (
            f"clean ledger row misread: {clean_row} ({reason})"
        )
    s, reason = evaluate_audit_status(
        "## Regression Ledger\n| Finding | Status | Evidence |\n|---|---|---|\n"
        "| #67 | FIXED | render fails closed |\nSTATUS: NO_FINDINGS\n",
        "",
        True,
    )
    assert s == STATUS_NO_FINDINGS, f"FIXED regression row misread: {reason}"

    status_gate_fail, _ = evaluate_audit_status(clean_report, "", False)
    assert status_gate_fail == STATUS_FINDINGS_DETECTED, (
        "Parser failed to reject NO_FINDINGS when verify gate failed!"
    )

    print(
        "  [PASS] Fail-closed sentinel evaluator verified against 20 adversarial test vectors"
    )
    print("SELF-TEST PASSED: audit_loop.py is ready for autonomous OpenCode execution.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run OpenCode adversarial audit/remediation loop until 3x STATUS: NO_FINDINGS."
    )
    parser.add_argument(
        "--repo-root", default=".", help="Path to heretek-rigs repository root"
    )
    parser.add_argument(
        "--required-passes",
        type=int,
        default=3,
        help="Consecutive STATUS: NO_FINDINGS passes required (default: 3)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=15,
        help="Maximum audit/remediation iterations before aborting (default: 15)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenCode model ID (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--run-implementation-first",
        action="store_true",
        help="Run docs/IMPLEMENTATION_PROMPT.md before starting audit loop",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic self-test without live OpenCode CLI invocation",
    )
    parser.add_argument("--dry-run", action="store_true", help="Alias for --self-test")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if args.self_test or args.dry_run:
        return run_self_test(repo_root)

    logs_dir = repo_root / ".scratch" / "audit-loop-logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if args.run_implementation_first:
        print(
            f"[{utc_now()}] Phase 0: Executing {IMPLEMENTATION_PROMPT_FILE} with {args.model}..."
        )
        invoke_opencode_agent(
            repo_root,
            repo_root / IMPLEMENTATION_PROMPT_FILE,
            "Execute all milestones in order and verify `./scripts/verify-rigs.sh` exits 0.",
            args.model,
            logs_dir / "00-implementation.log",
        )

    consecutive_passes = 0
    ledger = []

    for iteration in range(1, args.max_iterations + 1):
        print(
            f"\n[{utc_now()}] === Audit Iteration {iteration}/{args.max_iterations} (Consecutive Passes: {consecutive_passes}/{args.required_passes}) ==="
        )

        _, audit_out = invoke_opencode_agent(
            repo_root,
            repo_root / AUDIT_PROMPT_FILE,
            f"Execute the three-subagent (Alpha, Beta, Gamma) adversarial audit, write {REPORT_FILE}, and end with exactly `{STATUS_NO_FINDINGS}` or `{STATUS_FINDINGS_DETECTED}`.",
            args.model,
            logs_dir / f"iter-{iteration:02d}-audit.log",
        )

        gate_ok, gate_out = run_verify_gate(repo_root)
        report_path = repo_root / REPORT_FILE
        report_text = report_path.read_text() if report_path.exists() else ""

        status, reason = evaluate_audit_status(report_text, audit_out, gate_ok)
        ledger.append(
            {
                "iteration": iteration,
                "timestamp": utc_now(),
                "status": status,
                "reason": reason,
                "verify_gate": gate_ok,
            }
        )
        (logs_dir / "loop-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")

        if status == STATUS_NO_FINDINGS:
            consecutive_passes += 1
            print(
                f"[{utc_now()}] PASS {consecutive_passes}/{args.required_passes}: {reason}"
            )
            if consecutive_passes >= args.required_passes:
                print(
                    f"\n[{utc_now()}] SUCCESS: Achieved {args.required_passes} consecutive {STATUS_NO_FINDINGS} passes!"
                )
                return 0
        else:
            consecutive_passes = 0
            print(
                f"[{utc_now()}] {STATUS_FINDINGS_DETECTED} ({reason}) — triggering remediation pass..."
            )
            invoke_opencode_agent(
                repo_root,
                repo_root / REMEDIATION_PROMPT_FILE,
                f"Remediate every finding in {REPORT_FILE}, re-run `python3 ./scripts/generate-rigs.py` and `./scripts/verify-rigs.sh` until green, and append a dated entry to archive/2026-10-28-overhaul/REMEDIATION_LOG.md (archived log, append-only).",
                args.model,
                logs_dir / f"iter-{iteration:02d}-remediation.log",
            )

    print(
        f"\n[{utc_now()}] FAILED: Reached max iterations ({args.max_iterations}) without achieving {args.required_passes} consecutive passes.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
