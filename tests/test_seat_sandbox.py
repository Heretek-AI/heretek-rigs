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
        port = self._loopback_server()
        self._fake_rig(port)
        marker = self.outside / "chained"
        proc = self.run_jailed(f"rig whoami; touch {marker}")
        self.assertFalse(marker.exists(), "shell chaining escaped the rig route")
        self.assertIn("'whoami;'", proc.stdout)

    def test_env_prefixed_rig_stays_jailed(self):
        port = self._loopback_server()
        self._fake_rig(port)
        proc = self.run_jailed("OPENRIG_SESSION_NAME=other rig whoami")
        self.assertNotIn("DAEMON-OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
