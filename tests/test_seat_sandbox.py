#!/usr/bin/env python3
"""Escape corpus for scripts/seat-sandbox.sh (M4 #68; #105 review).

Drives the real wrapper exactly as pi does (`seat-sandbox.sh -c "<cmd>"`)
against a throwaway workspace. Needs `bwrap` with unprivileged user
namespaces; skips loudly otherwise. No real credentials: every "secret" is a
dummy file under the test's temp dir.
Run: python3 -m unittest tests/test_seat_sandbox.py -v
"""

import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WRAPPER = REPO_ROOT / "scripts/seat-sandbox.sh"


def _bwrap_works():
    if shutil.which("bwrap") is None:
        return False
    proc = subprocess.run(
        ["bwrap", "--unshare-net", "--ro-bind", "/", "/", "--dev", "/dev", "true"],
        capture_output=True,
    )
    return proc.returncode == 0


@unittest.skipUnless(_bwrap_works(), "bwrap with user namespaces unavailable")
class SeatSandboxEscapes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.ws = root / "ws"
        (self.ws / "src").mkdir(parents=True)
        (self.ws / ".git/hooks").mkdir(parents=True)
        (self.ws / "package.json").write_text("{}\n")
        (self.ws / "prod.env").write_text("TOKEN=dummy\n")
        self.outside = root / "outside"
        self.outside.mkdir()
        self.store = root / "secrets"
        self.store.mkdir(mode=0o700)
        (self.store / "opencode-go.key").write_text("dummy-key")
        self.home = root / "home"
        (self.home / ".ssh").mkdir(parents=True)
        (self.home / ".ssh/id_ed25519").write_text("dummy-private-key")
        (self.home / ".netrc").write_text("machine x password dummy")
        self.bin = root / "bin"
        self.bin.mkdir()
        self.env = {
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "HOME": str(self.home),
            "HERETEK_SANDBOX_WRITE": "src/:package.json:*.lock",
            "HERETEK_SECRET_STORE": str(self.store),
        }

    def tearDown(self):
        self.tmp.cleanup()

    def run_jailed(self, command, **env):
        return subprocess.run(
            ["bash", str(WRAPPER), "-c", command],
            cwd=str(self.ws),
            env={**self.env, **env},
            capture_output=True,
            text=True,
            timeout=60,
        )

    # --- in-scope work still succeeds ---------------------------------
    def test_seat_cannot_rewrite_its_own_permission_config(self):
        """#96: pi-permission-system hot-reloads config.json, so the jail
        must keep a seat's own agent dir read-only."""
        agent = Path(self.tmp.name) / "openrig/state/pi/blue-x@r/agent"
        cfg = agent / "extensions/pi-permission-system/config.json"
        cfg.parent.mkdir(parents=True)
        cfg.write_text('{"bash": {"*": "deny"}}\n')
        proc = self.run_jailed(
            f"echo '{{}}' > {cfg}; mv {cfg} {cfg}.bak; touch {cfg}",
            PI_CODING_AGENT_DIR=str(agent),
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(cfg.read_text(), '{"bash": {"*": "deny"}}\n')
        self.assertFalse(Path(f"{cfg}.bak").exists())

    def test_write_inside_dir_root(self):
        proc = self.run_jailed("echo ok > src/a.txt && cat src/a.txt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((self.ws / "src/a.txt").read_text(), "ok\n")

    def test_existing_granted_file_writable_in_place(self):
        proc = self.run_jailed("echo '{\"x\":1}' > package.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('"x"', (self.ws / "package.json").read_text())

    def test_tmp_and_tmpdir_writable(self):
        proc = self.run_jailed('echo t > "$TMPDIR/x" && echo t > /tmp/y')
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_toolchain_caches_point_into_scratch(self):
        """#91/#12: go (and anything on XDG_CACHE_HOME) needs a writable
        cache; it lives under the per-run scratch while $HOME stays
        read-only."""
        proc = self.run_jailed(
            'case "$GOCACHE" in "$TMPDIR"/*) ;; *) exit 3 ;; esac; '
            'case "$XDG_CACHE_HOME" in "$TMPDIR"/*) ;; *) exit 4 ;; esac; '
            'test -d "$GOCACHE" && echo t > "$XDG_CACHE_HOME/x"'
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.run_jailed('mkdir -p "$HOME/.cache/go-build"')
        self.assertFalse((self.home / ".cache").exists())

    def test_cache_does_not_survive_the_run(self):
        d = self._jail_scratch()
        proc = self.run_jailed(
            'echo t > "$GOCACHE/x"', HERETEK_JAIL_SCRATCH=str(d)
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(list(d.iterdir()), [], "seatjail cache leaked")

    @unittest.skipUnless(shutil.which("go"), "go toolchain not installed")
    def test_go_test_runs_in_seat_scope(self):
        """#91 live finding: `go test ./...` failed on a read-only GOCACHE."""
        (self.ws / "src/go.mod").write_text("module example.com/w\n\ngo 1.21\n")
        (self.ws / "src/w_test.go").write_text(
            'package w\nimport "testing"\nfunc TestW(t *testing.T) {}\n'
        )
        # The test HOME sits under /tmp, which the jail replaces with a
        # writable tmpfs; a real seat's HOME is on the read-only host root.
        proc = self.run_jailed("cd src && go test ./...", HOME=str(REPO_ROOT))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    # --- the per-command scratch dir is cleaned up ----------------------
    def _jail_scratch(self):
        d = Path(self.tmp.name) / "jailscratch"
        d.mkdir(exist_ok=True)
        return d

    def test_scratch_removed_and_exit_code_kept(self):
        d = self._jail_scratch()
        proc = self.run_jailed(
            'echo t > "$TMPDIR/x"; exit 7', HERETEK_JAIL_SCRATCH=str(d)
        )
        self.assertEqual(proc.returncode, 7, proc.stderr)
        self.assertEqual(list(d.iterdir()), [], "seatjail scratch dir leaked")

    def test_scratch_removed_when_terminated(self):
        d = self._jail_scratch()
        proc = subprocess.Popen(
            ["bash", str(WRAPPER), "-c", 'echo t > "$TMPDIR/x"; sleep 30'],
            cwd=str(self.ws),
            env={**self.env, "HERETEK_JAIL_SCRATCH": str(d)},
            start_new_session=True,  # pi kills the whole process group
        )
        for _ in range(50):
            if any((p / "x").exists() for p in d.iterdir()):
                break
            threading.Event().wait(0.1)
        os.killpg(proc.pid, 15)
        self.assertEqual(proc.wait(timeout=40), 143)
        self.assertEqual(list(d.iterdir()), [], "seatjail scratch dir leaked")

    def test_term_to_wrapper_alone_stops_command(self):
        # A supervisor may signal only the wrapper PID, not its group.
        d = self._jail_scratch()
        marker = d.parent / "still-running"
        proc = subprocess.Popen(
            [
                "bash",
                str(WRAPPER),
                "-c",
                f'echo t > "$TMPDIR/x"; sleep 3; echo late > {marker}',
            ],
            cwd=str(self.ws),
            env={
                **self.env,
                "HERETEK_JAIL_SCRATCH": str(d),
                "HERETEK_SANDBOX_WRITE": "src/",
            },
        )
        for _ in range(50):
            if any((p / "x").exists() for p in d.iterdir()):
                break
            threading.Event().wait(0.1)
        proc.terminate()
        self.assertEqual(proc.wait(timeout=2), 143)
        self.assertEqual(list(d.iterdir()), [], "seatjail scratch dir leaked")
        threading.Event().wait(4)
        self.assertFalse(marker.exists(), "jailed command outlived the wrapper")

    def test_stdin_passed_through_and_closed_stdin_ok(self):
        proc = subprocess.run(
            ["bash", str(WRAPPER), "-c", "cat"],
            input="piped-in\n",
            cwd=str(self.ws),
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.stdout, "piped-in\n", proc.stderr)
        proc = subprocess.run(
            ["bash", "-c", f'exec 0<&-; bash "{WRAPPER}" -c "echo RAN"'],
            cwd=str(self.ws),
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("RAN", proc.stdout)

    def test_unreadable_scratch_subdir_still_removed(self):
        # A jailed command can chmod 000 a non-empty dir in its scratch; that
        # must neither leak the scratch dir nor break the next run.
        if os.geteuid() == 0:
            self.skipTest("root ignores directory modes, so this can't fail as root")
        d = self._jail_scratch()
        proc = self.run_jailed(
            'mkdir -p "$TMPDIR/a/b" && touch "$TMPDIR/a/b/f" && chmod 000 "$TMPDIR/a"',
            HERETEK_JAIL_SCRATCH=str(d),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(list(d.iterdir()), [], "seatjail scratch dir leaked")
        proc = self.run_jailed("echo RAN", HERETEK_JAIL_SCRATCH=str(d))
        self.assertIn("RAN", proc.stdout, proc.stderr)

    def test_sigkilled_run_swept_by_next_run(self):
        # pi aborts with SIGKILL to the process group: no trap can run, so
        # the next wrapper invocation must sweep the orphan.
        d = self._jail_scratch()
        legacy = d / "seatjail.AbC123"
        legacy.mkdir()
        proc = subprocess.Popen(
            ["bash", str(WRAPPER), "-c", 'echo t > "$TMPDIR/x"; sleep 30'],
            cwd=str(self.ws),
            env={**self.env, "HERETEK_JAIL_SCRATCH": str(d)},
            start_new_session=True,
        )
        for _ in range(50):
            if any((p / "x").exists() for p in d.iterdir()):
                break
            threading.Event().wait(0.1)
        os.killpg(proc.pid, 9)
        proc.wait(timeout=10)
        self.assertEqual(len(list(d.iterdir())), 2, "expected the orphan to remain")
        self.run_jailed("true", HERETEK_JAIL_SCRATCH=str(d))
        self.assertEqual(list(d.iterdir()), [legacy], "orphan not swept")

    # --- writes outside the roots fail ---------------------------------
    def test_cwd_root_write_denied(self):
        proc = self.run_jailed("echo x > root.txt")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse((self.ws / "root.txt").exists())

    def test_new_file_beside_granted_file_denied(self):
        # `*.lock` grants nothing until a matching file exists.
        proc = self.run_jailed("echo x > new.lock")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse((self.ws / "new.lock").exists())

    def test_git_hooks_write_denied(self):
        proc = self.run_jailed("echo evil > .git/hooks/pre-commit")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse((self.ws / ".git/hooks/pre-commit").exists())

    def test_git_readonly_even_under_a_dir_root(self):
        proc = self.run_jailed(
            "echo evil > .git/hooks/pre-commit", HERETEK_SANDBOX_WRITE=".git/"
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse((self.ws / ".git/hooks/pre-commit").exists())

    def test_agent_control_paths_never_writable(self):
        (self.ws / "AGENTS.md").write_text("charter\n")
        (self.ws / ".pi").mkdir()
        proc = self.run_jailed(
            "echo x > AGENTS.md; echo x > .pi/settings.json; echo RAN",
            HERETEK_SANDBOX_WRITE=".pi/:AGENTS.md:src/.git/",
        )
        self.assertIn("RAN", proc.stdout, proc.stderr)
        self.assertEqual((self.ws / "AGENTS.md").read_text(), "charter\n")
        self.assertFalse((self.ws / ".pi/settings.json").exists())
        self.assertFalse(
            (self.ws / "src/.git").exists(), "control-path root was created"
        )

    def test_control_paths_inside_dir_root_read_only(self):
        (self.ws / "src/AGENTS.md").write_text("orig\n")
        (self.ws / "src/sub/.git/hooks").mkdir(parents=True)
        proc = self.run_jailed(
            "echo x > src/AGENTS.md; touch src/sub/.git/hooks/pre-commit; "
            "touch src/ok.txt; echo RAN"
        )
        self.assertIn("RAN", proc.stdout, proc.stderr)
        self.assertEqual((self.ws / "src/AGENTS.md").read_text(), "orig\n")
        self.assertFalse((self.ws / "src/sub/.git/hooks/pre-commit").exists())
        self.assertTrue((self.ws / "src/ok.txt").exists())

    def test_whole_cwd_and_dotdot_roots_refused(self):
        for roots in ("./", "../", "src/../../"):
            with self.subTest(roots=roots):
                proc = self.run_jailed("true", HERETEK_SANDBOX_WRITE=roots)
                self.assertEqual(proc.returncode, 126, proc.stderr)

    def test_symlinked_root_out_of_cwd_not_bound(self):
        (self.ws / "link").symlink_to(self.outside)
        proc = self.run_jailed(
            "echo x > link/pwn.txt", HERETEK_SANDBOX_WRITE="link/:link/deeper/"
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse((self.outside / "pwn.txt").exists())
        self.assertFalse((self.outside / "deeper").exists(), "mkdir escaped cwd")

    def test_symlinked_granted_file_not_bound(self):
        target = self.outside / "authorized_keys"
        target.write_text("orig\n")
        (self.ws / "package.json").unlink()
        (self.ws / "package.json").symlink_to(target)
        proc = self.run_jailed("echo pwn > package.json")
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(target.read_text(), "orig\n")

    # --- secrets and host sockets are masked ---------------------------
    # The masking probes end in `echo RAN` and assert it, so a wrapper that
    # dies before running the command can't pass them vacuously.
    def test_secret_store_masked(self):
        proc = self.run_jailed(
            f"cat {self.store}/opencode-go.key; echo RAN", HERETEK_SANDBOX_WRITE="src"
        )
        self.assertIn("RAN", proc.stdout, proc.stderr)
        self.assertNotIn("dummy-key", proc.stdout)

    def test_home_credentials_masked(self):
        proc = self.run_jailed(
            f"cat {self.home}/.ssh/id_ed25519 {self.home}/.netrc; echo RAN",
            HERETEK_SANDBOX_WRITE="src",
        )
        self.assertIn("RAN", proc.stdout, proc.stderr)
        self.assertNotIn("dummy-private-key", proc.stdout)
        self.assertNotIn("password dummy", proc.stdout)

    def test_extra_mask_hides_unix_socket(self):
        sock_path = Path(self.tmp.name) / "daemon.sock"
        srv = socket.socket(socket.AF_UNIX)
        srv.bind(str(sock_path))
        srv.listen(1)
        try:
            probe = (
                "python3 -c 'import socket,sys; s=socket.socket(socket.AF_UNIX); "
                f's.connect("{sock_path}"); print("CONNECTED")\''
            )
            proc = self.run_jailed(
                probe + "; echo RAN",
                HERETEK_SANDBOX_MASK=str(sock_path),
                HERETEK_SANDBOX_WRITE="src",
            )
            self.assertIn("RAN", proc.stdout, proc.stderr)
            self.assertNotIn("CONNECTED", proc.stdout)
        finally:
            srv.close()

    # --- network: jailed commands are offline, bare `rig` is not -------
    def _loopback_server(self):
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"DAEMON-OK")

            def log_message(self, *a):
                pass

        srv = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        return srv.server_address[1]

    def _fake_rig(self, port):
        rig = self.bin / "rig"
        rig.write_text(
            "#!/usr/bin/env python3\n"
            "import sys, urllib.request\n"
            "print('ARGV', sys.argv[1:])\n"
            f"print(urllib.request.urlopen('http://127.0.0.1:{port}/').read().decode())\n"
        )
        rig.chmod(rig.stat().st_mode | stat.S_IXUSR)

    def test_jailed_command_has_no_host_loopback(self):
        port = self._loopback_server()
        proc = self.run_jailed(
            f"python3 -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:{port}/')\""
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_bare_rig_reaches_daemon(self):
        port = self._loopback_server()
        self._fake_rig(port)
        proc = self.run_jailed("rig whoami --json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("DAEMON-OK", proc.stdout)

    def test_rig_route_does_not_interpret_shell(self):
        # REQ-A1: `whoami;` is not an allowlisted subcommand, so the hardened
        # relay denies before exec (no shell ever parses the `;`). The fake
        # rig must not run and the chained marker must not appear.
        port = self._loopback_server()
        self._fake_rig(port)
        marker = self.outside / "chained"
        proc = self.run_jailed(f"rig whoami; touch {marker}")
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertNotIn("DAEMON-OK", proc.stdout)
        self.assertIn("subcommand not allowlisted", proc.stderr)
        self.assertFalse(marker.exists(), "shell chaining escaped the rig route")

    def test_env_prefixed_rig_stays_jailed(self):
        port = self._loopback_server()
        self._fake_rig(port)
        proc = self.run_jailed("OPENRIG_SESSION_NAME=other rig whoami")
        self.assertNotIn("DAEMON-OK", proc.stdout)


class TestRigRelayEnforcement(unittest.TestCase):
    """REQ-A1: hardened `rig` relay in scripts/seat-sandbox.sh.

    The relay runs pre-jail (before any bwrap call), so this class carries
    NO bwrap gate and must pass with bubblewrap absent. A fake `rig` on PATH
    records execution; every "deny" case asserts the fake never ran (rc != 0
    with a refusal naming the reason), the "allow" case asserts it did.
    No real secrets: every body file carries dummy content only.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.ws = root / "ws"
        (self.ws / "src").mkdir(parents=True)
        self.outside = root / "outside"
        self.outside.mkdir()
        self.store = root / "secret-store"
        self.store.mkdir(mode=0o700)
        (self.store / "dummy-body.txt").write_text("dummy-body-content\n")
        (self.outside / "exfil.txt").write_text("dummy-outside-content\n")
        (self.ws / "src/body.json").write_text('{"slice": 12}\n')
        (self.ws / "src/link.json").symlink_to(self.ws / "src/body.json")
        self.home = root / "home"
        self.home.mkdir()
        self.bin = root / "fakebin"
        self.bin.mkdir()
        rig = self.bin / "rig"
        rig.write_text(
            f"#!{sys.executable}\n"
            "import sys\n"
            "print('FAKE-RIG-RAN', ' '.join(sys.argv[1:]))\n"
        )
        rig.chmod(rig.stat().st_mode | stat.S_IXUSR)
        self.env = {
            "PATH": f"{self.bin}{os.pathsep}/usr/bin{os.pathsep}/bin",
            "HOME": str(self.home),
            "HERETEK_SANDBOX_WRITE": "src/",
            "HERETEK_SECRET_STORE": str(self.store),
            "OPENRIG_SESSION_NAME": "testseat@testrig",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def run_relay(self, command, **env):
        merged = {**self.env, **env}
        return subprocess.run(
            ["bash", str(WRAPPER), "-c", command],
            cwd=str(self.ws),
            env=merged,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def assertDenied(self, proc, reason):
        self.assertNotEqual(proc.returncode, 0, proc.stdout)
        self.assertNotIn("FAKE-RIG-RAN", proc.stdout)
        self.assertIn(reason, proc.stderr)

    def test_deny_secret_store_body_file(self):
        target = self.store / "dummy-body.txt"
        for flag in (f"--body-file {target}", f"--body-file={target}"):
            with self.subTest(flag=flag):
                proc = self.run_relay(f"rig queue create --json --verify {flag}")
                self.assertDenied(proc, "inside secret store")

    def test_deny_out_of_scope_body_file(self):
        target = self.outside / "exfil.txt"
        for flag in (f"--body-file {target}", f"--body-file={target}"):
            with self.subTest(flag=flag):
                proc = self.run_relay(f"rig queue create --json --verify {flag}")
                self.assertDenied(proc, "outside scratch and seat workspace")
        # F2 rework: a scratch env root resolving to /, /tmp or /var/tmp
        # must not widen relay scope — the jail masks host /tmp, so a
        # host-/tmp file would launder bytes the seat could not read.
        probe_fd, probe_name = tempfile.mkstemp(
            prefix="relay-scope-probe-", suffix=".txt", dir="/tmp"
        )
        with os.fdopen(probe_fd, "w") as fh:
            fh.write("dummy-probe-content\n")
        probe = Path(probe_name)
        self.addCleanup(lambda: probe.unlink(missing_ok=True))
        link = Path(self.tmp.name) / "tmp-link"
        link.symlink_to("/tmp")
        for extra in ({"TMPDIR": "/tmp"}, {"TMPDIR": str(link)}):
            with self.subTest(extra=extra):
                proc = self.run_relay(
                    f"rig queue create --json --verify --body-file {probe}",
                    **extra,
                )
                self.assertDenied(proc, "outside scratch and seat workspace")

    def test_deny_forged_source(self):
        body = self.ws / "src/body.json"
        for flag in (
            "--source evil@otherrig",
            "--source=evil@otherrig",
            "-s evil@otherrig",
            "-s=evil@otherrig",
        ):
            with self.subTest(flag=flag):
                proc = self.run_relay(
                    f"rig queue create --json --verify {flag} --body-file {body}"
                )
                self.assertDenied(proc, "--source must equal")

    def test_deny_non_allowlisted_subcommand(self):
        for command in ("rig daemon status", "rig exfiltrate --json"):
            with self.subTest(command=command):
                proc = self.run_relay(command)
                self.assertDenied(proc, "subcommand not allowlisted")

    def test_deny_unsafe_note(self):
        body = self.ws / "src/body.json"
        # Values are shell-quoted so the note VALUE (not the wrapper shell,
        # which never evals) carries the newline / shell token into shlex.
        for note in (
            "done; rm -rf /",
            "done\nevil: 1",
            "done $(whoami)",
            "done `id`",
        ):
            for flag in (f"--note '{note}'", f"--note='{note}'"):
                with self.subTest(note=note, flag=flag):
                    proc = self.run_relay(
                        f"rig queue create --json --verify --body-file {body} {flag}"
                    )
                    self.assertDenied(proc, "--note fails restrictive pattern")

    def test_deny_symlink_body_file(self):
        link = self.ws / "src/link.json"
        for flag in (f"--body-file {link}", f"--body-file={link}"):
            with self.subTest(flag=flag):
                proc = self.run_relay(f"rig queue create --json --verify {flag}")
                self.assertDenied(proc, "must not be a symlink")

    def test_allow_valid_in_scope_matching_source_valid_note(self):
        body = self.ws / "src/body.json"
        for src in ("--source testseat@testrig", "--source=testseat@testrig"):
            with self.subTest(src=src):
                proc = self.run_relay(
                    f"rig queue create --json --verify {src} "
                    f"--note slice-12-done --body-file {body}"
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("FAKE-RIG-RAN", proc.stdout)


class TestRigRelayTOCTOU(unittest.TestCase):
    """TOCTOU pinning for --body-file (overhaul-a rework 2, F2).

    The relay validates the body path and then execs rig with that same
    path argument, so a swap winning the validation->exec window would
    redirect the granted read. The swapping fake rig below wins that race
    with probability 1: AFTER the relay's validation decision it replaces
    the validated path with a symlink to a secret file, then reads the
    granted body argument exactly as rig would (existsSync/statSync/
    readFileSync on the given path). A pinned relay still serves the
    validated bytes (the granted argument is /dev/fd/N); an unpinned one
    leaks the secret. No bwrap gate: the relay runs pre-jail.
    No real secrets: every "secret" is a dummy file under the test temp dir.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.ws = root / "ws"
        (self.ws / "src").mkdir(parents=True)
        self.outside = root / "outside"
        self.outside.mkdir()
        (self.outside / "secret.txt").write_text("dummy-secret-content\n")
        self.store = root / "secret-store"
        self.store.mkdir(mode=0o700)
        self.home = root / "home"
        self.home.mkdir()
        self.bin = root / "fakebin"
        self.bin.mkdir()
        rig = self.bin / "rig"
        rig.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "argv = sys.argv[1:]\n"
            "body = None\n"
            "for i, tok in enumerate(argv):\n"
            "    if tok == '--body-file' and i + 1 < len(argv):\n"
            "        body = argv[i + 1]\n"
            "    elif tok.startswith('--body-file='):\n"
            "        body = tok.partition('=')[2]\n"
            "print('FAKE-RIG-RAN', ' '.join(argv))\n"
            "orig = os.environ.get('RELAY_ORIG_BODY', '')\n"
            "secret = os.environ.get('RELAY_SWAP_SECRET', '')\n"
            "if orig and secret:\n"
            "    try:\n"
            "        os.unlink(orig)\n"
            "    except OSError:\n"
            "        pass\n"
            "    os.symlink(secret, orig)\n"
            "with open(body, 'rb') as fh:\n"
            "    print('RIG-READ:' + fh.read().decode())\n"
        )
        rig.chmod(rig.stat().st_mode | stat.S_IXUSR)
        self.env = {
            "PATH": f"{self.bin}{os.pathsep}/usr/bin{os.pathsep}/bin",
            "HOME": str(self.home),
            "HERETEK_SANDBOX_WRITE": "src/",
            "HERETEK_SECRET_STORE": str(self.store),
        }

    def tearDown(self):
        self.tmp.cleanup()

    def run_relay(self, command, **env):
        merged = {**self.env, **env}
        return subprocess.run(
            ["bash", str(WRAPPER), "-c", command],
            cwd=str(self.ws),
            env=merged,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_swapped_path_cannot_redirect_granted_read(self):
        for flag_tpl in ("--body-file {p}", "--body-file={p}"):
            with self.subTest(flag_tpl=flag_tpl):
                body = self.ws / "src/body.json"
                # A previous subTest's swap leaves a symlink behind; rebuild
                # a regular body file (and restore the dummy secret, which a
                # symlink-following write may have clobbered).
                if body.is_symlink() or body.exists():
                    body.unlink()
                body.write_text('{"slice": 12}\n')
                secret = self.outside / "secret.txt"
                secret.write_text("dummy-secret-content\n")
                proc = self.run_relay(
                    "rig queue create --json --verify " + flag_tpl.format(p=body),
                    RELAY_ORIG_BODY=str(body),
                    RELAY_SWAP_SECRET=str(secret),
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("FAKE-RIG-RAN", proc.stdout)
                self.assertIn("/dev/fd/", proc.stdout)
                self.assertIn('RIG-READ:{"slice": 12}', proc.stdout)
                self.assertNotIn("dummy-secret-content", proc.stdout)


if __name__ == "__main__":
    unittest.main()
