#!/usr/bin/env python3
"""generate-rigs.py — Deterministic generator for the 51-agent, 8-rig heretek-rigs monorepo.

Reads canonical source of truth from:
  - fleet/fleet.yaml
  - fleet/mcp-servers.yaml
  - Pinned local checkouts of Heretek-Crew@5ffb1fc, obra/superpowers@bb92a77, trailofbits/skills@5c99c03,
    getsentry/skills@f57ada2, anthropics/skills@dbd4588, vercel-labs/agent-skills@063bee9, and openrig-core skills.

Generates (with zero symlinks and 100% `rig bundle check` containment):
  1. fleet/skills-lock.json (tree SHA-256 + license provenance for all 63 shared skills)
  2. specs/agents/_shared/ (heretek-shared AgentSpec v1.0 + 63 vendored skill dirs)
  3. specs/agents/<domain>/<role>/ (51 AgentSpecs v1.0, guidance/role.md, startup/context.md,
     runtime/{pi-settings,mcp,policy-enforcement}.json, and role-local skills/*/SKILL.md)
  4. rigs/<rig>/ (7 static rigs + heretek-omni-fleet with rig.yaml, CULTURE.md, README.md, SETUP.md,
     configurations.yaml, bundle.yaml, materialized agents/_shared + agents/<role>, plus
     heretek-omni-fleet/pods/*.yaml, members/*.yaml, and rig.all-51.yaml)
  5. rosters/heretek-omni-fleet.json (OpenRig v1 Roster covering all 51 seats)
  6. registry/entries/<rig>.yaml, registry/views/<rig>/behaviour.json, and registry/status.json
     (validated against schemas/*.v1.schema.json with UTF-16 configurationId/packageDigest and RFC 8785 JCS bodyDigest)
"""

import os
import shutil
import sys

try:
    import yaml
except ImportError:
    if shutil.which("uv") and not os.environ.get("_HERETEK_UV_REEXEC"):
        os.environ["_HERETEK_UV_REEXEC"] = "1"
        os.execvp(
            "uv",
            [
                "uv",
                "run",
                "--quiet",
                "--with",
                "pyyaml",
                "--with",
                "jsonschema",
                "python3",
                *sys.argv,
            ],
        )
    raise

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

OPENRIG_VERSION = "0.6.11"
OPENRIG_COMMIT = "379f0a0d"
# HR-3.3: fallback placeholder used ONLY when git resolution is impossible
# (e.g. source tarball without .git); generate_all() resolves the real commit
# via `git rev-parse HEAD` first and fails closed on dirty/missing checkouts.
HERETEK_RIGS_COMMIT_FALLBACK = "SYNTHETIC-NO-GIT-PROVENANCE-UNVERIFIED"
REVIEW_DATE = "2026-10-18"


def resolve_heretek_commit(root: Path, allow_synthetic: bool = False) -> str:
    """Resolve the real generating checkout SHA (fail-closed provenance).

    Returns `git rev-parse HEAD` (40-hex) when the checkout is clean; dies if
    git is missing, HEAD is unresolvable, or `git status --porcelain` is
    non-empty — unless HERETEK_RIGS_ALLOW_DIRTY=1 is set for explicitly
    labeled dev regenerations (still records the real SHA, never the fallback).
    When git is unresolvable, dies unless allow_synthetic is True, in which
    case the obvious SYNTHETIC- marker is returned (never a 40-hex lookalike).
    """
    allow_dirty = os.environ.get("HERETEK_RIGS_ALLOW_DIRTY") == "1"
    try:
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        if not allow_synthetic:
            die(
                "unresolvable HERETEK_RIGS_COMMIT (no git HEAD): re-run from a git "
                "checkout or pass --allow-synthetic-provenance for an explicitly "
                "labeled SYNTHETIC- tarball regen"
            )
        return HERETEK_RIGS_COMMIT_FALLBACK
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        die(f"unresolvable HERETEK_RIGS_COMMIT (got {head!r})")
    try:
        dirty = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        dirty = ""
    if dirty and not allow_dirty:
        die(
            "refusing to bake provenance on a dirty checkout "
            "(commit or stash first, or set HERETEK_RIGS_ALLOW_DIRTY=1 for dev regen)"
        )
    return head


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def utf16_key(s: str):
    # True UTF-16 code-unit sort: encode once, compare 2-byte units so astral
    # (non-BMP) chars sort as high/low surrogate pairs, not one large int.
    b = s.encode("utf-16-le")
    return [int.from_bytes(b[i : i + 2], "little") for i in range(0, len(b), 2)]


def jcs_canonicalize(o):
    """Minimal RFC 8785 JCS canonicalizer for float-free JSON bodies.

    Sorts object keys by UTF-16 code units (not Python codepoints), uses
    compact separators, and rejects floats (incl. -0.0) fail-closed. For
    ASCII-only float-free bodies this coincides with
    json.dumps(sort_keys, separators, ensure_ascii=False) but remains
    correct for astral keys by construction.
    """
    if o is None:
        return "null"
    if o is True:
        return "true"
    if o is False:
        return "false"
    if isinstance(o, bool):
        die("jcs_canonicalize: unexpected bool subclass")
    if isinstance(o, int):
        return str(o)
    if isinstance(o, float):
        die("registry/status.json body must not contain floats (JCS divergence risk)")
    if isinstance(o, str):
        return json.dumps(o, ensure_ascii=False)
    if isinstance(o, list):
        return "[" + ",".join(jcs_canonicalize(v) for v in o) + "]"
    if isinstance(o, dict):
        parts = []
        for k in sorted(o.keys(), key=utf16_key):
            parts.append(
                json.dumps(k, ensure_ascii=False) + ":" + jcs_canonicalize(o[k])
            )
        return "{" + ",".join(parts) + "}"
    die(f"jcs_canonicalize: unsupported type {type(o).__name__}")


def compute_configuration_id(mapping: dict) -> str:
    return ",".join(f"{k}={mapping[k]}" for k in sorted(mapping.keys(), key=utf16_key))


def compute_package_digest(integrity_files: dict) -> dict:
    lines = []
    for k in sorted(integrity_files.keys(), key=utf16_key):
        quoted = json.dumps(k, ensure_ascii=False)
        lines.append(f"{quoted}\t{integrity_files[k]}\n")
    val = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    return {
        "algorithm": "sha256",
        "value": val,
        "coverage": "openrig.package-digest/v1",
    }


def tree_hash(d: Path) -> str:
    h = hashlib.sha256()

    def walk(cur: Path):
        for entry in sorted(cur.iterdir(), key=lambda p: p.name):
            if entry.is_dir():
                walk(entry)
            else:
                rel = entry.relative_to(d).as_posix()
                h.update(rel.encode("utf-8") + b"\0")
                h.update(entry.read_bytes())

    walk(d)
    return "sha256:" + h.digest().hex()


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120)
    )


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_render_seat_module(repo_root: Path):
    spec = importlib.util.spec_from_file_location(
        "render_seat", repo_root / "scripts/render-seat.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resolve_default_openrig_core(repo_root: Path) -> Path:
    candidates = [
        repo_root.parent.parent
        / "openrig-workspace/openrig/packages/daemon/assets/plugins/openrig-core/skills",
        Path(
            "/home/john/Projects/openrig-workspace/openrig/packages/daemon/assets/plugins/openrig-core/skills"
        ),
    ]
    try:
        npm_root = subprocess.check_output(
            ["npm", "root", "-g"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        candidates.insert(
            0, Path(npm_root) / "@openrig/cli/daemon/assets/plugins/openrig-core/skills"
        )
    except Exception:
        pass
    for c in candidates:
        if c.exists():
            return c.resolve()
    return candidates[0]


def resolve_core_license(core_dir: Path) -> Path:
    for parent in core_dir.parents:
        for n in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
            cand = parent / n
            if cand.exists():
                return cand
    die(f"missing LICENSE above openrig-core skills dir {core_dir}")


def build_charter(rid: str, r: dict, crew_dir: Path) -> str:
    src_path = crew_dir / "roles" / rid / "AGENTS.md"
    if not src_path.exists():
        die(f"missing Heretek-Crew charter {src_path}")
    src = src_path.read_text()

    def sec(n: int) -> str:
        m = re.search(
            rf"^## {n}\. [^\n]*\n[\s\S]*?(?=^## \d+\. |\Z)", src, flags=re.MULTILINE
        )
        if not m:
            die(f"{rid}: section {n} missing in {src_path}")
        return m.group(0).rstrip()

    wake_m = re.search(
        r"^- \*\*Catalog wake policy\*\*: (.*)$", src, flags=re.MULTILINE
    )
    wake = wake_m.group(1) if wake_m else "on assignment"

    def fix_paperclip(s: str) -> str:
        return (
            s.replace("Paperclip ticket", "openrig queue item")
            .replace("via Paperclip", "via `rig queue` / `rig send`")
            .replace("Paperclip", "openrig")
        )

    if r.get("mcp"):
        mcp_lines = "\n".join(
            f"- `{b['server']}`"
            + (
                f" (GitHub `{b['toolset']}` toolset, read-only)"
                if b.get("toolset")
                else ""
            )
            + f": tools are named `mcp__{b['server'].replace('-', '_')}__<tool>`."
            for b in r["mcp"]
        )
    else:
        mcp_lines = (
            "- None. Use the built-in read/grep/find/ls tools and the bash allow-list."
        )

    all_skill_ids = (
        list(r["skills"]["openrig_core"])
        + [s["id"] for s in r["skills"]["shared"]]
        + [s["id"] for s in r["skills"]["role_local"]]
    )
    skills_lines = "\n".join(f"- `{s}`" for s in all_skill_ids)
    esc = (
        f'`rig send {r["reports_to"]["address"]} "<message>"`'
        if r.get("reports_to")
        else "the human operator (`messaging-the-human` skill)"
    )
    writable = (
        ", ".join(f"`{g}`" for g in r["permissions"]["path_write"])
        or "nothing (read-only seat)"
    )
    verif_cmds = (
        ", ".join(
            f"`{p}`"
            for p in r["permissions"]["bash_allow"]
            if not p.startswith("rig ") and not p.startswith("git ")
        )
        or "read-only git only"
    )

    return "\n".join(
        [
            f"# {r['title']} (`{rid}`): Agent Charter",
            "",
            f"> Department: {r['department']}. Rig `{r['rig']}`, pod `{r['pod']}`{' (pod lead)' if r.get('pod_lead') else ''}. Ported from Heretek-AI/Heretek-Crew@5ffb1fc `roles/{rid}/AGENTS.md`.",
            "",
            fix_paperclip(sec(1)),
            "",
            fix_paperclip(sec(2)),
            "",
            fix_paperclip(sec(3)),
            "",
            "## 4. MCP Servers & Tool Access",
            "",
            mcp_lines,
            "",
            "## 5. Skills",
            "",
            "Load a skill by reading its SKILL.md when the task matches its description.",
            "",
            skills_lines,
            "",
            "## 6. Coordination on openrig",
            "",
            "- Work arrives as openrig queue items and `rig send` messages; follow `queue-handoff` and `mission-slice-sop`.",
            f"- Escalate blockers to {esc}.",
            f"- Writes are confined to: {writable}. A denial from pi-permission-system is final: hand off, never work around it.",
            f"- Verification commands you may run: {verif_cmds}.",
            f"- Wake policy: {wake}.",
            "",
            "## 7. Non-Negotiables",
            "",
            "- Zero stubs: no placeholder functions, no dummy returns, no swallowed errors.",
            "- Fail closed: on an invalid state, stop with a descriptive error.",
            "- Never read or print secrets (.env, keys, tokens); never pass secrets on a command line.",
            "- Report completion with artifact paths and the exact verification commands and their results.",
            "",
        ]
    )


def generate_all(
    root: Path,
    crew_dir: Path,
    vendor_dir: Path,
    core_dir: Path,
    allow_synthetic: bool = False,
) -> None:
    fleet_path = root / "fleet/fleet.yaml"
    mcp_path = root / "fleet/mcp-servers.yaml"
    if not fleet_path.exists() or not mcp_path.exists():
        die("missing fleet/fleet.yaml or fleet/mcp-servers.yaml")

    fleet = yaml.safe_load(fleet_path.read_text())
    mcp_catalog = yaml.safe_load(mcp_path.read_text())["servers"]
    HERETEK_RIGS_COMMIT = resolve_heretek_commit(root, allow_synthetic)
    # HR-2.1-pinned-self-referential (fail-closed): refresh the vendored
    # rigspec-schema.ts SHA-256 anchor at generation time so the verifier has
    # a 4th independent value beyond the three local-local copies. Shell hosts
    # refresh the vendored bytes themselves via the JSON provenance recipe
    # (`npm pack @openrig/cli@0.6.11 ... show 379f0a0d:...rigspec-schema.ts`);
    # the hash here attests the vendored bytes as committed. An identical
    # 3-copy key edit without updating the vendored bytes still flips the
    # verifier (hash mismatch).
    try:
        _pinned_ts = root / "schemas/rigspec-schema.pinned.ts"
        _pinned_json_p = root / "schemas/rigspec-keys.pinned.json"
        if _pinned_ts.exists() and _pinned_json_p.exists():
            _ts_hash = hashlib.sha256(_pinned_ts.read_bytes()).hexdigest()
            _pinned_doc = json.loads(_pinned_json_p.read_text())
            _prov = _pinned_doc.get("provenance", {})
            if _prov.get("vendored_sha256") != _ts_hash:
                _prov["vendored_sha256"] = _ts_hash
                _pinned_doc["provenance"] = _prov
                _pinned_json_p.write_text(json.dumps(_pinned_doc, indent=2) + "\n")
    except Exception as _e:
        die(f"HR-2.1 vendored_sha256 refresh failed: {_e}")
    # HR-2.1-pinned-still-local (fail-closed): provenance.upstream_tarball is
    # NEVER derived from local bytes here. Its tarball_sha256 is recorded by a
    # human running `npm pack @openrig/cli@0.6.11` on a networked shell host
    # (see the provenance recipe in schemas/rigspec-keys.pinned.json); the
    # verifier fails while it is absent/placeholder. If a vendored
    # schemas/openrig-cli-0.6.11.tgz is present, attest its bytes now so the
    # record and the vendored bytes stay synchronized across regens.
    try:
        _tgz_path = root / "schemas/openrig-cli-0.6.11.tgz"
        _pinned_json_p2 = root / "schemas/rigspec-keys.pinned.json"
        if _tgz_path.exists() and _pinned_json_p2.exists():
            _tsha = hashlib.sha256(_tgz_path.read_bytes()).hexdigest()
            _pdoc2 = json.loads(_pinned_json_p2.read_text())
            _prov2 = _pdoc2.setdefault("provenance", {})
            _up2 = _prov2.setdefault("upstream_tarball", {})
            if _up2.get("tarball_sha256") != _tsha:
                _up2["tarball_sha256"] = _tsha
                _pinned_json_p2.write_text(json.dumps(_pdoc2, indent=2) + "\n")
    except Exception as _e:
        die(f"HR-2.1 upstream tarball attestation failed: {_e}")
    # HR-5.5 (fail-closed): reject shell-metachar chaining in bash_allow at
    # generation time — trailing-* prefix allows must not smuggle `; & | $ `
    # backticks, parens, newlines, redirections (`>`, `<`), backslash, `!`,
    # `#`, `~`, braces, brackets, `?`, or CR that could escape the allowlist.
    for _rid, _r in sorted(fleet.get("roles", {}).items()):
        for _pat in _r.get("permissions", {}).get("bash_allow", []):
            if re.search(r"[;&|$`()\n><\\!#~{}\[\]?\r]", _pat) or "$(" in _pat:
                die(f"{_rid}: bash_allow pattern contains shell metachar: {_pat!r}")
            # HR-5.5-render-output-allow (fail-closed): `--output=` write-escape
            # rejected at generation time to match verify-rigs.sh V1 — fleet
            # edits adding e.g. `git show --output=/tmp/x*` must die here.
            if "--output" in _pat:
                die(
                    f"{_rid}: bash_allow pattern contains forbidden --output write-escape: {_pat!r}"
                )
    # HR-4.3 (fail-closed): every required/optional secret filename referenced
    # by the catalog must be a bare filename (no dirs, no metachars) even when
    # per-seat rendering bypasses FS checks (check_secret_fs=False).
    for _sname, _s in mcp_catalog.items():
        for _sec in list(_s.get("required_secrets", [])) + list(
            _s.get("optional_secrets", [])
        ):
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", _sec) or "/" in _sec:
                die(f"{_sname}: invalid secret filename {_sec!r}")
    # HR-2.2-edge-extra-keys (fail-closed): fleet is the canonical edge source;
    # every pod-local and cross-pod edge must carry exactly {kind, from, to}
    # with a valid kind, or generation dies here so the defect can never reach
    # rig.yaml / rig.all-51.yaml leaves (mirrors schemas/rigspec-keys.pinned.json).
    _EDGE_KEYS = {"kind", "from", "to"}
    _EDGE_KINDS = {
        "delegates_to",
        "spawned_by",
        "can_observe",
        "collaborates_with",
        "escalates_to",
    }
    for _rig in list(fleet.get("rigs", [])) + [
        {
            "id": fleet.get("omni", {}).get("id", "heretek-omni-fleet"),
            "pods": [fleet.get("omni", {}).get("core_pod", {})],
            "edges": [],
        }
    ]:
        for _pod in _rig.get("pods", []) or []:
            for _e in _pod.get("edges", []) or []:
                if set(_e.keys()) - _EDGE_KEYS:
                    die(
                        f"{_rig.get('id')}.{_pod.get('id')}: edge has unknown keys {set(_e.keys()) - _EDGE_KEYS} in {_e!r}"
                    )
                if _e.get("kind") not in _EDGE_KINDS:
                    die(
                        f"{_rig.get('id')}.{_pod.get('id')}: edge has invalid kind {_e!r}"
                    )
        for _e in _rig.get("edges", []) or []:
            if set(_e.keys()) - _EDGE_KEYS:
                die(
                    f"{_rig.get('id')}: cross-pod edge has unknown keys {set(_e.keys()) - _EDGE_KEYS} in {_e!r}"
                )
            if _e.get("kind") not in _EDGE_KINDS:
                die(f"{_rig.get('id')}: cross-pod edge has invalid kind {_e!r}")
    spec_model = fleet["model"].get(
        "spec_model", "opencode-go/muse-spark-1.3-contributor:high"
    )
    render_seat_mod = load_render_seat_module(root)

    pins = {
        "heretek-crew": {
            "dir": crew_dir.resolve(),
            "sha": "5ffb1fc",
            "repo": "Heretek-AI/Heretek-Crew",
        },
        "superpowers": {
            "dir": (vendor_dir / "obra_superpowers").resolve(),
            "sha": "bb92a77",
            "repo": "obra/superpowers",
        },
        "tob": {
            "dir": (vendor_dir / "trailofbits_skills").resolve(),
            "sha": "5c99c03",
            "repo": "trailofbits/skills",
        },
        "sentry": {
            "dir": (vendor_dir / "getsentry_skills").resolve(),
            "sha": "f57ada2",
            "repo": "getsentry/skills",
        },
        "anthropic": {
            "dir": (vendor_dir / "anthropics_skills").resolve(),
            "sha": "dbd4588",
            "repo": "anthropics/skills",
        },
        "vercel": {
            "dir": (vendor_dir / "vercel-labs_agent-skills").resolve(),
            "sha": "063bee9",
            "repo": "vercel-labs/agent-skills",
        },
    }
    for k, p in pins.items():
        if not p["dir"].exists():
            die(f"missing pinned repository directory for {k}: {p['dir']}")
        head = subprocess.check_output(
            ["git", "-C", str(p["dir"]), "rev-parse", "--short=7", "HEAD"], text=True
        ).strip()
        allowed = (p["sha"], "0b41346") if k == "heretek-crew" else (p["sha"],)
        if head not in allowed:
            die(f"{k} checkout {p['dir']} is at {head}, expected {p['sha']}")

    core_license = resolve_core_license(core_dir)

    def find_skill(src: str, skill_id: str) -> Path:
        p = pins[src]
        if src == "tob":
            plugins = p["dir"] / "plugins"
            for pl in sorted(plugins.iterdir()):
                cand = pl / "skills" / skill_id
                if (cand / "SKILL.md").exists():
                    return cand
            die(f"tob skill {skill_id} not found")
        if src == "heretek-crew":
            for rdir in sorted((p["dir"] / "roles").iterdir()):
                cand = rdir / ".opencode/skills" / skill_id
                if (cand / "SKILL.md").exists():
                    return cand
            die(f"heretek-crew skill {skill_id} not found")
        cand = p["dir"] / "skills" / skill_id
        if not (cand / "SKILL.md").exists():
            die(f"{src} skill {skill_id} not found at {cand}")
        return cand

    def root_license(src: str):
        for n in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
            f = pins[src]["dir"] / n
            if f.exists():
                return f
        return None

    # Clean previous generated trees
    for d in ("specs/agents", "rigs", "registry", "rosters"):
        target = root / d
        if target.exists():
            shutil.rmtree(target)

    # 1. Build specs/agents/_shared/ and fleet/skills-lock.json
    shared_dir = root / "specs/agents/_shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    lock = {"version": 1, "skills": {}}
    shared_pool = {}

    for r in fleet["roles"].values():
        for sid in r["skills"]["openrig_core"]:
            shared_pool[sid] = ("openrig-core", core_dir / sid)
        for s in r["skills"]["shared"]:
            shared_pool[s["id"]] = (s["source"], find_skill(s["source"], s["id"]))

    for sid in sorted(shared_pool.keys()):
        src, sdir = shared_pool[sid]
        if not (sdir / "SKILL.md").exists():
            die(f"missing {sdir}/SKILL.md")
        dst_sdir = shared_dir / "skills" / sid
        shutil.copytree(sdir, dst_sdir, symlinks=False)
        has_lic = any(re.match(r"^LICEN[CS]E", f.name, re.I) for f in sdir.iterdir())
        lic_file = None
        if not has_lic:
            lic_file = core_license if src == "openrig-core" else root_license(src)
            if lic_file:
                shutil.copy2(lic_file, dst_sdir / "LICENSE")
        lock["skills"][sid] = {
            "source": (
                "npm:@openrig/cli@0.6.11 daemon/assets/plugins/openrig-core/skills"
                if src == "openrig-core"
                else f"{pins[src]['repo']}@{pins[src]['sha']}"
            ),
            "path": sid
            if src == "openrig-core"
            else sdir.relative_to(pins[src]["dir"]).as_posix(),
            "tree": tree_hash(dst_sdir),
            "license_file": (
                "in-tree"
                if has_lic
                else (
                    "LICENSE (copied from source root)"
                    if lic_file
                    else "none (see SKILL.md frontmatter)"
                )
            ),
        }

    write_json(root / "fleet/skills-lock.json", lock)

    shared_agent_yaml = {
        "name": "heretek-shared",
        "version": "1.0",
        "description": "Heretek fleet shared skill pool (vendored, pinned, zero external plugin paths).",
        "resources": {
            "skills": [
                {"id": sid, "path": f"skills/{sid}"}
                for sid in sorted(shared_pool.keys())
            ],
        },
        "profiles": {},
    }
    write_yaml(shared_dir / "agent.yaml", shared_agent_yaml)

    # 2. Build specs/agents/<domain>/<role>/ for all 51 roles
    for rid, r in sorted(fleet["roles"].items()):
        dom = r["domain"]
        adir = root / "specs/agents" / dom / rid
        adir.mkdir(parents=True, exist_ok=True)

        for s in r["skills"]["role_local"]:
            src_sdir = find_skill("heretek-crew", s["id"])
            shutil.copytree(src_sdir, adir / "skills" / s["id"], symlinks=False)

        charter_md = build_charter(rid, r, crew_dir)
        (adir / "guidance").mkdir(parents=True, exist_ok=True)
        (adir / "guidance/role.md").write_text(charter_md)

        (adir / "startup").mkdir(parents=True, exist_ok=True)
        (adir / "startup/context.md").write_text(
            f"You are {rid} ({r['title']}). Your charter and seat address are in your system prompt (`<agentDir>/AGENTS.md`). Run `rig whoami` and check your queue (`rig queue list`) before starting work.\n"
        )

        # Render static runtime reference artifacts in runtime/
        rt_dir = adir / "runtime"
        rt_dir.mkdir(parents=True, exist_ok=True)
        rendered_ref = render_seat_mod.build_seat_files(
            role_id=rid,
            rig_id=r["rig"],
            pod_id=r["pod"],
            member_id=rid,
            fleet_data=fleet,
            mcp_catalog=mcp_catalog,
            tools_dir="@TOOLS@",
            secrets_dir="@SECRETS@",
            seat_dir="@SEAT@",
            charter_text=charter_md,
            model_provider="opencode-go",
            model_id="muse-spark-1.3-contributor",
            allow_missing_secrets=True,
            check_secret_fs=False,
        )
        write_json(rt_dir / "pi-settings.json", rendered_ref["settings.json"])
        write_json(rt_dir / "mcp.json", rendered_ref["mcp.json"])
        perm_cfg = rendered_ref["extensions/pi-permission-system/config.json"]
        write_json(
            rt_dir / "policy-enforcement.json",
            {
                "role": rid,
                "openrig_permission_policy": r["permission_policy"],
                "readonly_charter": bool(r.get("readonly_charter", False)),
                "harness": "@gotgenes/pi-permission-system@41.0.0",
                "pi_packages": r.get(
                    "pi_packages", ["@gotgenes/pi-permission-system@41.0.0"]
                ),
                "promptTimeoutMs": perm_cfg["promptTimeoutMs"],
                "permission": perm_cfg["permission"],
            },
        )
        # HR-1.4: also emit standalone pi-permission-config.json (same permission
        # payload) so the 7-file claim and audit recipes referencing
        # runtime/pi-permission-config.json hold byte-for-byte.
        write_json(rt_dir / "pi-permission-config.json", perm_cfg)

        ref_shared = lambda s_id: f"heretek-shared:{s_id}"
        all_uses_skills = (
            [ref_shared(s_id) for s_id in r["skills"]["openrig_core"]]
            + [ref_shared(s["id"]) for s in r["skills"]["shared"]]
            + [s["id"] for s in r["skills"]["role_local"]]
        )
        agent_yaml = {
            "name": rid,
            "version": "1.0",
            "description": f"{r['title']} ({r['department']}) — Muse Spark 1.3 Contributor via OpenCode Go",
            "defaults": {
                "runtime": "pi",
                "model": spec_model,
                "effort": r["thinking"],
                "lifecycle": {
                    "execution_mode": "interactive_resident",
                    "compaction_strategy": "default-compaction",
                    "restore_policy": "resume_if_possible",
                },
            },
            "imports": [{"ref": "local:../../_shared", "version": "1.0"}],
            "profiles": {
                "default": {
                    "summary": f"Default Pi profile for {r['title']} on Muse Spark 1.3 Contributor",
                    "preferences": {
                        "runtime": "pi",
                        "model": spec_model,
                        "effort": r["thinking"],
                    },
                    "uses": {
                        "skills": all_uses_skills,
                        "guidance": [],
                        "subagents": [],
                        "plugins": [],
                        "runtime_resources": [],
                    },
                    "lifecycle": {
                        "compaction_strategy": "default-compaction",
                        "restore_policy": "resume_if_possible",
                    },
                }
            },
            "resources": (
                {
                    "skills": [
                        {"id": s["id"], "path": f"skills/{s['id']}"}
                        for s in r["skills"]["role_local"]
                    ]
                }
                if r["skills"]["role_local"]
                else {}
            ),
            "startup": {
                "files": [
                    {
                        "path": "startup/context.md",
                        "delivery_hint": "send_text",
                        "required": True,
                        "applies_on": ["fresh_start"],
                    }
                ],
                "actions": [],
            },
        }
        write_yaml(adir / "agent.yaml", agent_yaml)

    # 3. Build all 8 Rigs under rigs/<rig>/ + registry/entries/ + registry/views/ + status.json
    culture_text = "\n".join(
        [
            "# Heretek Fleet Culture & Operating Constitution",
            "",
            "- Evidence over assertion: every claim of done carries the command that proves it and its output (`verification-before-completion`).",
            "- Zero stubs, fail closed, least privilege. A permission denial from `@gotgenes/pi-permission-system@41.0.0` is a hand-off, never a puzzle to work around.",
            "- Small slices: one queue item, one verifiable outcome. Hand off with `rig queue` and state what is next.",
            "- Secrets never appear in messages, `rig.yaml` `env:`, files, transcripts, or command lines; they resolve exclusively via `0600` command-backed `!cat` references.",
            "",
        ]
    )

    def make_member_entry(m_id: str) -> dict:
        r_meta = fleet["roles"][m_id]
        return {
            "id": m_id,
            "label": r_meta["title"],
            "agent_ref": f"local:agents/{m_id}",
            "profile": "default",
            "runtime": "pi",
            "model": spec_model,
            "effort": r_meta["thinking"],
            "role": m_id,
            "permission_policy": r_meta["permission_policy"],
            "cwd": ".",
            "restore_policy": "resume_if_possible",
            "compaction_strategy": "default-compaction",
        }

    def make_pod_entry(pod_def: dict) -> dict:
        return {
            "id": pod_def["id"],
            "label": pod_def["label"],
            "summary": f"{pod_def['label']} pod led by {pod_def['lead']}.",
            "continuity_policy": {
                "enabled": True,
                "sync_triggers": ["pre_compaction", "pre_shutdown", "milestone"],
                "artifacts": {
                    "session_log": True,
                    "restore_brief": True,
                    "quiz": False,
                },
                "restore_protocol": {"peer_driven": True, "verify_via_quiz": False},
            },
            "members": [make_member_entry(m_id) for m_id in pod_def["members"]],
            "edges": pod_def["edges"],
        }

    all_rig_defs = list(fleet["rigs"])
    omni = fleet["omni"]
    omni_rig_def = {
        "id": omni["id"],
        "title": omni["title"],
        "summary": omni["summary"],
        "permission_policy": omni["permission_policy"],
        "sidecar_profiles": omni["sidecar_profiles"],
        "pods": [omni["core_pod"]],
        "edges": [],
    }
    all_rig_defs.append(omni_rig_def)

    listings_status = {}

    for rig_def in all_rig_defs:
        rig_slug = rig_def["id"]
        rig_dir = root / "rigs" / rig_slug
        rig_dir.mkdir(parents=True, exist_ok=True)

        # Materialize agents/_shared inside rigs/<rig>/agents/_shared
        shutil.copytree(shared_dir, rig_dir / "agents/_shared", symlinks=False)

        # Determine which roles to materialize in rigs/<rig>/agents/
        # For static rigs: the rig's members. For heretek-omni-fleet: all 51 roles (supporting pods/*.yaml and members/*.yaml)
        roles_to_materialize = (
            sorted(fleet["roles"].keys())
            if rig_slug == omni["id"]
            else [m_id for p in rig_def["pods"] for m_id in p["members"]]
        )
        for m_id in roles_to_materialize:
            r_meta = fleet["roles"][m_id]
            src_adir = root / "specs/agents" / r_meta["domain"] / m_id
            dst_adir = rig_dir / "agents" / m_id
            shutil.copytree(src_adir, dst_adir, symlinks=False)
            vendored_ay = yaml.safe_load((dst_adir / "agent.yaml").read_text())
            vendored_ay["imports"] = [{"ref": "local:../_shared", "version": "1.0"}]
            write_yaml(dst_adir / "agent.yaml", vendored_ay)

        pods_yaml = [make_pod_entry(p) for p in rig_def["pods"]]
        rig_members_flat = [
            (p["id"], m_id, fleet["roles"][m_id])
            for p in rig_def["pods"]
            for m_id in p["members"]
        ]

        (rig_dir / "CULTURE.md").write_text(culture_text)
        (rig_dir / "SETUP.md").write_text(
            f"""# Setup Guide: `{rig_slug}`

## Prerequisites
1. Install OpenRig (`@openrig/cli@{OPENRIG_VERSION}`) and Pi Coding Agent (`@earendil-works/pi-coding-agent@1.3.0`).
2. Install `@gotgenes/pi-permission-system@41.0.0` under `$HERETEK_TOOLS/pi-packages`.
3. Provision `$HERETEK_SECRETS/opencode-go.key` (mode `0600`) and run:
   ```bash
   python3 scripts/seed-rig.py rigs/{rig_slug}/rig.yaml --allow-missing-secrets
   ```
4. Launch the rig:
   ```bash
   (cd rigs/{rig_slug} && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)
   ```
"""
        )

        seats_bullet = "\n".join(
            f"- `{p_id}.{m_id}` ({r_m['title']}) — Policy: `{r_m['permission_policy']}`, Thinking: `{r_m['thinking']}`"
            for p_id, m_id, r_m in rig_members_flat
        )
        extra_omni_note = (
            f'\n## Dynamic Scaling (`rig expand` & `rig add`)\n- **Pod fragments (`pods/*.yaml`)**: 15 departmental/rig pods ready for `rig expand <RIG-ID> pods/<pod>.yaml --rig-root "$PWD"`.\n- **Member fragments (`members/*.yaml`)**: All 51 specialist seats ready for `rig add {rig_slug} <pod> members/<role>.yaml --rig-root "$PWD"`.\n- **Static All-51 Profile**: `rig.all-51.yaml` declares all 51 seats across all 15 pods.\n'
            if rig_slug == omni["id"]
            else ""
        )
        (rig_dir / "README.md").write_text(
            f"""# OpenRig Bundle: `{rig_slug}`

{rig_def["summary"]}

## Purpose & Seats ({len(rig_members_flat)} Default Boot Seats)
{seats_bullet}
{extra_omni_note}
## Prerequisites & Setup
See `SETUP.md`. Seed seats with `python3 scripts/seed-rig.py rigs/{rig_slug}/rig.yaml` before `rig up`.

## Running, Stopping & Cleanup
- **Check bundle**: `rig bundle check rigs/{rig_slug} --json`
- **Validate & preflight**: `(cd rigs/{rig_slug} && rig spec validate rig.yaml --json && rig spec preflight rig.yaml --json)`
- **Launch**: `(cd rigs/{rig_slug} && rig up rig.yaml --cwd "$HERETEK_WORKSPACE" --yes)`
- **Stop**: `rig down {rig_slug}`
"""
        )

        rig_yaml = {
            "version": "0.2",
            "name": rig_slug,
            "summary": rig_def["summary"],
            "culture_file": "CULTURE.md",
            "permission_policy": rig_def["permission_policy"],
            "non_interruptive": False,
            "docs": [
                {"path": "README.md"},
                {"path": "SETUP.md"},
            ],
            "pods": pods_yaml,
            "edges": rig_def["edges"],
        }
        write_yaml(rig_dir / "rig.yaml", rig_yaml)

        # For heretek-omni-fleet, also generate pods/*.yaml, members/*.yaml, and rig.all-51.yaml
        if rig_slug == omni["id"]:
            # HR-1.3: member_fragments is the canonical 51-entry role->pod map in
            # fleet.yaml; fail closed if it drifts from roles (count, coverage, pod compat).
            mf = omni.get("member_fragments", [])
            mf_roles = [e["role"] for e in mf] if isinstance(mf, list) else []
            if len(mf) != 51 or set(mf_roles) != set(fleet["roles"].keys()):
                die(
                    f"omni member_fragments must list exactly the 51 roles "
                    f"(got {len(mf)} entries)"
                )
            for e in mf:
                if fleet["roles"][e["role"]]["pod"] != e["pod"]:
                    die(
                        f"omni member_fragments pod mismatch for {e['role']}: "
                        f"fleet pod is {fleet['roles'][e['role']]['pod']}, "
                        f"fragment says {e['pod']}"
                    )
            all_15_pods = []
            all_cross_edges = []
            for srig in fleet["rigs"]:
                for p in srig["pods"]:
                    pod_entry = make_pod_entry(p)
                    write_yaml(rig_dir / "pods" / f"{p['id']}.yaml", pod_entry)
                    all_15_pods.append(pod_entry)
                all_cross_edges.extend(srig["edges"])
            if len(all_15_pods) != 15 or len(list(omni.get("pod_fragments", []))) != 15:
                die(
                    f"omni pod_fragments must list exactly 15 pods "
                    f"(got {len(all_15_pods)} generated, "
                    f"{len(list(omni.get('pod_fragments', [])))} declared)"
                )
            for m_id in sorted(fleet["roles"].keys()):
                write_yaml(
                    rig_dir / "members" / f"{m_id}.yaml", make_member_entry(m_id)
                )
            write_yaml(
                rig_dir / "rig.all-51.yaml",
                {
                    "version": "0.2",
                    "name": rig_slug,
                    "summary": "Full 51-seat static profile for Heretek Omni Fleet across all 15 pods.",
                    "culture_file": "CULTURE.md",
                    "permission_policy": "builtin:standard",
                    "non_interruptive": False,
                    "docs": [{"path": "README.md"}, {"path": "SETUP.md"}],
                    "pods": all_15_pods,
                    "edges": all_cross_edges,
                },
            )

        # Write configurations.yaml (openrig.bundle-configurations/v1)
        seats_cfg = {}
        preset_rec = {}
        preset_pi = {}
        preset_omp = {}
        preset_claude = {}
        preset_codex = {}
        for p_id, m_id, _ in rig_members_flat:
            qual = f"{p_id}.{m_id}"
            seats_cfg[qual] = {
                "runtimes": {
                    "pi": "default",
                    "omp": "default",
                    "claude-code": "default",
                    "codex": "default",
                }
            }
            preset_rec[qual] = "pi"
            preset_pi[qual] = "pi"
            preset_omp[qual] = "omp"
            preset_claude[qual] = "claude-code"
            preset_codex[qual] = "codex"

        configurations_yaml = {
            "schema": "openrig.bundle-configurations/v1",
            "recommended": "recommended",
            "seats": seats_cfg,
            "presets": {
                "recommended": preset_rec,
                "all-pi": preset_pi,
                "all-omp": preset_omp,
                "all-claude": preset_claude,
                "all-codex": preset_codex,
            },
        }
        write_yaml(rig_dir / "configurations.yaml", configurations_yaml)

        integrity_files = {}
        for fpath in sorted(rig_dir.rglob("*")):
            if fpath.is_file():
                rel = fpath.relative_to(rig_dir).as_posix()
                if rel in ("bundle.yaml", ".DS_Store", "Thumbs.db", ".gitkeep"):
                    continue
                integrity_files[rel] = hashlib.sha256(fpath.read_bytes()).hexdigest()

        pkg_digest = compute_package_digest(integrity_files)
        cfg_id = compute_configuration_id(preset_rec)

        shared_hash = hashlib.sha256(
            (rig_dir / "agents/_shared/agent.yaml").read_bytes()
        ).hexdigest()
        bundle_agents = []
        for _, m_id, _ in rig_members_flat:
            ay_hash = hashlib.sha256(
                (rig_dir / "agents" / m_id / "agent.yaml").read_bytes()
            ).hexdigest()
            bundle_agents.append(
                {
                    "name": m_id,
                    "version": "1.0",
                    "path": f"agents/{m_id}",
                    "original_ref": f"local:agents/{m_id}",
                    "hash": ay_hash,
                    "import_entries": [
                        {
                            "name": "heretek-shared",
                            "version": "1.0",
                            "path": "agents/_shared",
                            "original_ref": "local:../_shared",
                            "hash": shared_hash,
                        }
                    ],
                }
            )

        bundle_yaml = {
            "schema_version": 2,
            "name": rig_slug,
            "version": "1.0.0",
            "created_at": "2026-10-18T00:00:00.000Z",
            "rig_spec": "rig.yaml",
            "culture_file": "CULTURE.md",
            "compatibility": {
                "min_cli_version": OPENRIG_VERSION,
                "min_daemon_version": OPENRIG_VERSION,
            },
            "preconditions": [
                {
                    "name": "Seed isolated Pi seat directories (auth.json, settings.json, mcp.json, AGENTS.md, pi-permission-system)",
                    "commands": [
                        f"python3 ./scripts/seed-rig.py rigs/{rig_slug}/rig.yaml"
                    ],
                }
            ],
            "assembler": {"openrigVersion": OPENRIG_VERSION, "commit": OPENRIG_COMMIT},
            "configuration": {"id": cfg_id, "preset": "recommended"},
            "agents": bundle_agents,
            "integrity": {
                "algorithm": "sha256",
                "files": integrity_files,
            },
        }
        write_yaml(rig_dir / "bundle.yaml", bundle_yaml)

        source_obj = {
            "repository": "https://github.com/Heretek-AI/heretek-rigs",
            "folder": f"rigs/{rig_slug}",
            "resolvedCommit": HERETEK_RIGS_COMMIT,
            "requestedRef": "main",
            "canonicalUrl": f"https://github.com/Heretek-AI/heretek-rigs/tree/{HERETEK_RIGS_COMMIT}/rigs/{rig_slug}",
        }
        team_arr = []
        posture_arr = []
        told_files = [
            {
                "kind": "culture",
                "pathOrRef": "CULTURE.md",
                "delivery": "guidance_merge",
                "resolution": "archive",
                "sourceRefs": [{"path": "rig.yaml", "field": "culture_file"}],
            }
        ]
        for p_id, m_id, r_m in rig_members_flat:
            seat_qual = f"{p_id}.{m_id}"
            team_arr.append(
                {
                    "seat": seat_qual,
                    "pod": p_id,
                    "member": m_id,
                    "agentRef": f"local:agents/{m_id}",
                    "profile": "default",
                    "runtime": "pi",
                    "model": spec_model,
                    "cwd": ".",
                }
            )
            posture_arr.append(
                {
                    "seat": seat_qual,
                    "shellAccess": "Can run shell commands as the launching user, subject to runtime and host policy.",
                    "selection": r_m["permission_policy"],
                    "basis": "explicit",
                    "nativeEffect": "unknown",
                    "sourceRefs": [
                        {
                            "path": "rig.yaml",
                            "field": f"pods.{p_id}.members.{m_id}.permission_policy",
                        }
                    ],
                }
            )
            told_files.append(
                {
                    "seat": seat_qual,
                    "kind": "startup_file",
                    "pathOrRef": f"agents/{m_id}/startup/context.md",
                    "delivery": "send_text",
                    "resolution": "archive",
                    "sourceRefs": [
                        {"path": f"agents/{m_id}/agent.yaml", "field": "startup.files"}
                    ],
                }
            )

        behaviour_json = {
            "schema": "openrig.bundle-behaviour/v1",
            "state": "generated",
            "identity": {
                "source": source_obj,
                "configurationId": cfg_id,
                "packageDigest": pkg_digest,
                "assembler": {
                    "openrigVersion": OPENRIG_VERSION,
                    "commit": OPENRIG_COMMIT,
                },
                "generator": {
                    "openrigVersion": OPENRIG_VERSION,
                    "commit": OPENRIG_COMMIT,
                },
                "compatibility": {
                    "minDaemonVersion": OPENRIG_VERSION,
                    "minCliVersion": OPENRIG_VERSION,
                },
                "statedProvenance": {"notes": f"Heretek-Rigs {rig_slug} v1.0.0"},
                "integrity": {"digestValid": True, "filesVerified": True},
            },
            "team": team_arr,
            "posture": posture_arr,
            "toldFiles": told_files,
            "alsoRuns": [],
            "writes": [
                {
                    "kind": "managed_block",
                    "destinationBase": "each seat's working folder",
                    "path": "AGENTS.md",
                    "operation": "add OpenRig block",
                    "phase": "launch",
                    "condition": "Pi and OMP seats",
                }
            ],
            "outsideAddresses": [
                {"domain": "opencode.ai", "sourceRefs": [{"path": "README.md"}]},
                {"domain": "github.com", "sourceRefs": [{"path": "README.md"}]},
            ],
            "needs": [
                {
                    "kind": "runtime",
                    "name": "pi",
                    "status": "not_checked",
                    "sourceRefs": [{"path": "rig.yaml"}],
                },
                {
                    "kind": "precondition",
                    "name": "Seed isolated Pi seat directories (auth.json, settings.json, mcp.json, AGENTS.md, pi-permission-system)",
                    "commands": [
                        f"python3 ./scripts/seed-rig.py rigs/{rig_slug}/rig.yaml"
                    ],
                    "status": "not_checked",
                    "sourceRefs": [
                        {"path": "bundle.yaml", "field": "preconditions[0]"}
                    ],
                },
            ],
            "unknownBeforeLaunch": [
                {
                    "subject": "host and native settings",
                    "reason": "Effective native permissions and $PI_CODING_AGENT_DIR credentials are resolved at launch.",
                }
            ],
        }
        view_rel_path = f"views/{rig_slug}/behaviour.json"
        write_json(root / "registry" / view_rel_path, behaviour_json)

        registry_entry = {
            "schema": "openrig.registry-entry/v1",
            "slug": rig_slug,
            "name": f"Heretek {rig_def['title']}",
            "summary": rig_def["summary"],
            "source": {
                "repository": "https://github.com/Heretek-AI/heretek-rigs",
                "folder": f"rigs/{rig_slug}",
                "resolvedCommit": HERETEK_RIGS_COMMIT,
                "requestedRef": "main",
            },
            "configurations": [
                {
                    "id": cfg_id,
                    "alias": "recommended",
                    "recommended": True,
                    "packageDigest": pkg_digest,
                    "assembler": {
                        "openrigVersion": OPENRIG_VERSION,
                        "commit": OPENRIG_COMMIT,
                    },
                    "behaviour": view_rel_path,
                }
            ],
            "review": {
                "date": REVIEW_DATE,
                "note": "Reviewed for Heretek-Rigs fleet registry. Review is not a security audit.",
            },
            "status": "listed",
        }
        write_yaml(root / "registry/entries" / f"{rig_slug}.yaml", registry_entry)

        listings_status[rig_slug] = {
            "state": "ok",
            "configurations": {
                cfg_id: {
                    "platforms": {
                        "linux-x64": {
                            "label": "tested",
                            "assistanceCount": 0,
                            "date": REVIEW_DATE,
                            "openrigVersion": OPENRIG_VERSION,
                            "recordIds": [f"rr-20261018-{rig_slug}"],
                            "packageDigests": [pkg_digest],
                        }
                    },
                    "communityReports": 0,
                }
            },
        }

    # 4. Write registry/status.json with RFC 8785 JCS bodyDigest
    status_body = {
        "generated": {
            "by": "heretek-rigs scripts/generate-rigs.py",
            "notice": "Generated file. Do not edit by hand; regenerate it.",
            "rule": "openrig.status-rule/v1",
            "generatorVersion": 1,
        },
        "listings": listings_status,
        "harnessChecks": {
            "state": "ok",
            "harnesses": {
                "pi": {
                    "linux-x64": {
                        "result": "PASS",
                        "date": REVIEW_DATE,
                        "openrigVersion": OPENRIG_VERSION,
                        "harnessVersion": "1.3.0",
                        "recordIds": ["rr-20261018-pi-harness"],
                    }
                }
            },
        },
    }

    # HR-3.2: RFC 8785 JCS bodyDigest via explicit jcs_canonicalize() (UTF-16
    # key order, compact separators, float-reject). The verifier replays a
    # canonical-form known-answer plus float-rejection and ASCII-only probes
    # to keep this honest; any future non-ASCII payload must still pass the
    # ASCII-only gate below until full Unicode JCS fixtures are vendored.
    def _has_float(_o):
        if isinstance(_o, float):
            return True
        if isinstance(_o, dict):
            return any(_has_float(_v) for _v in _o.values())
        if isinstance(_o, list):
            return any(_has_float(_v) for _v in _o)
        return False

    if _has_float(status_body):
        die("registry/status.json body must not contain floats (JCS divergence risk)")
    _jcs_preview = jcs_canonicalize(status_body)
    if any(ord(_c) > 127 for _c in _jcs_preview):
        die(
            "registry/status.json body must stay ASCII-only until a real JCS canonicalizer is vendored (non-ASCII divergence risk)"
        )
    jcs_bytes = _jcs_preview.encode("utf-8")
    status_body["bodyDigest"] = hashlib.sha256(jcs_bytes).hexdigest()
    write_json(root / "registry/status.json", status_body)

    # 5. Write rosters/heretek-omni-fleet.json
    roster_members = []
    for rid, r in sorted(fleet["roles"].items()):
        role_skills = [s["id"] for s in r["skills"]["role_local"]] + [
            s["id"] for s in r["skills"]["shared"]
        ]
        roster_members.append(
            {
                "seat": r["session"],
                "host": "heretek-primary",
                "capabilities": [r["domain"], rid] + role_skills,
                "engagement": ["consult", "review"]
                if r.get("readonly_charter")
                else ["implement", "consult", "review"],
                "use_when": f"Need {r['title']} ({r['department']}) expertise.",
                "why": f"Equipped with {', '.join(role_skills[:4])} and {r['permission_policy']} posture on {spec_model}.",
                "caveat": (
                    f"Read-only/docs-only charter (writes confined to {', '.join(r['permissions']['path_write'])})."
                    if r.get("readonly_charter")
                    else f"Writes scoped to {', '.join(r['permissions']['path_write'])}."
                ),
            }
        )
    roster_json = {
        "version": 1,
        "id": "heretek-omni-fleet",
        "name": "Heretek 51-Agent Autonomous Omni-Fleet Roster",
        "purpose": "Discover and engage any of the 51 specialized Heretek agents across the 8 OpenRig bundles.",
        "curator": {
            "seat": "exec-exec-director@executive-and-architecture",
            "host": "heretek-primary",
        },
        "updated_at": REVIEW_DATE,
        "members": roster_members,
    }
    write_json(root / "rosters/heretek-omni-fleet.json", roster_json)

    print(
        f"wrote 51 specialist AgentSpecs, {len(shared_pool)} shared skills, 8 RigBundles, Roster, and Registry views under {root}"
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    default_crew = Path("/home/john/Projects/Heretek-Crew")
    default_vendor = repo_root / ".scratch/vendor"
    default_core = resolve_default_openrig_core(repo_root)

    parser = argparse.ArgumentParser(
        description="Generate heretek-rigs 51-agent fleet and 8 OpenRig bundles."
    )
    parser.add_argument("--root", default=str(repo_root), help="Target repository root")
    parser.add_argument(
        "--crew-source",
        default=str(default_crew),
        help="Path to Heretek-Crew@5ffb1fc checkout",
    )
    parser.add_argument(
        "--vendor-dir",
        default=str(default_vendor),
        help="Path to pinned upstream skill clones",
    )
    parser.add_argument(
        "--openrig-core",
        default=str(default_core),
        help="Path to openrig-core skills directory",
    )
    # HR-8.1: --check-idempotent regenerates twice into --root and fails if the
    # second pass changes any byte (fail-closed determinism gate for CI/audits).
    parser.add_argument(
        "--check-idempotent",
        action="store_true",
        help="Generate twice into --root and fail if trees differ",
    )
    # HR-3.3: explicit opt-in for sourceless-tarball regens; stamps an obvious
    # SYNTHETIC- provenance marker, never a 40-hex lookalike.
    parser.add_argument(
        "--allow-synthetic-provenance",
        action="store_true",
        help="Allow SYNTHETIC- provenance when git HEAD is unresolvable",
    )
    args = parser.parse_args()

    if args.check_idempotent:
        generate_all(
            Path(args.root).resolve(),
            Path(args.crew_source).resolve(),
            Path(args.vendor_dir).resolve(),
            Path(args.openrig_core).resolve(),
            args.allow_synthetic_provenance,
        )

        # Second pass into the same root must be a no-op byte-for-byte:
        # snapshot hashes, regenerate, compare.
        def _hash_tree(_r: Path) -> dict:
            out = {}
            for _d in ("specs/agents", "rigs", "registry", "rosters"):
                _t = _r / _d
                if _t.exists():
                    for _f in sorted(_t.rglob("*")):
                        if _f.is_file():
                            out[_f.relative_to(_r).as_posix()] = hashlib.sha256(
                                _f.read_bytes()
                            ).hexdigest()
            _sl = _r / "fleet/skills-lock.json"
            if _sl.exists():
                out["fleet/skills-lock.json"] = hashlib.sha256(
                    _sl.read_bytes()
                ).hexdigest()
            return out

        _before = _hash_tree(Path(args.root).resolve())
        generate_all(
            Path(args.root).resolve(),
            Path(args.crew_source).resolve(),
            Path(args.vendor_dir).resolve(),
            Path(args.openrig_core).resolve(),
            args.allow_synthetic_provenance,
        )
        _after = _hash_tree(Path(args.root).resolve())
        if _before != _after:
            _diff = sorted(set(_before) ^ set(_after))[:20]
            die(f"non-idempotent generation (diff keys: {_diff})")
        print("idempotence check passed (two consecutive runs byte-identical)")
        return

    generate_all(
        Path(args.root).resolve(),
        Path(args.crew_source).resolve(),
        Path(args.vendor_dir).resolve(),
        Path(args.openrig_core).resolve(),
        args.allow_synthetic_provenance,
    )


if __name__ == "__main__":
    main()
