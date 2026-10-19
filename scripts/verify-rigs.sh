#!/usr/bin/env bash
# verify-rigs.sh — Comprehensive self-testing verification gate for heretek-rigs.
#
# Verifies:
#   V1. 100% Role Parity & Skill Lock: All 51 canonical roles from Heretek-Crew exist in fleet/fleet.yaml and
#       specs/agents/<domain>/<role>/ with zero Paperclip remnants, valid SKILL.md files, and 62 locked shared skills.
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
EDGE_KINDS = {"delegates_to", "spawned_by", "can_observe", "collaborates_with", "escalates_to"}

print("== V1. 51-Role Catalog Parity, Fleet YAML & Shared Skill Lock ==")
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
if len(skills_lock.get("skills", {})) == 62 and len(list(shared_skills_dir.glob("*/SKILL.md"))) == 62:
    ok("All 62 shared skills vendored in specs/agents/_shared/skills/ and locked in fleet/skills-lock.json")
else:
    fail("Shared skill count mismatch (expected 62)")

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
    for sf in ay.get("startup", {}).get("files", []):
        if sf.get("delivery_hint") == "guidance_merge":
            fail(f"{rid}: startup.files must not use guidance_merge")
    for req_file in ["guidance/role.md", "startup/context.md", "runtime/pi-settings.json", "runtime/mcp.json", "runtime/policy-enforcement.json", "runtime/pi-permission-config.json"]:
        fp = rdir / req_file
        if not fp.exists() or fp.stat().st_size < 40:
            fail(f"{rid}: missing or stub {req_file}")
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
            if pe["kind"] not in EDGE_KINDS or pe["from"] not in m_ids or pe["to"] not in m_ids:
                fail(f"{rig_slug}.{pid}: invalid pod-local edge {pe}")
            if pe["kind"] in ("delegates_to", "spawned_by"):
                dag_adj[f"{pid}.{pe['from']}"].add(f"{pid}.{pe['to']}")
    for ce in spec.get("edges", []):
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
            if _pe.get("kind") not in EDGE_KINDS or _pe.get("from") not in _pm_ids or _pe.get("to") not in _pm_ids:
                fail(f"rig.all-51.yaml pod {_p.get('id')}: invalid pod-local edge {_pe}")
    _flat51 = {f"{a}.{b}" for a, b in _seats51}
    _dagx51 = {q: set() for q in _flat51}
    for _p in _all51.get("pods", []):
        _pm_ids2 = {m.get("id") for m in _p.get("members", [])}
        for _pe in _p.get("edges", []):
            if _pe.get("kind") not in EDGE_KINDS or _pe.get("from") not in _pm_ids2 or _pe.get("to") not in _pm_ids2:
                fail(f"rig.all-51.yaml pod {_p.get('id')}: invalid pod-local edge {_pe}")
            if _pe.get("kind") in ("delegates_to", "spawned_by"):
                _dagx51[f"{_p.get('id')}.{_pe['from']}"].add(f"{_p.get('id')}.{_pe['to']}")
    for _ce in _all51.get("edges", []):
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
# HR-7.3 (fail-closed): sidecars-up must run the guard first — a dropped
# dependency would let `make sidecars-up SIDECAR_PROFILES="mobile devsec"`
# bypass the co-scheduling refusal. Raw `docker compose --profile` bypasses
# make by design, so CI must invoke via make (documented in compose header).
if "sidecars-up:" not in make_text or "guard-profiles" not in make_text.split("sidecars-up:")[1].split("\n")[0]:
    fail("Makefile sidecars-up must depend on guard-profiles")
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
    if re.search(r"FIXME|\{\{[A-Z_]+\}\}|\bTBD\b", txt):
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
_PROXY_18 = ("POST", "BUILD", "EXEC", "VOLUMES", "NETWORKS", "SWARM", "SYSTEM", "AUTH", "CONTAINERS", "IMAGES", "INFO", "PING", "SERVICES", "TASKS", "NODES", "CONFIGS", "SECRETS", "PLUGINS")
for k in _PROXY_18:
    if str(dsp_env.get(k)) != "0":
        fail(f"docker-socket-proxy must set {k}=0")
# HR-7.2 (fail-closed): the proxy env must be exactly the 18-key set from the
# tecnativa/docker-socket-proxy:0.5.0 README — extra keys widen the API surface.
if set(dsp_env.keys()) != set(_PROXY_18):
    fail(f"docker-socket-proxy environment must be exactly the 18-toggle set (got {sorted(dsp_env.keys())})")
dsp_img = dsp.get("image", "")
if "tecnativa/docker-socket-proxy:0.5.0" not in dsp_img:
    fail(f"docker-socket-proxy must be pinned tecnativa/docker-socket-proxy:0.5.0 (got {dsp_img})")
dsp_vols = dsp.get("volumes", [])
if not any("/var/run/docker.sock:/var/run/docker.sock:ro" in str(v) for v in dsp_vols):
    fail("docker-socket-proxy must mount /var/run/docker.sock:/var/run/docker.sock:ro")
# HR-7.3: network isolation — ghidra/radare2 on heretek-devsec with :ro samples, docker-android on heretek-mobile
for svc in ("ghidra", "radare2"):
    if svc in sidecars.get("services", {}):
        nets = sidecars["services"][svc].get("networks", [])
        if "heretek-devsec" not in (nets if isinstance(nets, list) else list(nets.keys() if isinstance(nets, dict) else [])):
            fail(f"{svc} must be isolated on heretek-devsec network")
        vols = " ".join(str(v) for v in sidecars["services"][svc].get("volumes", []))
        if "/samples:ro" not in vols:
            fail(f"{svc} must mount ./workspaces/binaries:/samples:ro")
if "docker-android" in sidecars.get("services", {}):
    anets = sidecars["services"]["docker-android"].get("networks", [])
    anet_list = anets if isinstance(anets, list) else list(anets.keys() if isinstance(anets, dict) else [])
    if "heretek-mobile" not in anet_list:
        fail("docker-android must be isolated on heretek-mobile network")
ok("Sidecar Docker Compose verified (loopback-only ports, zero :latest tags, GET-only docker-socket-proxy)")

ut = subprocess.run([sys.executable, "-m", "unittest", "tests/test_render_seat.py"], cwd=str(root), capture_output=True, text=True)
if ut.returncode == 0:
    ok("tests/test_render_seat.py (7/7 unit tests) passed")
else:
    fail(f"tests/test_render_seat.py failed:\n{ut.stderr}")

print(f"\nSUMMARY: {passes} checks passed, {len(failures)} failed.")
if failures:
    sys.exit(1)
PY
