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


def load_lint_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("manifest_closure", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    # discover_tree only collects filenames from os.walk, so a directory
    # named package.json is never opened for reading: the lint flow cannot
    # reach read_text_file's IsADirectoryError path (an explicit directory
    # path argument is walked by discover_tree, which yields no manifests
    # rather than reading the directory itself). Exercise the real path
    # directly: reading a directory must fail closed.
    def test_unreadable_manifest_fails_closed(self):
        mod = load_lint_module()
        target = self.root / "unreadable-dir"
        target.mkdir()
        with self.assertRaises(mod.ClosureError) as ctx:
            mod.read_text_file(target)
        self.assertIn("UNREADABLE MANIFEST", str(ctx.exception))

    def test_corrupt_manifest_fails_closed(self):
        fixed_tree(self.root)
        (self.root / "apps/web/package.json").write_text("{not json\n")
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("apps/web/package.json", proc.stdout + proc.stderr)

    # Extends chain: leaf omits `types`, base provides an undeclared entry
    # -> the base entry still fires (leaf-first chain read, not leaf-only).
    def test_extends_chain_base_types_fire_when_leaf_omits(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"t": "tsc --noEmit"},
                    "devDependencies": {"typescript": "5.7.2"},
                },
                "shared/base.json": {
                    "compilerOptions": {"types": ["undeclared-base-pkg"]}
                },
                "tsconfig.json": {
                    "extends": "./shared/base.json",
                    "compilerOptions": {"strict": True},
                },
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("undeclared-base-pkg", proc.stdout + proc.stderr)

    # Extends chain reverse: leaf provides `types` -> leaf's list wins and
    # the base list is ignored (tsc override semantics, not a union).
    def test_extends_chain_leaf_types_override_base(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"t": "tsc --noEmit"},
                    "devDependencies": {
                        "typescript": "5.7.2",
                        "@types/node": "22.10.0",
                    },
                },
                "tsconfig.json": {
                    "extends": "./shared/base.json",
                    "compilerOptions": {"types": ["node"]},
                },
                "shared/base.json": {
                    "compilerOptions": {"types": ["mystery-base-pkg"]}
                },
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # Tsconfig ownership: the NEAREST ancestor package resolves @types, so a
    # dep declared only in the nested package passes even though the root
    # lacks it (farthest-first traversal would fail this closed-wrong).
    def test_tsconfig_nearest_package_owns_types(self):
        write_tree(
            self.root,
            {
                "package.json": {"name": "root", "private": True},
                "sub/package.json": {
                    "name": "sub",
                    "devDependencies": {"@types/inner-lib": "1.0.0"},
                },
                "sub/nested/tsconfig.json": {
                    "compilerOptions": {"types": ["inner-lib"]}
                },
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # Tokenizer: backslash-newline joins before splitting; an unquoted `#`
    # beginning a word comments to EOL; `#` inside words/quotes is kept.
    def test_split_segments_continuation_comments_and_hashes(self):
        mod = load_lint_module()
        self.assertEqual(mod.split_segments("cmd arg \\\nmore"), ["cmd arg more"])
        self.assertEqual(mod.split_segments("cmd # comment"), ["cmd"])
        self.assertEqual(mod.split_segments("# full-line comment\ncmd"), ["cmd"])
        self.assertEqual(mod.split_segments('echo "a#b"'), ['echo "a#b"'])
        self.assertEqual(mod.split_segments("echo x#y"), ["echo x#y"])

    # Tokenizer end to end: continuations and full-line comments in script
    # bodies resolve (a dangling `#` or continuation fragment never becomes
    # the checked binary).
    def test_script_continuation_and_comment_lines_pass(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {
                        "lint": "eslint --flag \\\n.",
                        "note": "# tune later\neslint .",
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

    # PM run-strip: manager flags may precede `run`, so
    # `pnpm --filter pkg run build` still recurses into `build` (a binary
    # reachable only through `build` proves the recursion; treating `run`
    # as the head would wrongly pass via the allowlisted manager).
    def test_pnpm_filter_run_recurses_into_script(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {
                        "go": "pnpm --filter pkg run build",
                        "build": "secrettool --fast",
                    },
                    "devDependencies": {},
                },
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("secrettool", proc.stdout + proc.stderr)

        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"go": "pnpm run"},
                    "devDependencies": {},
                },
            },
        )
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # JSONC tsconfigs: comments and trailing commas parse, and the declared
    # `types` entry is still checked (undeclared `node` fires).
    def test_tsconfig_jsonc_parses_and_fires(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"t": "tsc --noEmit"},
                    "devDependencies": {"typescript": "5.7.2"},
                },
                "tsconfig.json": (
                    "{\n"
                    "  // workspace types gate\n"
                    '  "compilerOptions": {\n'
                    '    "types": ["node",], // trailing comma\n'
                    "  },\n"
                    "}\n"
                ),
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("@types/node", proc.stdout + proc.stderr)

    # package.json stays on strict JSON: a comment there still fails closed
    # (proves the JSONC path applies to TypeScript configs only).
    def test_commented_package_json_still_fails_closed(self):
        write_tree(
            self.root,
            {
                "package.json": (
                    "{\n"
                    "  // not legal in strict manifests\n"
                    '  "name": "mini",\n'
                    '  "scripts": {"t": "tsc --noEmit"},\n'
                    '  "devDependencies": {"typescript": "5.7.2"}\n'
                    "}\n"
                ),
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("UNREADABLE MANIFEST", proc.stdout + proc.stderr)

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

    def make_staged_repo(self, name):
        repo = self.root / name
        repo.mkdir()
        self.assertEqual(git("init", "-q", cwd=repo).returncode, 0)
        git("config", "user.email", "qa@example.test", cwd=repo)
        git("config", "user.name", "closure-qa", cwd=repo)
        return repo

    # REQ-C4: staging only a workflow still sees the committed root
    # manifest's dep context -> zero undeclared (no false UNDECLARED).
    def test_staged_workflow_uses_committed_root_context(self):
        repo = self.make_staged_repo("repoW")
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
        (repo / "allowlist.txt").write_text(TOOLCHAIN_ALLOWLIST)
        git("add", "-A", cwd=repo)
        git("commit", "-qm", "seed", cwd=repo)
        (repo / ".github" / "workflows").mkdir(parents=True)
        (repo / ".github/workflows/ci.yml").write_text(
            "name: ci\non: [push]\njobs:\n"
            "  unit:\n    runs-on: ubuntu-latest\n    steps:\n"
            "      - name: Vitest suite\n        run: pnpm unit\n"
        )
        git("add", ".github/workflows/ci.yml", cwd=repo)
        proc = run_lint(
            "--allowlist", str(repo / "allowlist.txt"), "--staged", cwd=repo
        )
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # REQ-C4: staging only a child manifest still sees the committed root
    # manifest's dep context; context-only manifests add no entry points.
    def test_staged_child_manifest_uses_committed_root_context(self):
        repo = self.make_staged_repo("repoC")
        write_tree(
            repo,
            {
                "package.json": {
                    "name": "root",
                    "private": True,
                    "devDependencies": {"eslint": "9.39.5"},
                },
            },
        )
        (repo / "allowlist.txt").write_text(TOOLCHAIN_ALLOWLIST)
        git("add", "-A", cwd=repo)
        git("commit", "-qm", "seed", cwd=repo)
        (repo / "apps" / "a").mkdir(parents=True)
        (repo / "apps/a/package.json").write_text(
            json.dumps(
                {
                    "name": "a",
                    "scripts": {"lint": "eslint ."},
                    "devDependencies": {},
                }
            )
        )
        git("add", "apps/a/package.json", cwd=repo)
        proc = run_lint(
            "--allowlist", str(repo / "allowlist.txt"), "--staged", cwd=repo
        )
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # REQ-C4 negative: index context never blanket-allows — a dep genuinely
    # absent from staged and committed manifests still fires.
    def test_staged_genuinely_absent_dep_still_fires(self):
        repo = self.make_staged_repo("repoN")
        write_tree(
            repo,
            {
                "package.json": {
                    "name": "root",
                    "private": True,
                    "devDependencies": {"eslint": "9.39.5"},
                },
            },
        )
        (repo / "allowlist.txt").write_text(TOOLCHAIN_ALLOWLIST)
        git("add", "-A", cwd=repo)
        git("commit", "-qm", "seed", cwd=repo)
        (repo / "apps" / "a").mkdir(parents=True)
        (repo / "apps/a/package.json").write_text(
            json.dumps(
                {
                    "name": "a",
                    "scripts": {"scan": "mysterytool --fast"},
                    "devDependencies": {},
                }
            )
        )
        git("add", "apps/a/package.json", cwd=repo)
        proc = run_lint(
            "--allowlist", str(repo / "allowlist.txt"), "--staged", cwd=repo
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("mysterytool", proc.stdout + proc.stderr)

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


class TestManifestClosureEvasionsD94(unittest.TestCase):
    """REQ-D94 corpus: every Wave-D evasion form fails loudly (exit 1,
    named finding), and the resolved forms pass when declared.

    Synthetic fixture trees in /tmp only — never live files.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "slice"
        self.root.mkdir()
        self.allowlist = str(self.root / "allowlist.txt")

    def tearDown(self):
        self.tmp.cleanup()

    def lint_root(self, *extra):
        return run_lint("--allowlist", self.allowlist, str(self.root), *extra)

    def mini_pkg(self, scripts, dev_deps=None):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": scripts,
                    "devDependencies": dev_deps or {},
                },
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )

    # `$`-leading command words are never skipped: command substitution.
    def test_dollar_substitution_needs_declaration(self):
        self.mini_pkg({"probe": "$(command -v eslint) --version"})
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("NEEDS-DECLARATION", out)
        self.assertIn("$(command", out)

    # `$`-leading command words are never skipped: parameter expansion.
    def test_dollar_brace_expansion_needs_declaration(self):
        self.mini_pkg({"probe": "${MYSTERY_BIN:-fallback} --help"})
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("NEEDS-DECLARATION", out)

    # `$`-leading command words are never skipped: bare variable head.
    def test_dollar_variable_head_needs_declaration(self):
        self.mini_pkg({"probe": "$MYSTERY_TOOL --fast"})
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("NEEDS-DECLARATION", out)
        self.assertIn("MYSTERY_TOOL", out)

    # `$`-leading `run:` step in a workflow fails naming the file.
    def test_dollar_run_step_needs_declaration(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"unit": "vitest run"},
                    "devDependencies": {"vitest": "3.0.0"},
                },
                ".github/workflows/ci.yml": (
                    "name: ci\non: [push]\njobs:\n"
                    "  unit:\n    runs-on: ubuntu-latest\n    steps:\n"
                    "      - name: dynamic runner\n        run: $(which vitest)\n"
                ),
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("NEEDS-DECLARATION", out)
        self.assertIn("ci.yml", out)

    # `node <path>` argv is inspected: undeclared .bin target fires even
    # though `node` itself is allowlisted.
    def test_node_bin_path_undeclared_fires(self):
        self.mini_pkg({"lint": "node node_modules/.bin/eslint ."})
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("eslint", proc.stdout + proc.stderr)

    # `node <path>` resolves: declared .bin target passes.
    def test_node_bin_path_declared_passes(self):
        self.mini_pkg(
            {"lint": "node node_modules/.bin/eslint ."},
            {"eslint": "9.39.5"},
        )
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # `node -e` inline evaluation is an exec form: always fails named.
    def test_node_eval_flag_fires(self):
        self.mini_pkg(
            {"pwn": "node -e \"require('fs').writeFileSync('/tmp/x','y')\""},
            {"typescript": "5.7.2"},
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("node -e", out)

    # `python -c` inline evaluation is an exec form: always fails named.
    def test_python_c_flag_fires(self):
        self.mini_pkg({"pwn": "python3 -c \"import os; os.system('id')\""})
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("python3 -c", out)

    # `git -c alias.*=!` shell-out aliases execute: always fail named even
    # though `git` itself is allowlisted.
    def test_git_alias_shellout_fires(self):
        self.mini_pkg(
            {"pwn": "git -c alias.lol='!touch /tmp/pwned' lol"},
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("alias", out)

    # Plain allowlisted `git` probe still passes (no false positive).
    def test_plain_git_probe_still_passes(self):
        self.mini_pkg({"probe": "git --version"})
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # `npx <undeclared>` resolves as a binary fetch: fails named.
    def test_npx_undeclared_binary_fires(self):
        self.mini_pkg({"serve": "npx mysteryserve ."})
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("mysteryserve", proc.stdout + proc.stderr)

    # `npx <declared-alias>` resolves through the alias table: passes.
    def test_npx_declared_alias_passes(self):
        self.mini_pkg(
            {"typecheck": "npx tsc --noEmit"},
            {"typescript": "5.7.2"},
        )
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # `.gitlab-ci.yml` is discovered: undeclared `script:` tool fires.
    def test_gitlab_ci_script_collected(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"lint": "eslint ."},
                    "devDependencies": {"eslint": "9.39.5"},
                },
                ".gitlab-ci.yml": (
                    "stages: [lint]\n"
                    "eslint-job:\n"
                    "  stage: lint\n"
                    "  script:\n"
                    "    - mysterytool --fast\n"
                ),
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("mysterytool", out)
        self.assertIn(".gitlab-ci.yml", out)

    # `.gitlab-ci.yml` string-form `script:` is collected too.
    def test_gitlab_ci_string_script_collected(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"lint": "eslint ."},
                    "devDependencies": {"eslint": "9.39.5"},
                },
                ".gitlab-ci.yml": (
                    "stages: [lint]\n"
                    "eslint-job:\n"
                    "  stage: lint\n"
                    "  script: mysterytool --fast\n"
                ),
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("mysterytool", proc.stdout + proc.stderr)

    # `.gitlab-ci.yml` resolving against declared deps passes.
    def test_gitlab_ci_declared_passes(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"lint": "eslint ."},
                    "devDependencies": {"eslint": "9.39.5"},
                },
                ".gitlab-ci.yml": (
                    "stages: [lint]\n"
                    "eslint-job:\n"
                    "  stage: lint\n"
                    "  script:\n"
                    "    - pnpm lint\n"
                ),
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertEqual(
            proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    # CircleCI dict-form `run: {command: ...}` steps are collected.
    def test_circleci_dict_run_collected(self):
        write_tree(
            self.root,
            {
                "package.json": {
                    "name": "mini",
                    "scripts": {"lint": "eslint ."},
                    "devDependencies": {"eslint": "9.39.5"},
                },
                ".circleci/config.yml": (
                    "version: 2.1\njobs:\n"
                    "  check:\n"
                    "    docker: [{image: cimg/base:stable}]\n"
                    "    steps:\n"
                    "      - run:\n"
                    "          name: mystery step\n"
                    "          command: mysterytool --fast\n"
                ),
                "allowlist.txt": TOOLCHAIN_ALLOWLIST,
            },
        )
        proc = self.lint_root()
        self.assertNotEqual(proc.returncode, 0)
        out = proc.stdout + proc.stderr
        self.assertIn("mysterytool", out)
        self.assertIn("config.yml", out)


if __name__ == "__main__":
    unittest.main()
