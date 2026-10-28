#!/usr/bin/env python3
"""send_identity.py — grant-bound sender attestation (09-send-identity, Refs #9).

Repo-side half of per-seat sender attestation for `rig send` / queue relays.
Extends the landed #121 bearer-grant model: where #121 bound an MCP bearer
token per seat, this module binds a **sender identity** per seat.

Layers (each mirrors the #121 precedent named in design.md):

- Issuance: `issue_sender_binding` mints a rig grant named
  `<session>/send-identity` via `rig mcp token add <name> --seat <session>
  --rig <rig>` — the same least-privilege scope as `issue_seat_grant`, the
  same fail-closed parse (`parse_issued_token`), the same 0600
  mkstemp+replace store, the same revoke-on-fail. The `/` separator cannot
  collide with a real session name (render dies on `.`/`@` in pod/member
  ids, so sessions never contain `/`). The binding file
  (`send-id-<session>.key`, same no-`..`-`/` filename rule as
  `seat_grant_token_filename`) holds the once-printed token; it is the HMAC
  key for attestation below.
- Attestation: `mint_attestation` / `verify_attestation` (HMAC-SHA256,
  stdlib only). The relay attaches the attestation server-side, never from
  client input; the receiver records the ATTESTED sender and IGNORES any
  conflicting client-supplied claim (`--source`, env). Missing attestation
  holds UNVERIFIED (no availability regression); replayed attestation is
  rejected (single-acceptance per verifier `seen` set). Daemon-side
  persistence of the seen-set is the #127 upstream gap — repo-side verifiers
  own their set (fail-closed: no set, no verify).
- Render: `render-seat.py` wires `send-identity.json` as a `!cat` reference
  for grant-bound seats — never an inline secret.
- Redaction: every new log path goes through `seed-rig.py`'s
  `_redact_for_log` (single choke point, reused — never duplicated).

Secrets discipline: dummy keys in tests/scratch (`/tmp`, 0600); the binding
secret is never printed, never logged, never rendered inline.
"""

import hashlib
import hmac
import os
import re
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Grant-name suffix for a seat's sender binding. `/` keeps the binding name
# out of the session namespace (sessions never contain `/`).
SENDER_BINDING_GRANT_SUFFIX = "/send-identity"

ATTESTATION_VERSION = "v1"

_NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{16,}$")
_HMAC_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def sender_binding_grant_name(session: str) -> str:
    """Rig-grant name for a seat's sender binding: `<session>/send-identity`."""
    return f"{session}{SENDER_BINDING_GRANT_SUFFIX}"


def sender_binding_filename(session: str) -> str:
    """Secrets-dir filename for a seat's sender binding.

    The session is embedded verbatim (grant names accept `@`; render dies on
    `.`/`@` in pod/member ids, so exactly one `@` separates member and rig).
    The `.key` suffix reuses the frozen `*.key` path deny, so no seat can
    read another seat's binding through the permission layer. Fail-closed:
    a session containing `/` or `..` raises (never build a secrets-dir path
    that escapes it — pod/member ids die on `.`/`@` at render, but `/` is
    refused here, at the path-construction choke point).
    """
    if "/" in session or ".." in session:
        raise ValueError(f"refusing sender-binding filename for session {session!r}")
    return f"send-id-{session}.key"


_SEED_RIG_MOD = None


def _seed_rig_mod():
    """Load scripts/seed-rig.py as a module: single source of truth for the
    issuance discipline (never duplicated here). Loaded once and cached —
    repeated verify/issue calls reuse the module instead of re-executing
    seed-rig.py each time."""
    global _SEED_RIG_MOD
    if _SEED_RIG_MOD is not None:
        return _SEED_RIG_MOD
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "seed_rig_send_identity", Path(__file__).resolve().parent / "seed-rig.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _SEED_RIG_MOD = mod
    return mod


def issue_sender_binding(
    session: str,
    secrets_dir: str,
    rig_bin: str = "rig",
    allow_missing_secrets: bool = False,
    rig: str | None = None,
) -> int:
    """Issue (or reuse) the seat's sender-binding grant.

    Mirrors `seed-rig.issue_seat_grant` exactly: same `--seat` + `--rig`
    scope, same scope-match reuse rule, same pre-mint 0600 store validation,
    same fail-closed parse with revoke-on-fail, same atomic 0600
    mkstemp+replace store. The grant name is
    `sender_binding_grant_name(session)`; the file is
    `sender_binding_filename(session)`. Returns 0 on issued/reused (or loud
    degrade under --allow-missing-secrets), 2 on fatal. The binding secret
    itself is never printed.
    """
    seed_mod = _seed_rig_mod()
    binding_name = sender_binding_grant_name(session)
    binding_path = Path(secrets_dir) / sender_binding_filename(session)
    _redact = seed_mod._redact_for_log

    def _fail(msg: str) -> int:
        msg = _redact(msg)
        if allow_missing_secrets:
            print(
                f"warn: {session}: sender binding not issued ({msg}), continuing degraded",
                file=sys.stderr,
            )
            return 0
        print(
            f"error: {session}: sender binding issuance failed: {msg}", file=sys.stderr
        )
        return 2

    for _ in range(2):
        grants = seed_mod._list_grants(rig_bin)
        if grants is None:
            return _fail(f"cannot list grants via {rig_bin}")
        if binding_name in grants:
            if not seed_mod._grant_scope_matches(grants[binding_name], session, rig):
                print(
                    f"warn: {session}: sender binding metadata mismatch (seat/scope); revoking and re-issuing",
                    file=sys.stderr,
                )
            elif binding_path.is_symlink():
                try:
                    binding_path.unlink()
                except OSError as e:
                    return _fail(f"cannot remove symlinked {binding_path.name}: {e}")
                print(
                    f"warn: {session}: {binding_path.name} was a symlink; removed, re-issuing",
                    file=sys.stderr,
                )
            elif binding_path.is_file():
                print(
                    f"ok {session}: sender binding already issued (reuse {binding_path.name})"
                )
                return 0
            else:
                print(
                    f"warn: {session}: binding grant exists but {binding_path.name} is missing; re-issuing",
                    file=sys.stderr,
                )
            if not seed_mod._revoke_grant(rig_bin, binding_name):
                return _fail(f"cannot revoke stale binding grant {binding_name}")
            continue
        try:
            _st = os.lstat(binding_path)
        except FileNotFoundError:
            _st = None
        if _st is not None and (
            not stat.S_ISREG(_st.st_mode) or stat.S_IMODE(_st.st_mode) != 0o600
        ):
            return _fail(
                f"refusing to store sender binding in existing {binding_path.name} "
                f"(not a 0600 regular file); remove it and re-seed"
            )
        add_cmd = [rig_bin, "mcp", "token", "add", binding_name, "--seat", session]
        if rig:
            add_cmd += ["--rig", rig]
        try:
            proc = subprocess.run(
                add_cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            return _fail(f"token add failed: {e}")
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip()
            if "already has a grant" in detail:
                continue
            return _fail(f"token add failed: {detail}")
        token = seed_mod.parse_issued_token(proc.stdout, binding_name)
        if token is None:
            seed_mod._revoke_grant(rig_bin, binding_name)
            print(
                f"error: {session}: token add printed unparseable output; minted binding grant revoked",
                file=sys.stderr,
            )
            return 2
        try:
            tmp_fd, tmp_name = tempfile.mkstemp(
                dir=str(binding_path.parent), prefix=binding_path.name + "."
            )
            try:
                os.fchmod(tmp_fd, 0o600)
                with os.fdopen(tmp_fd, "w") as fh:
                    fh.write(token)
                os.replace(tmp_name, binding_path)
            except BaseException:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
                raise
        except OSError as e:
            seed_mod._revoke_grant(rig_bin, binding_name)
            print(
                f"error: {session}: cannot store sender binding: {_redact(e)}; minted binding grant revoked",
                file=sys.stderr,
            )
            return 2
        print(f"ok {session}: sender binding issued ({binding_path.name})")
        return 0
    return _fail("binding grant state did not converge after retry")


def _attestation_mac(
    binding_secret: str, sender_session: str, rig: str, nonce: str
) -> str:
    msg = f"{ATTESTATION_VERSION}\n{sender_session}\n{rig}\n{nonce}".encode("utf-8")
    return hmac.new(binding_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def mint_attestation(
    binding_secret: str,
    sender_session: str,
    rig: str,
    nonce: str | None = None,
) -> str:
    """Mint a fresh sender attestation (server-side; never from client input).

    Format: `v1.<sender>.<rig>.<nonce>.<hmac-hex>` (`.` is safe: pod/member
    ids die on `.`/`@` at render, so exactly one `@` and no `.` appear in
    the sender/rig fields). The nonce is single-use (see `verify_attestation`).
    """
    if not binding_secret or not sender_session or not rig:
        raise ValueError("mint_attestation needs a binding secret, sender, and rig")
    if nonce is None:
        import secrets as _secrets

        nonce = _secrets.token_urlsafe(18)
    if _NONCE_RE.fullmatch(nonce) is None:
        raise ValueError("nonce must match ^[A-Za-z0-9_-]{16,}$")
    mac = _attestation_mac(binding_secret, sender_session, rig, nonce)
    return f"{ATTESTATION_VERSION}.{sender_session}.{rig}.{nonce}.{mac}"


@dataclass(frozen=True)
class AttestationResult:
    """Receiver-side verdict. `status` is one of:

    - `attested`: fresh valid attestation — `sender` is the proven sender.
      Any client-supplied claim is ignored (spoof-proof by construction).
    - `unverified`: no attestation, or one that fails shape/MAC/scope —
      hold exactly as today (no availability regression).
    - `rejected`: a proven replay — a previously accepted attestation
      presented again. `sender` is None.
    """

    status: str
    sender: str | None


def verify_attestation(
    binding_secret: str,
    attestation: str | None,
    *,
    expected_rig: str,
    expected_sender: str,
    seen: set,
    claimed_source: str | None = None,
) -> AttestationResult:
    """Verify an attested send against the seat's binding.

    `binding_secret` is this receiver's copy of the sender's binding secret
    (0600 store, `!cat` render — never inline). `expected_rig` pins the rig
    scope (cross-rig presentation fails, R3 analogue); `expected_sender`
    pins the seat scope — an attestation naming any other sender fails even
    when its MAC verifies under this secret, so one seat's secret can never
    authenticate another seat's identity. `seen` is the
    caller-owned set of accepted nonces (single-acceptance; daemon-side
    persistence is the #127 upstream gap — a verifier without a set cannot
    run, so `seen=None` fails closed to `unverified`). `claimed_source` is
    any client-supplied sender claim (`--source`, env): it is NEVER recorded
    — on a valid attestation the attested sender wins, otherwise the send is
    unverified. Every denial path logs redacted (no secret material).
    """
    seed_mod = _seed_rig_mod()
    _redact = seed_mod._redact_for_log

    def _deny(status: str, reason: str) -> AttestationResult:
        print(
            f"send-identity: {status} ({_redact(reason)})",
            file=sys.stderr,
        )
        return AttestationResult(status=status, sender=None)

    if not binding_secret or not isinstance(binding_secret, str):
        return _deny("unverified", "no binding secret configured")
    if seen is None:
        return _deny("unverified", "no replay set configured (fail closed)")
    if not attestation or not isinstance(attestation, str):
        return _deny("unverified", "no attestation presented")
    parts = attestation.split(".")
    if len(parts) != 5 or parts[0] != ATTESTATION_VERSION:
        return _deny("unverified", f"malformed attestation shape for {expected_rig}")
    _, sender, rig, nonce, mac = parts
    if not sender or not rig or _NONCE_RE.fullmatch(nonce) is None:
        return _deny("unverified", f"malformed attestation fields for {expected_rig}")
    if _HMAC_HEX_RE.fullmatch(mac) is None:
        return _deny("unverified", f"malformed attestation mac for {expected_rig}")
    if rig != expected_rig:
        return _deny(
            "unverified",
            f"scope mismatch: attestation rig {rig!r} != {expected_rig!r}",
        )
    if sender != expected_sender:
        return _deny(
            "unverified",
            f"sender mismatch: attestation sender {sender!r} != {expected_sender!r}",
        )
    try:
        expected_mac = _attestation_mac(binding_secret, sender, rig, nonce)
    except Exception as e:
        return _deny("unverified", f"mac computation failed: {e}")
    if not hmac.compare_digest(mac, expected_mac):
        if claimed_source is not None and claimed_source != sender:
            return _deny(
                "unverified",
                f"bad attestation mac; conflicting client claim {_redact(claimed_source)} ignored",
            )
        return _deny("unverified", "bad attestation mac")
    if nonce in seen:
        return _deny("rejected", f"replayed attestation for {sender}")
    seen.add(nonce)
    if claimed_source is not None and claimed_source != sender:
        print(
            f"send-identity: attested ({_redact(sender)}); "
            f"conflicting client claim {_redact(claimed_source)} ignored",
            file=sys.stderr,
        )
    return AttestationResult(status="attested", sender=sender)
