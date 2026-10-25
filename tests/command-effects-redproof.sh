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

# Rendered seat output carries both effects (descriptors, #106) plus the
# native enforcement map (#91: config.json commandEffects is a dict keyed
# by bare basename — the M0 winner; the list form is unparsed by pps).
def render_role(role, rig, pod):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/render-seat.py"), "--role", role,
         "--rig", rig, "--pod", pod,
         "--dry-run", "--allow-missing-secrets"],
        cwd=str(ROOT), env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        return None, proc.stderr[-300:]
    return json.loads(proc.stdout), ""

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
    files, err = render_role("appsec-engineer", "defensive-sec-and-red-team", "blue")
    record("render dry-run exit 0", files is not None, err if files is None else "")
    if files is not None:
        cfg = files["extensions/pi-permission-system/config.json"]
        sidecar = files["extensions/pi-permission-system/command-effects.descriptors.json"]
        ids = [e.get("id") for e in sidecar]
        record("rendered note-effect + body-file-effect", ids == ["note-effect", "body-file-effect"], f"got {ids}")
        record("rendered commandEffects is native map", isinstance(cfg.get("commandEffects"), dict), f"got {type(cfg.get('commandEffects')).__name__}")
    files, err = render_role("engine-systems-eng", "game-dev-and-sim-rig", "engine")
    record("render engine dry-run exit 0", files is not None, err if files is None else "")
    if files is not None:
        cfg = files["extensions/pi-permission-system/config.json"]
        sidecar = files["extensions/pi-permission-system/command-effects.descriptors.json"]
        ids = [e.get("id") for e in sidecar]
        # #91 deliberate id-list update: engine seat carries cmake + gcc
        # + ctest descriptors after the frozen #106 pair, in this exact order.
        record("engine sidecar ids note/body/cmake/gcc/ctest", ids == ["note-effect", "body-file-effect", "cmake-effect", "gcc-effect", "ctest-effect"], f"got {ids}")
        record("engine map keys cmake/gcc/g++/ctest", set(cfg.get("commandEffects", {}).keys()) == {"cmake", "gcc", "g++", "ctest"}, f"got {sorted(cfg.get('commandEffects', {}).keys())}")
        bkeys = list(cfg["permission"]["bash"].keys())
        record("gcc overlay after terminal denies", bkeys.index("gcc *") > bkeys.index("*OPENRIG_URL=*") and bkeys.index("g++ *") > bkeys.index("*OPENRIG_URL=*"), f"tail={bkeys[-4:]}")

# #91 classifier corpus both directions (audit side mirrors enforcement).
record("allow go ./...", mod.classify_go_package_arg("./...")[0] == "allow-effect")
record("allow go ./pkg/...", mod.classify_go_package_arg("./pkg/...")[0] == "allow-effect")
for _g in ["../../etc/...", "../...", "/abs/...", "./a/../b/...", "pkg/...;evil"]:
    record(f"deny go {_g!r}", mod.classify_go_package_arg(_g)[0] == "deny")
record("go plain path not-a-pattern", mod.classify_go_package_arg("./pkg/foo")[0] == "not-a-pattern")

with tempfile.TemporaryDirectory() as ws:
    for _flag, _val in mod.pair_cmake_flag_values(["cmake", "-S", ".", "-B", "build"]):
        v, _ = mod.classify_scoped_path_value(_val, cwd=ws, path_write=["src/engine/*"])
        record(f"allow cmake {_flag} {_val}", v == "allow-effect", f"got {v}")
    for _argv in (["cmake", "-S", "../../etc", "-B", "build"], ["cmake", "-S", ".", "-B", "/tmp/evil"]):
        _vs = [mod.classify_scoped_path_value(_v, cwd=ws, path_write=["src/engine/*"])[0] for _, _v in mod.pair_cmake_flag_values(_argv)]
        record(f"deny cmake {_argv[2:]}", "deny" in _vs, f"got {_vs}")

with tempfile.TemporaryDirectory() as ws:
    (Path(ws) / "src").mkdir()
    (Path(ws) / "src" / "foo.c").write_text("int main(void){return 0;}\n")
    v, _ = mod.classify_gcc_command(["gcc", "-c", "src/foo.c"], cwd=ws, path_write=["src/*"])
    record("allow gcc -c src/foo.c", v == "allow-effect", f"got {v}")
    v, _ = mod.classify_gcc_command(["gcc", "-Wall", "-c", "src/foo.c", "-o", "src/foo.o"], cwd=ws, path_write=["src/*"])
    record("allow gcc -Wall -c with in-scope -o", v == "allow-effect", f"got {v}")
    for _argv in (["gcc", "-c", "../../evil.c"], ["gcc", "-c", "src/foo.c", "-o", "/tmp/evil.o"], ["sh", "-c", "evil"], ["gcc", "-c"]):
        v, _ = mod.classify_gcc_command(_argv, cwd=ws, path_write=["src/*"])
        record(f"deny gcc {_argv[1:]}", v == "deny", f"got {v}")

print(f"redproof: {len(failures)} failures")
sys.exit(1 if failures else 0)
PY
