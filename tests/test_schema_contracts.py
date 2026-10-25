#!/usr/bin/env python3
"""Unit tests for the upstream-contract validation gate (issue #98, REQ-D98).

Proves the local contract schemas are not vacuous: the committed
`registry/status.json` validates clean AND a mutated copy (dropped
`bodyDigest`, the issue's mutation proof) fails local validation with
named errors. Also pins `schemas/contract-schemas.sha256` against disk
so silent local loosening flips red. Synthetic mutations live in /tmp
only — live registry files are never modified.
"""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "schemas"
STATUS_DOC = REPO_ROOT / "registry" / "status.json"
PIN_FILE = SCHEMA_DIR / "contract-schemas.sha256"

SCHEMA_FILES = [
    "agent-manifest.v1.schema.json",
    "bundle-behaviour.v1.schema.json",
    "bundle-common.v1.schema.json",
    "bundle-configurations.v1.schema.json",
    "bundle-status.v1.schema.json",
    "registry-entry.v1.schema.json",
]

try:
    from jsonschema import Draft202012Validator

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def load_validator(schema_name):
    schema = json.loads((SCHEMA_DIR / schema_name).read_text())
    return Draft202012Validator(schema)


class SchemaContractTests(unittest.TestCase):
    def test_pin_file_matches_disk(self):
        """REQ-D98: every pinned hash equals the file on disk."""
        self.assertTrue(PIN_FILE.exists(), f"missing {PIN_FILE}")
        for line in PIN_FILE.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            digest, name = stripped.split(None, 1)
            target = SCHEMA_DIR / name.strip()
            self.assertTrue(target.is_file(), f"pinned file missing: {name}")
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            self.assertEqual(
                actual, digest, f"schema drift without pin refresh: {name}"
            )

    def test_pin_covers_all_contract_schemas(self):
        """REQ-D98: the pin covers exactly the six contract schemas."""
        names = set()
        for line in PIN_FILE.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            _, name = stripped.split(None, 1)
            names.add(name.strip())
        self.assertEqual(names, set(SCHEMA_FILES))

    @unittest.skipUnless(HAS_JSONSCHEMA, "jsonschema library required")
    def test_committed_status_validates_clean(self):
        """Green direction: the committed status.json passes local validation."""
        validator = load_validator("bundle-status.v1.schema.json")
        doc = json.loads(STATUS_DOC.read_text())
        errors = list(validator.iter_errors(doc))
        self.assertEqual(
            errors, [], f"unexpected errors: {[e.message for e in errors]}"
        )

    @unittest.skipUnless(HAS_JSONSCHEMA, "jsonschema library required")
    def test_mutated_status_missing_digest_fails(self):
        """Red direction (the issue's mutation proof): dropping
        `bodyDigest` MUST fail local validation — a vacuous local schema
        (`errs []`) would pass this and hide the mutation."""
        validator = load_validator("bundle-status.v1.schema.json")
        doc = json.loads(STATUS_DOC.read_text())
        mutated = copy.deepcopy(doc)
        mutated.pop("bodyDigest", None)
        errors = list(validator.iter_errors(mutated))
        self.assertTrue(
            errors,
            "mutated status.json (no bodyDigest) passed local validation: "
            "the local schema is vacuous",
        )
        self.assertTrue(
            any("bodyDigest" in e.message for e in errors),
            f"mutation error must name bodyDigest: {[e.message for e in errors]}",
        )

    @unittest.skipUnless(HAS_JSONSCHEMA, "jsonschema library required")
    def test_mutated_status_wrong_type_fails(self):
        """Red direction: a mistyped `bodyDigest` MUST fail locally, and
        the error must survive a round-trip through a temp file (proves
        the gate reads bytes, not symbols)."""
        validator = load_validator("bundle-status.v1.schema.json")
        doc = json.loads(STATUS_DOC.read_text())
        doc["bodyDigest"] = 12345
        with tempfile.TemporaryDirectory() as tmp:
            victim = Path(tmp) / "status.json"
            victim.write_text(json.dumps(doc))
            reloaded = json.loads(victim.read_text())
        errors = list(validator.iter_errors(reloaded))
        self.assertTrue(errors, "mistyped bodyDigest passed local validation")


if __name__ == "__main__":
    unittest.main()
