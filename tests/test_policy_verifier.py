#!/usr/bin/env python3
"""Unit tests for the stage-time policy-text verifier (issue #41).

Synthetic fixture trees in /tmp only — never the live mission checkout and
never this repo's live files. The stale ``cast_lossy`` stanza below replicates
the live stale text read-only from the mission repo
(``src/w3-06-staging/root-lints-reference.toml``); the verifier must FIRE on
that text and PASS on the corrected (``cast_possible_truncation``) text.
Likewise a ``pnpm eslint .``-style ``run:`` step must FAIL citing the ``lint``
script it duplicates, while the reconciled ``pnpm lint`` / ``format:check`` /
``typecheck`` / ``unit`` steps resolve clean. Workflow YAML is validated
with PyYAML (fail closed on unparseable files); ``run:`` bodies are then
line-scanned so every diagnostic carries an exact file:line.

Covers REQ-P1 (lint-table names vs the checked-in known-lint snapshot with
stale-pin failure), REQ-P2 (workflow ``run:`` vs staged package scripts plus
``cargo`` subcommands/aliases), REQ-P3 (offline, parse-only, fail closed, no
auto-fix) and REQ-P4 (stage-time ``--staged`` path). The vendored
``tests/fixtures/policy-verifier/live-corrected-lints.toml`` copy of the real
live table is scanned with the CHECKED-IN snapshot (F1: full rust + clippy
sections must exit 0; the stale cast_lossy swap-in must fire only on that
name), and the default pin-file path is proven enforcing (F2).
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "policy-verifier.py"
CHECKED_IN_SNAPSHOT = REPO_ROOT / "scripts" / "policy-verifier.known-lints.txt"
CHECKED_IN_PIN = REPO_ROOT / "scripts" / "policy-verifier.toolchain-pin"
# REQ-D95: the toolchain pin derives from the repo rust-toolchain.toml
# (fail-closed when absent) — never from a hand-kept revision string.
RUST_TOOLCHAIN = REPO_ROOT / "rust-toolchain.toml"
VENDORED_LIVE_TABLE = (
    REPO_ROOT / "tests" / "fixtures" / "policy-verifier" / "live-corrected-lints.toml"
)

# Grounded read-only in the live stale state (mission repo, 2026-10-22):
# the [workspace.lints.clippy] stanza of root-lints-reference.toml with the
# nonexistent `cast_lossy` name at its tail. Fixture line of `cast_lossy` is
# computed in the test (no hardcoded line number to drift).
STALE_CLIPPY_STANZA = """\
[workspace.lints.clippy]
all = { level = "deny", priority = -1 }
pedantic = { level = "warn", priority = -1 }
unwrap_used = "warn"
expect_used = "warn"
missing_errors_doc = "warn"
cast_lossy = "deny"
"""

FIXED_CLIPPY_STANZA = STALE_CLIPPY_STANZA.replace(
    'cast_lossy = "deny"', 'cast_possible_truncation = "deny"'
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
}

FLAT_PKG = {
    "name": "flat-pkg",
    "private": True,
    "scripts": {
        "lint": "eslint .",
        "unit": "vitest run",
    },
}

# Reconciled-shape workflow: the proven steps from
# pipelines/w2-07-ci-reconciled.yml (:134-138 pnpm lint / format:check /
# typecheck via turbo, :174 pnpm unit) plus the proven cargo lines. Must pass.
RECONCILED_WORKFLOW = """\
name: ci-reconciled
on: [push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: pnpm install --frozen-lockfile
      - name: ESLint via turbo (proven 3/3 exit 0)
        run: pnpm lint
      - name: Prettier check via turbo (proven 3/3 exit 0)
        run: pnpm format:check
      - name: TypeScript strict via turbo (proven 3/3 exit 0)
        run: pnpm typecheck
      - name: cargo fmt check (proven exit 0)
        run: cargo fmt --all -- --check
      - name: Clippy (PENDING proven run)
        run: cargo clippy --all-targets -- -D warnings
  unit:
    runs-on: ubuntu-latest
    steps:
      - run: pnpm install --frozen-lockfile
      - name: Vitest unit suite via turbo (proven 4/4 exit 0)
        run: pnpm unit
      - name: Rust unit suite (PENDING proven run)
        run: cargo test --locked
"""

SNAPSHOT_TEXT = """\
# synthetic known-lint snapshot for tests (offline authority fixture)
pin: fixture-toolchain-1
clippy::all
clippy::pedantic
clippy::unwrap_used
clippy::expect_used
clippy::missing_errors_doc
clippy::cast_possible_truncation
rust::rust_2018_idioms
"""


def run_verifier(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd or os.getcwd(),
    )


def git(*args, cwd):
    env = dict(
        os.environ,
        GIT_CONFIG_NOSYSTEM="1",
        HOME=tempfile.gettempdir(),
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@t",
    )
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=cwd, env=env
    )
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc


def read_checked_in_pin():
    """Checked-in audit-revision pin, ignoring `#` header comments."""
    for line in CHECKED_IN_PIN.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    raise AssertionError("toolchain pin file must not be empty")


def read_derived_pin():
    """REQ-D95: the toolchain pin derived from rust-toolchain.toml.

    Mirrors scripts/policy-verifier.py parse_toolchain_pin_text (TOML
    channel first, else first non-comment line) so the corpus and the
    checker can never disagree on what "derived" means.
    """
    import tomllib

    text = RUST_TOOLCHAIN.read_text()
    try:
        channel = tomllib.loads(text).get("toolchain", {}).get("channel")
        if isinstance(channel, str) and channel.strip():
            return channel.strip()
    except Exception:
        pass
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    raise AssertionError("rust-toolchain.toml must carry a channel pin")


def write_snapshot(directory, pin=None):
    if pin is None:
        pin = read_derived_pin()
    path = Path(directory) / "known-lints.txt"
    path.write_text(SNAPSHOT_TEXT.replace("fixture-toolchain-1", pin))
    return path


class PolicyVerifierLintTests(unittest.TestCase):
    def test_stale_cast_lossy_fires_naming_lint_and_line(self):
        """REQ-P1 red: the live stale `cast_lossy` text fails at stage time."""
        with tempfile.TemporaryDirectory() as tmp:
            cargo = Path(tmp) / "Cargo.toml"
            cargo.write_text('[workspace]\nresolver = "2"\n\n' + STALE_CLIPPY_STANZA)
            snapshot = write_snapshot(tmp)
            proc = run_verifier(str(cargo), "--known-lints", str(snapshot))
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            lineno = (
                '[workspace]\nresolver = "2"\n\n' + STALE_CLIPPY_STANZA
            ).splitlines().index('cast_lossy = "deny"') + 1
            out = proc.stdout + proc.stderr
            self.assertIn("clippy::cast_lossy", out)
            self.assertIn(f":{lineno}", out)

    def test_corrected_cast_possible_truncation_passes(self):
        """REQ-P1 green: the corrected live table passes."""
        with tempfile.TemporaryDirectory() as tmp:
            cargo = Path(tmp) / "Cargo.toml"
            cargo.write_text('[workspace]\nresolver = "2"\n\n' + FIXED_CLIPPY_STANZA)
            snapshot = write_snapshot(tmp)
            proc = run_verifier(str(cargo), "--known-lints", str(snapshot))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_non_workspace_lints_table_checked(self):
        """REQ-P1: plain `[lints.clippy]` tables are checked too."""
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "crate.toml"
            manifest.write_text('[lints.clippy]\ncast_lossy = "deny"\n')
            snapshot = write_snapshot(tmp)
            proc = run_verifier(str(manifest), "--known-lints", str(snapshot))
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("clippy::cast_lossy", proc.stdout + proc.stderr)

    def test_unparseable_toml_fails_closed(self):
        """REQ-P3: unreadable policy TOML is a failure, never skip-silent."""
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "Cargo.toml"
            bad.write_text("[workspace.lints.clippy\ncast_lossy = oops\n")
            snapshot = write_snapshot(tmp)
            proc = run_verifier(str(bad), "--known-lints", str(snapshot))
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("UNREADABLE", proc.stdout + proc.stderr)

    def test_stale_snapshot_pin_fails(self):
        """REQ-P1: snapshot pin != repo toolchain pin fails as stale."""
        with tempfile.TemporaryDirectory() as tmp:
            cargo = Path(tmp) / "Cargo.toml"
            cargo.write_text('[workspace]\nresolver = "2"\n\n' + FIXED_CLIPPY_STANZA)
            snapshot = write_snapshot(tmp, pin="fixture-toolchain-1")
            proc = run_verifier(
                str(cargo),
                "--known-lints",
                str(snapshot),
                "--expect-pin",
                "fixture-toolchain-2",
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("STALE", proc.stdout + proc.stderr)

    def test_matching_pin_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cargo = Path(tmp) / "Cargo.toml"
            cargo.write_text('[workspace]\nresolver = "2"\n\n' + FIXED_CLIPPY_STANZA)
            snapshot = write_snapshot(tmp, pin="fixture-toolchain-9")
            proc = run_verifier(
                str(cargo),
                "--known-lints",
                str(snapshot),
                "--expect-pin",
                "fixture-toolchain-9",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class PolicyVerifierLiveTableTests(unittest.TestCase):
    """F1: the complete real live table (vendored read-only copy) vs the
    CHECKED-IN snapshot — the synthetic clippy-only stanzas above never
    reproduce the live [workspace.lints.rust] section, so these tests do."""

    def test_vendored_live_corrected_table_passes_checked_in_snapshot(self):
        """REQ-P1 corrected-live-table scenario: the full vendored live
        table (both rust and clippy sections) exits 0 against the shipped
        snapshot — no false positives on unsafe_code/missing_docs."""
        self.assertTrue(VENDORED_LIVE_TABLE.exists(), f"missing {VENDORED_LIVE_TABLE}")
        proc = run_verifier(
            str(VENDORED_LIVE_TABLE), "--known-lints", str(CHECKED_IN_SNAPSHOT)
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_vendored_live_table_with_stale_cast_lossy_fires_only_that_name(self):
        """True positive preserved: the vendored live table with the stale
        cast_lossy name swapped back in fires ONLY on clippy::cast_lossy —
        the rust names must not false-positive (no masking by the snapshot
        expansion)."""
        with tempfile.TemporaryDirectory() as tmp:
            stale = Path(tmp) / "Cargo.toml"
            stale.write_text(
                VENDORED_LIVE_TABLE.read_text().replace(
                    'cast_possible_truncation = "deny"', 'cast_lossy = "deny"'
                )
            )
            proc = run_verifier(str(stale), "--known-lints", str(CHECKED_IN_SNAPSHOT))
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("clippy::cast_lossy", out)
            self.assertNotIn("rust::unsafe_code", out)
            self.assertNotIn("rust::missing_docs", out)

    def test_default_pin_file_enforces_freshness_without_pin_flags(self):
        """F2/REQ-P3: a snapshot whose pin disagrees with the checked-in
        toolchain pin fails even when NO pin flag is passed (freshness is
        the default, not opt-in)."""
        with tempfile.TemporaryDirectory() as tmp:
            cargo = Path(tmp) / "Cargo.toml"
            cargo.write_text('[workspace]\nresolver = "2"\n\n' + FIXED_CLIPPY_STANZA)
            snapshot = write_snapshot(tmp, pin="fixture-toolchain-9")
            proc = run_verifier(str(cargo), "--known-lints", str(snapshot))
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("STALE", out)


class PolicyVerifierWorkflowTests(unittest.TestCase):
    def _tree(self, tmp, workflow_text, pkg=None):
        root = Path(tmp)
        (root / "package.json").write_text(
            json.dumps(pkg if pkg is not None else ROOT_PKG)
        )
        wf_dir = root / "pipelines"
        wf_dir.mkdir()
        wf = wf_dir / "ci.yml"
        wf.write_text(workflow_text)
        snapshot = write_snapshot(tmp)
        return root, wf, snapshot

    def test_reconciled_steps_resolve_clean(self):
        """REQ-P2 green: reconciled pnpm + cargo steps resolve."""
        with tempfile.TemporaryDirectory() as tmp:
            root, _, snapshot = self._tree(tmp, RECONCILED_WORKFLOW)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_pnpm_eslint_dot_duplicates_lint_script(self):
        """REQ-P2 red: `pnpm eslint .` duplicates the `lint` script."""
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: dup\non: [push]\njobs:\n"
                "  lint:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - name: direct eslint\n        run: pnpm eslint .\n"
            )
            root, _, snapshot = self._tree(tmp, text, pkg=FLAT_PKG)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = proc.stdout + proc.stderr
            self.assertIn("lint", out)
            self.assertIn("DUPLICATE", out)

    def test_renamed_script_reference_fails_named(self):
        """REQ-P2 red: `run: pnpm <name>` with no such script fails."""
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: typo\non: [push]\njobs:\n"
                "  lint:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - name: typo step\n        run: pnpm lintt\n"
            )
            root, wf, snapshot = self._tree(tmp, text)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            out = proc.stdout + proc.stderr
            self.assertIn("lintt", out)
            self.assertIn(str(wf), out)

    def test_unknown_cargo_subcommand_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: cargo\non: [push]\njobs:\n"
                "  build:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - name: bogus\n        run: cargo frobnicate --locked\n"
            )
            root, _, snapshot = self._tree(tmp, text)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("frobnicate", proc.stdout + proc.stderr)

    def test_cargo_alias_from_staged_config_passes(self):
        """REQ-P2: `cargo <alias>` resolves via staged .cargo/config.toml."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps(ROOT_PKG))
            cargo_dir = root / ".cargo"
            cargo_dir.mkdir()
            (cargo_dir / "config.toml").write_text(
                '[alias]\nxit = "test -- --nocapture"\n'
            )
            wf_dir = root / "pipelines"
            wf_dir.mkdir()
            (wf_dir / "ci.yml").write_text(
                "name: alias\non: [push]\njobs:\n"
                "  t:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: cargo xit\n"
            )
            snapshot = write_snapshot(tmp)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_unparseable_workflow_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, snapshot = self._tree(tmp, "jobs: [unclosed\n  - :\n")
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("UNREADABLE", proc.stdout + proc.stderr)

    def test_pnpm_install_builtin_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: inst\non: [push]\njobs:\n"
                "  i:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: pnpm install --frozen-lockfile\n"
            )
            root, _, snapshot = self._tree(tmp, text)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_github_expression_with_separators_stays_single_segment(self):
        """REQ-P2: `echo ${{ a || b }}` stays one segment with no finding."""
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: expr\non: [push]\njobs:\n"
                "  e:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: echo ${{ a || b }}\n"
            )
            root, _, snapshot = self._tree(tmp, text)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, out)

    def test_pm_dynamic_expression_script_skipped_without_finding(self):
        """REQ-P2: `pnpm ${{ matrix.script }}` skips with no UNRESOLVABLE."""
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: dyn\non: [push]\njobs:\n"
                "  d:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: pnpm ${{ matrix.script }}\n"
            )
            root, _, snapshot = self._tree(tmp, text)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, out)
            self.assertNotIn("UNRESOLVABLE", out)

    def test_pm_static_script_alongside_expression_resolves(self):
        """REQ-P2: `pnpm lint ${{ matrix.args }}` still resolves lint."""
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: mix\non: [push]\njobs:\n"
                "  m:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: pnpm lint ${{ matrix.args }}\n"
            )
            root, _, snapshot = self._tree(tmp, text)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_npm_test_with_script_passes(self):
        """REQ-P2: `npm test` resolves via the test script when present."""
        with tempfile.TemporaryDirectory() as tmp:
            pkg = {"name": "t", "scripts": {"test": "vitest run"}}
            text = (
                "name: t\non: [push]\njobs:\n"
                "  t:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: npm test\n"
            )
            root, _, snapshot = self._tree(tmp, text, pkg=pkg)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_npm_test_without_script_passes_as_default(self):
        """REQ-P2: `npm test` with no test script applies the manager
        default (no UNRESOLVABLE SCRIPT finding)."""
        with tempfile.TemporaryDirectory() as tmp:
            pkg = {"name": "t", "scripts": {}}
            text = (
                "name: t\non: [push]\njobs:\n"
                "  t:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: npm test\n"
            )
            root, _, snapshot = self._tree(tmp, text, pkg=pkg)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, out)
            self.assertNotIn("UNRESOLVABLE", out)

    def test_npm_t_alias_behaves_as_test(self):
        """REQ-P2: alias `npm t` behaves as `test` (script or default)."""
        with tempfile.TemporaryDirectory() as tmp:
            pkg = {"name": "t", "scripts": {"test": "vitest run"}}
            text = (
                "name: t\non: [push]\njobs:\n"
                "  t:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: npm t\n"
            )
            root, _, snapshot = self._tree(tmp, text, pkg=pkg)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_yarn_workspace_resolves_command(self):
        """REQ-P2: `yarn workspace foo build` resolves build."""
        with tempfile.TemporaryDirectory() as tmp:
            pkg = {"name": "t", "scripts": {"build": "tsc -p ."}}
            text = (
                "name: y\non: [push]\njobs:\n"
                "  y:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: yarn workspace foo build\n"
            )
            root, _, snapshot = self._tree(tmp, text, pkg=pkg)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_yarn_workspace_unknown_command_fails(self):
        """REQ-P2 control: `yarn workspace foo bogus` still fails named."""
        with tempfile.TemporaryDirectory() as tmp:
            pkg = {"name": "t", "scripts": {"build": "tsc -p ."}}
            text = (
                "name: y\non: [push]\njobs:\n"
                "  y:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: yarn workspace foo bogus\n"
            )
            root, _, snapshot = self._tree(tmp, text, pkg=pkg)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("bogus", out)

    def test_quoted_inline_run_double_quotes_duplicates(self):
        """REQ-P2: `run: "pnpm eslint ."` fires DUPLICATE citing lint."""
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: q\non: [push]\njobs:\n"
                "  q:\n    runs-on: ubuntu-latest\n    steps:\n"
                '      - run: "pnpm eslint ."\n'
            )
            root, _, snapshot = self._tree(tmp, text, pkg=FLAT_PKG)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("DUPLICATE", out)
            self.assertIn("lint", out)

    def test_quoted_inline_run_single_quotes_duplicates(self):
        """REQ-P2: `run: 'pnpm eslint .'` fires DUPLICATE citing lint."""
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: q\non: [push]\njobs:\n"
                "  q:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: 'pnpm eslint .'\n"
            )
            root, _, snapshot = self._tree(tmp, text, pkg=FLAT_PKG)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("DUPLICATE", out)
            self.assertIn("lint", out)

    def test_quoted_inline_run_interior_escapes_still_resolve(self):
        """REQ-P2: outer quotes strip once; interior quotes survive and
        the step still folds to the script body (`lint: eslint .`)."""
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "name: q\non: [push]\njobs:\n"
                "  q:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: \"pnpm eslint '.'\"\n"
            )
            root, _, snapshot = self._tree(tmp, text, pkg=FLAT_PKG)
            proc = run_verifier(str(root), "--known-lints", str(snapshot))
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("DUPLICATE", out)
            self.assertIn("lint", out)


class PolicyVerifierStagedTests(unittest.TestCase):
    def test_staged_stale_toml_fails_then_fixed_passes(self):
        """REQ-P4: --staged fires on the stale text, passes when fixed."""
        with tempfile.TemporaryDirectory() as tmp:
            git("init", cwd=tmp)
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps(ROOT_PKG))
            git("add", "package.json", cwd=tmp)
            git("commit", "-qm", "seed", cwd=tmp)
            snapshot = write_snapshot(tmp)
            staged = root / "Cargo.toml"
            staged.write_text('[workspace]\nresolver = "2"\n\n' + STALE_CLIPPY_STANZA)
            git("add", "Cargo.toml", cwd=tmp)
            proc = run_verifier("--known-lints", str(snapshot), "--staged", cwd=tmp)
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("clippy::cast_lossy", proc.stdout + proc.stderr)
            staged.write_text('[workspace]\nresolver = "2"\n\n' + FIXED_CLIPPY_STANZA)
            git("add", "Cargo.toml", cwd=tmp)
            proc = run_verifier("--known-lints", str(snapshot), "--staged", cwd=tmp)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_missing_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            cargo = Path(tmp) / "Cargo.toml"
            cargo.write_text('[lints.clippy]\ncast_lossy = "deny"\n')
            proc = run_verifier(
                str(cargo), "--known-lints", str(Path(tmp) / "absent.txt")
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("SNAPSHOT", proc.stdout + proc.stderr)

    def test_checked_in_snapshot_and_pin_agree(self):
        """REQ-P4/D95: the shipped authority files exist and pin-match.

        The snapshot `pin:` line must equal the rust-toolchain.toml
        channel (derived, fail-closed); the legacy toolchain-pin mirror
        must agree with the same channel.
        """
        self.assertTrue(CHECKED_IN_SNAPSHOT.exists(), f"missing {CHECKED_IN_SNAPSHOT}")
        self.assertTrue(CHECKED_IN_PIN.exists(), f"missing {CHECKED_IN_PIN}")
        self.assertTrue(RUST_TOOLCHAIN.exists(), f"missing {RUST_TOOLCHAIN}")
        pin = read_derived_pin()
        self.assertTrue(pin, "toolchain pin must not be empty")
        names = {
            line.strip()
            for line in CHECKED_IN_SNAPSHOT.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        pins = {entry[4:].strip() for entry in names if entry.startswith("pin:")}
        self.assertIn(pin, pins)
        self.assertIn("clippy::cast_possible_truncation", names)
        self.assertNotIn("clippy::cast_lossy", names)
        self.assertEqual(
            read_checked_in_pin(),
            pin,
            "scripts/policy-verifier.toolchain-pin mirror must equal "
            "the rust-toolchain.toml channel",
        )

    def test_staged_uses_indexed_snapshot_not_worktree(self):
        """REQ-P4 index-authority: a worktree snapshot edit left UNSTAGED
        does not affect staged validation (the INDEX blob wins)."""
        with tempfile.TemporaryDirectory() as tmp:
            git("init", cwd=tmp)
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps(ROOT_PKG))
            snapshot = root / "known.txt"
            snapshot.write_text(SNAPSHOT_TEXT)
            git("add", "package.json", "known.txt", cwd=tmp)
            git("commit", "-qm", "seed", cwd=tmp)
            staged = root / "Cargo.toml"
            staged.write_text('[workspace]\nresolver = "2"\n\n' + FIXED_CLIPPY_STANZA)
            git("add", "Cargo.toml", cwd=tmp)
            # Break the worktree copy WITHOUT staging: staged validation
            # must still pass because the indexed snapshot is authoritative.
            snapshot.write_text("pin: wrong-pin\n")
            proc = run_verifier(
                "--known-lints",
                str(snapshot),
                "--expect-pin",
                "fixture-toolchain-1",
                "--staged",
                cwd=tmp,
            )
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, out)

    def test_staged_snapshot_edit_is_honored(self):
        """REQ-P4 index-authority positive: a STAGED snapshot edit that
        adds a lint name is honored by staged validation."""
        with tempfile.TemporaryDirectory() as tmp:
            git("init", cwd=tmp)
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps(ROOT_PKG))
            snapshot = root / "known.txt"
            snapshot.write_text(SNAPSHOT_TEXT)
            git("add", "package.json", "known.txt", cwd=tmp)
            git("commit", "-qm", "seed", cwd=tmp)
            snapshot.write_text(SNAPSHOT_TEXT + "clippy::new_hotness\n")
            git("add", "known.txt", cwd=tmp)
            staged = root / "Cargo.toml"
            staged.write_text('[workspace.lints.clippy]\nnew_hotness = "warn"\n')
            git("add", "Cargo.toml", cwd=tmp)
            proc = run_verifier(
                "--known-lints",
                str(snapshot),
                "--expect-pin",
                "fixture-toolchain-1",
                "--staged",
                cwd=tmp,
            )
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, out)

    def test_staged_committed_cargo_alias_resolves_without_staging(self):
        """REQ-P2: a staged workflow using a COMMITTED (not staged)
        .cargo/config.toml alias resolves."""
        with tempfile.TemporaryDirectory() as tmp:
            git("init", cwd=tmp)
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps(ROOT_PKG))
            cargo_dir = root / ".cargo"
            cargo_dir.mkdir()
            (cargo_dir / "config.toml").write_text(
                '[alias]\nxit = "test -- --nocapture"\n'
            )
            snapshot = write_snapshot(tmp)
            git("add", "package.json", ".cargo/config.toml", cwd=tmp)
            git("commit", "-qm", "seed", cwd=tmp)
            wf_dir = root / "pipelines"
            wf_dir.mkdir()
            (wf_dir / "ci.yml").write_text(
                "name: alias\non: [push]\njobs:\n"
                "  t:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: cargo xit\n"
            )
            git("add", "pipelines/ci.yml", cwd=tmp)
            proc = run_verifier("--known-lints", str(snapshot), "--staged", cwd=tmp)
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, out)

    def test_staged_unknown_cargo_alias_still_fails(self):
        """REQ-P2 control: an alias absent from every context still fails."""
        with tempfile.TemporaryDirectory() as tmp:
            git("init", cwd=tmp)
            root = Path(tmp)
            (root / "package.json").write_text(json.dumps(ROOT_PKG))
            snapshot = write_snapshot(tmp)
            git("add", "package.json", cwd=tmp)
            git("commit", "-qm", "seed", cwd=tmp)
            wf_dir = root / "pipelines"
            wf_dir.mkdir()
            (wf_dir / "ci.yml").write_text(
                "name: alias\non: [push]\njobs:\n"
                "  t:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - run: cargo frobnicate --locked\n"
            )
            git("add", "pipelines/ci.yml", cwd=tmp)
            proc = run_verifier("--known-lints", str(snapshot), "--staged", cwd=tmp)
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("frobnicate", out)


class PolicyVerifierStructuralD95Tests(unittest.TestCase):
    """REQ-D95 corpus: the `tomllib` structural walk is authoritative.

    Every spelling below exits 0 on the old line-scan (no table header
    for the text scan to anchor on) and MUST fail loudly on the
    structural walk, naming the fake lint with file:line attribution.
    Synthetic fixtures in /tmp only.
    """

    def run_toml(self, tmp, text):
        manifest = Path(tmp) / "crate.toml"
        manifest.write_text(text)
        snapshot = write_snapshot(tmp)
        proc = run_verifier(str(manifest), "--known-lints", str(snapshot))
        return proc, manifest

    def test_top_level_dotted_workspace_lints_fires(self):
        """No table header at all: `workspace.lints.clippy.x` fires."""
        with tempfile.TemporaryDirectory() as tmp:
            proc, manifest = self.run_toml(
                tmp, 'workspace.lints.clippy.cast_lossy = "deny"\n'
            )
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("clippy::cast_lossy", out)
            self.assertIn(str(manifest), out)

    def test_top_level_dotted_plain_lints_fires(self):
        """No table header at all: `lints.clippy.x` fires."""
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = self.run_toml(tmp, 'lints.clippy.cast_lossy = "deny"\n')
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("clippy::cast_lossy", out)

    def test_inline_table_lints_value_fires(self):
        """Inline-table spelling: `lints = { clippy = { fake = ... } }`."""
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = self.run_toml(
                tmp, 'lints = { clippy = { fake_fake_lint = "warn" } }\n'
            )
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("clippy::fake_fake_lint", out)

    def test_inline_table_under_header_fires(self):
        """`[workspace.lints]` with an inline-table tool value fires."""
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = self.run_toml(
                tmp,
                '[workspace.lints]\nclippy = { fake_inline_lint = "warn" }\n',
            )
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("clippy::fake_inline_lint", out)

    def test_dotted_key_under_tool_header_fires(self):
        """`[workspace.lints.clippy]` with a dotted fake name fires."""
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = self.run_toml(
                tmp,
                '[workspace.lints.clippy]\nnot_a_real_lint_xyz = "deny"\n',
            )
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("clippy::not_a_real_lint_xyz", out)

    def test_inline_table_with_real_names_passes(self):
        """Structural walk never descends into lint values: `{ level,
        priority }` inline tables with real names pass."""
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = self.run_toml(
                tmp,
                "[workspace.lints.clippy]\n"
                'all = { level = "deny", priority = -1 }\n'
                'unwrap_used = "warn"\n',
            )
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, out)

    def test_lints_workspace_true_inheritance_passes(self):
        """`[lints] workspace = true` is inheritance, not a tool table."""
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = self.run_toml(tmp, "[lints]\nworkspace = true\n")
            out = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, out)
            self.assertNotIn("UNKNOWN LINT TOOL", out)

    def test_missing_rust_toolchain_pin_fails_closed(self):
        """REQ-D95 derived pin: an absent rust-toolchain.toml is exit 1,
        never a silent default-allow."""
        with tempfile.TemporaryDirectory() as tmp:
            cargo = Path(tmp) / "Cargo.toml"
            cargo.write_text('[workspace]\nresolver = "2"\n\n' + FIXED_CLIPPY_STANZA)
            snapshot = write_snapshot(tmp)
            proc = run_verifier(
                str(cargo),
                "--known-lints",
                str(snapshot),
                "--pin-file",
                str(Path(tmp) / "absent-toolchain.toml"),
            )
            out = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0, out)
            self.assertIn("TOOLCHAIN PIN", out)


if __name__ == "__main__":
    unittest.main()
