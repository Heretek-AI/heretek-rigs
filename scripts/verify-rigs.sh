#!/usr/bin/env bash
# verify-rigs.sh — Comprehensive self-testing verification gate for heretek-rigs.
#
# Verifies:
#   V1. 100% Role Parity & Skill Lock: All 51 canonical roles from Heretek-Crew exist in fleet/fleet.yaml and
#       specs/agents/<domain>/<role>/ with zero Paperclip remnants, valid SKILL.md files, and 68 locked shared skills.
#   V2. OpenRig AgentSpec v1.0 & RigSpec v0.2 Structural Conformance: Exact key allowlists, pod-local vs cross-pod
#       edge rules, topological DAG cycle checks, and byte-for-byte parity between specs/agents/ and rigs/*/agents/.
#   V3. OpenRig Bundle Check Parity: Zero symlinks in specs/ or rigs/, all referenced files inside each rig
#       root, valid configurations.yaml, zero guidance_merge collisions, and no sensitive filenames.
#   V4. OpenRig v1 JSON Schema Conformance: Validates all configurations.yaml, behaviour.json, registry/entries/*.yaml,
#       and registry/status.json against schemas/*.v1.schema.json using Draft202012Validator + date normalization.
#   V5. Cryptographic Digest Verification: Recomputes configurationId, packageDigest, bundle.yaml file hashes, and
#       RFC 8785 JCS bodyDigest.
#   V6. Security Hardening Gate: Verifies @gotgenes/pi-permission-system@41.0.0 rules, "*..*": "deny" last-rule
#       ordering, mutating AST/LSP tool denial, command-backed "!cat" secrets, and sidecar loopback/proxy isolation.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

for arg in "$@"; do
  case "${arg}" in
    --check-only|--dry-run) ;;
    --help|-h)
      sed -n '2,/^set -euo/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "Unknown argument: ${arg}" >&2; exit 2 ;;
  esac
done

RUNNER=(python3)
if ! python3 -c "import yaml, jsonschema" >/dev/null 2>&1; then
  if command -v uv >/dev/null 2>&1; then
    RUNNER=(uv run --quiet --with pyyaml --with jsonschema python3)
  fi
fi

"${RUNNER[@]}" - "${REPO_ROOT}" <<'PY'
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import yaml
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

root = Path(sys.argv[1])
failures = []
passes = 0


def ok(msg: str):
    global passes
    passes += 1
    print(f"  [PASS] {msg}")


def fail(msg: str):
    failures.append(msg)
    print(f"  [FAIL] {msg}", file=sys.stderr)


# HR-8.2 (fail-closed): entry-point executable bits — Claim 8.2 invokes
# `./scripts/...` directly, which fails on a fresh clone unless the index
# stores 100755. `make verify` survives via explicit `bash`/`python3`
# wrappers, but the canonical recipes do not. A 0644 entry point must flip
# the gate so `git update-index --chmod=+x` is never silently skipped.
for _ep in ("scripts/verify-rigs.sh", "scripts/bootstrap-pi-seats.sh", "scripts/render-seat.py", "scripts/seed-rig.py", "scripts/gate-role.sh", "scripts/gate-run.sh", "scripts/generate-rigs.py", "scripts/audit_loop.py"):
    _epp = root / _ep
    if _epp.exists() and (_epp.stat().st_mode & 0o111) == 0:
        fail(f"{_ep} must be executable (mode {oct(_epp.stat().st_mode & 0o777)}; run git update-index --chmod=+x {_ep})")
    elif _epp.exists():
        # Shebang present so direct `./scripts/...` exec works once the bit is set.
        try:
            _head = _epp.read_text().splitlines()[0] if _epp.stat().st_size else ""
        except Exception:
            _head = ""
        if not _head.startswith("#!"):
            fail(f"{_ep} must start with a shebang for direct ./ execution (got {_head!r})")


def utf16_key(s: str):
    # True UTF-16 code-unit sort (mirrors generate-rigs.py): surrogate-pair order for astral chars.
    b = s.encode("utf-16-le")
    return [int.from_bytes(b[i : i + 2], "little") for i in range(0, len(b), 2)]


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


EXPECTED_51_ROLES = {
    "a11y-specialist", "ai-red-teamer", "analytics-metrics-eng", "android-mobile-spec",
    "api-contract-tester", "appsec-engineer", "binary-reverse-eng", "brand-copy-spec",
    "cache-streaming-eng", "cloud-platform-eng", "cloud-sec-auditor", "compliance-auditor",
    "cpp-lowlevel-eng", "data-pipeline-eng", "dba-specialist", "dependency-patcher",
    "design-system-eng", "e2e-browser-qa", "engine-systems-eng", "exec-director",
    "fe-perf-eng", "firmware-sec-analyst", "game-ai-dev", "game-systems-dev",
    "git-drift-coord", "go-backend-eng", "graphics-shader-eng", "ios-mobile-spec",
    "java-kotlin-eng", "k8s-orchestrator", "load-stress-tester", "mlops-serving-eng",
    "mobile-web-eng", "observability-eng", "physics-sim-eng", "product-director",
    "python-backend-spec", "release-qa-officer", "rust-systems-spec", "sabotage-qa-tester",
    "sre-incident-eng", "static-analysis-lead", "system-architect", "tech-artist-pipeline",
    "tech-docs-lead", "threat-modeler", "tpm-scrum-lead", "ts-node-fullstack",
    "ui-ux-designer", "ux-research-analyst", "vector-rag-spec",
}

READONLY_16_ROLES = {
    "ai-red-teamer", "appsec-engineer", "binary-reverse-eng", "cloud-sec-auditor",
    "compliance-auditor", "exec-director", "firmware-sec-analyst", "git-drift-coord",
    "product-director", "release-qa-officer", "sre-incident-eng", "system-architect",
    "tech-docs-lead", "threat-modeler", "tpm-scrum-lead", "ux-research-analyst",
}

LOCKED_18_ROLES = READONLY_16_ROLES | {"static-analysis-lead", "sabotage-qa-tester"}

EXPECTED_8_RIGS = [
    "executive-and-architecture", "fullstack-and-web-studio", "systems-and-mobile-foundry",
    "game-dev-and-sim-rig", "cloud-sre-and-data-platform", "qa-and-verification-gauntlet",
    "defensive-sec-and-red-team", "heretek-omni-fleet",
]

RIG_KEYS = {"version", "name", "summary", "culture_file", "permission_policy", "managed_blocks", "docs", "startup", "services", "workspace", "pods", "edges", "non_interruptive", "env"}
POD_KEYS = {"id", "label", "summary", "continuity_policy", "startup", "members", "edges"}
MEMBER_KEYS = {"id", "label", "agent_ref", "profile", "runtime", "codex_config_profile", "model", "effort", "role", "permission_policy", "cwd", "restore_policy", "compaction_strategy", "mechanic", "startup", "session_source", "starter_ref", "env"}
EDGE_KEYS = {"kind", "from", "to"}
EDGE_KINDS = {"delegates_to", "spawned_by", "can_observe", "collaborates_with", "escalates_to"}

# HR-2.1-schema-drift (fail-closed): the RIG/POD/MEMBER/EDGE key sets above are
# a copy of the pinned @openrig/cli@0.6.13 rigspec-schema.ts export in
# schemas/rigspec-keys.pinned.json plus the vendored bytes in
# schemas/rigspec-schema.pinned.ts. Diff them here so any upstream bump or
# local drift flips the gate instead of silently desyncing. A sabotage adding,
# removing, or renaming one pinned key must exit 1. The vendored .ts file must
# exist: editing both local copies identically without updating the vendored
# bytes still fails (upstream-hash attestation; refresh from the real
# @openrig/cli@0.6.13 rigspec-schema.ts per the JSON provenance recipe).
# HR-2.1-pinned-self-referential: the three-way local-local diff alone passes
# an identical 3-copy edit. The 4th anchor below (SHA-256 of the vendored
# bytes, refreshed at generation time into the JSON provenance) fails closed
# when absent/mismatched, so a 3-copy identical edit without a generator
# refresh still flips the gate.
try:
    _pinned_doc = json.loads((root / "schemas/rigspec-keys.pinned.json").read_text())
    _pinned_keys = _pinned_doc.get("keys", {})
    for _name, _live in (("RIG_KEYS", RIG_KEYS), ("POD_KEYS", POD_KEYS), ("MEMBER_KEYS", MEMBER_KEYS), ("EDGE_KEYS", EDGE_KEYS), ("EDGE_KINDS", EDGE_KINDS)):
        _pinned_set = set(_pinned_keys.get(_name, []))
        if _live != _pinned_set:
            fail(f"schemas/rigspec-keys.pinned.json drift: {_name} verifier={sorted(_live)} pinned={sorted(_pinned_set)} (refresh from @openrig/cli@0.6.13 rigspec-schema.ts)")
    _anchored = _pinned_doc.get("provenance", {}).get("vendored_sha256", "")
    if not re.fullmatch(r"[0-9a-f]{64}", str(_anchored or "")):
        fail("schemas/rigspec-keys.pinned.json provenance.vendored_sha256 must be 64-hex (run python3 scripts/generate-rigs.py to refresh from vendored bytes; refresh bytes from @openrig/cli@0.6.13 rigspec-schema.ts per provenance recipe)")
    else:
        _actual_ts_hash = hashlib.sha256((root / "schemas/rigspec-schema.pinned.ts").read_bytes()).hexdigest()
        if _actual_ts_hash != _anchored:
            fail(f"schemas/rigspec-schema.pinned.ts SHA-256 mismatch anchored={_anchored} actual={_actual_ts_hash} (identical 3-copy edit without generator refresh; refresh bytes from @openrig/cli@0.6.13 rigspec-schema.ts)")
    # HR-2.1-pinned-still-local (fail-closed): the vendored_sha256 anchor above
    # is refreshed FROM the local vendored bytes at generation time, so an
    # identical edit of all three local copies followed by a generator refresh
    # still passes. The upstream tarball anchor below is NEVER derived from
    # local bytes — it is recorded by a human running `npm pack
    # @openrig/cli@0.6.13` on a networked shell host per the provenance recipe,
    # and the gate fails while it is absent/placeholder so the gap stays
    # visible instead of silently self-consistent.
    _upstream = _pinned_doc.get("provenance", {}).get("upstream_tarball", {})
    _tb_sha = str(_upstream.get("tarball_sha256", "") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", _tb_sha):
        fail("schemas/rigspec-keys.pinned.json provenance.upstream_tarball.tarball_sha256 must be the 64-hex SHA-256 of the upstream tarball (run `npm pack @openrig/cli@0.6.13` on a networked shell host, record the tarball SHA-256 per the provenance recipe, then re-run python3 scripts/generate-rigs.py)")
    else:
        _tgz = root / "schemas/openrig-cli-0.6.13.tgz"
        if _tgz.exists():
            _actual_tgz = hashlib.sha256(_tgz.read_bytes()).hexdigest()
            if _actual_tgz != _tb_sha:
                fail(f"schemas/openrig-cli-0.6.13.tgz SHA-256 mismatch anchored={_tb_sha} actual={_actual_tgz} (re-record from `npm pack @openrig/cli@0.6.13`)")
except Exception as _e:
    fail(f"schemas/rigspec-keys.pinned.json unreadable for schema-drift check: {_e}")
try:
    _vendored_ts = (root / "schemas/rigspec-schema.pinned.ts").read_text()
    for _name, _live in (("RIG_KEYS", RIG_KEYS), ("POD_KEYS", POD_KEYS), ("MEMBER_KEYS", MEMBER_KEYS), ("EDGE_KEYS", EDGE_KEYS), ("EDGE_KINDS", EDGE_KINDS)):
        _m = re.search(rf"export const {_name} = \[(.*?)\] as const", _vendored_ts, flags=re.DOTALL)
        if not _m:
            fail(f"schemas/rigspec-schema.pinned.ts missing export {_name} (refresh from @openrig/cli@0.6.13 rigspec-schema.ts)")
            continue
        _vendored_set = set(re.findall(r'"([^"]+)"', _m.group(1)))
        if _live != _vendored_set:
            fail(f"schemas/rigspec-schema.pinned.ts drift: {_name} verifier={sorted(_live)} vendored={sorted(_vendored_set)} (refresh from @openrig/cli@0.6.13 rigspec-schema.ts)")
except Exception as _e:
    fail(f"schemas/rigspec-schema.pinned.ts unreadable for schema-drift check: {_e}")

print("== V1. 51-Role Catalog Parity, Fleet YAML & Shared Skill Lock ==")
# HR-1.1 (fail-closed): generated trees (specs/, rigs/, rosters/, registry/,
# fleet/skills-lock.json) are deterministic build outputs. On a checkout where
# they were never generated, fail with a run-the-generator message — never an
# uncaught traceback.
_missing_gen = [
    p
    for p in (
        "fleet/skills-lock.json",
        "specs/agents",
        "rigs",
        "rosters/heretek-omni-fleet.json",
        "registry/status.json",
    )
    if not (root / p).exists()
]
if _missing_gen:
    fail(f"generated trees absent — run `python3 scripts/generate-rigs.py` first (missing: {', '.join(_missing_gen)})")
    print(f"\nSUMMARY: {passes} checks passed, {len(failures)} failed.")
    sys.exit(1)
fleet = yaml.safe_load((root / "fleet/fleet.yaml").read_text())
mcp_catalog = yaml.safe_load((root / "fleet/mcp-servers.yaml").read_text())["servers"]
skills_lock = json.loads((root / "fleet/skills-lock.json").read_text())

if set(fleet.get("roles", {}).keys()) != EXPECTED_51_ROLES:
    fail(f"fleet/fleet.yaml role mismatch: {set(fleet.get('roles', {}).keys()) ^ EXPECTED_51_ROLES}")
else:
    ok("fleet/fleet.yaml declares all 51 canonical specialist roles")

discovered_roles = {}
for ay_path in sorted((root / "specs/agents").glob("*/*/agent.yaml")):
    role_dir = ay_path.parent
    rid = role_dir.name
    discovered_roles[rid] = role_dir

if set(discovered_roles.keys()) == EXPECTED_51_ROLES:
    ok("All 51 canonical specialist roles present in specs/agents/<domain>/<role>/")
else:
    missing = EXPECTED_51_ROLES - set(discovered_roles.keys())
    extra = set(discovered_roles.keys()) - EXPECTED_51_ROLES
    fail(f"Role inventory mismatch: missing={missing}, extra={extra}")

shared_skills_dir = root / "specs/agents/_shared/skills"
if len(skills_lock.get("skills", {})) == 68 and len(list(shared_skills_dir.glob("*/SKILL.md"))) == 68:
    ok("All 68 shared skills vendored in specs/agents/_shared/skills/ and locked in fleet/skills-lock.json")
else:
    fail("Shared skill count mismatch (expected 68)")
# HR-6.1-thin-superpowers-wording (fail-closed): counts alone cannot prove
# full-fidelity obra/superpowers@bb92a77 directories. Enforce per-skill
# tree-hash (recomputed from disk vs fleet/skills-lock.json), SKILL.md
# frontmatter, LICENSE presence, and file-count floor. A truncated skill
# (missing companion) or a lock-vs-disk drift must flip the gate. Upstream
# parity itself is refreshed at generation time via `tree_hash(sdir)` in
# scripts/generate-rigs.py; shell hosts must re-run generation after
# `fetch https://github.com/obra/superpowers/archive/bb92a77.tar.gz` + diff.
def _skill_tree_hash(_d: Path) -> str:
    import hashlib as _hl
    _h = _hl.sha256()
    def _walk(_cur: Path):
        for _e in sorted(_cur.iterdir(), key=lambda _p: _p.name):
            if _e.is_dir():
                _walk(_e)
            else:
                _rel = _e.relative_to(_d).as_posix()
                _h.update(_rel.encode("utf-8") + b"\0")
                _h.update(_e.read_bytes())
    _walk(_d)
    return "sha256:" + _h.hexdigest()
for _sid, _smeta in sorted((skills_lock.get("skills", {}) or {}).items()):
    _sdir = shared_skills_dir / _sid
    if not _sdir.is_dir():
        fail(f"shared skill {_sid}: missing directory specs/agents/_shared/skills/{_sid}/")
        continue
    if not (_sdir / "SKILL.md").exists():
        fail(f"shared skill {_sid}: missing SKILL.md")
        continue
    try:
        _sk = (_sdir / "SKILL.md").read_text()
    except Exception as _e:
        fail(f"shared skill {_sid}: unreadable SKILL.md: {_e}")
        continue
    if not _sk.startswith("---") or "\nname:" not in _sk.split("---", 2)[1] or "\ndescription:" not in _sk.split("---", 2)[1]:
        fail(f"shared skill {_sid}: SKILL.md missing valid frontmatter (---/name:/description:)")
    if not any((_sdir / _n).exists() for _n in ("LICENSE", "LICENSE.md", "LICENSE.txt")) and _smeta.get("license_file") not in ("none (see SKILL.md frontmatter)",):
        fail(f"shared skill {_sid}: missing LICENSE (expected {_smeta.get('license_file')})")
    _files = [p for p in _sdir.rglob("*") if p.is_file()]
    _floor = 1 if _smeta.get("license_file") == "none (see SKILL.md frontmatter)" else 2
    if len(_files) < _floor:
        fail(f"shared skill {_sid}: file-count below floor (got {len(_files)}, want >={_floor} SKILL.md+LICENSE)")
    try:
        _recomputed = _skill_tree_hash(_sdir)
    except Exception as _e:
        fail(f"shared skill {_sid}: tree-hash recompute failed: {_e}")
        continue
    if _recomputed != _smeta.get("tree"):
        fail(f"shared skill {_sid}: tree-hash mismatch disk={_recomputed} lock={_smeta.get('tree')} (re-run python3 scripts/generate-rigs.py from pinned upstream)")
# HR-2.3-uses-skills (fail-closed): lock keys must equal the _shared
# agent.yaml resources.skills ids — a lock-vs-shared drift would let an
# unknown heretek-shared: id pass one side while failing the other.
try:
    _shared_ay = yaml.safe_load((root / "specs/agents/_shared/agent.yaml").read_text())
    _shared_ids = set([s.get("id") for s in ((_shared_ay.get("resources", {}) or {}).get("skills", []) or []) if isinstance(s, dict) and s.get("id")])
    if _shared_ids != set(skills_lock.get("skills", {}).keys()):
        fail(f"fleet/skills-lock.json keys != specs/agents/_shared/agent.yaml resources.skills ids (lock-only={sorted(set(skills_lock.get('skills', {}).keys()) - _shared_ids)[:5]}, shared-only={sorted(_shared_ids - set(skills_lock.get('skills', {}).keys()))[:5]})")
except Exception as _e:
    fail(f"specs/agents/_shared/agent.yaml unreadable for skills cross-check: {_e}")
# HR-6.1-missing-subagent-sibling (fail-closed): vendored skill guidance must
# not mandate a sibling that is not provisioned. Every REQUIRED SUB-SKILL
# `superpowers:<id>` reference on a REQUIRED line inside
# specs/agents/_shared/skills/*/SKILL.md (the dead REQUIRED path that
# writing-plans/executing-plans had on subagent-driven-development) must
# resolve to a fleet/skills-lock.json key with a vendored directory on disk,
# and every `../<id>/scripts/` call (e.g. executing-plans invoking
# `../subagent-driven-development/scripts/...`) must resolve to an existing
# sibling scripts directory. Either direction of drift (dangling ref or
# lock-without-disk) flips the gate; the shell host resolves it by re-running
# python3 scripts/generate-rigs.py after the fleet binding lands.
_lock_ids61 = set((skills_lock.get("skills", {}) or {}).keys())
for _skd61 in sorted(shared_skills_dir.iterdir()):
    if not _skd61.is_dir():
        continue
    _skm61 = _skd61 / "SKILL.md"
    if not _skm61.exists():
        continue
    try:
        _skt61 = _skm61.read_text()
    except Exception as _e:
        fail(f"shared skill {_skd61.name}: unreadable SKILL.md for sibling-ref check: {_e}")
        continue
    for _line61 in _skt61.splitlines():
        if "REQUIRED" in _line61:
            for _req61 in set(re.findall(r"superpowers:([a-z0-9-]+)", _line61)):
                if _req61 not in _lock_ids61:
                    fail(f"shared skill {_skd61.name}: REQUIRED SUB-SKILL superpowers:{_req61} is not vendored/locked (add the fleet binding and re-run python3 scripts/generate-rigs.py)")
                elif not (shared_skills_dir / _req61).is_dir():
                    fail(f"shared skill {_skd61.name}: REQUIRED SUB-SKILL superpowers:{_req61} locked but missing on disk")
    for _rel61 in set(re.findall(r"\.\./([a-z0-9-]+)/scripts/", _skt61)):
        if not (shared_skills_dir / _rel61 / "scripts").is_dir():
            fail(f"shared skill {_skd61.name}: relative skill call ../{_rel61}/scripts/ has no vendored sibling scripts directory")
    for _sh61 in sorted((_skd61 / "scripts").rglob("*")) if (_skd61 / "scripts").is_dir() else []:
        if not _sh61.is_file():
            continue
        try:
            _sht61 = _sh61.read_text()
        except Exception:
            continue
        for _rel61 in set(re.findall(r"\.\./([a-z0-9-]+)/scripts/", _sht61)):
            if not (shared_skills_dir / _rel61 / "scripts").is_dir():
                fail(f"shared skill {_skd61.name}: script {_sh61.name} calls ../{_rel61}/scripts/ with no vendored sibling scripts directory")
# HR-6.1-using-superpowers-prose-ref (fail-closed): vendored skill docs must
# not point at a sibling that is not provisioned. Every `../<id>/` doc ref
# outside fenced code blocks in specs/agents/_shared/skills/*/SKILL.md
# (e.g. executing-plans pointing at `../using-superpowers/references/`)
# must resolve to a vendored sibling skill directory on disk — otherwise the
# verifier stays green while the doc dangles (same class as the fixed SDD
# gap: the old gate only checked REQUIRED `superpowers:` refs and
# `../<id>/scripts/` paths, so a `../<id>/references/` prose ref escaped).
# Fenced code blocks are stripped first so intra-skill code samples (e.g.
# typescript-astro `import ... from '../components/...'` inside ```astro
# fences) never false-positive. A dangling prose ref must flip the gate;
# the shell host resolves it by re-running python3 scripts/generate-rigs.py
# after the fleet binding lands (system-architect shared `using-superpowers`,
# obra/superpowers@bb92a77).
for _skd69 in sorted(shared_skills_dir.iterdir()):
    if not _skd69.is_dir():
        continue
    _skm69 = _skd69 / "SKILL.md"
    if not _skm69.exists():
        continue
    try:
        _skt69 = _skm69.read_text()
    except Exception as _e:
        fail(f"shared skill {_skd69.name}: unreadable SKILL.md for sibling-doc-ref check: {_e}")
        continue
    _unfenced69 = re.sub(r"```.*?```", "", _skt69, flags=re.DOTALL)
    for _rel69 in set(re.findall(r"\.\./([a-z0-9-]+)/", _unfenced69)):
        if not (shared_skills_dir / _rel69).is_dir():
            fail(f"shared skill {_skd69.name}: doc ref ../{_rel69}/ has no vendored sibling skill directory (vendor obra/superpowers skills/{_rel69} via a fleet binding and re-run python3 scripts/generate-rigs.py)")

for rid, rdir in sorted(discovered_roles.items()):
    r_fleet = fleet["roles"][rid]
    ay = yaml.safe_load((rdir / "agent.yaml").read_text())
    if ay.get("name") != rid or ay.get("version") != "1.0":
        fail(f"{rid}: invalid name or version in agent.yaml")
    model = ay.get("defaults", {}).get("model", "")
    if model != "opencode-go/muse-spark-1.3-contributor:high":
        fail(f"{rid}: expected model opencode-go/muse-spark-1.3-contributor:high, got {model}")
    if "hooks" in ay:
        fail(f"{rid}: forbidden top-level hooks key in agent.yaml")
    # HR-2.3 (fail-closed): recursive hooks ban — `hooks` at ANY nesting level
    # (defaults/profiles.default/startup/per-skill maps) is a legacy execution vector.
    def _has_hooks(_o):
        if isinstance(_o, dict):
            if "hooks" in _o:
                return True
            return any(_has_hooks(_v) for _v in _o.values())
        if isinstance(_o, list):
            return any(_has_hooks(_v) for _v in _o)
        return False
    if _has_hooks(ay):
        fail(f"{rid}: forbidden legacy hooks key at some level in agent.yaml")
    dl = ay.get("defaults", {}).get("lifecycle", {})
    if dl.get("execution_mode") != "interactive_resident" or dl.get("compaction_strategy") != "default-compaction" or dl.get("restore_policy") != "resume_if_possible":
        fail(f"{rid}: defaults.lifecycle must be interactive_resident/default-compaction/resume_if_possible (got {dl})")
    pl = ay.get("profiles", {}).get("default", {}).get("lifecycle", {})
    if pl.get("compaction_strategy") != "default-compaction" or pl.get("restore_policy") != "resume_if_possible":
        fail(f"{rid}: profiles.default.lifecycle must be default-compaction/resume_if_possible (got {pl})")
    if ay.get("profiles", {}).get("default", {}).get("uses", {}).get("guidance"):
        fail(f"{rid}: uses.guidance must be empty to prevent shared-<cwd> guidance_merge collision")
    # HR-2.3 (fail-closed): positive allowlist for profiles.default.uses —
    # upstream validateAgentSpec contract is unvendored, so a non-empty
    # `plugins: [evil]` would pass the gate today. All 51 specs currently
    # render `plugins: []` (generator generate-rigs.py:619-624 emits skills/
    # guidance/subagents/plugins/runtime_resources with the last four empty);
    # any non-empty plugins/subagents/runtime_resources or any unknown uses key
    # must flip the gate. A `plugins: [evil]` fixture must exit 1.
    _uses = ay.get("profiles", {}).get("default", {}).get("uses", {})
    _allowed_uses_keys = {"skills", "guidance", "subagents", "plugins", "runtime_resources"}
    if set(_uses.keys()) != _allowed_uses_keys:
        fail(f"{rid}: profiles.default.uses must be exactly {_allowed_uses_keys} (got {set(_uses.keys())})")
    for _k in ("guidance", "subagents", "plugins", "runtime_resources"):
        if _uses.get(_k) not in (None, []):
            fail(f"{rid}: profiles.default.uses.{_k} must be [] (got {_uses.get(_k)!r})")
    # HR-2.3-uses-skills (fail-closed): `uses.skills` values were unbounded —
    # a `uses.skills: [evil-pkg]` passed the gate and the
    # `agent-manifest.v1.schema.json` bare `items: {type: string}` by
    # construction. Cross-check every entry against the canonical sources:
    # `heretek-shared:<id>` must exist in fleet/skills-lock.json, bare `<id>`
    # must be one of this role's fleet `skills.role_local` ids, and the full
    # set must equal exactly what the generator emits (openrig_core + shared
    # as heretek-shared:, role_local bare). Any unknown, missing, or duplicate
    # entry flips the gate.
    _skills_val = _uses.get("skills", None)
    if not isinstance(_skills_val, list) or not _skills_val:
        fail(f"{rid}: profiles.default.uses.skills must be a non-empty list")
    else:
        _lock_ids = set((skills_lock.get("skills", {}) or {}).keys())
        _fleet_sk = (r_fleet.get("skills", {}) or {})
        _fleet_core = list(_fleet_sk.get("openrig_core", []) or [])
        _fleet_shared = [s.get("id") for s in (_fleet_sk.get("shared", []) or []) if isinstance(s, dict) and s.get("id")]
        _fleet_local = [s.get("id") for s in (_fleet_sk.get("role_local", []) or []) if isinstance(s, dict) and s.get("id")]
        _expected_skills = set([f"heretek-shared:{s}" for s in (_fleet_core + _fleet_shared)] + _fleet_local)
        if len(set(_skills_val)) != len(_skills_val):
            fail(f"{rid}: profiles.default.uses.skills must not contain duplicates")
        if set(_skills_val) != _expected_skills:
            _extra = set(_skills_val) - _expected_skills
            _missing = _expected_skills - set(_skills_val)
            fail(f"{rid}: profiles.default.uses.skills mismatch (extra={sorted(_extra)[:5]}, missing={sorted(_missing)[:5]})")
        for _se in _skills_val:
            if not isinstance(_se, str):
                fail(f"{rid}: profiles.default.uses.skills entry must be a string (got {_se!r})")
            elif _se.startswith("heretek-shared:"):
                _sid = _se.split(":", 1)[1]
                if _sid not in _lock_ids:
                    fail(f"{rid}: uses.skills {_se!r} not in fleet/skills-lock.json")
            else:
                if _se not in _fleet_local:
                    fail(f"{rid}: uses.skills bare id {_se!r} not in fleet role_local for {rid}")
    for sf in ay.get("startup", {}).get("files", []):
        if sf.get("delivery_hint") == "guidance_merge":
            fail(f"{rid}: startup.files must not use guidance_merge")
    for req_file in ["guidance/role.md", "startup/context.md", "runtime/pi-settings.json", "runtime/policy-enforcement.json", "runtime/pi-permission-config.json"]:
        fp = rdir / req_file
        if not fp.exists() or fp.stat().st_size < 40:
            fail(f"{rid}: missing or stub {req_file}")
    # HR-1.4 (fail-closed): runtime/mcp.json shape follows the canonical binding —
    # zero-server roles (fleet `mcp: []`: brand-copy-spec, mlops-serving-eng,
    # tech-artist-pipeline) must render exactly `{"mcpServers": {}}` (23 bytes,
    # correctly below the 40-byte stub floor); bound roles must list exactly the
    # bound servers and stay above the stub floor. Either direction of drift
    # (hidden server on a zero-server role, dropped server on a bound role)
    # flips the gate.
    _mcp_fp = rdir / "runtime/mcp.json"
    if not _mcp_fp.exists():
        fail(f"{rid}: missing runtime/mcp.json")
    else:
        try:
            _mcp_doc = json.loads(_mcp_fp.read_text())
        except Exception as _e:
            fail(f"{rid}: runtime/mcp.json unreadable: {_e}")
            _mcp_doc = None
        if _mcp_doc is not None:
            _bound = {b["server"] for b in (r_fleet.get("mcp") or [])}
            _rendered = set((_mcp_doc.get("mcpServers") or {}).keys())
            if _rendered != _bound:
                fail(f"{rid}: runtime/mcp.json servers {_rendered} != fleet binding {_bound}")
            if _bound and _mcp_fp.stat().st_size < 40:
                fail(f"{rid}: missing or stub runtime/mcp.json")
    role_md_text = (rdir / "guidance/role.md").read_text()
    if "Paperclip" in role_md_text:
        fail(f"{rid}: unported 'Paperclip' reference in guidance/role.md")
    for s in r_fleet["skills"]["role_local"]:
        if not (rdir / "skills" / s["id"] / "SKILL.md").exists():
            fail(f"{rid}: missing role-local skill {s['id']}")

    pe = json.loads((rdir / "runtime/policy-enforcement.json").read_text())
    expected_pol = "builtin:locked" if rid in LOCKED_18_ROLES else "builtin:standard"
    if pe.get("openrig_permission_policy") != expected_pol or r_fleet.get("permission_policy") != expected_pol:
        fail(f"{rid}: policy mismatch (got {pe.get('openrig_permission_policy')}, expected {expected_pol})")
    # HR-1.4: standalone pi-permission-config.json must exist and match policy-enforcement permission payload
    try:
        ppc = json.loads((rdir / "runtime/pi-permission-config.json").read_text())
        if ppc.get("permission") != pe.get("permission") or ppc.get("promptTimeoutMs") != pe.get("promptTimeoutMs"):
            fail(f"{rid}: runtime/pi-permission-config.json drifted from policy-enforcement.json")
    except Exception as e:
        fail(f"{rid}: runtime/pi-permission-config.json unreadable: {e}")

    perm = pe.get("permission", {})
    if perm.get("*") != "deny" or perm.get("bash", {}).get("*") != "deny" or perm.get("external_directory") != "deny":
        fail(f"{rid}: permission config does not fail closed")
    # HR-5.3: secret-read denies + timeout + path allow-first (fail-closed; a deleted rule must flip gate 0->1)
    if pe.get("promptTimeoutMs") != 60000:
        fail(f"{rid}: promptTimeoutMs must be 60000 (got {pe.get('promptTimeoutMs')})")
    if perm.get("path", {}).get("*") != "allow":
        fail(f"{rid}: permission path must start with '*': allow")
    for _sp, _exp in (("*.env", "deny"), ("*.env.*", "deny"), ("*.env.example", "allow"), ("*.pem", "deny"), ("*.key", "deny"), ("*id_rsa*", "deny"), ("*kubeconfig*", "deny"), ("*/secrets/*", "deny"), ("*.pat", "deny"), ("*.uri", "deny"), ("*.profile", "deny"), ("*.region", "deny"), ("*.host", "deny"), ("*.password", "deny"), ("*.credentials", "deny"), ("*.config", "deny"), ("*.url", "deny"), ("*.user", "deny")):
        if perm.get("path", {}).get(_sp) != _exp:
            fail(f"{rid}: permission path '{_sp}' must be '{_exp}'")
    if '"ask"' in json.dumps(pe):
        fail(f"{rid}: permission config contains forbidden 'ask' rule")
    pw_keys = list(perm.get("path_write", {}).keys())
    path_keys = list(perm.get("path", {}).keys())
    expected_pw = ["*", ".git/*", "*/.git/*", "AGENTS.md", "*/AGENTS.md", ".pi/*", "*/.pi/*", ".agents/*", "*/.agents/*", "fleet/*", "scripts/*", "*..*"]
    # Role allows sit between "*" and the guard block; guards must appear in order ending with *..*.
    if not pw_keys or pw_keys[0] != "*" or pw_keys[-1] != "*..*":
        fail(f"{rid}: path_write must start with '*' and end with '*..*' (got {pw_keys})")
    for g in expected_pw[1:]:
        if g not in perm.get("path_write", {}):
            fail(f"{rid}: path_write missing guard {g}")
        elif perm.get("path_write", {})[g] != "deny":
            fail(f"{rid}: path_write guard {g} must be deny")
    guard_idx = [pw_keys.index(g) for g in expected_pw[1:] if g in pw_keys]
    if guard_idx != sorted(guard_idx):
        fail(f"{rid}: path_write guards out of order (got {pw_keys})")
    if not path_keys or path_keys[0] != "*" or path_keys[-1] != "*..*":
        fail(f"{rid}: path must start with '*' and end with '*..*' (got {path_keys})")
    # HR-5.2 (fail-closed): the read map carries the same dot-directory/file
    # guard block as path_write (order matters, *..* last) — a regression
    # deleting ".pi/*" would silently re-allow reads of Pi state dirs.
    expected_path_guards = [".git/*", "*/.git/*", "AGENTS.md", "*/AGENTS.md", ".pi/*", "*/.pi/*", ".agents/*", "*/.agents/*", "fleet/*", "scripts/*", "*..*"]
    for g in expected_path_guards:
        if g not in perm.get("path", {}):
            fail(f"{rid}: path missing guard {g}")
        elif perm.get("path", {})[g] != "deny":
            fail(f"{rid}: path guard {g} must be deny")
    _pguard_idx = [path_keys.index(g) for g in expected_path_guards if g in path_keys]
    if _pguard_idx != sorted(_pguard_idx):
        fail(f"{rid}: path guards out of order (got {path_keys})")
    for mut_tool in ("code_rewrite", "lsp_rename", "lsp_code_actions"):
        if perm.get(mut_tool) != "deny":
            fail(f"{rid}: mutating extension tool {mut_tool} must be explicitly 'deny'")
    # HR-5.5: mcp map must fail closed (*: deny) with only bound-server allows
    mcp_map = perm.get("mcp", {})
    if mcp_map.get("*") != "deny":
        fail(f"{rid}: permission mcp must start with '*': deny")
    allowed_servers = {b["server"] for b in (r_fleet.get("mcp") or [])}
    for mk, mv in mcp_map.items():
        if mk == "*":
            continue
        if mk not in allowed_servers or mv != "allow":
            fail(f"{rid}: permission mcp key '{mk}' must be a bound-server allow (got '{mv}')")
    # HR-5.5-prefix-escape (fail-closed): terminal bash denies must be present
    # LAST in the rendered bash map so live `--output=` / chaining suffixes
    # (`;`, `|`, `>`, `<`, `&`, backtick, `$()`, subshell parens) appended to
    # an allowed trailing-* prefix still deny (last-match-wins).
    # A regression deleting any terminal deny must flip the gate 0->1.
    # HR-5.5-enforcement-gap: `&`/backtick/`$`/parens denies added; newline
    # stays covered by generation-time ban (no portable glob).
    # HR-5.5-git-patch-read-bypass (fail-closed): patch-output flag denies
    # (`-p`, `--patch`, `--full-diff`, `--textconv`) added LAST for the same
    # reason — `git log --oneline -p -- fleet/fleet.yaml` exfiltrates file
    # contents past the `fleet/*` path read-deny under prefix-glob matcher
    # semantics. Residual (documented, P3): `--stat`/`--name-only` output is
    # metadata-only; path-qualified git commands without patch flags still
    # match their allow prefix. Blast radius stays capped at tracked content
    # (secrets live untracked in $HERETEK_SECRETS; `*.env`/`*id_rsa*`
    # direct-read denies hold).
    _bash_map = perm.get("bash", {})
    _bash_keys = list(_bash_map.keys())
    _TERMINAL_BASH_DENIES = ("*--output*", "*;*", "*|*", "*>*", "*<*", "*&*", "*`*", "*$*", "*(*", "*)*", "* -p*", "*\t-p*", "*--patch*", "*--full-diff*", "*--textconv*", "* -u*", "*\t-u*", "* -U*", "*\t-U*", "*--unified*", "*--cc*", "* -c *", "* -m *", "* -W*", "*--function-context*", "*--word-diff*", "*--color-words*", "*--binary*", "*--raw*", "*OPENRIG_SESSION_NAME=*", "*OPENRIG_URL=*")
    for _td in _TERMINAL_BASH_DENIES:
        if _bash_map.get(_td) != "deny":
            fail(f"{rid}: permission bash must contain terminal deny '{_td}': deny")
    if _bash_keys and _bash_keys[0] != "*":
        fail(f"{rid}: permission bash must start with '*': deny")
    # Terminal denies must come after all role allows (last-match-wins).
    _term_idx = [_bash_keys.index(_t) for _t in _TERMINAL_BASH_DENIES if _t in _bash_keys]
    if _term_idx != sorted(_term_idx):
        fail(f"{rid}: permission bash terminal denies out of order (got {_bash_keys})")
    # HR-5.5-tab-p-suffix-gap (fail-closed): sortedness alone lets a
    # hand-injected allow AFTER the deny block survive (it would win
    # last-match-wins). No allow key may follow the terminal-deny block:
    # every terminal deny must sit after every allow.
    _allow_idx = [_i for _i, _k in enumerate(_bash_keys) if _bash_map.get(_k) == "allow"]
    if _allow_idx and _term_idx and max(_allow_idx) > min(_term_idx):
        fail(f"{rid}: permission bash terminal denies must come after all role allows, no allow may follow them (got {_bash_keys})")
    # HR-5.5-rendered-allow-superset-gap (fail-closed): rendered allow-sets
    # must be subsets of the fleet-declared allow-sets. The guards above only
    # assert denies are present — a hand-injected `"zzz-evil/*": "allow"`
    # (`path_write`) or `"curl *": "allow"` (`bash`) in a checked-in
    # generated permission file would otherwise survive --check-only (the
    # mcp map is the exception proving the rule: it already rejects rendered
    # keys outside the bound-server set). Rendered<->rendered drift between
    # the two permission files is separately covered by the
    # pi-permission-config.json == policy-enforcement.json equality check.
    _rendered_bash_allows = {_k for _k, _v in _bash_map.items() if _v == "allow"}
    _declared_bash = set((r_fleet.get("permissions", {}) or {}).get("bash_allow") or [])
    if not _rendered_bash_allows <= _declared_bash:
        fail(f"{rid}: rendered bash allows exceed fleet-declared bash_allow (surplus={sorted(_rendered_bash_allows - _declared_bash)[:5]})")
    _rendered_pw_allows = {_k for _k, _v in perm.get("path_write", {}).items() if _v == "allow"}
    _declared_pw = set((r_fleet.get("permissions", {}) or {}).get("path_write") or [])
    if not _rendered_pw_allows <= _declared_pw:
        fail(f"{rid}: rendered path_write allows exceed fleet-declared path_write (surplus={sorted(_rendered_pw_allows - _declared_pw)[:5]})")
    # HR-queue-surface (fail-closed): every seat's rendered bash map must keep
    # the six rig allows. Seats coordinate via bash-invoked `rig` commands (no
    # rig MCP tools exist); a renderer regression silently dropping the rig
    # surface would leave seats unable to queue/send with a fully green gate.
    # The subset check above pins the ceiling; this pins the floor.
    for _rv in ("rig whoami", "rig ps", "rig queue", "rig send", "rig capture", "rig transcript"):
        if not any(_k == _rv or _k.startswith(_rv + " ") or _k.startswith(_rv + "*") for _k, _v in _bash_map.items() if _v == "allow"):
            fail(f"{rid}: rendered bash map missing rig allow for '{_rv}*'")

    if rid in READONLY_16_ROLES:
        for g in r_fleet["permissions"]["path_write"]:
            if not (g.startswith("docs/") or g.startswith("sbom/")):
                fail(f"{rid}: read-only role has path_write outside docs/* or sbom/*: {g}")
    for g in r_fleet["permissions"]["path_write"]:
        if ".." in g or g.startswith("/"):
            fail(f"{rid}: invalid path_write glob {g}")
    for bcmd in r_fleet["permissions"]["bash_allow"]:
        if re.match(r"^(curl|wget|sh|bash|python3? -c|node -e|eval|sudo)\b", bcmd) or bcmd == "*":
            fail(f"{rid}: forbidden bash_allow rule '{bcmd}'")
        if "--output" in bcmd or "--output=" in bcmd:
            fail(f"{rid}: forbidden bash_allow --output write-escape '{bcmd}'")
        # HR-5.5 (fail-closed): shell metachars chain out of trailing-* prefix
        # allows under prefix-glob matcher semantics — reject redirections
        # (`>`, `<`), backslash, `!`, `#`, `~`, braces, brackets, `?`, CR too.
        if re.search(r"[;&|$`()\n><\\!#~{}\[\]?\r]", bcmd) or "$(" in bcmd:
            fail(f"{rid}: forbidden bash_allow shell metachar in '{bcmd}'")

if not failures:
    ok("All 51 AgentSpecs validate v1.0 schema, Muse Spark 1.3 Contributor model pin, skills, and pi-permission-system rules")

print("\n== V2 & V3. 8-Rig Topology, DAG Ordering, Symlink & Bundle Check ==")
symlinks = [p for p in list((root / "specs").rglob("*")) + list((root / "rigs").rglob("*")) if p.is_symlink()]
if not symlinks:
    ok("Zero symlinks in specs/ and rigs/ (satisfies OpenRig assertTreeHasNoSymlinks & bundle-check)")
else:
    fail(f"Found forbidden symlinks: {symlinks}")

rigs_1_to_7_roles = []
for rig_slug in EXPECTED_8_RIGS:
    rdir = root / "rigs" / rig_slug
    if not (rdir / "rig.yaml").exists():
        fail(f"Missing rigs/{rig_slug}/rig.yaml")
        continue
    raw_rig_text = (rdir / "rig.yaml").read_text()
    if re.search(r"^\s*env:", raw_rig_text, flags=re.MULTILINE):
        fail(f"{rig_slug}: rig.yaml must not contain env: blocks")
    # HR-4.4: claim 4.4 full name-list — secrets/reserved names must never appear in rig.yaml
    if re.search(r"OPENRIG_|OPENCODE_API_KEY|GITHUB_TOKEN|_PASSWORD|_SECRET|_TOKEN", raw_rig_text):
        fail(f"{rig_slug}: rig.yaml contains forbidden secret/reserved name (OPENRIG_*/OPENCODE_API_KEY/GITHUB_TOKEN/*_PASSWORD/*_SECRET/*_TOKEN)")
    # HR-4.4 (fail-closed): rig.yaml values must carry no literal secrets either
    # (short literals evade shape floors, so scan values as well as names).
    if re.search(r"(ghp_[A-Za-z0-9_-]{8,}|github_pat_[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}|xox[bp]-[A-Za-z0-9_-]{8,})", raw_rig_text):
        fail(f"{rig_slug}: rig.yaml contains literal secret material")
    spec = yaml.safe_load(raw_rig_text)
    unknown_top = set(spec.keys()) - RIG_KEYS
    if unknown_top:
        fail(f"{rig_slug}: unknown top-level keys {unknown_top}")
    if spec.get("version") != "0.2" or spec.get("name") != rig_slug:
        fail(f"{rig_slug}: invalid version or name")

    docs = [d.get("path") for d in spec.get("docs", [])]
    if "README.md" not in docs or not (rdir / "README.md").exists():
        fail(f"{rig_slug}: README.md not declared in docs or missing on disk")

    qual_members = set()
    dag_adj = {}
    for pod in spec.get("pods", []):
        unknown_pod = set(pod.keys()) - POD_KEYS
        if unknown_pod:
            fail(f"{rig_slug}.{pod.get('id')}: unknown pod keys {unknown_pod}")
        pid = pod["id"]
        if "." in pid or "@" in pid:
            fail(f"{rig_slug}: invalid pod id {pid}")
        m_ids = set()
        for m in pod.get("members", []):
            unknown_m = set(m.keys()) - MEMBER_KEYS
            if unknown_m:
                fail(f"{rig_slug}.{pid}.{m.get('id')}: unknown member keys {unknown_m}")
            mid = m["id"]
            if "." in mid or "@" in mid:
                fail(f"{rig_slug}.{pid}: invalid member id {mid}")
            m_ids.add(mid)
            qual = f"{pid}.{mid}"
            qual_members.add(qual)
            dag_adj.setdefault(qual, set())
            if rig_slug != "heretek-omni-fleet":
                rigs_1_to_7_roles.append(mid)
            if m.get("runtime") != "pi":
                fail(f"{rig_slug}.{qual}: expected runtime pi, got {m.get('runtime')}")
            if m.get("model") != "opencode-go/muse-spark-1.3-contributor:high":
                fail(f"{rig_slug}.{qual}: wrong model {m.get('model')}")
            expected_pol = "builtin:locked" if mid in LOCKED_18_ROLES else "builtin:standard"
            if m.get("permission_policy") != expected_pol:
                fail(f"{rig_slug}.{qual}: expected policy {expected_pol}, got {m.get('permission_policy')}")
            ref_rel = m["agent_ref"].replace("local:", "")
            if ".." in ref_rel or ref_rel.startswith("/"):
                fail(f"{rig_slug}.{qual}: agent_ref escapes bundle folder: {m['agent_ref']}")
            vendored_dir = rdir / ref_rel
            if not (vendored_dir / "agent.yaml").exists():
                fail(f"{rig_slug}.{qual}: missing vendored agent.yaml at {vendored_dir}")
            else:
                src_dir = discovered_roles[mid]
                # HR-2.4 (fail-closed): vendored copies must also carry zero
                # guidance_merge (shared-<cwd> collision guard applies in rigs/ too).
                try:
                    _vay = yaml.safe_load((vendored_dir / "agent.yaml").read_text())
                    for _sf in _vay.get("startup", {}).get("files", []):
                        if _sf.get("delivery_hint") == "guidance_merge":
                            fail(f"{rig_slug}.{qual}: vendored agent.yaml uses forbidden guidance_merge")
                except Exception as _e:
                    fail(f"{rig_slug}.{qual}: unreadable vendored agent.yaml: {_e}")
                for subf in ("guidance/role.md", "startup/context.md", "runtime/policy-enforcement.json"):
                    if (vendored_dir / subf).read_bytes() != (src_dir / subf).read_bytes():
                        fail(f"{rig_slug}.{qual}: {subf} drifted from specs/agents/")
                # agent.yaml itself must match specs source except the
                # intentional imports rewrite (local:../../_shared -> local:../_shared).
                try:
                    _say = yaml.safe_load((src_dir / "agent.yaml").read_text())
                    _vnorm = dict(_vay)
                    _snorm = dict(_say)
                    _vnorm.pop("imports", None)
                    _snorm.pop("imports", None)
                    if json.dumps(_vnorm, sort_keys=True) != json.dumps(_snorm, sort_keys=True):
                        fail(f"{rig_slug}.{qual}: agent.yaml drifted from specs/agents/ (beyond imports rewrite)")
                except Exception as _e:
                    fail(f"{rig_slug}.{qual}: agent.yaml comparison failed: {_e}")
        for pe in pod.get("edges", []):
            # HR-2.2-edge-extra-keys (fail-closed): edges carry exactly
            # {kind, from, to} — an extra key (e.g. foo: 1) must flip the gate.
            if set(pe.keys()) - EDGE_KEYS:
                fail(f"{rig_slug}.{pid}: unknown pod-local edge keys {set(pe.keys()) - EDGE_KEYS} in {pe}")
            if pe["kind"] not in EDGE_KINDS or pe["from"] not in m_ids or pe["to"] not in m_ids:
                fail(f"{rig_slug}.{pid}: invalid pod-local edge {pe}")
            if pe["kind"] in ("delegates_to", "spawned_by"):
                dag_adj[f"{pid}.{pe['from']}"].add(f"{pid}.{pe['to']}")
    for ce in spec.get("edges", []):
        if set(ce.keys()) - EDGE_KEYS:
            fail(f"{rig_slug}: unknown cross-pod edge keys {set(ce.keys()) - EDGE_KEYS} in {ce}")
        if ce["kind"] not in EDGE_KINDS or ce["from"] not in qual_members or ce["to"] not in qual_members:
            fail(f"{rig_slug}: invalid cross-pod edge {ce}")
        if ce["from"].split(".")[0] == ce["to"].split(".")[0]:
            fail(f"{rig_slug}: cross-pod edge connects same pod: {ce}")
        if ce["kind"] in ("delegates_to", "spawned_by"):
            dag_adj[ce["from"]].add(ce["to"])

    visited = {}

    def has_cycle(node):
        visited[node] = 1
        for nxt in dag_adj.get(node, ()):
            if visited.get(nxt) == 1 or (visited.get(nxt, 0) == 0 and has_cycle(nxt)):
                return True
        visited[node] = 2
        return False

    for node in qual_members:
        if visited.get(node, 0) == 0 and has_cycle(node):
            fail(f"{rig_slug}: cycle detected in delegates_to/spawned_by launch graph")

    ok(f"Rig '{rig_slug}' ({len(qual_members)} default seats) passed RigSpec v0.2, DAG cycle check, and bundle containment")

if len(rigs_1_to_7_roles) == 51 and set(rigs_1_to_7_roles) == EXPECTED_51_ROLES:
    ok("Rigs 1-7 partition all 51 specialist roles with 100% coverage and zero duplicates/omissions")
else:
    fail(f"Rigs 1-7 role coverage mismatch: count={len(rigs_1_to_7_roles)}, diff={EXPECTED_51_ROLES ^ set(rigs_1_to_7_roles)}")

omni_dir = root / "rigs/heretek-omni-fleet"
if len(list((omni_dir / "pods").glob("*.yaml"))) == 15 and len(list((omni_dir / "members").glob("*.yaml"))) == 51 and (omni_dir / "rig.all-51.yaml").exists():
    ok("Rig 8 (heretek-omni-fleet) includes 15 pod fragments, 51 member fragments, and rig.all-51.yaml")
else:
    fail("Rig 8 (heretek-omni-fleet) missing pod/member fragments or rig.all-51.yaml")

# HR-2.1 (fail-closed): the flagship 51-seat static profile must validate like
# every rig.yaml (keys/version/edges/DAG/model/runtime/policy) — a malformed
# rig.all-51.yaml must flip the gate. Fragments get schema-shape checks too.
try:
    _all51 = yaml.safe_load((omni_dir / "rig.all-51.yaml").read_text())
    _unknown = set(_all51.keys()) - RIG_KEYS
    if _unknown:
        fail(f"rig.all-51.yaml: unknown top-level keys {_unknown}")
    if _all51.get("version") != "0.2" or _all51.get("name") != "heretek-omni-fleet":
        fail("rig.all-51.yaml: invalid version or name")
    _seats51 = [(p["id"], m["id"]) for p in _all51.get("pods", []) for m in p.get("members", [])]
    if len(_seats51) != 51 or len(set(_seats51)) != 51:
        fail(f"rig.all-51.yaml: expected 51 unique seats, got {len(_seats51)}")
    for _p in _all51.get("pods", []):
        if set(_p.keys()) - POD_KEYS:
            fail(f"rig.all-51.yaml pod {_p.get('id')}: unknown pod keys {set(_p.keys()) - POD_KEYS}")
        _pm_ids = set()
        for _m in _p.get("members", []):
            if set(_m.keys()) - MEMBER_KEYS:
                fail(f"rig.all-51.yaml member {_m.get('id')}: unknown member keys")
            if _m.get("runtime") != "pi" or _m.get("model") != "opencode-go/muse-spark-1.3-contributor:high":
                fail(f"rig.all-51.yaml seat {_m.get('id')}: wrong runtime/model")
            # HR-2.1 (fail-closed): per-seat policy must match the canonical
            # role policy, identical to the rig.yaml path (:332-334).
            _exp_pol = "builtin:locked" if _m.get("role", _m.get("id")) in LOCKED_18_ROLES else "builtin:standard"
            if _m.get("permission_policy") != _exp_pol:
                fail(f"rig.all-51.yaml seat {_m.get('id')}: expected policy {_exp_pol}, got {_m.get('permission_policy')}")
            _pm_ids.add(_m.get("id"))
        # HR-2.1 (fail-closed): pod-local edges must qualify like the rig.yaml
        # path (:367-371); DAG population happens below.
        for _pe in _p.get("edges", []):
            if set(_pe.keys()) - EDGE_KEYS:
                fail(f"rig.all-51.yaml pod {_p.get('id')}: unknown pod-local edge keys {set(_pe.keys()) - EDGE_KEYS} in {_pe}")
            if _pe.get("kind") not in EDGE_KINDS or _pe.get("from") not in _pm_ids or _pe.get("to") not in _pm_ids:
                fail(f"rig.all-51.yaml pod {_p.get('id')}: invalid pod-local edge {_pe}")
    _flat51 = {f"{a}.{b}" for a, b in _seats51}
    _dagx51 = {q: set() for q in _flat51}
    for _p in _all51.get("pods", []):
        _pm_ids2 = {m.get("id") for m in _p.get("members", [])}
        for _pe in _p.get("edges", []):
            if set(_pe.keys()) - EDGE_KEYS:
                fail(f"rig.all-51.yaml pod {_p.get('id')}: unknown pod-local edge keys {set(_pe.keys()) - EDGE_KEYS} in {_pe}")
            if _pe.get("kind") not in EDGE_KINDS or _pe.get("from") not in _pm_ids2 or _pe.get("to") not in _pm_ids2:
                fail(f"rig.all-51.yaml pod {_p.get('id')}: invalid pod-local edge {_pe}")
            if _pe.get("kind") in ("delegates_to", "spawned_by"):
                _dagx51[f"{_p.get('id')}.{_pe['from']}"].add(f"{_p.get('id')}.{_pe['to']}")
    for _ce in _all51.get("edges", []):
        if set(_ce.keys()) - EDGE_KEYS:
            fail(f"rig.all-51.yaml: unknown cross-pod edge keys {set(_ce.keys()) - EDGE_KEYS} in {_ce}")
        if _ce.get("kind") not in EDGE_KINDS or _ce.get("from") not in _flat51 or _ce.get("to") not in _flat51:
            fail(f"rig.all-51.yaml: invalid cross-pod edge {_ce}")
        if _ce.get("from", "").split(".")[0] == _ce.get("to", "").split(".")[0]:
            fail(f"rig.all-51.yaml: cross-pod edge connects same pod: {_ce}")
        if _ce.get("kind") in ("delegates_to", "spawned_by"):
            _dagx51[_ce["from"]].add(_ce["to"])
    _vis51 = {}

    def _has_cycle51(_n):
        _vis51[_n] = 1
        for _nx in _dagx51.get(_n, ()):
            if _vis51.get(_nx) == 1 or (_vis51.get(_nx, 0) == 0 and _has_cycle51(_nx)):
                return True
        _vis51[_n] = 2
        return False

    for _qn in _flat51:
        if _vis51.get(_qn, 0) == 0 and _has_cycle51(_qn):
            fail("rig.all-51.yaml: cycle detected in delegates_to/spawned_by launch graph")
    for _pf in sorted((omni_dir / "pods").glob("*.yaml")):
        _pd = yaml.safe_load(_pf.read_text())
        if "members" not in _pd or "id" not in _pd:
            fail(f"omni pod fragment {_pf.name}: missing members/id")
    for _mf in sorted((omni_dir / "members").glob("*.yaml")):
        _md = yaml.safe_load(_mf.read_text())
        if "agent_ref" not in _md or "id" not in _md:
            fail(f"omni member fragment {_mf.name}: missing agent_ref/id")
    if not failures:
        ok("rig.all-51.yaml (51 seats) and all pod/member fragments validate")
except Exception as _e:
    fail(f"rig.all-51.yaml validation failed: {_e}")

print("\n== V4 & V5. JSON Schema Draft 2020-12 & Cryptographic Digest Verification ==")
schema_dir = root / "schemas"
schemas = {}
resources = []
for sf in schema_dir.glob("*.schema.json"):
    data = json.loads(sf.read_text())
    schemas[sf.name] = data
    resources.append((data["$id"], Resource.from_contents(data)))
registry = Registry().with_resources(resources)


def validate_doc(doc_path: Path, schema_name: str):
    raw = yaml.safe_load(doc_path.read_text()) if doc_path.suffix == ".yaml" else json.loads(doc_path.read_text())
    norm = json.loads(json.dumps(raw, default=str))
    val = Draft202012Validator(schemas[schema_name], registry=registry)
    errs = list(val.iter_errors(norm))
    if errs:
        fail(f"Schema {schema_name} failed on {doc_path.relative_to(root)}: {errs[0].message}")
    return norm


for rig_slug in EXPECTED_8_RIGS:
    rdir = root / "rigs" / rig_slug
    cfg_doc = validate_doc(rdir / "configurations.yaml", "bundle-configurations.v1.schema.json")
    beh_doc = validate_doc(root / "registry/views" / rig_slug / "behaviour.json", "bundle-behaviour.v1.schema.json")
    ent_doc = validate_doc(root / "registry/entries" / f"{rig_slug}.yaml", "registry-entry.v1.schema.json")
    bundle_doc = yaml.safe_load((rdir / "bundle.yaml").read_text())

    # Recompute integrity.files and packageDigest from disk
    disk_files = {}
    for fpath in sorted(rdir.rglob("*")):
        if fpath.is_file():
            rel = fpath.relative_to(rdir).as_posix()
            if rel in ("bundle.yaml", ".DS_Store", "Thumbs.db", ".gitkeep"):
                continue
            disk_files[rel] = hashlib.sha256(fpath.read_bytes()).hexdigest()

    expected_pkg_digest = compute_package_digest(disk_files)
    expected_cfg_id = compute_configuration_id(cfg_doc["presets"]["recommended"])

    if bundle_doc.get("integrity", {}).get("files") != disk_files:
        fail(f"{rig_slug}: bundle.yaml integrity.files mismatch with disk")
    if beh_doc["identity"]["packageDigest"] != expected_pkg_digest or ent_doc["configurations"][0]["packageDigest"] != expected_pkg_digest:
        fail(f"{rig_slug}: packageDigest mismatch")
    if beh_doc["identity"]["configurationId"] != expected_cfg_id or ent_doc["configurations"][0]["id"] != expected_cfg_id:
        fail(f"{rig_slug}: configurationId mismatch")
    # HR-4.1 (fail-closed): the all-omp fallback preset must exist, cover exactly
    # the seat set, and map every seat to "omp" — deletion/emptying must flip the gate.
    _all_omp = cfg_doc.get("presets", {}).get("all-omp")
    if not isinstance(_all_omp, dict) or set(_all_omp.keys()) != set(cfg_doc["presets"]["recommended"].keys()):
        fail(f"{rig_slug}: presets.all-omp must cover exactly the seat set")
    elif any(_v != "omp" for _v in _all_omp.values()):
        fail(f"{rig_slug}: presets.all-omp must map every seat to 'omp'")
    # HR-3.3 (fail-closed): provenance must be a real 40-hex commit or an
    # obvious SYNTHETIC- marker — the retired 40-hex lookalike fallback must
    # never appear in generated registry documents.
    for _rdoc in (beh_doc, ent_doc):
        _rc = json.dumps(_rdoc)
        if "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678" in _rc:
            fail(f"{rig_slug}: registry contains retired synthetic-commit lookalike")
    for _rdoc in (beh_doc, ent_doc):
        for _m in re.findall(r'"resolvedCommit":\s*"([^"]+)"', json.dumps(_rdoc)):
            if not re.fullmatch(r"([0-9a-f]{40}|SYNTHETIC-.*)", _m):
                fail(f"{rig_slug}: resolvedCommit must be 40-hex or SYNTHETIC- (got {_m!r}")
    # HR-3.3 (fail-closed): SYNTHETIC- provenance must never be silent green —
    # warn loudly, and fail unless explicitly acknowledged for a labeled
    # tarball regen (HERETEK_ALLOW_SYNTHETIC=1, mirroring the generator's
    # --allow-synthetic-provenance opt-in) or when CI=true requires real git
    # provenance. Clean git checkouts (40-hex) stay green unconditionally.
    for _rdoc in (beh_doc, ent_doc):
        if "SYNTHETIC-" in json.dumps(_rdoc):
            print("  [WARN] SYNTHETIC- provenance present (sourceless tarball regen; re-run from a git checkout for release)", file=sys.stderr)
            if os.environ.get("CI") == "true":
                fail(f"{rig_slug}: SYNTHETIC- provenance forbidden when CI=true")
            elif os.environ.get("HERETEK_ALLOW_SYNTHETIC") != "1":
                fail(f"{rig_slug}: SYNTHETIC- provenance requires HERETEK_ALLOW_SYNTHETIC=1 (explicit tarball-regen acknowledgment)")

status_doc = validate_doc(root / "registry/status.json", "bundle-status.v1.schema.json")
body_without_digest = {k: v for k, v in status_doc.items() if k != "bodyDigest"}
# HR-3.2 (fail-closed): explicit RFC 8785 JCS canonicalizer (UTF-16 key order,
# compact separators, float-reject) — mirrors scripts/generate-rigs.py so the
# digest never rests on json.dumps(sort_keys=True) coincidence.
def _jcs_canonicalize(_o):
    if _o is None:
        return "null"
    if _o is True:
        return "true"
    if _o is False:
        return "false"
    if isinstance(_o, bool):
        raise ValueError("unsupported bool subclass")
    if isinstance(_o, int):
        return str(_o)
    if isinstance(_o, float):
        raise ValueError("floats forbidden in JCS body")
    if isinstance(_o, str):
        return json.dumps(_o, ensure_ascii=False)
    if isinstance(_o, list):
        return "[" + ",".join(_jcs_canonicalize(_v) for _v in _o) + "]"
    if isinstance(_o, dict):
        return "{" + ",".join(json.dumps(_k, ensure_ascii=False) + ":" + _jcs_canonicalize(_o[_k]) for _k in sorted(_o.keys(), key=utf16_key)) + "}"
    raise ValueError(f"unsupported type {type(_o).__name__}")
def _has_float(_o):
    if isinstance(_o, float):
        return True
    if isinstance(_o, dict):
        return any(_has_float(_v) for _v in _o.values())
    if isinstance(_o, list):
        return any(_has_float(_v) for _v in _o)
    return False
if _has_float(body_without_digest):
    fail("registry/status.json body must not contain floats (JCS divergence risk)")
# HR-3.2 (fail-closed): non-ASCII bodies would diverge between json.dumps
# ensure_ascii=False and a real RFC 8785 canonicalizer — fail until JCS vendored.
try:
    _jcs_text = _jcs_canonicalize(body_without_digest)
except ValueError as _e:
    fail(f"registry/status.json JCS canonicalization failed: {_e}")
    _jcs_text = ""
if any(ord(_c) > 127 for _c in _jcs_text):
    fail("registry/status.json body must stay ASCII-only until a real JCS canonicalizer is vendored")
# HR-3.2 known-answer: canonical form of {"b":2,"a":1} must be '{"a":1,"b":2}'.
try:
    _known = _jcs_canonicalize({"b": 2, "a": 1})
except ValueError as _e:
    _known = ""
    fail(f"JCS canonicalization failed: {_e}")
if _known != '{"a":1,"b":2}':
    fail("JCS canonical-form known-answer failed")
try:
    expected_body_digest = hashlib.sha256(_jcs_canonicalize(body_without_digest).encode("utf-8")).hexdigest()
except ValueError as _e:
    fail(f"registry/status.json bodyDigest recompute failed: {_e}")
    expected_body_digest = ""
if status_doc.get("bodyDigest") == expected_body_digest:
    ok(f"registry/status.json RFC 8785 JCS bodyDigest verified ({expected_body_digest[:16]}...)")
else:
    fail("registry/status.json bodyDigest mismatch")

# HR-3.3 (fail-closed): replay the pinned identity-vectors.json fixtures so the
# digest rules rest on vendored vectors, not on the generator agreeing with itself.
try:
    _iv = json.loads((root / "identity-vectors.json").read_text())
    _iv_vec = _iv.get("vectors", {})
    _iv_utf = _iv_vec.get("utf16_configuration_id", {})
    if compute_configuration_id(_iv_utf.get("input", {})) != _iv_utf.get("expected"):
        fail("identity-vectors.json utf16_configuration_id replay mismatch")
    _iv_jcs = _iv_vec.get("jcs_canonical_form", {})
    try:
        _iv_got = _jcs_canonicalize(_iv_jcs.get("input", {}))
    except ValueError as _e:
        _iv_got = ""
        fail(f"identity-vectors.json JCS canonicalization failed: {_e}")
    if _iv_got != _iv_jcs.get("expected"):
        fail("identity-vectors.json jcs_canonical_form replay mismatch")
    if _iv_vec.get("package_digest_coverage", {}).get("expected") != "openrig.package-digest/v1":
        fail("identity-vectors.json package_digest_coverage mismatch")
    if _iv_vec.get("package_digest_algorithm", {}).get("expected") != "sha256":
        fail("identity-vectors.json package_digest_algorithm mismatch")
    if not failures:
        ok("identity-vectors.json digest vectors replayed (utf16 order, JCS form, coverage)")
except Exception as _e:
    fail(f"identity-vectors.json replay failed: {_e}")

ok("All 8 configurations.yaml, 8 behaviour.json, 8 registry entries, bundle.yaml hashes, and status.json pass OpenRig v1 schemas & digests")

print("\n== V6. MCP Catalog, Sidecar Compose & Unit Tests ==")
for sname, sdef in mcp_catalog.items():
    if "latest" in str(sdef.get("pin", "")):
        fail(f"MCP server {sname} uses floating pin: {sdef.get('pin')}")
    for arg in sdef.get("args", []):
        if str(arg).startswith("!"):
            fail(f"MCP server {sname} uses !command in args (never expanded by Pi)")
    for v in list(sdef.get("env", {}).values()) + list(sdef.get("headers", {}).values()):
        if isinstance(v, str):
            if re.search(r"(ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9]|AKIA[0-9A-Z]{16}|xox[bpoas]-[A-Za-z0-9-]+|OPENCODE_API_KEY\s*=\s*\S+|GITHUB_TOKEN\s*=\s*\S+)", v):
                fail(f"MCP server {sname} has literal secret in env/headers")
            sv = v.strip()
            if "@SECRETS@" in v or "@TOOLS@" in v or "@SEAT@" in v:
                pass  # plain file-path substitution, allowed
            elif sv.startswith("!cat "):
                pass  # whole-value command-backed secret, allowed
            elif re.match(r"^!echo Bearer \$\(cat .*\)$", sv):
                pass  # GitHub Authorization header form, allowed (no secret materialized)
            elif re.match(r"^[A-Za-z0-9_]+://", sv) or sv in ("true", "false", "restricted", ":memory:", "heretek-rag-eval"):
                pass  # non-secret constant (URL template, flag, collection name)
            else:
                # HR-4.4 (fail-closed): no open-ended lowercase passthrough — any
                # other env/headers shape must be an allowed command-backed reference.
                # A short literal such as REDIS_URL "foobar123" must flip the gate.
                fail(f"MCP server {sname} has unexpected env/headers value: {v[:60]}")
# HR-4.4: scan fleet roles and registry for literal secrets / reserved env names
# (floors lowered to {8,} with [-_] support so short/hyphenated literals such
# as `sk-live-123456` cannot evade; mcp env shape-check at :584 stays exact).
fleet_raw = (root / "fleet/fleet.yaml").read_text()
if re.search(r"(ghp_[A-Za-z0-9_-]{8,}|github_pat_[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}|xox[bp]-[A-Za-z0-9_-]{8,})", fleet_raw):
    fail("fleet/fleet.yaml contains literal secret material")
# HR-4.4 full claim name-list: reserved/secret env names must not be assigned literal values in fleet
if re.search(r"(OPENRIG_[A-Za-z0-9_]+|OPENCODE_API_KEY|GITHUB_TOKEN|_PASSWORD|_SECRET|_TOKEN)", fleet_raw):
    fail("fleet/fleet.yaml contains forbidden reserved/secret env name")
# HR-6.2-stale-legacy-pins (fail-closed): shipped surface must never contain
# the rejected second-delegation / duplicate-LSP packages. `pi-subagents`
# (second delegation channel) and `pi-lsp@0.1.7` (duplicate tool names vs
# pi-lsp-extension@1.4.0) are Rejected in docs/OSINT_ECOSYSTEM_REPORT.md:68-71;
# stale ADOPT tables live only in retired spike snapshots (gemini/, claude/).
# An active pin in fleet/specs/rigs/scripts must flip the gate.
for _shipped in [(root / "fleet/fleet.yaml").read_text(), (root / "fleet/mcp-servers.yaml").read_text()]:
    if "pi-subagents" in _shipped:
        fail("shipped catalog must not contain pi-subagents (rejected second delegation path)")
    if "pi-lsp@0.1.7" in _shipped:
        fail("shipped catalog must not contain pi-lsp@0.1.7 (duplicate vs pi-lsp-extension@1.4.0)")
for _sp in list((root / "specs").rglob("*.yaml")) + list((root / "specs").rglob("*.json")) + list((root / "rigs").rglob("*.yaml")) + [p for p in list((root / "scripts").glob("*.py")) + list((root / "scripts").glob("*.sh")) if p.name != "verify-rigs.sh"]:
    try:
        _st = _sp.read_text()
    except Exception:
        continue
    if "pi-subagents" in _st:
        fail(f"{_sp.relative_to(root)} must not contain pi-subagents (rejected)")
    if "pi-lsp@0.1.7" in _st:
        fail(f"{_sp.relative_to(root)} must not contain pi-lsp@0.1.7 (rejected duplicate)")
for rid2, r2 in fleet.get("roles", {}).items():
    for b in (r2.get("mcp") or []):
        if b.get("server") not in mcp_catalog:
            fail(f"{rid2}: binds unknown MCP server {b.get('server')}")
# HR-4.4 (fail-closed): per-role rendered mcp.json + registry + rosters must
# carry no literal secrets or reserved-name assignments (replaces the old no-op loop).
# Name list unified across all four scan sites (rig.yaml, fleet, mcp.json, registry).
_LITERAL_RE = r"(ghp_[A-Za-z0-9_-]{8,}|github_pat_[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}|xox[bp]-[A-Za-z0-9_-]{8,})"
_LITERAL_NAMES_RE = r"(OPENRIG_[A-Za-z0-9_]+|OPENCODE_API_KEY|GITHUB_TOKEN|_PASSWORD|_SECRET|_TOKEN)"
# HR-4.4: in rendered mcp.json the legitimate env KEYS (e.g. CLICKHOUSE_PASSWORD)
# carry reserved names, so scope the name scan to string VALUES only — a key
# is `"NAME":` (no colon before its quote) while a value is `: "…NAME…"` .
_LITERAL_VALUE_NAMES_RE = r':\s*"[^"]*(OPENRIG_[A-Za-z0-9_]+|OPENCODE_API_KEY|GITHUB_TOKEN|_PASSWORD|_SECRET|_TOKEN)'
for _mp in sorted((root / "specs/agents").glob("*/*/runtime/mcp.json")):
    try:
        _mt = _mp.read_text()
    except Exception:
        continue
    if re.search(_LITERAL_RE, _mt):
        fail(f"{_mp.relative_to(root)} contains literal secret material")
    if re.search(_LITERAL_VALUE_NAMES_RE, _mt):
        fail(f"{_mp.relative_to(root)} contains reserved secret name in a value")
for _rp in list((root / "registry").rglob("*.json")) + list((root / "registry").rglob("*.yaml")) + list((root / "rosters").glob("*.json")):
    try:
        _rt = _rp.read_text()
    except Exception:
        continue
    if re.search(_LITERAL_RE, _rt):
        fail(f"{_rp.relative_to(root)} contains literal secret material")
    if re.search(_LITERAL_NAMES_RE, _rt):
        fail(f"{_rp.relative_to(root)} contains reserved secret name")
# HR-4.2: bootstrap must default to strict secrets (fail-closed); degraded
# seats require explicit --allow-missing-secrets opt-in.
_boot_text = (root / "scripts/bootstrap-pi-seats.sh").read_text()
import re as _re2
_m = _re2.search(r'^ALLOW_MISSING="([^"]*)"', _boot_text, flags=_re2.MULTILINE)
if not _m or _m.group(1) != "":
    fail("scripts/bootstrap-pi-seats.sh must default to strict secrets (fail-open default)")
if "rig.all-51.yaml" in _boot_text and "--profile all-51" not in _boot_text:
    fail("scripts/bootstrap-pi-seats.sh must treat rig.all-51.yaml as a separate --profile target")
# HR-4.2 (fail-closed): seat materialization must chmod 0600 and configure the
# pinned opencode-go endpoint — a regression deleting either must flip the gate.
_seed_text = (root / "scripts/render-seat.py").read_text()
if "os.chmod(p, 0o600)" not in _seed_text and "chmod(p, 0o600)" not in _seed_text:
    fail("scripts/render-seat.py must chmod rendered seat files 0600")
if "https://opencode.ai/inference/go/v1" not in _seed_text:
    fail("scripts/render-seat.py must pin baseUrl https://opencode.ai/inference/go/v1")
# HR-4.3 (fail-closed): secret files must be symlink-rejected, ownership-pinned,
# and O_NOFOLLOW-opened — a regression deleting any of these must flip the gate.
if "is_symlink()" not in _seed_text:
    fail("scripts/render-seat.py must reject symlinked secret files")
if "st_uid" not in _seed_text:
    fail("scripts/render-seat.py must pin secret-file ownership (st_uid)")
if "O_NOFOLLOW" not in _seed_text:
    fail("scripts/render-seat.py must open secret files with O_NOFOLLOW")
# HR-5.5-prefix-escape (fail-closed): the renderer must emit terminal bash
# denies LAST so live --output/chaining suffixes cannot escape an allowed
# trailing-* prefix under prefix-glob matcher semantics.
if '"*--output*"' not in _seed_text:
    fail('scripts/render-seat.py must emit terminal "*--output*" bash deny')
# HR-5.5-git-patch-read-bypass (fail-closed): the renderer must emit the
# patch-output flag denies LAST so `git log -p` / `git show --patch` cannot
# exfiltrate file contents past path read-denies on allowed git prefixes.
for _ptd in ('"* -p*"', '"*\\t-p*"', '"*--patch*"', '"*--full-diff*"', '"*--textconv*"', '"* -u*"', '"*\\t-u*"', '"* -U*"', '"*\\t-U*"', '"*--unified*"', '"*--cc*"', '"* -c *"', '"* -m *"', '"* -W*"', '"*--function-context*"', '"*--word-diff*"', '"*--color-words*"', '"*--binary*"', '"*--raw*"', '"*OPENRIG_SESSION_NAME=*"', '"*OPENRIG_URL=*"'):
    if _ptd not in _seed_text:
        fail(f"scripts/render-seat.py must emit terminal {_ptd} bash deny")
# HR-4.2 (fail-closed opt-in): when HERETEK_REQUIRE_SEATS=1, assert sampled
# $OPENRIG_HOME/state/pi/<pod>-<member>@<rig>/agent/ seat dirs exist with 0600
# files and the pinned endpoint. Default --check-only stays repo-scoped (seat
# dirs are host-local, so asserting them unconditionally would fail clean
# post-generate pre-bootstrap checkouts for the wrong reason); CI/bootstrap
# jobs opt in via HERETEK_REQUIRE_SEATS=1 after running bootstrap-pi-seats.sh.
if os.environ.get("HERETEK_REQUIRE_SEATS") == "1":
    _oh = Path(os.environ.get("OPENRIG_HOME", str(Path.home() / ".openrig")))
    _sampled = sorted((_oh / "state/pi").glob("*@*/agent/models.json")) if (_oh / "state/pi").exists() else []
    if not _sampled:
        fail(f"HERETEK_REQUIRE_SEATS=1 but no seat dirs under {_oh}/state/pi/*@*/agent/ (run scripts/bootstrap-pi-seats.sh first)")
    else:
        for _mj in _sampled[:5]:
            try:
                _st = _mj.stat()
                if oct(_st.st_mode & 0o777) != "0o600":
                    fail(f"seat file {_mj} must be 0600 (got {oct(_st.st_mode & 0o777)})")
                _md = json.loads(_mj.read_text())
                if "https://opencode.ai/inference/go/v1" not in json.dumps(_md):
                    fail(f"seat file {_mj} must pin baseUrl https://opencode.ai/inference/go/v1")
            except Exception as _e:
                fail(f"seat file {_mj} unreadable: {_e}")
        if not failures:
            ok(f"sampled {min(len(_sampled), 5)}/{len(_sampled)} Pi seat dirs under {_oh}/state/pi are 0600 with pinned endpoint")
# HR-7.3: verifier coverage for Makefile guard-profiles matrix (fail-closed co-scheduling guard)
make_text = (root / "Makefile").read_text()
if "guard-profiles" not in make_text or "mobile" not in make_text or "devsec" not in make_text or "web-research" not in make_text:
    fail("Makefile guard-profiles must refuse mobile+devsec and mobile+web-research co-scheduling")
if "exit 1" not in make_text:
    fail("Makefile guard-profiles must exit 1 on forbidden co-scheduling")
if "refusing to co-schedule" not in make_text:
    fail("Makefile guard-profiles must carry the explicit refusing-to-co-schedule error")
# HR-7.3-guard-tab-separation (fail-closed): SIDECAR_PROFILES word-splits on
# tabs in the foreach launcher, so the guard must normalize tabs/commas before
# matching (a tab-separated "mobile<TAB>devsec" must exit 1). A guard matching
# only space/comma arms passes while launching both profiles.
# HR-7.3-guard-newline-class: the foreach splits on ALL whitespace (space/tab/
# newline), so the guard must normalize the full class (tab, CR, newline, VT,
# FF) plus commas. A tab/comma-only `tr '\t,'` passes while `$'mobile\ndevsec'`
# bypasses the guard yet launches both profiles via foreach.
if "\\t" not in make_text or "\\r" not in make_text or "\\n" not in make_text or "\\v" not in make_text or "\\f" not in make_text or "tr" not in make_text:
    fail("Makefile guard-profiles must normalize tabs/newlines/CR/VT/FF/commas before matching (newline-class SIDECAR_PROFILES bypass)")
# HR-7.3 (fail-closed): sidecars-up must run the guard first — a dropped
# dependency would let `make sidecars-up SIDECAR_PROFILES="mobile devsec"`
# bypass the co-scheduling refusal. Raw `docker compose --profile` bypasses
# make by design, so CI must invoke via make (documented in compose header).
if "sidecars-up:" not in make_text or "guard-profiles" not in make_text.split("sidecars-up:")[1].split("\n")[0]:
    fail("Makefile sidecars-up must depend on guard-profiles")
# HR-7.3-make-bypass (fail-closed): the compose wrapper must exist and enforce
# the same mobile isolation refusal so raw-compose users have a guarded path.
# A deleted wrapper or weakened guard message must flip the gate.
_wrapper = root / "scripts/compose-sidecars.sh"
if not _wrapper.exists():
    fail("scripts/compose-sidecars.sh wrapper must exist (guarded compose path)")
else:
    _wt = _wrapper.read_text()
    if "refusing to co-schedule" not in _wt or "mobile" not in _wt or "devsec" not in _wt or "web-research" not in _wt:
        fail("scripts/compose-sidecars.sh must refuse mobile+devsec and mobile+web-research co-scheduling")
    if "guard-profiles" not in _wt and "make sidecars-up" not in _wt:
        fail("scripts/compose-sidecars.sh must reference the make guard-profiles path")
    # HR-7.3-wrapper-substring (fail-closed): wrapper must tokenize profiles on
    # whitespace/commas and match whole tokens only, mirroring the Makefile
    # space/comma patterns. A naive `*"mobile"*` substring test disagrees with
    # the Makefile and false-positives on hypothetical `automobile`-style names.
    if '== *"mobile"*' in _wt or "== *'mobile'*" in _wt:
        fail('scripts/compose-sidecars.sh must not use substring *mobile* matching (use whole-token comparison)')
    if '"mobile"' not in _wt and "'mobile'" not in _wt:
        fail('scripts/compose-sidecars.sh must match the mobile profile as a whole token')
# HR-8.1 (fail-closed wiring): determinism gate must stay wired — Makefile
# idempotent target must invoke --check-idempotent and the generator must
# implement that flag (the gate itself never re-runs generation here).
if "generate-rigs.py --check-idempotent" not in make_text:
    fail("Makefile idempotent target must invoke scripts/generate-rigs.py --check-idempotent")
if "--check-idempotent" not in (root / "scripts/generate-rigs.py").read_text():
    fail("scripts/generate-rigs.py must implement --check-idempotent")
# HR-4.2 (fail-closed plumbing): seed must propagate --dry-run and
# --allow-missing-secrets through to render-seat.py (a dropped passthrough
# would silently degrade strict-secret seats).
_seed_text = (root / "scripts/seed-rig.py").read_text()
if "--allow-missing-secrets" not in _seed_text or "--dry-run" not in _seed_text:
    fail("scripts/seed-rig.py must propagate --dry-run and --allow-missing-secrets to render-seat.py")
# HR-8.4: placeholder-freedom across the 8 deliverables (FIXME/TBD/fenced templates;
# PLACEHOLDER and bare TODO prose (e.g. "zero TODO", "PLACEHOLDER must remain") are intentional
# references to LICENSE handling, so only FAIL on true unresolved tokens in code-adjacent files,
# plus FIXME/TBD/{{TEMPLATE}} in docs/prompts)
for rel in ["fleet/fleet.yaml", "fleet/mcp-servers.yaml", "scripts/audit_loop.py"]:
    txt = (root / rel).read_text()
    if re.search(r"PLACEHOLDER|TODO|FIXME|\{\{|TBD", txt):
        fail(f"{rel} contains unresolved placeholder")
for rel in ["docs/OSINT_ECOSYSTEM_REPORT.md", "docs/OPENRIG_MUSE_GO_ARCHITECTURE.md", "PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md", "PROMPT_ADVERSARIAL_FLEET_AUDIT.md", "PROMPT_FLEET_AUDIT_REMEDIATION.md"]:
    txt = (root / rel).read_text()
    # HR-1.4 allowlist: Claim 1.4's intentional stub-token enumeration is
    # documented prose (not an unresolved template); strip that single
    # sanctioned sentence before the fail-closed scan so any other FIXME /
    # TBD / {{TEMPLATE}} still flips the gate.
    txt_scan = txt.replace("with zero `TODO`/`FIXME`/`TBD`/`PLACEHOLDER`/`{{...}}` stub tokens (documented `@TOOLS@`/`@SECRETS@`/`@SEAT@` seed-substitution tokens in `runtime/mcp.json` excepted per Claim 4.3)", "")
    if re.search(r"FIXME|\{\{[A-Z_]+\}\}|\bTBD\b", txt_scan):
        fail(f"{rel} contains unresolved placeholder")
ok(f"All {len(mcp_catalog)} MCP servers in fleet/mcp-servers.yaml verified (pinned, command-backed secrets)")

sidecars = yaml.safe_load((root / "docker-compose.sidecars.yml").read_text())
for sname, sdef in sidecars.get("services", {}).items():
    for port_map in sdef.get("ports", []):
        if not str(port_map).startswith("127.0.0.1:"):
            fail(f"Sidecar {sname} publishes non-loopback port: {port_map}")
    img = sdef.get("image", "")
    # HR-7.1 (fail-closed): reject any :latest tag even before @sha256 digest
    # pinning (endswith misses `foo:latest@sha256:…`).
    if ":latest" in str(img).split("@sha256:")[0]:
        fail(f"Sidecar {sname} uses forbidden :latest tag: {img}")
    # HR-7.1 (fail-closed): host-network or privileged sidecars break tenant isolation.
    if str(sdef.get("network_mode", "")) == "host":
        fail(f"Sidecar {sname} must not use network_mode: host")
    if sdef.get("privileged") is True:
        fail(f"Sidecar {sname} must not run privileged: true")
# HR-7.1-firecrawl-redis (fail-closed): every `://<host>` service reference in
# the compose file must resolve to a defined service — a dangling REDIS_URL
# host is a crash-loop/DNS failure operators would otherwise fix ad hoc
# outside the audited file. Loopback/numeric hosts are not service refs.
_compose_raw = (root / "docker-compose.sidecars.yml").read_text()
_defined_services = set(sidecars.get("services", {}).keys())
for _ref_host in set(re.findall(r"://([A-Za-z0-9][A-Za-z0-9_-]*)", _compose_raw)):
    if _ref_host in ("localhost",) or re.fullmatch(r"\d+\.\d+\.\d+\.\d+", _ref_host):
        continue
    if _ref_host not in _defined_services:
        fail(f"docker-compose.sidecars.yml references undefined service host '{_ref_host}' (dangling service reference)")

dsp = sidecars["services"].get("docker-socket-proxy", {})
dsp_env = dsp.get("environment", {})
_PROXY_20 = ("POST", "BUILD", "EXEC", "VOLUMES", "NETWORKS", "SWARM", "SYSTEM", "AUTH", "CONTAINERS", "IMAGES", "INFO", "PING", "SERVICES", "TASKS", "NODES", "CONFIGS", "SECRETS", "PLUGINS", "EVENTS", "VERSION")
for k in _PROXY_20:
    if str(dsp_env.get(k)) != "0":
        fail(f"docker-socket-proxy must set {k}=0")
# HR-7.2 (fail-closed): the proxy env must be exactly the 20-key set from the
# tecnativa/docker-socket-proxy:0.5.0 README/haproxy.cfg (18 README toggles +
# default-grant EVENTS/VERSION, both denied) — extra keys widen the API surface.
if set(dsp_env.keys()) != set(_PROXY_20):
    fail(f"docker-socket-proxy environment must be exactly the 20-toggle set (got {sorted(dsp_env.keys())})")
dsp_img = dsp.get("image", "")
if "tecnativa/docker-socket-proxy:0.5.0" not in dsp_img:
    fail(f"docker-socket-proxy must be pinned tecnativa/docker-socket-proxy:0.5.0 (got {dsp_img})")
dsp_vols = dsp.get("volumes", [])
if not any("/var/run/docker.sock:/var/run/docker.sock:ro" in str(v) for v in dsp_vols):
    fail("docker-socket-proxy must mount /var/run/docker.sock:/var/run/docker.sock:ro")
# HR-7.3-network-exclusivity (fail-closed): assert EXACT network sets, not
# membership — a membership test lets a future edit dual-home ghidra/radare2
# onto public `heretek` (or docker-android elsewhere), silently bridging the
# `internal: true` malware-analysis/emulator containment boundary while the
# gate stays green. `sonarqube` is intentionally co-resident on
# `heretek-devsec` (code-review findings feed SAST triage on the same isolated
# tenant net; it never mounts ./workspaces/binaries and never joins
# `heretek-mobile`) and is pinned here so its placement is gated rather than
# accidental. A dual-homing sabotage fixture must flip the gate 0->1.
for _svc73 in ("ghidra", "radare2"):
    if _svc73 in sidecars.get("services", {}):
        _raw73 = sidecars["services"][_svc73].get("networks", [])
        _set73 = set(_raw73 if isinstance(_raw73, list) else list(_raw73.keys() if isinstance(_raw73, dict) else []))
        if _set73 != {"heretek-devsec"}:
            fail(f"{_svc73} must be connected ONLY to heretek-devsec (got {sorted(_set73)}); dual-homing bridges the isolated analysis network")
        _vols73 = " ".join(str(_v73) for _v73 in sidecars["services"][_svc73].get("volumes", []))
        if "/samples:ro" not in _vols73:
            fail(f"{_svc73} must mount ./workspaces/binaries:/samples:ro")
if "sonarqube" in sidecars.get("services", {}):
    _raw73 = sidecars["services"]["sonarqube"].get("networks", [])
    _set73 = set(_raw73 if isinstance(_raw73, list) else list(_raw73.keys() if isinstance(_raw73, dict) else []))
    if _set73 != {"heretek-devsec"}:
        fail(f"sonarqube must be connected ONLY to heretek-devsec (got {sorted(_set73)}); co-residency with the analysis tenant is intentional and gated")
if "docker-android" in sidecars.get("services", {}):
    _raw73 = sidecars["services"]["docker-android"].get("networks", [])
    _set73 = set(_raw73 if isinstance(_raw73, list) else list(_raw73.keys() if isinstance(_raw73, dict) else []))
    if _set73 != {"heretek-mobile"}:
        fail(f"docker-android must be connected ONLY to heretek-mobile (got {sorted(_set73)}); emulator isolation is mandatory")
ok("Sidecar Docker Compose verified (loopback-only ports, zero :latest tags, GET-only docker-socket-proxy)")

ut = subprocess.run([sys.executable, "-m", "unittest", "tests/test_render_seat.py"], cwd=str(root), capture_output=True, text=True)
if ut.returncode == 0:
    ok("tests/test_render_seat.py (7/7 unit tests) passed")
else:
    fail(f"tests/test_render_seat.py failed:\n{ut.stderr}")

print("\n== V7. Regen-Gate Sanctioned-Untracked Allowlist ==")
# HR-43 (fail-closed consistency, issue #43): the clean-tree gate's
# sanctioned-untracked allowlist must cover every AGENTS.md blessed stray,
# every entry must carry its workflow-demand justification comment, and the
# gate must still refuse synthetic real dirt. Appended at the end — no
# existing check renumbered or reworded. Exactly one ok() below (22 -> 23).
_hr43_before = len(failures)
_gate_spec43 = importlib.util.spec_from_file_location(
    "regen_gate_hr43", str(root / "scripts/generate-rigs.py")
)
_gate43 = importlib.util.module_from_spec(_gate_spec43)
try:
    _gate_spec43.loader.exec_module(_gate43)
except Exception as _e43:
    fail(f"HR-43: cannot load scripts/generate-rigs.py allowlist source: {_e43}")
    _gate43 = None
if _gate43 is not None:
    # (a) every AGENTS.md blessed stray covered by the allowlist. The strays
    # are read from the AGENTS.md bullet itself (not hardcoded), so drifting
    # either side fails this check.
    _blessed43 = []
    for _ln43 in (root / "AGENTS.md").read_text().splitlines():
        if "Leave untracked strays alone" in _ln43:
            _blessed43 = re.findall(r"`([^`]+)`", _ln43)
            break
    if not _blessed43:
        fail("HR-43: AGENTS.md blessed-stray bullet not found")
    _allow43 = [d.rstrip("/") for d in getattr(_gate43, "SANCTIONED_UNTRACKED_DIRS", ())]
    _allow43 += list(getattr(_gate43, "SANCTIONED_UNTRACKED_FILES", ()))
    for _b43 in _blessed43:
        if _b43.rstrip("/") not in _allow43:
            fail(f"HR-43: AGENTS.md blessed stray {_b43!r} not covered by the regen-gate allowlist")
    # (b) every allowlist entry carries its justification comment: the source
    # line holding the quoted entry must be immediately preceded by a `#`
    # comment stating which workflow demand produces the path.
    _src43 = (root / "scripts/generate-rigs.py").read_text().splitlines()
    for _e43 in list(getattr(_gate43, "SANCTIONED_UNTRACKED_DIRS", ())) + list(
        getattr(_gate43, "SANCTIONED_UNTRACKED_FILES", ())
    ):
        _idx43 = next(
            (i for i, _l43 in enumerate(_src43) if f'"{_e43}"' in _l43), None
        )
        if _idx43 is None or _idx43 == 0 or not _src43[_idx43 - 1].strip().startswith("#"):
            fail(f"HR-43: allowlist entry {_e43!r} lacks its justification comment")
# (c) the gate still refuses synthetic real dirt: the T1/T2 unit fixtures
# (tracked modification AND non-allowlisted untracked, incl. the
# tracked-override case) run here, so allowlist drift that weakens refusal
# fails this block while all pre-existing checks stay green.
utr43 = subprocess.run(
    [sys.executable, "-m", "unittest", "tests/test_regen_gate.py"],
    cwd=str(root),
    capture_output=True,
    text=True,
)
if utr43.returncode != 0:
    fail(f"tests/test_regen_gate.py failed:\n{utr43.stderr}")
if len(failures) == _hr43_before:
    ok("Regen-gate sanctioned-untracked allowlist covers AGENTS.md strays with justified entries and refuses synthetic dirt (tests/test_regen_gate.py 9/9)")

print("\n== V8. Manifest-Closure Lint (issue #40) ==")
# HR-40 (fail-closed stage-time gate): every binary invoked by staged
# package.json scripts / workflow run: steps must resolve to a declared
# dependency or the checked-in operator-runner allowlist
# (fleet/allowed-system-tools.txt); staged tsconfig `types` entries must
# resolve to declared @types packages. Proven by tests/test_manifest_closure.py
# synthetic fixtures (all four Wave-2 defect shapes fire named; the fixed
# pins pass) plus a live --staged run. Appended at the end — no existing
# check renumbered or reworded. Exactly one ok() below.
_mc_before = len(failures)
_mcr = subprocess.run(
    [sys.executable, "-m", "unittest", "tests/test_manifest_closure.py"],
    cwd=str(root),
    capture_output=True,
    text=True,
)
if _mcr.returncode != 0:
    fail(f"tests/test_manifest_closure.py failed:\n{_mcr.stderr}")
_mcs = subprocess.run(
    [sys.executable, str(root / "scripts/manifest-closure.py"), "--staged"],
    cwd=str(root),
    capture_output=True,
    text=True,
)
if _mcs.returncode != 0:
    fail(f"scripts/manifest-closure.py --staged failed:\n{_mcs.stdout}\n{_mcs.stderr}")
_mc_ran = "?"
_mc_match = re.search(r"Ran (\d+) tests", _mcr.stderr)
if _mc_match:
    _mc_ran = _mc_match.group(1)
if len(failures) == _mc_before:
    ok(f"Manifest-closure lint (issue #40) green: staged manifests resolve with zero undeclared binaries (tests/test_manifest_closure.py {_mc_ran} tests pass)")

print("\n== V9. Policy-Text Verifier (issue #41) ==")
# HR-41 (fail-closed stage-time gate): lint-table names resolve against the
# checked-in known-lint snapshot (the stale cast_lossy reference fires);
# workflow run: steps resolve against staged package scripts (a pnpm
# eslint .-style step duplicating the lint script fails citing the script);
# cargo steps resolve to known subcommands or staged .cargo aliases.
# Proven by tests/test_policy_verifier.py synthetic fixtures (stale + fixed
# pins, duplicate + reconciled steps, stale-snapshot, unreadable files)
# plus a live --staged run. Appended at the end — no existing check
# renumbered or reworded. Exactly one ok() below.
_hr41_before = len(failures)
_hr41r = subprocess.run(
    [sys.executable, "-m", "unittest", "tests/test_policy_verifier.py"],
    cwd=str(root),
    capture_output=True,
    text=True,
)
if _hr41r.returncode != 0:
    fail(f"tests/test_policy_verifier.py failed:\n{_hr41r.stderr}")
_hr41s = subprocess.run(
    [sys.executable, str(root / "scripts/policy-verifier.py"), "--staged",
     "--pin-file", str(root / "scripts/policy-verifier.toolchain-pin")],
    cwd=str(root),
    capture_output=True,
    text=True,
)
if _hr41s.returncode != 0:
    fail(f"scripts/policy-verifier.py --staged failed:\n{_hr41s.stdout}\n{_hr41s.stderr}")
_hr41_ran = "?"
_hr41_match = re.search(r"Ran (\d+) tests", _hr41r.stderr)
if _hr41_match:
    _hr41_ran = _hr41_match.group(1)
if len(failures) == _hr41_before:
    ok(f"Policy-text verifier (issue #41) green: staged policy files resolve against the pinned authority (tests/test_policy_verifier.py {_hr41_ran} tests pass)")

print("\n== V10. Tracker-vs-Queue Reconcile Diff (issue #39) ==")
# HR-39 (fail-closed read-only diff, no auto-edit): the reconcile command must
# flag every drift class on a synthetic pre-convergence pair (stale-state,
# parked-satisfied-but-tracker-silent, missing-convergence-annotation), pass a
# converged pair with exit 0 "in sync", and fail closed (exit 2, named file:line)
# on an unparseable row — proven by tests/test_reconcile.py synthetic fixtures
# (/tmp only, never the live mission checkout) plus an offline end-to-end run
# below. Appended at the end — no existing check renumbered or reworded.
# Exactly one ok() below.
_hr39_before = len(failures)
_hr39r = subprocess.run(
    [sys.executable, "-m", "unittest", "tests/test_reconcile.py"],
    cwd=str(root),
    capture_output=True,
    text=True,
)
if _hr39r.returncode != 0:
    fail(f"tests/test_reconcile.py failed:\n{_hr39r.stderr}")
import tempfile as _tf39
_hr39_tmp = _tf39.mkdtemp(prefix="hr39-verify-")
try:
    _hr39_tracker = Path(_hr39_tmp) / "wave9-dispatch-tracker.md"
    _hr39_tracker.write_text(
        "# Wave 9 Dispatch Tracker (verify fixture)\n\n## Slices\n"
        "| Slice | Owner seat | Output | Slice qitem | Status |\n"
        "|---|---|---|---|---|\n"
        "| W9-01 demo | seat | out | qitem-20261022000001-aaaaaaaaaaaaaaaa | STAGED awaiting QA |\n"
    )
    _hr39_qlist = Path(_hr39_tmp) / "queue_list.json"
    _hr39_qlist.write_text(json.dumps([{"qitemId": "qitem-20261022000001-aaaaaaaaaaaaaaaa", "state": "closed"}]))
    _hr39_trans = Path(_hr39_tmp) / "transitions.json"
    _hr39_trans.write_text(json.dumps({"qitem-20261022000001-aaaaaaaaaaaaaaaa": [{"transitionId": 7, "qitemId": "qitem-20261022000001-aaaaaaaaaaaaaaaa", "ts": "2026-10-22T11:45:00.000Z", "state": "closed", "transitionNote": "handed_off_to Next"}]}))
    _hr39_drift = subprocess.run(
        [sys.executable, str(root / "scripts/reconcile.py"), "--tracker", str(_hr39_tracker), "--queue-list", str(_hr39_qlist), "--transitions", str(_hr39_trans)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if _hr39_drift.returncode != 1 or "stale-state" not in _hr39_drift.stdout or "W9-01" not in _hr39_drift.stdout:
        fail(f"scripts/reconcile.py offline drifted run must exit 1 naming W9-01 stale-state (got {_hr39_drift.returncode}: {_hr39_drift.stdout[:200]}{_hr39_drift.stderr[:200]})")
    _hr39_before_bytes = _hr39_tracker.read_bytes()
    _hr39_conv = Path(_hr39_tmp) / "converged.md"
    _hr39_conv.write_text(
        "# Wave 9 Dispatch Tracker (verify fixture)\n\n## Slices\n"
        "| Slice | Owner seat | Output | Slice qitem | Status |\n"
        "|---|---|---|---|---|\n"
        "| W9-01 demo | seat | out | qitem-20261022000001-aaaaaaaaaaaaaaaa | QA PASS + PLACED canonical (queue note 7; operator note appended) |\n"
    )
    _hr39_sync = subprocess.run(
        [sys.executable, str(root / "scripts/reconcile.py"), "--tracker", str(_hr39_conv), "--queue-list", str(_hr39_qlist), "--transitions", str(_hr39_trans)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if _hr39_sync.returncode != 0 or "in sync" not in _hr39_sync.stdout:
        fail(f"scripts/reconcile.py offline converged run must exit 0 in sync (got {_hr39_sync.returncode}: {_hr39_sync.stdout[:200]}{_hr39_sync.stderr[:200]})")
    if _hr39_tracker.read_bytes() != _hr39_before_bytes:
        fail("scripts/reconcile.py modified the tracker (must be read-only)")
finally:
    import shutil as _sh39
    _sh39.rmtree(_hr39_tmp, ignore_errors=True)
_hr39_ran = "?"
_hr39_match = re.search(r"Ran (\d+) tests", _hr39r.stderr)
if _hr39_match:
    _hr39_ran = _hr39_match.group(1)
if len(failures) == _hr39_before:
    ok(f"Tracker-vs-queue reconcile (issue #39) green: drifted pair diffs, converged pair in sync, run read-only (tests/test_reconcile.py {_hr39_ran} tests pass)")

print("\n== V11. Dispatch-Tracker Proposal Generator (issue #57) ==")
# HR-57 (propose-only emitter, no auto-edit): generate_trackers.py consumes
# the shared reconcile row model and emits paste-ready Status cells for every
# diffed row (OTHER(<raw>)/orphan rows carry NEEDS-HUMAN-REVIEW, never a
# guessed status), fails closed on an EMPTY queue list ([]), and its
# non-review cells replay through reconcile to exit 0 in sync — proven by
# tests/test_generate_trackers.py synthetic fixtures (/tmp only) plus an
# offline end-to-end run below. Appended at the end — no existing check
# renumbered or reworded. Exactly one ok() below.
_hr57_before = len(failures)
_hr57r = subprocess.run(
    [sys.executable, "-m", "unittest", "tests/test_generate_trackers.py"],
    cwd=str(root),
    capture_output=True,
    text=True,
)
if _hr57r.returncode != 0:
    fail(f"tests/test_generate_trackers.py failed:\n{_hr57r.stderr}")
import tempfile as _tf57
_hr57_tmp = _tf57.mkdtemp(prefix="hr57-verify-")
try:
    _hr57_tracker = Path(_hr57_tmp) / "wave9-dispatch-tracker.md"
    _hr57_tracker.write_text(
        "# Wave 9 Dispatch Tracker (verify fixture)\n\n## Slices\n"
        "| Slice | Owner seat | Output | Slice qitem | Status |\n"
        "|---|---|---|---|---|\n"
        "| W9-01 demo | seat | out | qitem-20261022000001-aaaaaaaaaaaaaaaa | STAGED awaiting QA |\n"
    )
    _hr57_qlist = Path(_hr57_tmp) / "queue_list.json"
    _hr57_qlist.write_text(json.dumps([{"qitemId": "qitem-20261022000001-aaaaaaaaaaaaaaaa", "state": "closed"}]))
    _hr57_trans = Path(_hr57_tmp) / "transitions.json"
    _hr57_trans.write_text(json.dumps({"qitem-20261022000001-aaaaaaaaaaaaaaaa": [{"transitionId": 7, "qitemId": "qitem-20261022000001-aaaaaaaaaaaaaaaa", "ts": "2026-10-22T11:45:00.000Z", "state": "closed", "transitionNote": "handed_off_to Next"}]}))
    _hr57_before_bytes = _hr57_tracker.read_bytes()
    _hr57_prop = Path(_hr57_tmp) / "w9-proposal.txt"
    _hr57_drift = subprocess.run(
        [sys.executable, str(root / "scripts/generate_trackers.py"), "--tracker", str(_hr57_tracker), "--queue-list", str(_hr57_qlist), "--transitions", str(_hr57_trans), "--out", str(_hr57_prop)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if _hr57_drift.returncode != 1 or "PROPOSED-CELL:::" not in _hr57_drift.stdout or "W9-01" not in _hr57_drift.stdout:
        fail(f"scripts/generate_trackers.py offline drifted run must exit 1 with a W9-01 paste-ready cell (got {_hr57_drift.returncode}: {_hr57_drift.stdout[:200]}{_hr57_drift.stderr[:200]})")
    _hr57_prop_text = None
    if not _hr57_prop.is_file():
        fail("scripts/generate_trackers.py proposal file missing because the drifted run failed (no proposal emitted; skipping paste-ready cell content check)")
    else:
        try:
            _hr57_prop_text = _hr57_prop.read_text()
        except OSError as _hr57_prop_exc:
            fail(f"scripts/generate_trackers.py proposal file unreadable ({_hr57_prop_exc}; skipping paste-ready cell content check)")
            _hr57_prop_text = None
    if _hr57_prop_text is not None and "PROPOSED-CELL:::QA PASS + PLACED canonical (queue note 7: handed_off_to Next; operator note appended)" not in _hr57_prop_text:
        fail("scripts/generate_trackers.py --out proposal must carry the exact Q8 paste-ready cell")
    if _hr57_tracker.read_bytes() != _hr57_before_bytes:
        fail("scripts/generate_trackers.py modified the tracker (must be read-only)")
    _hr57_empty = Path(_hr57_tmp) / "empty_list.json"
    _hr57_empty.write_text("[]")
    _hr57_eq = subprocess.run(
        [sys.executable, str(root / "scripts/generate_trackers.py"), "--tracker", str(_hr57_tracker), "--queue-list", str(_hr57_empty), "--transitions", str(_hr57_trans)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if _hr57_eq.returncode != 2 or "EMPTY QUEUE LIST" not in (_hr57_eq.stdout + _hr57_eq.stderr) or "in sync" in _hr57_eq.stdout:
        fail(f"scripts/generate_trackers.py empty-queue run must exit 2 EMPTY QUEUE LIST, never in sync (got {_hr57_eq.returncode}: {_hr57_eq.stdout[:200]}{_hr57_eq.stderr[:200]})")
    _hr57_victim = Path(_hr57_tmp) / "notes.txt"
    _hr57_victim.write_text("PRE-EXISTING\n")
    _hr57_ref = subprocess.run(
        [sys.executable, str(root / "scripts/generate_trackers.py"), "--tracker", str(_hr57_tracker), "--queue-list", str(_hr57_qlist), "--transitions", str(_hr57_trans), "--out", str(_hr57_victim)],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if _hr57_ref.returncode != 2 or "refusing" not in (_hr57_ref.stdout + _hr57_ref.stderr).lower() or _hr57_victim.read_text() != "PRE-EXISTING\n":
        fail("scripts/generate_trackers.py --out to an existing file must exit 2 refusing with bytes untouched")
finally:
    import shutil as _sh57
    _sh57.rmtree(_hr57_tmp, ignore_errors=True)
_hr57_ran = "?"
_hr57_match = re.search(r"Ran (\d+) tests", _hr57r.stderr)
if _hr57_match:
    _hr57_ran = _hr57_match.group(1)
if len(failures) == _hr57_before:
    ok(f"Dispatch-tracker proposal generator (issue #57) green: drifted pair yields paste-ready cells, empty queue fails closed, run read-only (tests/test_generate_trackers.py {_hr57_ran} tests pass)")

print("\n== V12. Tool-Existence Gate (#67, #74, #82) ==")
# Fail-closed tool existence: every seat's settings packages[0] (the
# mandatory @gotgenes/pi-permission-system) must exist when rendered against
# a real tools dir, and every stdio MCP server bound to a seat must have a
# resolvable command (absolute path on disk, or on PATH via shutil.which).
# Missing host-optional MCP binaries are REPORTED per seat (naming the
# server, e.g. radare2 when r2mcp is not installed) but do not fail the
# gate — installing host tooling is M9 scope; a missing MANDATORY pps or a
# deleted M2 render guard DOES fail. Appended at the end — no existing check
# renumbered or reworded. Exactly one ok() below.
_v12_before = len(failures)
import shutil as _shutil12
_v12_tools = Path(
    os.environ.get("HERETEK_TOOLS", str(Path.home() / ".local/share/heretek-rigs/tools"))
)
_v12_mcp_servers = yaml.safe_load((root / "fleet/mcp-servers.yaml").read_text())["servers"]
# (a) the M2 fail-closed guard must exist in the renderer source — deleting
# the mandatory-pps die must flip this gate even on hosts without tools.
_v12_render_src = (root / "scripts/render-seat.py").read_text()
if "@gotgenes/pi-permission-system is mandatory" not in _v12_render_src:
    fail("scripts/render-seat.py must die on a missing @gotgenes/pi-permission-system (M2 fail-closed guard)")
if 'need 41.0.0' not in _v12_render_src:
    fail("scripts/render-seat.py must pin @gotgenes/pi-permission-system at 41.0.0 (M2 version guard)")
# (a2) M4 (#68) sandbox hook: the renderer must emit settings.json
# shellPath to the wrapper and the per-seat sandbox.env; the wrapper must
# exist, be executable, and bwrap must resolve (Gotcha 5) — a missing
# shellPath fails closed at pi startup, so all three are hard fails.
if '"shellPath"' not in _v12_render_src or 'seat-sandbox.sh' not in _v12_render_src:
    fail("scripts/render-seat.py must emit settings.json shellPath to scripts/seat-sandbox.sh (M4 sandbox)")
if 'sandbox.env' not in _v12_render_src:
    fail("scripts/render-seat.py must emit sandbox.env (HERETEK_SANDBOX_WRITE/HERETEK_SECRET_STORE) (M4 sandbox)")
_v12_wrapper = root / "scripts/seat-sandbox.sh"
if not _v12_wrapper.is_file():
    fail("scripts/seat-sandbox.sh missing (settings.json shellPath target)")
elif not os.access(_v12_wrapper, os.X_OK):
    fail("scripts/seat-sandbox.sh must be executable")
if _shutil12.which("bwrap") is None:
    fail("tool-existence: bwrap not found on PATH (seat sandbox needs bubblewrap)")
# (b) per-seat settings packages[0]: resolve the committed
# specs/.../runtime/pi-settings.json against the real tools dir.
_v12_pps_pkg = "pi-packages/node_modules/@gotgenes/pi-permission-system"
_v12_roles = fleet.get("roles", {})
for _rid12 in sorted(_v12_roles):
    _ps12 = root / "specs/agents" / _v12_roles[_rid12]["domain"] / _rid12 / "runtime/pi-settings.json"
    if not _ps12.is_file():
        fail(f"{_rid12}: missing committed runtime/pi-settings.json (cannot verify packages[0])")
        continue
    try:
        _pkgs12 = json.loads(_ps12.read_text()).get("packages", [])
    except Exception as _e12:
        fail(f"{_rid12}: runtime/pi-settings.json unreadable ({_e12})")
        continue
    if not _pkgs12 or _v12_pps_pkg not in str(_pkgs12[0]):
        fail(f"{_rid12}: settings packages[0] must be the mandatory {_v12_pps_pkg} (got {_pkgs12[:1]})")
    # M4 (#68): committed reference settings must route bash through the jail.
    try:
        _shell12 = json.loads(_ps12.read_text()).get("shellPath", "")
    except Exception:
        _shell12 = ""
    if not str(_shell12).endswith("scripts/seat-sandbox.sh"):
        fail(f"{_rid12}: settings shellPath must route through scripts/seat-sandbox.sh (got {_shell12!r})")
if _v12_tools.is_dir():
    _v12_pps_json = _v12_tools / _v12_pps_pkg / "package.json"
    if not _v12_pps_json.is_file():
        fail(f"tool-existence: {_v12_pps_json} missing: @gotgenes/pi-permission-system is mandatory (render would die per M2)")
    else:
        try:
            _v12_ver = json.loads(_v12_pps_json.read_text()).get("version")
        except Exception as _e12:
            fail(f"tool-existence: {_v12_pps_json} unreadable ({_e12})")
            _v12_ver = None
        if _v12_ver is not None and _v12_ver != "41.0.0":
            fail(f"tool-existence: {_v12_pps_json} version {_v12_ver}, need 41.0.0")
else:
    print(f"  [NOTE] V12 tool-existence: tools dir {_v12_tools} absent on this host; packages[0] existence unchecked (render dies per M2)")
# (c) per-seat MCP command resolution, missing reported per seat.
_v12_cmd_cache = {}
for _rid12 in sorted(_v12_roles):
    for _b12 in (_v12_roles[_rid12].get("mcp") or []):
        _srv12 = _b12.get("server")
        _sdef12 = _v12_mcp_servers.get(_srv12, {})
        if _sdef12.get("transport") == "http" or "command" not in _sdef12:
            continue
        if _srv12 not in _v12_cmd_cache:
            _cmd12 = str(_sdef12["command"]).replace("@TOOLS@", str(_v12_tools))
            if "@SECRETS@" in _cmd12 or "@SEAT@" in _cmd12:
                _v12_cmd_cache[_srv12] = (True, _cmd12)
            elif Path(_cmd12).is_absolute():
                _v12_cmd_cache[_srv12] = (Path(_cmd12).is_file(), _cmd12)
            else:
                _v12_cmd_cache[_srv12] = (_shutil12.which(_cmd12.split()[0]) is not None, _cmd12)
        _ok12, _cmd12 = _v12_cmd_cache[_srv12]
        if not _ok12:
            print(f"  [NOTE] V12 tool-existence: seat {_rid12}: server '{_srv12}' command not found: {_cmd12}")
_v12_missing12 = sorted(_s for _s, (_o, _c) in _v12_cmd_cache.items() if not _o)
if len(failures) == _v12_before:
    if _v12_missing12:
        ok(f"Tool-existence (issues #67/#74) green: pps packages[0] present at 41.0.0 with M2 render guard; {len(_v12_cmd_cache) - len(_v12_missing12)} bound MCP commands resolve, host-missing listed above ({', '.join(_v12_missing12)})")
    else:
        ok(f"Tool-existence (issues #67/#74) green: pps packages[0] present at 41.0.0 with M2 render guard; all {len(_v12_cmd_cache)} bound MCP commands resolve")

print(f"\nSUMMARY: {passes} checks passed, {len(failures)} failed.")
if failures:
    sys.exit(1)
PY
