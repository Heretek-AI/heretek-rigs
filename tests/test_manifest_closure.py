#!/usr/bin/env python3
"""Unit tests for the stage-time manifest-closure lint (issue #40).

Synthetic fixture trees in /tmp only — never the live mission checkout and
never this repo's live files. Covers REQ-C1 (entry-point collection incl.
pnpm indirection), REQ-C2 (undeclared-binary failure incl. npx/dlx one-shots
and the GLOBAL-leak class), REQ-C3 (checked-in allowlist, offline, fail
closed), REQ-C4 (stage-time --staged path) and REQ-C5 (tsconfig `types`
resolution). Instance #2 (ambient JSX without @types/react) is the documented
limitation: the lint MUST pass it (design.md); the tsc gate covers that class.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "manifest-closure.py"
CHECKED_IN_ALLOWLIST = REPO_ROOT / "fleet" / "allowed-system-tools.txt"

TOOLCHAIN_ALLOWLIST = (
    "\n".join(["node", "npm", "pnpm", "yarn", "git", "cargo", "rig", "echo"]) + "\n"
)

ROOT_PKG = {
    "name": "asset-manager",
    "private": True,
    "scripts": {
        "lint": "turbo run lint",
        "format:check": "turbo run format:check",
        "typecheck": "turbo run typecheck",
        "unit": "turbo run unit",
    },
    "devDependencies": {
        "eslint": "9.39.5",
        "prettier": "3.9.10",
        "turbo": "2.3.3",
        "typescript-eslint": "8.72.0",
    },
}

WEB_PKG = {
    "name": "@asset-manager/web",
    "private": True,
    "scripts": {
        "build": "vite build",
        "typecheck": "tsc --noEmit",
        "lint": "eslint .",
        "format:check": "prettier --check .",
        "unit": "vitest run --passWithNoTests",
    },
    "dependencies": {"react": "19.0.0", "react-dom": "19.0.0"},
    "devDependencies": {
        "@types/react": "19.0.0",
        "@types/react-dom": "19.0.0",
        "eslint": "9.39.5",
        "prettier": "3.9.10",
        "typescript": "5.7.2",
        "typescript-eslint": "8.72.0",
        "vite": "6.0.7",
        "vitest": "3.0.0",
    },
}

E2E_PKG = {
    "name": "@asset-manager/e2e",
    "private": True,
    "scripts": {
        "typecheck": "tsc --noEmit",
        "lint": "eslint .",
        "format:check": "prettier --check .",
        "e2e": "playwright test",
    },
    "devDependencies": {
        "@playwright/test": "1.49.1",
        "@types/node": "22.10.0",
        "eslint": "9.39.5",
        "prettier": "3.9.10",
        "typescript": "5.7.2",
        "typescript-eslint": "8.72.0",
    },
}

TESTS_PKG = {
    "name": "@asset-manager/tests",
    "private": True,
    "scripts": {
        "typecheck": "tsc --noEmit",
        "lint": "eslint .",
        "format:check": "prettier --check .",
        "integration": "vitest run --passWithNoTests",
    },
    "devDependencies": {
        "@types/node": "22.10.0",
        "eslint": "9.39.5",
        "prettier": "3.9.10",
        "typescript": "5.7.2",
        "typescript-eslint": "8.72.0",
        "vitest": "3.0.0",
    },
}

TSCONFIG_BASE = {"compilerOptions": {"strict": True, "noEmit": True}}

E2E_TSCONFIG = {
    "extends": "../tsconfig.base.json",
    "compilerOptions": {"types": ["node", "@playwright/test"]},
    "include": ["specs"],
}

WEB_TSCONFIG = {
    "extends": "../../tsconfig.base.json",
    "compilerOptions": {"jsx": "react-jsx", "types": ["vite/client"]},
    "include": ["src"],
}

CI_WORKFLOW = """\
name: ci
on: [push]
jobs:
  lint-format-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install --frozen-lockfile
      - name: ESLint via turbo
        run: pnpm lint
      - name: Prettier check via turbo
        run: pnpm format:check
      - name: TypeScript strict via turbo
        run: pnpm typecheck
      - name: cargo fmt check
        run: cargo fmt --all -- --check
      - name: Clippy
        run: cargo clippy --all-targets -- -D warnings
  unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install --frozen-lockfile
      - name: Vitest unit suite via turbo
        run: pnpm unit
      - name: Rust unit suite
        run: cargo test --locked
  integration-git:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install --frozen-lockfile
      - name: Runner capability probe
        run: git --version && git lfs version
      - name: VCS service contract suite
        run: pnpm --filter @asset-manager/tests integration
      - name: LFS lock round-trip note
        run: echo "lock round-trips pending"
"""


def write_tree(root: Path, files: dict) -> None:
    for rel, content in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, dict):
            target.write_text(json.dumps(content, indent=2) + "\n")
        else:
            target.write_text(content)


def fixed_tree(root: Path) -> None:
    write_tree(
        root,
        {
            "package.json": ROOT_PKG,
            "tsconfig.base.json": TSCONFIG_BASE,
            "apps/web/package.json": WEB_PKG,
            "apps/web/tsconfig.json": WEB_TSCONFIG,
            "e2e/package.json": E2E_PKG,
            "e2e/tsconfig.json": E2E_TSCONFIG,
            "tests/package.json": TESTS_PKG,
            ".github/workflows/ci.yml": CI_WORKFLOW,
            "allowlist.txt": TOOLCHAIN_ALLOWLIST,
        },
    )


def run_lint(*args, cwd=None, env_extra=None):
    env = {**os.environ}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        env=env,
    )


def git(*args, cwd, env=None):
    base = {
        **os.environ,
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(Path(cwd).parent),
    }
    if env:
        base.update(env)
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, env=base
    )


class TestManifestClosure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "slice"
        self.root.mkdir()
        self.allowlist = str(self.root / "allowlist.txt")

    def tearDown(self):
        self.tmp.cleanup()

    def lint_root(self, *extra):
        return run_lint("--allowlist", self.allowlist, str(self.root), *extra)

    # REQ-C2 scenario: four fixed pins resolve clean.
    def test_fixed_pins_pass(self):
        fixed_tree(self.root)
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
        self.assertIn("zero undeclared", proc.stdout)

    # REQ-C5 scenario: explicit `types` entry without declared package fails.
    def test_defect1_missing_types_node_fails_named(self):
        fixed_tree(self.root)
        e2e = json.loads((self.root / "e2e/package.json").read_text())
        del e2e["devDependencies"]["@types/node"]
        (self.root / "e2e/package.json").write_text(json.dumps(e2e))
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("@types/node", proc.stdout + proc.stderr)
        self.assertIn("tsconfig", proc.stdout + proc.stderr)

    # REQ-C2 scenario: each original omission fails named (bare eslint).
    def test_defect3a_bare_eslint_fails_named(self):
        fixed_tree(self.root)
        for rel in (
            "package.json",
            "apps/web/package.json",
            "e2e/package.json",
            "tests/package.json",
        ):
            doc = json.loads((self.root / rel).read_text())
            for section in ("dependencies", "devDependencies"):
                doc.get(section, {}).pop("eslint", None)
                doc.get(section, {}).pop("typescript-eslint", None)
            (self.root / rel).write_text(json.dumps(doc))
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("eslint", proc.stdout + proc.stderr)

    # REQ-C2 scenario: each original omission fails named (bare prettier).
    def test_defect3b_bare_prettier_fails_named(self):
        fixed_tree(self.root)
        for rel in (
            "package.json",
            "apps/web/package.json",
            "e2e/package.json",
            "tests/package.json",
        ):
            doc = json.loads((self.root / rel).read_text())
            for section in ("dependencies", "devDependencies"):
                doc.get(section, {}).pop("prettier", None)
            (self.root / rel).write_text(json.dumps(doc))
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("prettier", proc.stdout + proc.stderr)

    # REQ-C2 scenario: each original omission fails named (vitest undeclared).
    def test_defect4_missing_vitest_fails_named(self):
        fixed_tree(self.root)
        web = json.loads((self.root / "apps/web/package.json").read_text())
        del web["devDependencies"]["vitest"]
        (self.root / "apps/web/package.json").write_text(json.dumps(web))
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("vitest", proc.stdout + proc.stderr)

    # REQ-C2 scenario: tsc is collected (typescript omitted -> named failure).
    def test_tsc_collected_typescript_omitted_fails_named(self):
        fixed_tree(self.root)
        web = json.loads((self.root / "apps/web/package.json").read_text())
        del web["devDependencies"]["typescript"]
        (self.root / "apps/web/package.json").write_text(json.dumps(web))
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("tsc", proc.stdout + proc.stderr)

    # REQ-C3 scenario: GLOBAL-leak binary still fails (PATH is never consulted).
    def test_global_leak_binary_still_fails(self):
        fixed_tree(self.root)
        bindir = self.root / "bin"
        bindir.mkdir()
        fake = bindir / "fakeglobaltool"
        fake.write_text("#!/bin/sh\nexit 0\n")
        fake.chmod(0o755)
        web = json.loads((self.root / "apps/web/package.json").read_text())
        web["scripts"]["leak"] = "fakeglobaltool --help"
        (self.root / "apps/web/package.json").write_text(json.dumps(web))
        proc = run_lint(
            "--allowlist",
            self.allowlist,
            str(self.root),
            env_extra={"PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"},
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("fakeglobaltool", proc.stdout + proc.stderr)

    # REQ-C3 scenario: unreadable manifest fails closed, never skip-silent.
    def test_unreadable_manifest_fails_closed(self):
        fixed_tree(self.root)
        (self.root / "e2e/package.json").unlink()
        (self.root / "e2e/package.json").mkdir()
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("e2e", proc.stdout + proc.stderr)

    def test_corrupt_manifest_fails_closed(self):
        fixed_tree(self.root)
        (self.root / "apps/web/package.json").write_text("{not json\n")
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("apps/web/package.json", proc.stdout + proc.stderr)

    # Instance #2 documented limitation: ambient JSX without @types/react has
    # no textual hook, so the lint MUST pass it; tsc remains the covering gate.
    def test_instance2_react_omission_passes_lint(self):
        fixed_tree(self.root)
        web = json.loads((self.root / "apps/web/package.json").read_text())
        del web["devDependencies"]["@types/react"]
        del web["devDependencies"]["@types/react-dom"]
        (self.root / "apps/web/package.json").write_text(json.dumps(web))
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # REQ-C1: pnpm script indirection resolves recursively; cycles fail named.
    def test_pnpm_indirection_recurses_and_cycles_fail(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {
                        "check": "pnpm lint",
                        "lint": "eslint .",
                    },
                    "devDependencies": {"eslint": "9.39.5"},
                },
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
        doc = json.loads((self.root / "package.json").read_text())
        del doc["devDependencies"]["eslint"]
        (self.root / "package.json").write_text(json.dumps(doc))
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("eslint", proc.stdout + proc.stderr)

        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"a": "pnpm b", "b": "pnpm a"},
                    "devDependencies": {},
                },
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("cycle", (proc.stdout + proc.stderr).lower())

    # The npx/pnpx/dlx one-shot hole: fetching without a pinned dep fails.
    def test_npx_dlx_one_shots_fail_named(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {
                        "serve": "npx serve .",
                        "fetch": "pnpm dlx cowsay hi",
                    },
                    "devDependencies": {},
                },
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("serve", out)
        self.assertIn("cowsay", out)

    # REQ-C2d/REQ-C3: allowlisted toolchain binaries pass; unknown ones fail;
    # a missing allowlist file fails instead of default-allowing.
    def test_toolchain_allowlist_and_fail_closed(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {
                        "probe": "git --version",
                        "note": "echo hello",
                    },
                    "devDependencies": {},
                },
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

        doc = json.loads((self.root / "package.json").read_text())
        doc["scripts"]["probe"] = "frobnicate --x"
        (self.root / "package.json").write_text(json.dumps(doc))
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("frobnicate", proc.stdout + proc.stderr)

        proc = run_lint("--allowlist", str(self.root / "nope.txt"), str(self.root))
        self.assertNotEqual(proc.returncode, 0)

    # REQ-C1: workflow `run:` bodies are collected; `uses:` steps are ignored.
    def test_workflow_run_steps_collected(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"lint": "eslint ."},
                    "devDependencies": {"eslint": "9.39.5"},
                },
                ".github/workflows/ci.yml": (
                    "name: ci\non: [push]\njobs:\n"
                    "  check:\n    runs-on: ubuntu-latest\n    steps:\n"
                    "      - uses: actions/checkout@v4\n"
                    "      - name: Lint\n        run: pnpm lint\n"
                    "      - name: Mystery\n        run: mysterytool --fast\n"
                ),
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("mysterytool", out)
        self.assertIn("ci.yml", out)

    # REQ-C1: operators inside quotes never split; redirections are skipped.
    def test_quoted_operators_and_redirects_ignored(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {
                        "note": 'echo "lock round-trips; harness above"',
                        "lint": "eslint . 2>&1",
                    },
                    "devDependencies": {"eslint": "9.39.5"},
                },
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # REQ-C4: --staged reads the git index (stage-time hook point).
    def test_staged_mode_reads_index(self):
        repo = self.root / "repo"
        repo.mkdir()
        self.assertEqual(git("init", "-q", cwd=repo).returncode, 0)
        git("config", "user.email", "qa@example.test", cwd=repo)
        git("config", "user.name", "closure-qa", cwd=repo)
        write_tree(
            repo,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"unit": "vitest run"},
                    "devDependencies": {"vitest": "3.0.0"},
                },
            },
        )
        allowlist = repo / "allowlist.txt"
        allowlist.write_text(TOOLCHAIN_ALLOWLIST)
        git("add", "-A", cwd=repo)
        git("commit", "-qm", "seed", cwd=repo)
        # Nothing staged -> green.
        proc = run_lint("--allowlist", str(allowlist), "--staged", cwd=repo)
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
        # Stage a broken manifest -> red naming the binary, even though the
        # committed tree is clean (proves index content is what is checked).
        doc = json.loads((repo / "package.json").read_text())
        del doc["devDependencies"]["vitest"]
        (repo / "package.json").write_text(json.dumps(doc))
        git("add", "package.json", cwd=repo)
        proc = run_lint("--allowlist", str(allowlist), "--staged", cwd=repo)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("vitest", proc.stdout + proc.stderr)

    # REQ-C3: the checked-in allowlist exists and names the toolchain binaries.
    def test_checked_in_allowlist_covers_toolchain(self):
        self.assertTrue(
            CHECKED_IN_ALLOWLIST.exists(),
            f"missing {CHECKED_IN_ALLOWLIST}",
        )
        entries = {
            line.strip()
            for line in CHECKED_IN_ALLOWLIST.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        for tool in ("node", "npm", "git", "rig"):
            self.assertIn(tool, entries)


if __name__ == "__main__":
    unittest.main()
