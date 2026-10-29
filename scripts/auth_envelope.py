#!/usr/bin/env python3
"""auth_envelope.py — pre-authorization envelopes for slice classes (15-auth-envelope, Refs #15).

Standing authorization artifacts binding the TPM-verified premise to the
exact landing they authorize: diff-hash + scope paths + mandatory expiry
+ single-use nonce, HMAC-bound (wave-9 nonce/MAC discipline reused where
it fits — the extra premise fields carry their own validation).

Mint is a standing operator/TPM order; validate is a pure check plus a
redacted log. Any drift (landing diff != envelope diff-hash),
scope-breach (landing file-set outside scope paths), expiry, or replay
(consumed nonce) at landing is a fail-closed refusal with a redacted log
— never a silent landing. Envelopes NEVER self-execute and NEVER
auto-commit: no executor exists in this module and none is added
(REQ-E3); landing still requires its actor, and recovery dismissal
requires a row state change (scripts/sweep-typed-blocks.py
check_recovery_dismissal — the wave-4/81 refusal-guard precedent).

Envelope wire format (`.`-joined, no `.` inside fields: scope travels as
urlsafe-base64 of the comma-joined sorted scope list):
  `v2.<diff-hash>.<scope-b64>.<expires-epoch>.<nonce>.<hmac-hex>`

Secrets discipline: dummy keys in tests/scratch (`/tmp`, 0600); the HMAC
secret is never printed, never logged, never rendered inline — every log
path goes through seed-rig.py's `_redact_for_log` (single choke point,
reused — never duplicated).
"""

import base64
import hashlib
import hmac
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ENVELOPE_VERSION = "v2"

_DIFF_HASH_RE = re.compile(r"^[0-9a-fA-F]{8,128}$")
_NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{16,}$")
_HMAC_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPIRES_RE = re.compile(r"^[0-9]{1,19}$")
# Mint-side scope jailbreak tail (mirrors the check-envelope discipline:
# absolute, parent-traversal, whitespace, glob, option-shaped, refspec,
# non-ASCII, and percent-encoded entries never bind a premise).
_SCOPE_BAD_RE = re.compile(r"(^/|^\-|\.\.|[\s*?\[\]{}!:\\]|%|[^\x00-\x7f])")


def _scope_csv(scope_paths):
    """Canonical scope form: sorted, comma-joined (MAC'd and encoded)."""
    return ",".join(sorted(scope_paths))


def _scope_b64_encode(scope_csv):
    return (
        base64.urlsafe_b64encode(scope_csv.encode("utf-8")).decode("ascii").rstrip("=")
    )


def _scope_b64_decode(scope_b64):
    padded = scope_b64 + "=" * (-len(scope_b64) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")


_SEED_RIG_MOD = None


def _seed_rig_mod():
    """Load scripts/seed-rig.py as a module: single source of truth for log
    redaction (never duplicated here). Loaded once and cached — repeated
    validate calls reuse the module instead of re-executing seed-rig.py
    each time."""
    global _SEED_RIG_MOD
    if _SEED_RIG_MOD is not None:
        return _SEED_RIG_MOD
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "seed_rig_auth_envelope", Path(__file__).resolve().parent / "seed-rig.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _SEED_RIG_MOD = mod
    return mod


def _check_scope_entry(entry):
    """Fail-closed scope entry check at mint time (ValueError on breach)."""
    if not entry or not isinstance(entry, str):
        raise ValueError("scope paths must be non-empty strings")
    if _SCOPE_BAD_RE.search(entry):
        raise ValueError(
            "scope entry %r is absolute, traversing, option/refspec-shaped, "
            "globbed, or non-ASCII — refused" % entry
        )
    if entry.rstrip("/").strip() in ("", "."):
        raise ValueError("scope entry %r is a repository-root alias — refused" % entry)


def _envelope_mac(binding_secret, diff_hash, scope_csv, expires, nonce):
    msg = f"{ENVELOPE_VERSION}\n{diff_hash}\n{scope_csv}\n{expires}\n{nonce}".encode(
        "utf-8"
    )
    return hmac.new(binding_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def mint_envelope(
    binding_secret,
    diff_hash,
    scope_paths,
    expires_at,
    nonce=None,
):
    """Mint a standing pre-authorization envelope (operator/TPM order).

    Binds the exact TPM-verified diff hash plus scope paths plus a
    mandatory expiry epoch plus a single-use nonce, HMAC-bound under the
    seat binding secret (0600 store, `!cat`-style render where seats
    consume it — never inline). The envelope is an authorization artifact
    only: it never self-executes and never auto-commits.
    """
    if not binding_secret or not isinstance(binding_secret, str):
        raise ValueError("mint_envelope needs a binding secret")
    if not isinstance(diff_hash, str) or _DIFF_HASH_RE.fullmatch(diff_hash) is None:
        raise ValueError("diff hash must match ^[0-9a-fA-F]{8,128}$")
    diff_hash = diff_hash.lower()
    if not scope_paths or not isinstance(scope_paths, (list, tuple)):
        raise ValueError("scope paths must be a non-empty list")
    for entry in scope_paths:
        _check_scope_entry(entry)
    try:
        expires = int(expires_at)
    except (TypeError, ValueError):
        raise ValueError("expires_at must be an epoch integer")
    if expires <= 0:
        raise ValueError("expires_at must be a positive epoch (mandatory expiry)")
    if nonce is None:
        import secrets as _secrets

        nonce = _secrets.token_urlsafe(18)
    if not isinstance(nonce, str) or _NONCE_RE.fullmatch(nonce) is None:
        raise ValueError("nonce must match ^[A-Za-z0-9_-]{16,}$")
    scope_csv = _scope_csv(scope_paths)
    mac = _envelope_mac(binding_secret, diff_hash, scope_csv, str(expires), nonce)
    scope_b64 = _scope_b64_encode(scope_csv)
    return f"{ENVELOPE_VERSION}.{diff_hash}.{scope_b64}.{expires}.{nonce}.{mac}"


@dataclass(frozen=True)
class EnvelopeResult:
    """Landing-validation verdict. `status` is one of:

    - `authorized`: clean envelope (hash matches, scope covers, live,
      fresh nonce — the nonce is now consumed in the caller's seen set).
      Authorization only: the actor still performs the landing.
    - `refused`: drifted/scope-breached/expired/replayed/malformed —
      the landing must not proceed; the row keeps its state.
    """

    status: str
    reason: str | None = None


def _scope_covers(scope_csv, landing_paths):
    """Landing paths NOT covered by the envelope scope (empty when covered).

    A scope entry covers its exact path and, when it names a directory
    (trailing `/`), everything beneath it. Mirrors the premise-side rule
    in reconcile_model._scope_covers (same semantics, envelope spelling).
    """
    scope_paths = [part for part in scope_csv.split(",") if part]
    uncovered = []
    for path in landing_paths:
        covered = False
        for entry in scope_paths:
            if entry.endswith("/"):
                if path == entry.rstrip("/") or path.startswith(entry):
                    covered = True
                    break
            elif path == entry:
                covered = True
                break
        if not covered:
            uncovered.append(path)
    return uncovered


def validate_envelope(
    binding_secret,
    envelope,
    landing_diff_hash,
    landing_paths,
    now,
    seen,
):
    """Validate a landing against a standing envelope (pure check + log).

    `binding_secret` is the seat binding secret (0600 store, `!cat`
    render — never inline). `landing_diff_hash`/`landing_paths` describe
    the live landing; `now` is the landing epoch; `seen` is the
    caller-owned set of consumed nonces (single-use — daemon-side
    persistence is the #127 upstream gap, so a verifier without a set
    cannot run: `seen=None` fails closed to refused). Every denial path
    logs redacted (no secret material). The nonce joins `seen` ONLY on
    authorization — a refused landing never consumes it, and the store
    is never rewound. Performs no landing, no commit, no state write.
    """
    seed_mod = _seed_rig_mod()
    _redact = seed_mod._redact_for_log

    def _deny(reason):
        print(f"auth-envelope: refused ({_redact(reason)})", file=sys.stderr)
        return EnvelopeResult(status="refused", reason=reason)

    if not binding_secret or not isinstance(binding_secret, str):
        return _deny("no binding secret configured")
    if seen is None:
        return _deny("no replay set configured (fail closed)")
    if not envelope or not isinstance(envelope, str):
        return _deny("no envelope presented")
    parts = envelope.split(".")
    if len(parts) != 6 or parts[0] != ENVELOPE_VERSION:
        return _deny("malformed envelope shape")
    _, diff_hash, scope_b64, expires, nonce, mac = parts
    if _DIFF_HASH_RE.fullmatch(diff_hash) is None:
        return _deny("malformed envelope diff hash")
    try:
        scope_csv = _scope_b64_decode(scope_b64)
    except Exception:
        return _deny("malformed envelope scope")
    if not scope_csv or _EXPIRES_RE.fullmatch(expires) is None:
        return _deny("malformed envelope scope or expiry")
    if _NONCE_RE.fullmatch(nonce) is None:
        return _deny("malformed envelope nonce")
    if _HMAC_HEX_RE.fullmatch(mac) is None:
        return _deny("malformed envelope mac")
    try:
        expected_mac = _envelope_mac(
            binding_secret, diff_hash.lower(), scope_csv, expires, nonce
        )
    except Exception as exc:
        return _deny(f"mac computation failed: {exc}")
    if not hmac.compare_digest(mac, expected_mac):
        return _deny("bad envelope mac")
    if int(now) >= int(expires):
        return _deny("envelope expired")
    if nonce in seen:
        return _deny("replayed envelope (nonce already consumed)")
    landing_hash = str(landing_diff_hash or "").lower()
    if _DIFF_HASH_RE.fullmatch(landing_hash) is None:
        return _deny("malformed landing diff hash")
    if landing_hash != diff_hash.lower():
        return _deny(
            f"landing diff {landing_hash} drifted from authorized premise {diff_hash}"
        )
    uncovered = _scope_covers(scope_csv, list(landing_paths or []))
    if uncovered:
        return _deny(
            "landing file-set breaches the authorized scope: " + ", ".join(uncovered)
        )
    seen.add(nonce)
    print(
        f"auth-envelope: authorized ({_redact(diff_hash)} scope "
        f"{_redact(scope_csv)}; actor still performs the landing)",
        file=sys.stderr,
    )
    return EnvelopeResult(status="authorized", reason="clean envelope")


def write_envelope_exclusive(path, text):
    """Write an envelope artifact to a fresh 0600 path; never overwrite.

    Reuses the shared O_EXCL guard (same rule as reconcile proposals):
    any existing destination is refused, never clobbered.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from reconcile_model import write_out_exclusive

    write_out_exclusive(path, text)
    try:
        os.chmod(path, 0o600)
    except OSError as exc:
        raise ValueError(f"UNWRITABLE envelope path '{path}' ({exc})")
