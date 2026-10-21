#!/usr/bin/env python3
"""Fleet topology model, referential-integrity gates, and renderers.

Reads the canonical catalog (fleet/fleet.yaml, fleet/mcp-servers.yaml,
fleet/skills-lock.json) plus generated trees (specs/, rigs/) and produces:

  - graph.json            machine-readable nodes + edges (single source for tooling)
  - org-chart.svg/.mmd    15 pods + command pod, cross-pod edges by kind
  - rig-<id>.svg          per-rig agent graph (intra-pod edges)
  - bipartite-<id>.svg    per-rig seat x {skills, mcp, packages} wiring
  - matrix.md             51-row agent x resources table
  - advisory.md           orphan / omni-divergence findings (non-blocking)

Validators are fail-closed (exit 1). Advisory findings warn only (exit 0).

Usage:
  python3 scripts/topology.py --out <dir> [--no-svg] [--check-only]
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_PI_PACKAGES = {
    "@ff-labs/pi-fff@0.11.0",
    "@gotgenes/pi-permission-system@41.0.0",
    "@narumitw/pi-lsp@0.49.10",
    "@nicknisi/pi-ast-grep@0.3.1",
    "pi-ast-grep@0.1.0",
    "pi-btw@0.8.0",
    "pi-lens@4.4.4",
    "pi-lsp-extension@1.4.0",
    "pi-mcp-adapter@5.4.0",
    "pi-web-access@0.44.0",
}
EDGE_KINDS = {"delegates_to", "spawned_by", "can_observe", "collaborates_with", "escalates_to"}


def load():
    with open(os.path.join(ROOT, "fleet", "fleet.yaml")) as f:
        fleet = yaml.safe_load(f)
    with open(os.path.join(ROOT, "fleet", "mcp-servers.yaml")) as f:
        mcp = yaml.safe_load(f)["servers"]
    with open(os.path.join(ROOT, "fleet", "skills-lock.json")) as f:
        lock = json.load(f)["skills"]
    return fleet, mcp, lock


def skill_ids(skills):
    out = []
    for tier in ("openrig_core", "shared", "role_local"):
        for it in skills.get(tier, []) or []:
            out.append((tier, it["id"] if isinstance(it, dict) else it))
    return out


def role_dir(role):
    hits = glob.glob(os.path.join(ROOT, "specs", "agents", "*", role))
    return hits[0] if hits else None


class Report:
    def __init__(self):
        self.blocking = []
        self.advisory = []

    def fail(self, msg):
        self.blocking.append(msg)

    def warn(self, msg):
        self.advisory.append(msg)

    def ok(self):
        return not self.blocking


def validate(fleet, mcp_cat, lock, rep):
    roles = fleet["roles"]
    sessions = {d["session"] for d in roles.values()}
    # Command-pod seats are also reachable at their omni-fleet address.
    for m in fleet.get("omni", {}).get("core_pod", {}).get("members", []):
        sessions.add(f"command-{m}@{fleet.get('omni', {}).get('id', 'heretek-omni-fleet')}")

    # 1. reports_to resolves to a real seat session
    for rid, d in sorted(roles.items()):
        rt = d.get("reports_to")
        if rt and rt.get("address") not in sessions:
            rep.fail(f"reports_to unresolvable: {rid} -> {rt.get('address')}")

    # 2. collaborators are known roles
    for rid, d in sorted(roles.items()):
        for c in d.get("collaborators", []) or []:
            if c not in roles:
                rep.fail(f"unknown collaborator: {rid} -> {c}")

    # 3. skill ids exist in lock + on disk
    for rid, d in sorted(roles.items()):
        for tier, sid in skill_ids(d.get("skills", {})):
            if tier == "role_local":
                rd = role_dir(rid)
                if rd is None:
                    rep.fail(f"role dir missing on disk: {rid}")
                elif not os.path.isfile(os.path.join(rd, "skills", sid, "SKILL.md")):
                    rep.fail(f"role-local skill missing: {rid} -> skills/{sid}/SKILL.md")
            else:
                if sid not in lock:
                    rep.fail(f"shared skill not in lock: {rid} -> {sid}")
                elif not os.path.isfile(os.path.join(ROOT, "specs", "agents", "_shared", "skills", sid, "SKILL.md")):
                    rep.fail(f"shared skill missing on disk: {sid}")

    # 4. mcp bindings exist in catalog
    for rid, d in sorted(roles.items()):
        for m in d.get("mcp", []) or []:
            srv = m["server"] if isinstance(m, dict) else m
            if srv not in mcp_cat:
                rep.fail(f"unknown mcp server: {rid} -> {srv}")

    # 5. pi_packages allowlist
    for rid, d in sorted(roles.items()):
        for p in d.get("pi_packages", []) or []:
            if p not in ALLOWED_PI_PACKAGES:
                rep.fail(f"unlisted pi_package: {rid} -> {p}")

    # 6. rig.yaml members match fleet (both directions), including the omni rig
    for rig in list(fleet["rigs"]) + [fleet.get("omni", {})]:
        if not rig.get("id"):
            continue
        rig_path = os.path.join(ROOT, "rigs", rig["id"], "rig.yaml")
        try:
            with open(rig_path) as fh:
                ry = yaml.safe_load(fh)
        except (OSError, yaml.YAMLError) as err:
            rep.fail(f"rig.yaml unreadable: {rig['id']}: {err}")
            continue
    # 6. rig.yaml members match fleet (both directions), including the omni rig
    for rig in list(fleet["rigs"]) + [fleet.get("omni", {})]:
        if not rig.get("id"):
            continue
        ry = yaml.safe_load(open(os.path.join(ROOT, "rigs", rig["id"], "rig.yaml")))
        disk_members = {}
        for pod in ry.get("pods", []):
            for m in pod.get("members", []):
                mid = m["id"] if isinstance(m, dict) else m
                disk_members[mid] = pod["id"]
        if rig["id"] == fleet.get("omni", {}).get("id"):
            core_pod = fleet["omni"]["core_pod"]
            fleet_members = {
                m["id"] if isinstance(m, dict) else m: core_pod["id"]
                for m in core_pod.get("members", [])
            }
        else:
            fleet_members = {r: d["pod"] for r, d in roles.items() if d.get("rig") == rig["id"]}
        for mid, pod in sorted(fleet_members.items()):
            if mid not in disk_members:
                rep.fail(f"fleet role missing from rig.yaml: {rig['id']} lacks {mid}")
            elif disk_members[mid] != pod:
                rep.fail(f"pod mismatch: {mid} fleet={pod} rig.yaml={disk_members[mid]}")
        for mid in sorted(disk_members):
            if mid not in fleet_members:
                rep.fail(f"rig.yaml member not in fleet: {rig['id']}/{mid}")

    # 7. member fragments == all 51 roles
    frags = {}
    for fp in glob.glob(os.path.join(ROOT, "rigs", "heretek-omni-fleet", "members", "*.yaml")):
        fd = yaml.safe_load(open(fp))
        frags[fd["id"]] = fp
    if set(frags) != set(roles):
        rep.fail(f"member fragments != 51 roles: missing={sorted(set(roles) - set(frags))} extra={sorted(set(frags) - set(roles))}")

    # 8. edge endpoints exist; no self-edges; known kinds
    for rig in fleet["rigs"]:
        for pod in rig.get("pods", []):
            members = set()
            for m in pod.get("members", []):
                members.add(m["id"] if isinstance(m, dict) else m)
            if pod.get("lead") not in members:
                rep.fail(f"pod lead not a member: {rig['id']}/{pod['id']} lead={pod.get('lead')}")
            for e in pod.get("edges", []):
                if e["kind"] not in EDGE_KINDS:
                    rep.fail(f"unknown edge kind: {rig['id']}/{pod['id']} {e}")
                if e["from"] not in members or e["to"] not in members:
                    rep.fail(f"pod edge endpoint missing: {rig['id']}/{pod['id']} {e}")
                if e["from"] == e["to"]:
                    rep.fail(f"self-edge: {rig['id']}/{pod['id']} {e}")
        pods = {p["id"]: set(m["id"] if isinstance(m, dict) else m for m in p.get("members", [])) for p in rig.get("pods", [])}
        for e in rig.get("edges", []):
            if e["kind"] not in EDGE_KINDS:
                rep.fail(f"unknown rig edge kind: {rig['id']} {e}")
            for side in ("from", "to"):
                if "." not in e[side]:
                    rep.fail(f"rig edge not pod.member qualified: {rig['id']} {e}")
                else:
                    p, m = e[side].split(".", 1)
                    if p not in pods or m not in pods[p]:
                        rep.fail(f"rig edge endpoint missing: {rig['id']} {e}")

    # --- advisory ---
    referenced = set()
    for d in roles.values():
        for _, sid in skill_ids(d.get("skills", {})):
            referenced.add(sid)
    vendored = {os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "specs", "agents", "_shared", "skills", "*"))}
    for sid in sorted(vendored - referenced):
        rep.warn(f"orphan vendored skill (referenced by no role): {sid}")
    bound = {m["server"] if isinstance(m, dict) else m for d in roles.values() for m in d.get("mcp", []) or []}
    for srv in sorted(set(mcp_cat) - bound):
        rep.warn(f"mcp server bound to no role: {srv}")
    for rid, d in sorted(roles.items()):
        if not skill_ids(d.get("skills", {})):
            rep.warn(f"role loads zero skills: {rid}")
    omni_div = [(rid, d["reports_to"]["address"]) for rid, d in sorted(roles.items())
                if d.get("reports_to") and "@heretek-omni-fleet" not in d["reports_to"]["address"]]
    if omni_div:
        rep.warn(f"{len(omni_div)} reports_to addresses point at static rigs (unresolvable inside heretek-omni-fleet; command pod is the practical escalation point)")


def build_graph(fleet, mcp_cat, lock):
    nodes, edges = [], []
    seen = set()

    def add_n(nid, ntype, **kw):
        if nid not in seen:
            seen.add(nid)
            nodes.append({"id": nid, "type": ntype, **kw})

    roles = fleet["roles"]
    for rig in fleet["rigs"]:
        add_n(f"rig:{rig['id']}", "rig", title=rig.get("title", ""))
        for pod in rig.get("pods", []):
            pid = f"pod:{pod['id']}"
            add_n(pid, "pod", rig=rig["id"], lead=pod.get("lead"))
            edges.append({"from": f"rig:{rig['id']}", "to": pid, "kind": "contains", "scope": rig["id"]})
            for m in pod.get("members", []):
                mid = m["id"] if isinstance(m, dict) else m
                sid = f"seat:{pod['id']}-{mid}@{rig['id']}"
                add_n(sid, "seat", role=mid, pod=pod["id"], rig=rig["id"])
                edges.append({"from": pid, "to": sid, "kind": "contains", "scope": f"{rig['id']}/{pod['id']}"})
            for e in pod.get("edges", []):
                edges.append({"from": f"seat:{pod['id']}-{e['from']}@{rig['id']}",
                              "to": f"seat:{pod['id']}-{e['to']}@{rig['id']}",
                              "kind": e["kind"], "scope": f"{rig['id']}/{pod['id']}"})
        for e in rig.get("edges", []):
            fp, fm = e["from"].split(".", 1)
            tp, tm = e["to"].split(".", 1)
            edges.append({"from": f"seat:{fp}-{fm}@{rig['id']}", "to": f"seat:{tp}-{tm}@{rig['id']}",
                          "kind": e["kind"], "scope": rig["id"]})
    omni = fleet.get("omni", {})
    add_n("pod:command", "pod", rig="heretek-omni-fleet", lead="exec-director")
    for m in omni.get("core_pod", {}).get("members", []):
        add_n(f"seat:command-{m}@heretek-omni-fleet", "seat", role=m, pod="command", rig="heretek-omni-fleet")
    for e in omni.get("core_pod", {}).get("edges", []):
        edges.append({"from": f"seat:command-{e['from']}@heretek-omni-fleet",
                      "to": f"seat:command-{e['to']}@heretek-omni-fleet",
                      "kind": e["kind"], "scope": "heretek-omni-fleet/command"})
    for rid, d in sorted(roles.items()):
        sid = f"seat:{d['pod']}-{rid}@{d['rig']}"
        for tier, sk in skill_ids(d.get("skills", {})):
            add_n(f"skill:{sk}", "skill")
            edges.append({"from": sid, "to": f"skill:{sk}", "kind": f"loads-{tier}", "scope": rid})
        for m in d.get("mcp", []) or []:
            srv = m["server"] if isinstance(m, dict) else m
            add_n(f"mcp:{srv}", "mcp")
            edges.append({"from": sid, "to": f"mcp:{srv}", "kind": "binds", "scope": rid})
        for p in d.get("pi_packages", []) or []:
            add_n(f"pkg:{p}", "package")
            edges.append({"from": sid, "to": f"pkg:{p}", "kind": "loads", "scope": rid})
        rt = d.get("reports_to")
        if rt:
            edges.append({"from": sid, "to": f"seat:{rt['address']}", "kind": "reports_to", "scope": rid})
        for c in d.get("collaborators", []) or []:
            if c in roles:
                cd = roles[c]
                edges.append({"from": sid, "to": f"seat:{cd['pod']}-{c}@{cd['rig']}",
                              "kind": "collaborates_with", "scope": rid})
    return {"nodes": nodes, "edges": edges}


def dot_escape(s):
    return s.replace('"', '\\"')


def render_orgchart(fleet, path):
    lines = ["digraph omni {", '  rankdir=LR;', '  node [shape=box, style=rounded];']
    for rig in fleet["rigs"]:
        for pod in rig.get("pods", []):
            lines.append(f'  "{pod["id"]}" [label="{pod["id"]} ({len(pod.get("members", []))})\\nlead: {pod.get("lead")}\\n{rig["id"]}"];')
    lines.append('  "command" [label="command (3)\\nlead: exec-director\\nheretek-omni-fleet", style="rounded,filled"];')
    for rig in fleet["rigs"]:
        for e in rig.get("edges", []):
            a, b = e["from"].split("."), e["to"].split(".")
            lines.append(f'  "{a[0]}" -> "{b[0]}" [label="{e["kind"]}\\n{a[1]} → {b[1]}"];')
    lines.append("}")
    open(path + ".dot", "w").write("\n".join(lines) + "\n")
    subprocess.run(["dot", "-Tsvg", path + ".dot", "-o", path + ".svg"], check=True)
    mmd = ["graph LR"]
    for rig in fleet["rigs"]:
        for pod in rig.get("pods", []):
            mmd.append(f'    {pod["id"]}["{pod["id"]} ({len(pod.get("members", []))})"]')
    for rig in fleet["rigs"]:
        for e in rig.get("edges", []):
            a, b = e["from"].split("."), e["to"].split(".")
            mmd.append(f'    {a[0]} -- "{e["kind"]}" --> {b[0]}')
    open(path + ".mmd", "w").write("\n".join(mmd) + "\n")


def render_rig(fleet, rig_id, path):
    rig = next(r for r in fleet["rigs"] if r["id"] == rig_id)
    lines = [f'digraph "{rig_id}" {{', "  rankdir=TB;", '  node [shape=box, style=rounded];']
    for pod in rig.get("pods", []):
        lines.append(f'  subgraph "cluster_{pod["id"]}" {{')
        lines.append(f'    label="{pod["id"]} (lead: {pod.get("lead")})";')
        for m in pod.get("members", []):
            mid = m["id"] if isinstance(m, dict) else m
            lines.append(f'    "{pod["id"]}.{mid}" [label="{mid}"];')
        for e in pod.get("edges", []):
            lines.append(f'    "{pod["id"]}.{e["from"]}" -> "{pod["id"]}.{e["to"]}" [label="{e["kind"]}"];')
        lines.append("  }")
    for e in rig.get("edges", []):
        lines.append(f'  "{e["from"]}" -> "{e["to"]}" [label="{e["kind"]}", style=dashed];')
    lines.append("}")
    open(path + ".dot", "w").write("\n".join(lines) + "\n")
    subprocess.run(["dot", "-Tsvg", path + ".dot", "-o", path + ".svg"], check=True)


def render_bipartite(fleet, rig_id, path):
    rig = next(r for r in fleet["rigs"] if r["id"] == rig_id)
    roles = fleet["roles"]
    lines = [f'digraph "bipartite-{rig_id}" {{', "  rankdir=LR;",
               '  node [shape=box, style=rounded];']
    for pod in rig.get("pods", []):
        for m in pod.get("members", []):
            mid = m["id"] if isinstance(m, dict) else m
            d = roles[mid]
            lines.append(f'  "seat:{mid}" [label="{mid}"];')
            for _, sk in skill_ids(d.get("skills", {})):
                lines.append(f'  "skill:{sk}" [shape=ellipse];')
                lines.append(f'  "seat:{mid}" -> "skill:{sk}";')
            for mcp in d.get("mcp", []) or []:
                srv = mcp["server"] if isinstance(mcp, dict) else mcp
                lines.append(f'  "mcp:{srv}" [shape=component];')
                lines.append(f'  "seat:{mid}" -> "mcp:{srv}" [style=dashed];')
            for p in d.get("pi_packages", []) or []:
                short = p.split("@")[0]
                lines.append(f'  "pkg:{short}" [shape=diamond];')
                lines.append(f'  "seat:{mid}" -> "pkg:{short}" [style=dotted];')
    lines.append("}")
    open(path + ".dot", "w").write("\n".join(lines) + "\n")
    subprocess.run(["dot", "-Tsvg", path + ".dot", "-o", path + ".svg"], check=True)


def short_pkg(p):
    name = p[1:] if p.startswith("@") else p
    return name.split("@")[0].split("/")[-1]


def render_matrix(fleet, path):
    roles = fleet["roles"]
    L = ["| Role | Rig / Pod | Lead | Policy | Skills (core/shared/local) | MCP | Packages | Reports to |",
         "|---|---|---|---|---|---|---|---|"]
    for rid, d in sorted(roles.items()):
        sk = d.get("skills", {})
        counts = "/".join(str(len(sk.get(k, []) or [])) for k in ("openrig_core", "shared", "role_local"))
        mcp = ",".join(m["server"] if isinstance(m, dict) else m for m in d.get("mcp", []) or []) or "—"
        pkgs = ",".join(short_pkg(p) for p in d.get("pi_packages", []) or [])
        rt = (d.get("reports_to") or {}).get("address", "—")
        lead = "yes" if d.get("pod_lead") else "no"
        L.append(f"| `{rid}` | `{d.get('rig')}` / `{d.get('pod')}` | {lead} | `{d.get('permission_policy')}` | {counts} | {mcp} | {pkgs} | `{rt}` |")
    open(path, "w").write("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-svg", action="store_true")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    try:
        fleet, mcp_cat, lock = load()
    except Exception as e:  # fail-closed: unparseable catalog is a blocking defect
        print(f"FAIL catalog unreadable: {e}")
        print("topology: 1 blocking failure(s)")
        sys.exit(1)
    rep = Report()
    try:
        validate(fleet, mcp_cat, lock, rep)
    except Exception as e:  # fail-closed: malformed catalog/rig data
        rep.fail(f"catalog malformed during validation: {type(e).__name__}: {e}")
    for msg in rep.blocking:
        print(f"FAIL {msg}")
    if not rep.ok():
        print(f"topology: {len(rep.blocking)} blocking failure(s)")
        sys.exit(1)
    print(f"topology: all referential-integrity checks passed ({len(fleet['roles'])} roles)")
    if args.check_only:
        return
    os.makedirs(args.out, exist_ok=True)
    graph = build_graph(fleet, mcp_cat, lock)
    json.dump(graph, open(os.path.join(args.out, "graph.json"), "w"), indent=1)
    print(f"topology: graph.json ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")
    have_dot = not args.no_svg and shutil.which("dot") is not None
    if not args.no_svg and not have_dot:
        print("topology: graphviz `dot` not found; skipping SVG render")
    if have_dot:
        render_orgchart(fleet, os.path.join(args.out, "org-chart"))
        for rig in fleet["rigs"]:
            render_rig(fleet, rig["id"], os.path.join(args.out, f"rig-{rig['id']}"))
            render_bipartite(fleet, rig["id"], os.path.join(args.out, f"bipartite-{rig['id']}"))
        print("topology: org-chart + per-rig + bipartite SVGs rendered")
    render_matrix(fleet, os.path.join(args.out, "matrix.md"))
    with open(os.path.join(args.out, "advisory.md"), "w") as fh:
        fh.write("# Topology advisory findings (non-blocking)\n\n")
        for msg in rep.advisory:
            print(f"WARN {msg}")
            fh.write(f"- {msg}\n")
        if not rep.advisory:
            fh.write("None.\n")


if __name__ == "__main__":
    main()
