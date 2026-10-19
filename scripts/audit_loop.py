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
    `AUDIT_REPORT_FINDINGS.md` contains any open `### HR-` finding headers, or if any
    Claim Ledger row is marked `BROKEN` or `PARTIAL`.
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
REMEDIATION_PROMPT_FILE = "PROMPT_FLEET_AUDIT_REMEDIATION.md"
IMPLEMENTATION_PROMPT_FILE = "PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md"
REPORT_FILE = "AUDIT_REPORT_FINDINGS.md"
STATUS_NO_FINDINGS = "STATUS: NO_FINDINGS"
STATUS_FINDINGS_DETECTED = "STATUS: FINDINGS_DETECTED"


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


def evaluate_audit_status(report_text: str, agent_output: str, gate_passed: bool) -> Tuple[str, str]:
    """Deterministically classify audit outcome (fail-closed)."""
    if not gate_passed:
        return STATUS_FINDINGS_DETECTED, "verify-rigs.sh gate failed"

    combined = f"{report_text}\n{agent_output}"
    if STATUS_FINDINGS_DETECTED in combined:
        return STATUS_FINDINGS_DETECTED, "Explicit STATUS: FINDINGS_DETECTED sentinel present"

    open_finding_headers = re.findall(r"^###\s+HR-[A-Za-z0-9._-]+:", report_text, flags=re.MULTILINE)
    if open_finding_headers:
        return STATUS_FINDINGS_DETECTED, f"Report contains {len(open_finding_headers)} finding section(s)"

    broken_claims = re.findall(r"\|\s*Claim\s+\d+\.\d+[^|]*\|\s*(BROKEN|PARTIAL)\s*\|", report_text)
    if broken_claims:
        return STATUS_FINDINGS_DETECTED, f"Claim Ledger contains {len(broken_claims)} BROKEN/PARTIAL claim(s)"

    if STATUS_NO_FINDINGS in combined:
        return STATUS_NO_FINDINGS, "Verified STATUS: NO_FINDINGS with 0 open findings and green verify-rigs.sh"

    return STATUS_FINDINGS_DETECTED, "Missing deterministic STATUS: NO_FINDINGS sentinel (fail-closed)"


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
    for req in [IMPLEMENTATION_PROMPT_FILE, AUDIT_PROMPT_FILE, REMEDIATION_PROMPT_FILE, "fleet/fleet.yaml", "fleet/mcp-servers.yaml"]:
        p = repo_root / req
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
        print("  [PASS] ./scripts/verify-rigs.sh passed all static, schema, digest, and security checks")
    else:
        print("  [INFO] ./scripts/verify-rigs.sh not yet generated (pre-implementation state); verifying evaluator invariants")

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
    assert status_lie == STATUS_FINDINGS_DETECTED, "Parser failed to catch false NO_FINDINGS with ### HR- header!"

    broken_claim_lie = (
        "# AUDIT_REPORT_FINDINGS: heretek-rigs\n"
        "| Claim 2.1 [A] | BROKEN | finding |\n"
        f"\n{STATUS_NO_FINDINGS}\n"
    )
    status_broken, _ = evaluate_audit_status(broken_claim_lie, "", True)
    assert status_broken == STATUS_FINDINGS_DETECTED, "Parser failed to catch BROKEN claim in ledger!"

    status_gate_fail, _ = evaluate_audit_status(clean_report, "", False)
    assert status_gate_fail == STATUS_FINDINGS_DETECTED, "Parser failed to reject NO_FINDINGS when verify gate failed!"

    print("  [PASS] Fail-closed sentinel evaluator verified against 4 adversarial test vectors")
    print("SELF-TEST PASSED: audit_loop.py is ready for autonomous OpenCode execution.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OpenCode adversarial audit/remediation loop until 3x STATUS: NO_FINDINGS.")
    parser.add_argument("--repo-root", default=".", help="Path to heretek-rigs repository root")
    parser.add_argument("--required-passes", type=int, default=3, help="Consecutive STATUS: NO_FINDINGS passes required (default: 3)")
    parser.add_argument("--max-iterations", type=int, default=15, help="Maximum audit/remediation iterations before aborting (default: 15)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"OpenCode model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--run-implementation-first", action="store_true", help="Run PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md before starting audit loop")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic self-test without live OpenCode CLI invocation")
    parser.add_argument("--dry-run", action="store_true", help="Alias for --self-test")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if args.self_test or args.dry_run:
        return run_self_test(repo_root)

    logs_dir = repo_root / ".scratch" / "audit-loop-logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if args.run_implementation_first:
        print(f"[{utc_now()}] Phase 0: Executing {IMPLEMENTATION_PROMPT_FILE} with {args.model}...")
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
        print(f"\n[{utc_now()}] === Audit Iteration {iteration}/{args.max_iterations} (Consecutive Passes: {consecutive_passes}/{args.required_passes}) ===")

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
        ledger.append({
            "iteration": iteration,
            "timestamp": utc_now(),
            "status": status,
            "reason": reason,
            "verify_gate": gate_ok,
        })
        (logs_dir / "loop-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")

        if status == STATUS_NO_FINDINGS:
            consecutive_passes += 1
            print(f"[{utc_now()}] PASS {consecutive_passes}/{args.required_passes}: {reason}")
            if consecutive_passes >= args.required_passes:
                print(f"\n[{utc_now()}] SUCCESS: Achieved {args.required_passes} consecutive {STATUS_NO_FINDINGS} passes!")
                return 0
        else:
            consecutive_passes = 0
            print(f"[{utc_now()}] {STATUS_FINDINGS_DETECTED} ({reason}) — triggering remediation pass...")
            invoke_opencode_agent(
                repo_root,
                repo_root / REMEDIATION_PROMPT_FILE,
                f"Remediate every finding in {REPORT_FILE}, re-run `python3 ./scripts/generate-rigs.py` and `./scripts/verify-rigs.sh` until green, and update REMEDIATION_LOG.md.",
                args.model,
                logs_dir / f"iter-{iteration:02d}-remediation.log",
            )

    print(f"\n[{utc_now()}] FAILED: Reached max iterations ({args.max_iterations}) without achieving {args.required_passes} consecutive passes.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
