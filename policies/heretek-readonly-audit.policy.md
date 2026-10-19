---
source: custom
name: heretek-readonly-audit
surface: config
policy_schema_version: 1
description: Strict read-only and docs-only posture for Executive, PM, Architecture, QA Gate, and Defensive Security / Red-Team seats.
default_posture: deny
allow: [run_toolchain, rig_up, rig_down]
ask: []
deny: [push_to_remote, create_pr, publish_package, merge_or_release, force_push, delete_files]
destructive_class: [delete_everything, drop_persistent_store, reset_or_discard_vcs, delete_files, force_push]
---

# Heretek Read-Only Audit Policy

Enforces strict Principle of Least Privilege (PoLP) for the 16 non-code-mutating roles (`exec-director`, `product-director`, `tpm-scrum-lead`, `system-architect`, `tech-docs-lead`, `ux-research-analyst`, `sre-incident-eng`, `release-qa-officer`, `threat-modeler`, `appsec-engineer`, `cloud-sec-auditor`, `compliance-auditor`, `ai-red-teamer`, `binary-reverse-eng`, `firmware-sec-analyst`, `git-drift-coord`), recorded in OpenRig as `builtin:locked` and enforced at runtime by `@gotgenes/pi-permission-system@41.0.0` with `"*..*": "deny"` traversal defense.
