---
source: custom
name: heretek-builder-standard
surface: config
policy_schema_version: 1
description: Scoped builder posture for engineering and active QA seats — local toolchain and scoped writes allowed; outward/history-rewriting acts denied or gated.
default_posture: allow
allow: [run_toolchain]
ask: [push_to_remote, create_pr, publish_package, merge_or_release, force_push]
deny: []
destructive_class: [delete_everything, drop_persistent_store, reset_or_discard_vcs]
---

# Heretek Builder Standard Policy

Allows local compilation, unit/integration testing, and role-scoped directory writes while enforcing `@gotgenes/pi-permission-system@41.0.0` `path_write` globs, `"*..*": "deny"` path traversal protection, and explicit `bash` allow-lists.
