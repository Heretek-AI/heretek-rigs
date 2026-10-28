// Pinned RigSpec key allowlists vendored from @openrig/cli@0.7.4
// packages/daemon/src/domain/rigspec-schema.ts (commit 6d9e8e27).
//
// Provenance: this file is the vendored upstream bytes that
// schemas/rigspec-keys.pinned.json and scripts/verify-rigs.sh diff against
// fail-closed. Refresh recipe (shell host with network):
//   npm pack @openrig/cli@0.7.4 && tar -xzf openrig-cli-0.7.4.tgz package/daemon/assets \
//   git -C <openrig-checkout> show 6d9e8e27:packages/daemon/src/domain/rigspec-schema.ts \
// then diff RIG_KEYS/POD_KEYS/MEMBER_KEYS/EDGE_KEYS/EDGE_KINDS below against the
// upstream export and update this file + schemas/rigspec-keys.pinned.json +
// scripts/verify-rigs.sh together. The verifier fails when this file is absent
// or when its key sets disagree with the live sets (kept alongside the existing
// local-local diff as defense-in-depth).
export const RIG_KEYS = [
  "version",
  "name",
  "summary",
  "culture_file",
  "permission_policy",
  "managed_blocks",
  "docs",
  "startup",
  "services",
  "workspace",
  "pods",
  "edges",
  "non_interruptive",
  "env",
] as const;

export const POD_KEYS = [
  "id",
  "label",
  "summary",
  "continuity_policy",
  "startup",
  "members",
  "edges",
] as const;

export const MEMBER_KEYS = [
  "id",
  "label",
  "agent_ref",
  "profile",
  "runtime",
  "codex_config_profile",
  "model",
  "effort",
  "advisor",
  "role",
  "permission_policy",
  "claude_permissions",
  "codex_permissions",
  "cwd",
  "restore_policy",
  "compaction_strategy",
  "mechanic",
  "startup",
  "session_source",
  "starter_ref",
  "env",
  "agent_file",
  "append_system_prompt_file",
  "plugin_dirs",
] as const;

export const EDGE_KEYS = ["kind", "from", "to"] as const;

export const EDGE_KINDS = [
  "delegates_to",
  "spawned_by",
  "can_observe",
  "collaborates_with",
  "escalates_to",
] as const;
