#!/usr/bin/env bash
# tests/command-effects-redproof.sh — #106 red-proofs both directions.
# Runnable, binary pass/fail: exit 0 all green, exit 1 any failure.
# Allow: --note "a/b | c", in-scope --body-file. Deny (non-zero + deny
# record): prod.env outside scope, /etc/passwd, ../../etc/passwd, symlink
# escape, oversize, ;/$/backtick/$()/newline/OPENRIG_* note values.
set -u
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

python3 - <<'PY'
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(".").resolve()
failures = []

def record(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)

spec = importlib.util.spec_from_file_location("render_seat_rp", str(ROOT / "scripts/render-seat.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Allow direction: note value with path + pipe.
record("allow note 'a/b | c'", mod.is_note_value_allowed("a/b | c") is True)
# Deny direction: note values.
for sample in ["a;b", "x$y", "a`b", "x$(id)", "a\nb", "OPENRIG_SESSION_NAME=e", "OPENRIG_URL=e"]:
    record(f"deny note {sample!r}", mod.is_note_value_allowed(sample) is False)

with tempfile.TemporaryDirectory() as ws:
    inscope = Path(ws) / "body.md"
    inscope.write_text("staged queue body")
    v, _ = mod.check_body_file_path(str(inscope), cwd=ws, path_write=["docs/*"])
    record("allow in-scope body-file", v == "allow-effect", f"got {v}")
    outsider = Path(ws).parent / "prod.env"
    outsider.write_text("SECRET=x")
    try:
        for raw, label in [
            (str(outsider), "deny prod.env outside scope"),
            ("/etc/passwd", "deny /etc/passwd"),
            (str(Path(ws) / "../../etc/passwd"), "deny dotdot escape"),
            (str(Path(ws) / "missing.md"), "deny missing file"),
            ("/tmp/rp-absolute.md", "deny absolute /tmp"),
        ]:
            v, reason = mod.check_body_file_path(raw, cwd=ws, path_write=["docs/*"])
            record(label, v == "deny" and bool(reason), f"got {v}")
        link = Path(ws) / "link.md"
        link.symlink_to("/etc/hostname")
        v, reason = mod.check_body_file_path(str(link), cwd=ws, path_write=["docs/*"])
        record("deny symlink escape", v == "deny" and bool(reason), f"got {v}")
        link.unlink()
        big = Path(ws) / "big.md"
        big.write_bytes(b"x" * (262144 + 1))
        v, reason = mod.check_body_file_path(str(big), cwd=ws, path_write=["docs/*"])
        record("deny oversize body-file", v == "deny" and bool(reason), f"got {v}")
    finally:
        outsider.unlink(missing_ok=True)

# Rendered seat output carries both effects.
with tempfile.TemporaryDirectory() as tmp:
    secrets = Path(tmp) / "secrets"
    secrets.mkdir(mode=0o700)
    (secrets / "opencode-go.key").write_text("dummy")
    os.chmod(secrets / "opencode-go.key", 0o600)
    tools = Path(tmp) / "tools"
    pps = tools / "pi-packages/node_modules/@gotgenes/pi-permission-system"
    pps.mkdir(parents=True)
    (pps / "package.json").write_text(json.dumps({"version": "41.0.0"}))
    env = {**os.environ, "HERETEK_SECRETS": str(secrets),
           "HERETEK_TOOLS": str(tools), "OPENRIG_HOME": "/tmp/hr-openrig"}
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/render-seat.py"), "--role", "appsec-engineer",
         "--rig", "defensive-sec-and-red-team", "--pod", "blue",
         "--dry-run", "--allow-missing-secrets"],
        cwd=str(ROOT), env=env, capture_output=True, text=True)
    ok_render = proc.returncode == 0
    record("render dry-run exit 0", ok_render, proc.stderr[-300:] if not ok_render else "")
    if ok_render:
        cfg = json.loads(proc.stdout)["extensions/pi-permission-system/config.json"]
        ids = [e.get("id") for e in cfg.get("commandEffects", [])]
        record("rendered note-effect + body-file-effect", ids == ["note-effect", "body-file-effect"], f"got {ids}")

print(f"redproof: {len(failures)} failures")
sys.exit(1 if failures else 0)
PY
