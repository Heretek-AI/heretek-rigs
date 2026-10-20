# Heretek-Rigs Prompt Enhancement Pass (`PROMPT_REVIEW.md`)

**Target Repository:** `Heretek-AI/heretek-rigs` (51-seat OpenRig v0.6.11 fleet, Pi Coding Agent v1.3.0, `@gotgenes/pi-permission-system@41.0.0`, `opencode-go/muse-spark-1.3-contributor:high`)
**Reference System Prompts Analyzed Fresh:**
- `Anthropic/claude-fable-5.1.md` (474,916 bytes, 8,742 lines; `official/2026-09-01-claude-fable-5.1.md` lineage)
- `Anthropic/claude-opus-5.5.md` (477,020 bytes, 8,262 lines; `official/2026-09-22-claude-opus-5.5.md` lineage)

## 1. Review Scope & Audit Order

### 1.1 Pilot Seat (`exec-director`)
- **Files Reviewed:** `specs/agents/executive/exec-director/guidance/role.md`, `specs/agents/executive/exec-director/startup/context.md`, `specs/agents/executive/exec-director/runtime/policy-enforcement.json`, and upstream `Heretek-Crew@5ffb1fc` `roles/exec-director/AGENTS.md`.
- **Posture:** `builtin:locked`, `readonly_charter: true`, `path_write: ["docs/executive/*"]`, `bash_allow: ["git status*", "git diff*", "git log --oneline*", "git show --stat*", "rig whoami*", "rig ps*", "rig queue*", "rig send*", "rig capture*", "rig transcript*"]`, bound MCP servers `github` (`issues` read-only) and `memory` (`mcp__memory__*`).
- **Baseline Gaps Identified:**
  1. **Flat Refusal Guidance:** Section 6 states *"A denial reports one blocked command and one rule -- never a capability. Never conclude a tool is unavailable from a single denial"*, and *"Before reporting a blocked capability: retry bare, then read `extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl` and quote its `command` and `matchedPattern` verbatim."* However, it provides no **decision tree over `matchedPattern`** to distinguish (a) a strippable terminal bash syntax/flag guard (`*;*`, `*|*`, `*--output*`, `* -p*`, `*\t-p*`) where a bare retry succeeds, from (b) a path/scope guard (`*..*`, `fleet/*`, `scripts/*`, `.git/*`, `.pi/*`, `.agents/*`, `AGENTS.md`, `*.env*`, or out-of-scope `path_write`) where retrying bare still fails and immediate queue handoff is required, vs. (c) a tool-level lock (`code_rewrite`, `lsp_rename`, `lsp_code_actions`, or unbound `mcp`).
  2. **Missing Anti-Fabrication / Provenance Invariant:** Section 7 requires reporting artifact paths and verification commands/results, but lacks an explicit epistemic floor prohibiting the seat from guessing `qitem-...` IDs, commit SHAs, or command outputs when a tool call is denied or unexecuted (`BLOCKED` / `UNVERIFIED:`).
  3. **Passive Skill-Loading Instruction:** Section 5 says *"Load a skill by reading its SKILL.md when the task matches its description"* without binding high-risk operational moments (slice completion, turn closure, human escalation, compaction restore) to mandatory pre-action `read` calls.
  4. **Unbound `mcp__memory__*` & Executive Decision Calibration:** Section 3 and Section 4 do not distinguish draft agent proposals from ratified Human Board mandates (`[stated]` origin test) or transient single-slice state (`NOTES.md`) from durable 30-day policy (`STRATEGY.md`, `OKRS.md`, `mcp__memory__*`).
  5. **Minor Generator Punctuation Artifact:** `scripts/generate-rigs.py` emits `f"- Wake policy: {wake}."` where `wake` already ends with a period, producing a double period (`..`) at the end of Section 6.

### 1.2 Fleet Constitution (`rigs/*/CULTURE.md`)
- **Files Reviewed:** All 8 `rigs/<rig>/CULTURE.md` files (generated identically from `culture_text` in `scripts/generate-rigs.py`).
- **Baseline Assessment:** Concise 6-bullet constitution covering `verification-before-completion`, bare-retry + `command`/`matchedPattern` log quoting, `PENDING_DISPATCH` vs `DISPATCHED`, fail-closed handoff on `@gotgenes/pi-permission-system@41.0.0` denial, small slices, and `0600` `!cat` secret hygiene.
- **Enhancement Opportunity:** Adding three constitutional clauses (3-way denial taxonomy, live tool-result provenance / `UNVERIFIED:` labeling, and effect-based boundary compliance + 1–2 sentence post-tool turn receipts) hardens all 8 rigs at the constitutional level without touching the other 50 individual seat charters during the pilot phase.

### 1.3 Remaining 50 Seat Charters (`specs/agents/<domain>/<role>/guidance/role.md`)
Reviewed across the 5 structural cohorts defined in `fleet/fleet.yaml`:

| Cohort | Seat Count | Representative Seats | Permission & Tool Posture | Charter Enhancement Needs (Post-Pilot) |
| :--- | :--- | :--- | :--- | :--- |
| **Read-Only Governance, Architecture & Security Auditors** | 16 (incl. `exec-director`) | `product-director`, `system-architect`, `tpm-scrum-lead`, `git-drift-coord`, `tech-docs-lead`, `appsec-engineer`, `threat-modeler`, `cloud-sec-auditor`, `compliance-auditor`, `binary-reverse-eng`, `firmware-sec-analyst`, `ai-red-teamer`, `release-qa-officer`, `sre-incident-eng`, `ux-research-analyst` | `builtin:locked`, `readonly_charter: true`, writes confined to `docs/*` or `sbom/*` | Need P1–P6 (universal) + P7 (memory/chain calibration where `memory`/`codebase-memory` bound) + P8 (steelmanned tradeoff & non-binary audit/sign-off framing). |
| **Locked Adversarial & Static-Analysis Evaluators** | 2 | `sabotage-qa-tester`, `static-analysis-lead` | `builtin:locked`, `readonly_charter: false` (`tests/chaos/*`, `docs/qa/*`) | High risk of command-flag denials during mutation/SAST sweeps; need P1–P6 + P8 (evidence-backed fault/SAST triage). |
| **Pod Leads (Implementation & Domain)** | 15 (7 in `readonly_charter`, 8 in `builtin:standard`) | `ts-node-fullstack`, `rust-systems-spec`, `engine-systems-eng`, `game-systems-dev`, `cloud-platform-eng`, `dba-specialist`, `mlops-serving-eng`, `android-mobile-spec`, `ui-ux-designer` | Mix of `builtin:locked` and `builtin:standard`; own pod `LEARNED.md` and `continuity_policy` | Need P1–P6 + P7 (`LEARNED.md` pod-level distillation & dispatcher outbox supersession closure per `queue-handoff`). |
| **Standard Builder Specialists (with MCP)** | 30 | `go-backend-eng`, `python-backend-spec`, `cpp-lowlevel-eng`, `k8s-orchestrator`, `data-pipeline-eng`, `vector-rag-spec`, `e2e-browser-qa`, `dependency-patcher`, etc. | `builtin:standard`, scoped `path_write` (`src/*`, `tests/*`, `infra/*`, etc.) + language test `bash_allow` | Need P1–P6 + P7 (`codebase-memory` read-before-write calibration). |
| **Zero-MCP Specialist Seats** | 3 | `brand-copy-spec`, `mlops-serving-eng`, `tech-artist-pipeline` | `mcp: []` (`runtime/mcp.json` is `{"mcpServers": {}}`, 23 bytes); rely solely on Pi built-ins + `bash_allow` | Must NOT receive MCP-specific instructions; need P1–P6 universal generator clauses only. |

### 1.4 Shared Skills Spot-Check (`specs/agents/_shared/skills/*/SKILL.md`)
Spot-checked 8 of the 64 vendored shared skills before considering any skill-layer changes:

| Skill ID | Upstream Source (`fleet/skills-lock.json`) | Key Existing Rules Verified | Verdict on Skill-File Edits |
| :--- | :--- | :--- | :--- |
| `openrig-operating-model` | `npm:@openrig/cli@0.6.11` | §2 Grid (`CULTURE.md`, `LEARNED.md`, `SPEC.md`, `NOTES.md`, `PROOF.md`); §4.7 `TRIGGER POINTERS` ("when X happens, read Y"); §6.2 ("Shipped things belong to their authors... never by an instance editing in place"). | **Do NOT edit vendored `SKILL.md`.** Surface trigger pointers in Charter §5 (P6) and Horizon/Origin rules in Charter §3/§4 (P7). |
| `mission-slice-sop` | `npm:@openrig/cli@0.6.11` | Light Part-A loop; `PROOF.md` honesty ("State plainly what is proven and what is **not**; an honest 'this half is untested' is worth more than a checkmark"); terminal ghost-text autocomplete trap (`rig capture`). | **Do NOT edit vendored `SKILL.md`.** Bind slice-close in Charter §5 to reading `mission-slice-sop` (P6). |
| `verification-before-completion` | `obra/superpowers@bb92a77` | Iron Law (`NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE`); 5-step Gate Function (`IDENTIFY → RUN → READ → VERIFY → CLAIM`); bans `"should"`, `"probably"`, `"seems to"`. | **Do NOT edit vendored `SKILL.md`.** Promote its anti-rationalization & fresh-evidence gate into always-resident Charter §7 / `CULTURE.md` (P3, P5) so it holds even before the skill is read. |
| `queue-handoff` | `npm:@openrig/cli@0.6.11` | Hot-potato terminal-turn rule; drafted-park failure (`draft != throw` — last act must be an EDIT or SEND); dispatcher outbox supersession audit; `--body-file` hygiene (no raw backticks or large dumps inline); default-nudge semantics (omit `--no-nudge` in live loops; `--notify` does not exist). | **Do NOT edit vendored `SKILL.md`.** Reinforce terminal-turn receipt in Charter §6 (P5) and add pre-handoff trigger pointer in Charter §5 (P6). |
| `messaging-the-human` | `npm:@openrig/cli@0.6.11` | `rig gateway human list --json` address discovery (`<entityId>@external`, never guessed); `--human-intent decision|update`; `--body-file` 100–150w phone brief; `posted` proves connector posting, not human readership. | **Do NOT edit vendored `SKILL.md`.** Add explicit trigger pointer in Charter §5 before any human escalation (P6). |
| `delegating-work` | `npm:@openrig/cli@0.6.11` | Context-holding agent vs. blank-slate subagent test ("would a wrong-but-plausible answer here be detectable?"); hand over intent + requester's words, not narrow step lists. | **Do NOT edit vendored `SKILL.md`.** Reference in Charter §5 trigger pointers (P6). |
| `seat-continuity-and-handover` | `npm:@openrig/cli@0.6.11` | Two-outcome honesty model (`continuityOutcome` vs `seatBindingOutcome` recorded independently); `rig context recap-write` requiring `## Decisions, with reasons` and `UNVERIFIED:` lines. | **Do NOT edit vendored `SKILL.md`.** Adopt `UNVERIFIED:` / `BLOCKED` marker convention directly into Charter §7 and `CULTURE.md` (P3). |
| `refocusing` | `npm:@openrig/cli@0.6.11` | Plain-command `trace-to-root.py` invocation (no shell loops, variables, or `cd`); consuming delivered topology/work traces on restore. | **Do NOT edit vendored `SKILL.md`.** Reference in Charter §5 orientation/compaction trigger pointer (P6). |

**Why Fleet-Wide Skill Edits Are Rejected in Favor of Resident Charter / `CULTURE.md` Edits:**
1. Every directory under `specs/agents/_shared/skills/` is tree-hashed into `fleet/skills-lock.json` and verified by `scripts/verify-rigs.sh` V1 (`_recomputed != _smeta.get("tree")`) against pinned upstream checkouts (`obra/superpowers@bb92a77`, `@openrig/cli@0.6.11`, etc.).
2. More importantly, skills are **lazy-loaded on demand**. In the real incident, the failure occurred when a seat hit a `pi-permission-system` denial before loading `verification-before-completion` or `openrig-operating-model`. Putting denial-taxonomy and anti-fabrication gates in `CULTURE.md`, `guidance/role.md`, and `startup/context.md` guarantees they are active on Turn 0.

## 2. Incident Chain Analysis (Method §3.2)

**Real Incident Reconstructed (also evidenced in `docs/NOTES.md` M1–M6):**
A seat attempted a command or path operation that triggered a `@gotgenes/pi-permission-system@41.0.0` denial (`permission.rejected` or a rule match in `extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl`). The seat:
1. **Link 1 (Trigger → Misclassification):** Treated a single command/pattern denial as proof that the entire *tool* (`bash`, `read`, or `write`) was globally disabled for the seat.
2. **Link 2 (Over-Generalization → Premature Abandonment / Blind Loops):** Either repeated the exact same blocked invocation 3+ times until hitting a hard stop or abandoned all remaining allowed commands in the slice instead of stripping forbidden shell metacharacters/flags or handing off the out-of-scope path.
3. **Link 3 (Unverified Gap → Fabricated Evidence):** When formatting its completion/status output, synthesized plausible command outputs, verification claims, or `qitem-...` IDs rather than reporting `BLOCKED` / `UNVERIFIED:` with the verbatim denial log entry.

### Link-by-Link Evaluation Against Anthropic System Prompt Techniques

| Incident Link | Anthropic Techniques That Prevent This Link (Transferred & Adapted) | Anthropic Techniques That Do NOT Transfer (Dropped with Reason) |
| :--- | :--- | :--- |
| **Link 1:** Command-scoped denial → concluded entire *tool* was banned | **1. Error-Taxonomic Refusal Dispatch** (`claude-fable-5.1.md#memory_filesystem` L748–785; `claude-opus-5.5.md#memory_filesystem` L376–395: *"Which sentence depends on the refusal error alone"*): Anthropic separates mechanical/format rejections (version/match errors → fix syntax & retry immediately) from scoped content rejections (strip only the refused element & retry the permitted remainder once) and hard `<never_store>` boundaries (stop immediately). Adapted to `@gotgenes/pi-permission-system@41.0.0`, seats must branch on `matchedPattern`: (a) 15 terminal bash syntax/flag denies (`*;*`, `*|*`, `*>*`, `*<*`, `*&*`, `` `*` ``, `*$*`, `*(*`, `*)*`, `*--output*`, `* -p*`, `*\t-p*`, `*--patch*`, `*--full-diff*`, `*--textconv*`) → strip operator/flag and retry bare once; (b) path/scope guards (`*..*`, `fleet/*`, `scripts/*`, `.git/*`, `.pi/*`, `.agents/*`, `AGENTS.md`, `*.env*`, or `path_write`) → tool still works on allowed paths, hand off the blocked path; (c) locked tool (`code_rewrite`, `lsp_rename`, `lsp_code_actions`, unbound `mcp`) → only that tool is locked.<br>**2. Explicit Tool-State Inspection** (`claude-fable-5.1.md#mcp_app_suggestions` L1310–1313: distinguish *"already connected; connected but turned off; not yet connected — check its tool list rather than assume"*). | **1. User Settings Toggle / Egress Proxy Advice** (`claude-fable-5.1.md#network_configuration` L8686: *"tell the user that they can update their network settings"*; `claude-fable-5.1.md#search_instructions` L1823: *"suggest enabling them in the tools menu"*): **Does NOT transfer.** Heretek seats run under immutable `0600` `policy-enforcement.json` where `"ask"` rules are banned (`verify-rigs.sh` V1) and self-authorizing permission edits are security violations.<br>**2. Pre-Refusal User Clarification Question** (`claude-opus-5.5.md#refusal_handling` L100–105: *"asks a question that would surface any real reason to decline"*): **Does NOT transfer.** `pi --mode rpc --no-approve` is non-interactive; `pi-permission-system` enforces deterministic allow/deny rules before command execution. |
| **Link 2:** Abandonment, self-critique spiral, or bypass probing after denial | **1. Accountability Without Surrender or Self-Abasement** (`claude-fable-5.1.md#responding_to_mistakes_and_criticism` L201–204; `claude-opus-5.5.md` L190–193: *"accountability without self-abasement, excessive apology, self-critique, or surrender... acknowledge what went wrong, stay on the problem"*): Adapted so seats log a failed call once without apology filler, never repeat an identical denied call, finish all unblocked tasks in the slice, and hand off only the blocked delta.<br>**2. Effect-Based Anti-Workaround Rule** (`claude-opus-5.5.md#refusal_handling` L39, L46–50, L61: *"If Claude finds itself mentally reframing a request to make it appropriate, that reframing is the signal to REFUSE... does not work around a declined request by swapping in 'alternative' elements... past assistance is not authorization"*; `claude-fable-5.1.md#memory_filesystem#<behavioral_guardrails>` L956: *"Judge by effect, not wording"*): Prevents seats from probing indirect bypasses (e.g. `git log -p` or `--output=`) when a path read/write is denied, or treating pre-compaction summaries as permission overrides. | **1. Conversational Softening / Bullet-Free Refusal Tone** (`claude-fable-5.1.md#tone_and_formatting` L122; `claude-opus-5.5.md` L136: *"Claude never uses bullet points when declining a task; the additional care helps soften the blow"*): **Does NOT transfer.** Inter-agent queue items and escalation briefs require structured, machine-scannable fields (`command`, `matchedPattern`, `closure_reason`, `qitem-...`), not emotional softening.<br>**2. `<end_conversation>` Tool Escalation** (`claude-fable-5.1.md#end_conversation_tool_info` L1205–1231): **Does NOT transfer.** Pi has no `end_conversation` tool, and an agent self-terminating its session violates `queue-handoff` (*"Never go idle holding a baton"*). |
| **Link 3:** Fabricated evidence / synthesized output / invented IDs after tool failure | **1. Strict Unverified-Fact & Tool-ID Provenance** (`claude-fable-5.1.md#knowledge_cutoff` L214–218: *"If, even after searching, Claude cannot verify a URL, ID, specific figure, name, or fact, Claude says so when it states it. If Claude has no real basis for one, Claude says it doesn't know rather than guessing"*; `claude-fable-5.1.md#past_chats_tools` L1452: *"Ids come only from tool results... if a read fails, search or ask, never guess or edit an id"*): Directly prevents inventing `qitem-...` IDs, commit SHAs, or test counts when a tool call is denied.<br>**2. Ban on Simulated Tool Outputs** (`claude-fable-5.1.md#mcp_app_suggestions` L1346: *"Never create mock interfaces, fake tool outputs, or simulated MCP experiences"*): Directly forbids synthesizing plausible stdout/stderr after a `bash` denial.<br>**3. Post-Write Confirmation Gate** (`claude-fable-5.1.md#memory_filesystem` L783–785: *"Nothing is kept until that new write succeeds, so never tell the user the rest was saved unless it has"*): Prevents claiming an artifact write or queue dispatch succeeded before receiving the tool result.<br>**4. Ban on Disingenuous Confidence Modifiers & Bare `"Done."`** (`claude-fable-5.1.md#tone_and_formatting` L128; `#reply_after_tool_calls` L135–138): Replaces `"honestly"`/`"genuinely"`/`"Done."` with a 1–2 sentence factual post-tool receipt. | **1. `<antml:cite index="DOC_INDEX-SENTENCE_INDEX">` XML Citation Wrapping & 15-Word Quote Cap** (`claude-fable-5.1.md#<citation_instructions>` L8597–8618; `#search_instructions` L1794–1798: *"15+ words from any single source is a SEVERE VIOLATION... Claims must be in your own words, never exact quoted text"*): **Actively harmful if transferred.** In `heretek-rigs`, paraphrasing tool output or capping quotes at 15 words **violates** the fleet's core rule (*"Evidence is raw output, never paraphrase"*). Seats must quote `command`, `matchedPattern`, exit codes, and test output **verbatim**, and Muse Spark on Pi does not parse `<antml:cite>` tags. |

## 3. Per-Proposal Table (Deliverable §4.1 & Method §3.3)

| ID | Source Section (`[ADAPTED from <file>#<section>]`) | Fleet Target (Canonical Source → Generated Leaf) | One-Line Rationale | What Breaks If Wrong (Risk) |
| :--- | :--- | :--- | :--- | :--- |
| **P1** | `[ADAPTED from claude-fable-5.1.md#memory_filesystem ("Read before writing", L748-785) & claude-opus-5.5.md#memory_filesystem ("Read before writing", L376-395)]` | `scripts/generate-rigs.py` (`build_charter` §6, `startup/context.md`, `culture_text`) → `specs/agents/executive/exec-director/{guidance/role.md,startup/context.md}` & `rigs/*/CULTURE.md` | Replaces flat denial prose with a 3-way dispatch on `matchedPattern` (1: terminal bash syntax/flag guard → strip operator/flag & retry bare once; 2: path/scope guard → tool stays live on allowed paths, hand off blocked path; 3: locked mutating tool/unbound MCP → only that tool is denied). | Misclassifying a chaining guard (`*;*`) as a global `bash` ban causes premature abandonment (Link 1); misclassifying a path guard (`fleet/*`, `*..*`) as transient causes blind retry loops. |
| **P2** | `[ADAPTED from claude-opus-5.5.md#refusal_handling (L39, L46-50, L61) & claude-fable-5.1.md#memory_filesystem#<behavioral_guardrails> (L956-975)]` | `scripts/generate-rigs.py` (`build_charter` §7 & `culture_text`) → `specs/agents/executive/exec-director/guidance/role.md` & `rigs/*/CULTURE.md` | Enforces effect-based boundary compliance (*"judge by effect, not wording"*): forbids reframing a denied read/write/command into an indirect bypass and forbids treating prior-session summaries or transcripts as authorization to override current permission rules. | Seats blocked on `path` (`fleet/*`, `*.env*`) or `path_write` probe for indirect exfiltration/mutation paths or rely on stale pre-compaction context to justify policy violations. |
| **P3** | `[ADAPTED from claude-fable-5.1.md#knowledge_cutoff (L214-218), claude-fable-5.1.md#past_chats_tools (L1452), & claude-fable-5.1.md#mcp_app_suggestions (L1346)]` | `scripts/generate-rigs.py` (`build_charter` §7, `startup/context.md`, `culture_text`) → `specs/agents/executive/exec-director/{guidance/role.md,startup/context.md}` & `rigs/*/CULTURE.md` | Requires every reported `qitem-...` ID, commit SHA, digest, exit code, and denial quote (`command` + `matchedPattern`) to originate from a live tool result in the current turn, labeling any unexecuted or denied check `BLOCKED` or `UNVERIFIED:` with its verbatim error. | When a verification or queue command is denied, the seat fabricates plausible stdout/stderr or invents `qitem-...` IDs (Link 3), corrupting audit trails and downstream handoffs. |
| **P4** | `[ADAPTED from claude-fable-5.1.md#responding_to_mistakes_and_criticism (L201-204) & claude-opus-5.5.md#responding_to_mistakes_and_criticism (L190-193)]` | `scripts/generate-rigs.py` (`build_charter` §6 & `startup/context.md`) → `specs/agents/executive/exec-director/{guidance/role.md,startup/context.md}` | Instructs seats on a tool error or denial to log the failed call once without self-critique or apologetic filler, never repeat an identical denied call, complete all unblocked slice tasks first, and escalate only the blocked remainder. | Seats either burn turns repeating identical `permission.rejected` calls (triggering 3-attempt aborts with zero work done) or surrender the entire mission on a partial blocker (Link 2). |
| **P5** | `[ADAPTED from claude-fable-5.1.md#reply_after_tool_calls (L135-138) & claude-fable-5.1.md#tone_and_formatting (L114, L128-133)]` | `scripts/generate-rigs.py` (`build_charter` §6 & §7, `culture_text`) → `specs/agents/executive/exec-director/guidance/role.md` & `rigs/*/CULTURE.md` | Requires turns to end after a state-advancing tool call with a 1–2 sentence factual receipt (artifact paths, verification command + exit status, successor `qitem-...` ID), bans bare `"Done."` and persuasion modifiers (`"honestly"`, `"genuinely"`, `"obviously"`, `"should pass"`), and requires verifying file existence via `read`/`ls`. | Seats emit bare `"Done."` or drafted-park self-instructions without a durable handoff, cite nonexistent files assumed from prompt context, or mask unrun checks with confidence modifiers. |
| **P6** | `[ADAPTED from claude-fable-5.1.md#computer_use##skills & ##additional_skills_reminder (L1500-1518, L1652-1656)]` | `scripts/generate-rigs.py` (`build_charter` §5) → `specs/agents/executive/exec-director/guidance/role.md` | Converts Section 5's passive one-liner into explicit moment-of-action trigger pointers (before slice sign-off → `mission-slice-sop`; before turn end/handoff → `queue-handoff` & `delegating-work`; before human escalation → `messaging-the-human`; on boot/compaction/drift → `openrig-operating-model`, `orienting-to-an-inherited-seat`, `session-compaction-and-restore`, `refocusing`). | Seats skip reading `SKILL.md` files because they assume pre-training familiarity, hitting CLI syntax footguns (`--notify` vs default nudge, inline backticks in `--body`, or guessed `@external` addresses). |
| **P7** | `[ADAPTED from claude-fable-5.1.md#memory_filesystem ("What's already filed" L246-318, "File format" L349-415, "Calibration" L519-613, "Read before writing" L615-655)]` | `.scratch/Heretek-Crew/roles/exec-director/AGENTS.md` (§3) & `scripts/generate-rigs.py` (`build_charter` §4) → `specs/agents/executive/exec-director/guidance/role.md` | Enforces read-before-write, in-place updates over duplication, the 30-day durability horizon (`STRATEGY.md`/`OKRS.md`/`mcp__memory__*` vs transient `NOTES.md`), and the `[stated]` origin test (only ratified Human Board mandates are recorded as committed policy; agent proposals stay labeled as drafts). | `exec-director` (or other `memory`/`codebase-memory` seats) duplicates memory nodes, pollutes durable memory with transient single-slice status, or records unapproved agent-drafted OKRs as ratified board mandates. |
| **P8** | `[ADAPTED from claude-fable-5.1.md#evenhandedness (L184-197) & claude-opus-5.5.md#evenhandedness (L173-186)]` | `.scratch/Heretek-Crew/roles/exec-director/AGENTS.md` (§3) → `specs/agents/executive/exec-director/guidance/role.md` | Requires strategic roadmaps, budget allocations, and architectural/milestone sign-offs to present steelmanned competing options, explicit cost/risk tradeoffs, and unresolved empirical dependencies, and to decline binary pass/fail sign-offs when verification evidence is incomplete or contested. | Executive, architectural, or security sign-offs collapse multi-variable engineering tradeoffs into one-sided advocacy or rubber-stamp incomplete milestone deliverables. |

## 4. Generalization Plan Across the Fleet (Method §3.4)

Once the `exec-director` pilot pattern is approved, the 8 proposals generalize across the repository's canonical source layers as follows:

| Scope Tier | Proposals | Canonical Source File(s) to Edit | Target Generated Leaves | Generalization Mechanics |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: `CULTURE.md` Constitutional Layer** | **P1, P2, P3, P5** (condensed constitutional invariants) | `scripts/generate-rigs.py` (`culture_text`) | All 8 `rigs/<rig>/CULTURE.md` files (already live in this pass) | Shared by all 51 seats via `rig.yaml` `culture_file: CULTURE.md` (`toldFiles` archive resolution). |
| **Tier 2: Universal Charter & Startup Layer (All 51 Seats)** | **P1, P2, P3, P4, P5, P6** (+ `wake.rstrip(".")` fix) | `scripts/generate-rigs.py` (`build_charter` §5, §6, §7 and `startup/context.md`) | All 51 `specs/agents/<domain>/<role>/{guidance/role.md,startup/context.md}` and materialized `rigs/*/agents/<role>/` copies | Promote `PILOT_ENHANCED_ROLES = {"exec-director"}` to `PILOT_ENHANCED_ROLES = set(fleet["roles"].keys())` (or remove the `is_pilot` guard) in `scripts/generate-rigs.py`. Dynamically tailor §5 skill trigger pointers from each seat's `r["skills"]` set (e.g. include `verification-before-completion` pointer whenever bound in `r["skills"]["shared"]`, `messaging-the-human` whenever bound in `r["skills"]["openrig_core"]`). |
| **Tier 3A: Memory-Bound Seats (48 Seats with `memory` or `codebase-memory` MCP)** | **P7** (MCP memory & chain-file calibration) | `scripts/generate-rigs.py` (`build_charter` §4 conditional on `any(b.get("server") in ("memory", "codebase-memory") for b in r.get("mcp", []))`) | 48 `specs/agents/<domain>/<role>/guidance/role.md` §4 (automatically skipped for the 3 zero-MCP seats `brand-copy-spec`, `mlops-serving-eng`, `tech-artist-pipeline` and seats without memory MCP) | Already coded conditionally in `scripts/generate-rigs.py`; promoting `PILOT_ENHANCED_ROLES` activates it across all memory-bound seats automatically. |
| **Tier 3B: Role-Specific Governance, Architecture & Audit Seats (18 Locked Seats)** | **P7 (origin test) & P8 (steelmanned tradeoffs / non-binary sign-offs)** | Upstream `Heretek-Crew/roles/<role>/AGENTS.md` §3 for the 18 `builtin:locked` roles (`exec-director`, `product-director`, `system-architect`, `tpm-scrum-lead`, `git-drift-coord`, `tech-docs-lead`, `appsec-engineer`, `threat-modeler`, `cloud-sec-auditor`, `compliance-auditor`, `binary-reverse-eng`, `firmware-sec-analyst`, `ai-red-teamer`, `release-qa-officer`, `sre-incident-eng`, `ux-research-analyst`, `sabotage-qa-tester`, `static-analysis-lead`) | Section 3 (`Core Responsibilities & Workflows`) of those 18 `guidance/role.md` charters | Role-specific wording: executive/PM seats enforce board/stakeholder mandate origin (`[stated]`) and roadmap tradeoff steelmanning; security/QA auditors enforce exploit-reachability vs. false-positive steelmanning (`fp-check`) and decline binary sign-offs when reproduction evidence is partial. |

## 5. Evaluated-and-Rejected Reference Sections (Method §3.5)

Every major section of both `claude-fable-5.1.md` and `claude-opus-5.5.md` was evaluated. The following 16 sections and techniques were **explicitly rejected**:

| # | Reference Section (`<file>#<section>`) | Summary of Anthropic Technique | Rejection Reason (Hard Rule / Architectural Incompatibility) |
| :--- | :--- | :--- | :--- |
| **R1** | `claude-fable-5.1.md#product_information` (L5–29) & `claude-opus-5.5.md#product_information` (L3–31) | Model self-identification as Claude Fable 5.1 / Mythos 5.1 / Opus 5.5, Anthropic product catalog (Claude Code, Claude Cowork, Claude Tag, Project Glasswing), export-control history, and `docs.claude.com` search routing. | **Violates Hard Rule 1 & Rule 2.** Heretek seats are scoped engineering operators running `opencode-go/muse-spark-1.3-contributor:high` on Pi (`runtime: pi`), verified by `verify-rigs.sh` V1 (`model != "opencode-go/muse-spark-1.3-contributor:high"` fails the gate). |
| **R2** | `claude-fable-5.1.md#refusal_handling#<critical_child_safety_instructions>`, CBRN/weapons, illicit substances, malicious code blanket ban, & song-lyric/SVG copyright rules (L34–89) | Consumer safety guardrails, harm-reduction website redirects (`dancesafe.org`), pre-1929 lyric cutoff, character/mascot SVG drawing bans, and declining all work on vulnerability exploits/malware even for education. | **Violates Hard Rule 1 & Role Charters.** Consumer safety/copyright boilerplate bloats operator tokens, and a blanket ban on analyzing exploits/malware would incapacitate `defensive-sec-and-red-team` (`appsec-engineer`, `binary-reverse-eng`, `firmware-sec-analyst`, `ai-red-teamer`, `threat-modeler`) and `sabotage-qa-tester`, which are explicitly chartered to analyze binaries in read-only `/samples:ro` sidecars and run fault-injection tests. |
| **R3** | `claude-opus-5.5.md#refusal_handling` pre-decline user questioning (L100–105: *"rather than declining... Claude says what it will help with and asks a question that would surface any real reason to decline"*) | Asking the user a clarifying social-context question (e.g., the Nadia pregnancy toast example) before deciding whether to refuse an ambiguous request. | **Violates Hard Rule 2 & Rule 3.** Seats execute in non-interactive RPC mode (`pi --mode rpc --no-approve`) under `@gotgenes/pi-permission-system@41.0.0`, where `"ask"` rules are strictly forbidden by `verify-rigs.sh` V1 (`if '"ask"' in json.dumps(pe): fail(...)`). Permission boundaries are deterministic and non-negotiable. |
| **R4** | `claude-opus-5.5.md#tone_and_formatting###lists_and_bullets` prose-only technical documentation rule (L133–135) | *"For reports, documents, technical documentation, and explanations, Claude writes prose without bullets, numbered lists, or excessive bolding (i.e. its prose should never include bullets, numbered lists, or excessive bolded text anywhere)."* | **Breaks OpenRig File Contracts.** OpenRig `SPEC.md`, `PROGRESS.md`, `PROOF.md`, `RECAP.md`, and executive `OKRS.md` / `SEC-*.md` advisories require structured Markdown headings (`## Mini-requirements`, `## Proof contract`, `## Decisions, with reasons`) and bulleted checklists. Banning bullets in technical docs would break `rig scope audit` and `rig context recap-write`. |
| **R5** | `claude-fable-5.1.md#tone_and_formatting` & `claude-opus-5.5.md#tone_and_formatting` no-bullet refusal rule & anti-quoting rule (Fable L100, L122; Opus L136) | *"Claude generally does not quote or paraphrase parts of the user's messages unless asked to, since this can come across as rude"* and *"Claude never uses bullet points when declining a task; the additional care helps soften the blow."* | **Directly Contradicts Fleet Evidence Rules.** `CULTURE.md` and `role.md` §6 mandate quoting `command` and `matchedPattern` **verbatim** and formatting structured blocker escalations. Refusing to quote inputs or avoiding structured bullets on a block degrades auditability. |
| **R6** | `claude-fable-5.1.md#legal_and_financial_advice` (L91–94) & `#user_wellbeing` (L140–173) | Disclaimers that Claude is not a lawyer, financial advisor, or licensed psychiatrist; crisis helpline routing; disordered-eating and self-harm counseling rules. | **Violates Hard Rule 1.** Pure consumer-assistant wellbeing and liability prose with zero applicability to autonomous software engineering seats. |
| **R7** | `claude-fable-5.1.md#anthropic_reminders` (L175–182) & Line 1 `<antml:voice_note>` ban | Handling Anthropic-injected classifier tags (`image_reminder`, `cyber_warning`, `ethics_reminder`, `ip_reminder`, `long_conversation_reminder`) and `<antml:voice_note>`. | **Violates Hard Rule 2.** Anthropic-specific classifier injections and `<antml:*>` XML blocks do not exist in Pi Coding Agent or OpenCode Go (`openai-responses` API). |
| **R8** | `claude-fable-5.1.md#memory_filesystem#<privacy_requirements>`, `<protected_attributes>`, `<sensitive_information>`, `<never_store>`, `<omission_guidance>`, `<forbidden_memory_phrases>`, `<appropriate_boundaries_re_memory>` (L791–1184) | Consumer personal-memory taxonomy (`/people/`, `/topics/`, `/profile.md`), server-side save-time consent checks for health/religion/ethnicity, sensitive-split write batching, and bans on saying *"Based on my memories"* to avoid sounding like surveillance. | **Violates Hard Rule 1 & Rule 2.** Seats do not manage consumer personal dossiers or platform consent popups. Moreover, `<forbidden_memory_phrases>` (hiding provenance of retrieved context) is the **exact opposite** of OpenRig's traceability rules (`openrig-operating-model` §5 & §7), where seats **must** cite which `SPEC.md`, `LEARNED.md`, `NOTES.md`, or `PROOF.md` file a constraint came from. |
| **R9** | `claude-fable-5.1.md#end_conversation_tool_info` (L1205–1231) & `claude-opus-5.5.md` (L725–751) | Two-step confirmation protocol for terminating a chat session via `<end_conversation>` when a user is abusive or asks to end. | **Violates Hard Rule 2 & `queue-handoff`.** Pi has no `end_conversation` tool; seats are resident workers (`execution_mode: interactive_resident`) governed by the hot-potato terminal-turn rule. |
| **R10** | `claude-fable-5.1.md#persistent_storage_for_artifacts` (`window.storage`), `#publishing_artifacts`, `#request_evaluation_checklist`, `#when_to_use_visualizer_for_inline_visuals`, `#anthropic_api_in_artifacts` (L1233–1307, L1659–1788, L8304–8595) | Browser `window.storage` API, `Artifact` publish tool, `present_files` mobile cards, `mcp__visualize__show_widget`, and calling `https://api.anthropic.com/v1/messages` with `claude-sonnet-4-6` inside sandboxed web artifacts. | **Violates Hard Rule 2.** None of these claude.ai UI tools exist in Pi. Furthermore, hardcoding `https://api.anthropic.com/v1/messages` violates the fleet's pinned inference endpoint (`https://opencode.ai/inference/go/v1`) and `outsideAddresses` registry manifest (`opencode.ai`, `github.com` only). |
| **R11** | `claude-fable-5.1.md#mcp_app_suggestions` consumer partner opt-in (`[third_party_mcp_app]`, `search_mcp_registry`, `suggest_connectors`) & `#suggest_catalog_plugins_and_skills` (`suggest_plugin_install`, `suggest_skills`) (L1308–1377) | Consumer partner picker cards (rideshare, trail guides) and UI cards suggesting plugin installations. | **Violates Hard Rule 2 & Rule 3.** In `heretek-rigs`, `profiles.default.uses.plugins` is strictly locked to `[]` (`verify-rigs.sh` V1 HR-2.3), MCP servers are statically bound per role in `fleet/fleet.yaml` with `mcp["*"]: "deny"`, and `tool_search` only discovers pre-bound `deferred` MCP servers (never `rig` commands or third-party registry apps). |
| **R12** | `claude-fable-5.1.md#past_chats_tools` (`conversation_search`, `recent_chats`, `read_conversation`, L1378–1497) & `#preferences_info` (`<userPreferences>`, `<userStyle>`, L1410–1497) | Searching consumer chat history by UUID/`page_token` and applying consumer hobby/profession `<userPreferences>`. | **Violates Hard Rule 2.** Pi seats do not have `conversation_search` or `<userPreferences>`; cross-session continuity in OpenRig uses `rig transcript`, `rig capture`, `LEARNED.md`, `RECAP.md`, and `NOTES.md`. (Only the tool-returned ID provenance rule from `past_chats_tools` L1452 was extracted into P3.) |
| **R13** | `claude-fable-5.1.md#computer_use` container paths (`/home/claude`, `/mnt/user-data/uploads`, `/mnt/user-data/outputs`, `/mnt/skills/public/*`) & `#package_management` (`pip install --break-system-packages`) (L1534–1640) | Writing scratch work to `/home/claude`, deliverables to `/mnt/user-data/outputs`, and installing ad-hoc pip/npm packages. | **Violates Hard Rule 2 & Rule 3.** In `heretek-rigs`, `external_directory: "deny"` and `*..*: "deny"` confine seats to their workspace `<cwd>` (`path_write` allowlist), skills live at `specs/agents/_shared/skills/<id>/SKILL.md` (or `agents/_shared/skills/<id>/SKILL.md`), and ad-hoc `pip`/`npm`/`curl` installs are denied by `bash_allow`. |
| **R14** | `claude-fable-5.1.md#search_instructions##CRITICAL_COPYRIGHT_COMPLIANCE` & `<citation_instructions>` (`<antml:cite>`, 15-word quote hard limit, mandatory paraphrasing, L1794–1962, L8597–8618) | Wrapping claims in `<antml:cite index="...">` and banning quotes >=15 words (*"DEFAULT to paraphrasing... Claims must be in your own words, never exact quoted text"*). | **Directly Violates Fleet Evidence Invariants.** Paraphrasing tool output or truncating log quotes at 15 words violates `CULTURE.md` and `role.md` §6 (*"Evidence is raw output, never paraphrase"*), which was the exact failure vector in Link 3 of the incident. |
| **R15** | `claude-fable-5.1.md#network_configuration` & `#filesystem_configuration` (L8680–8710) | `Allowed Domains: *`, egress proxy `x-deny-reason` user-settings advice, and `/mnt/*` read-only mounts. | **Violates Hard Rule 3.** Heretek sidecars are isolated on loopback (`127.0.0.1`) and internal Docker networks (`heretek-devsec`, `heretek-mobile`), and filesystem read/write guards are enforced by `@gotgenes/pi-permission-system@41.0.0` (`path` and `path_write` maps ending in `*..*: deny`). |
| **R16** | `claude-opus-5.5.md#thinking_behavior` (L8219–8222) | *"At the end of its thinking, Claude restates which language it should respond in."* | **Violates Hard Rule 2.** Claude-specific thinking-block postscript ritual; Muse Spark 1.3 Contributor uses OpenCode Go `thinkingLevelMap` (`high` / `xhigh` / `medium`) without `<antml:thinking>` language-restatement tags. |

## 6. Unified Diffs — Pilot-First (Deliverable §4.2 & Method §3.3)

Per Deliverable §4.2 (*"Unified diffs, pilot-first. Do not touch the other 50 charters until the pilot pattern is approved"*) and Hard Rule 4 (*"Edit sources, never generated leaves"*), all edits were applied to the canonical source files (`.scratch/Heretek-Crew/roles/exec-director/AGENTS.md` and `scripts/generate-rigs.py` with `PILOT_ENHANCED_ROLES = {"exec-director"}`). Running `python3 scripts/generate-rigs.py` updated **only** `specs/agents/executive/exec-director/{guidance/role.md,startup/context.md}` (and `rigs/*/CULTURE.md`), leaving all 50 other charters (`100/100` `role.md` and `context.md` files) **100% byte-identical** to baseline.

### 6.1 Tagged Source Diff 1: Upstream Pilot Role (`Heretek-Crew/roles/exec-director/AGENTS.md`)
- **Tags:**
  - `[ADAPTED from claude-fable-5.1.md#evenhandedness (L184-197) & claude-opus-5.5.md#evenhandedness (L173-186)]` (Proposal **P8**)
  - `[ADAPTED from claude-fable-5.1.md#memory_filesystem ("File format" L349-415 & "Calibration" L519-613) & claude-opus-5.5.md#memory_filesystem (L260-366)]` (Proposal **P7**)
- **One-Line Rationale:** Enforces steelmanned tradeoff analysis, non-binary milestone sign-offs when verification is incomplete, and strict separation between ratified Human Board mandates (`[stated]`) and unapproved agent proposals.
- **What Breaks If Wrong:** `exec-director` rubber-stamps contested architectural milestones with binary pass/fail verdicts or records unapproved draft OKRs/roadmaps as committed board policy in `docs/executive/STRATEGY.md`, `OKRS.md`, and `mcp__memory__*`.

```diff
--- a/roles/exec-director/AGENTS.md
+++ b/roles/exec-director/AGENTS.md
@@ -22,6 +22,9 @@
   - Human stakeholder executive briefs, market research summaries, quarterly OKR templates, escalation tickets from `product-director`.
 - **Expected Output Deliverables**:
   - Executive strategy documents (`docs/executive/STRATEGY.md`), approved company OKRs (`docs/executive/OKRS.md`), signed milestone charters, delegation briefs dispatched to openrig agent queues.
+- **Decision Provenance & Tradeoff Discipline**:
+  - Frame strategic roadmaps, budget allocations, and architectural sign-offs with steelmanned competing options, explicit cost/risk tradeoffs, and unresolved empirical dependencies; decline binary pass/fail sign-offs when verification evidence from `product-director` or `system-architect` is incomplete or contested.
+  - Record only ratified Human Board mandates as committed policy in `docs/executive/STRATEGY.md`, `docs/executive/OKRS.md`, and `mcp__memory__*`; keep unapproved agent proposals, candidate roadmaps, and single-slice working state labeled as draft proposals or in mission `NOTES.md` until human decision confirmation arrives.
 
 ## 4. Catalog
 
```

### 6.2 Tagged Source Diff 2: Deterministic Fleet Generator (`scripts/generate-rigs.py`)
- **Tags:**
  - `[ADAPTED from claude-fable-5.1.md#memory_filesystem ("Read before writing" L748-785) & claude-opus-5.5.md#memory_filesystem ("Read before writing" L376-395)]` (Proposal **P1**: 3-way refusal dispatch on `matchedPattern`)
  - `[ADAPTED from claude-opus-5.5.md#refusal_handling (L39, L46-50, L61) & claude-fable-5.1.md#memory_filesystem#<behavioral_guardrails> (L956-975)]` (Proposal **P2**: effect-based boundary compliance & no prior-session authorization override)
  - `[ADAPTED from claude-fable-5.1.md#knowledge_cutoff (L214-218), claude-fable-5.1.md#past_chats_tools (L1452), & claude-fable-5.1.md#mcp_app_suggestions (L1346)]` (Proposal **P3**: live tool-result provenance & `BLOCKED` / `UNVERIFIED:` labeling)
  - `[ADAPTED from claude-fable-5.1.md#responding_to_mistakes_and_criticism (L201-204) & claude-opus-5.5.md#responding_to_mistakes_and_criticism (L190-193)]` (Proposal **P4**: steady fault recovery, zero blind retries, complete unblocked slice tasks first)
  - `[ADAPTED from claude-fable-5.1.md#reply_after_tool_calls (L135-138) & claude-fable-5.1.md#tone_and_formatting (L114, L128-133)]` (Proposal **P5**: 1–2 sentence post-tool receipt, ban on bare `"Done."` and persuasion modifiers, verify files on disk)
  - `[ADAPTED from claude-fable-5.1.md#computer_use##skills & ##additional_skills_reminder (L1500-1518, L1652-1656)]` (Proposal **P6**: moment-of-action skill `read` trigger pointers)
  - `[ADAPTED from claude-fable-5.1.md#memory_filesystem ("What's already filed" L246-318, "Calibration" L519-613, "Read before writing" L615-655)]` (Proposal **P7**: read-before-write & 30-day horizon for `memory` / `codebase-memory` MCP)
- **One-Line Rationale:** Encodes P1–P7 at the generator source level with a `PILOT_ENHANCED_ROLES = {"exec-director"}` gate for seat charters/startup files and updates `culture_text` for `rigs/*/CULTURE.md`.
- **What Breaks If Wrong:** Editing generated leaves directly in `specs/` or `rigs/` would be wiped on the next `generate-rigs.py` run and desynchronize `bundle.yaml` SHA-256 file hashes, `packageDigest`, and `registry/status.json` `bodyDigest` (failing `verify-rigs.sh` V4/V5).

```diff
--- a/scripts/generate-rigs.py
+++ b/scripts/generate-rigs.py
@@ -60,6 +60,9 @@
 # via `git rev-parse HEAD` first and fails closed on dirty/missing checkouts.
 HERETEK_RIGS_COMMIT_FALLBACK = "SYNTHETIC-NO-GIT-PROVENANCE-UNVERIFIED"
 REVIEW_DATE = "2026-10-18"
+# Pilot-first prompt enhancement gate: apply enhanced charter/startup prompt patterns
+# only to the pilot seat until approved for fleet-wide 51-seat propagation.
+PILOT_ENHANCED_ROLES = {"exec-director"}
 
 
 def resolve_heretek_commit(root: Path, allow_synthetic: bool = False) -> str:
@@ -264,6 +267,7 @@
             .replace("Paperclip", "openrig")
         )
 
+    is_pilot = rid in PILOT_ENHANCED_ROLES
     if r.get("mcp"):
         mcp_lines = "\n".join(
             f"- `{b['server']}`"
@@ -275,6 +279,15 @@
             + f": tools are named `mcp__{b['server'].replace('-', '_')}__<tool>`."
             for b in r["mcp"]
         )
+        if is_pilot and any(
+            b.get("server") in ("memory", "codebase-memory") for b in r["mcp"]
+        ):
+            mcp_lines += (
+                "\n- Memory & chain-file calibration (`mcp__memory__*`, `LEARNED.md`, `NOTES.md`): "
+                "read existing entries before writing or claiming a gap; update in place rather than "
+                "duplicating; store only durable cross-session decisions and ratified constraints "
+                "(30-day horizon), never transient slice state or unverified command outputs."
+            )
     else:
         mcp_lines = (
             "- None. Use the built-in read/grep/find/ls tools and the bash allow-list."
@@ -286,6 +299,20 @@
         + [s["id"] for s in r["skills"]["role_local"]]
     )
     skills_lines = "\n".join(f"- `{s}`" for s in all_skill_ids)
+    if is_pilot:
+        skills_intro = "\n".join(
+            [
+                "Load a skill by reading its SKILL.md via the native `read` tool when the task matches its description (never rely on pre-training memory for OpenRig/fleet workflows):",
+                "",
+                "- Before claiming completion, signing off, or closing a slice: read `mission-slice-sop`.",
+                "- Before ending a turn, parking a blocker, or dispatching work: read `queue-handoff` and `delegating-work`.",
+                "- Before escalating a decision or update to the human operator: read `messaging-the-human`.",
+                "- On fresh boot, inherited seat, compaction restore, or context drift: read `openrig-operating-model`, `orienting-to-an-inherited-seat`, `session-compaction-and-restore`, and `refocusing`.",
+            ]
+        )
+    else:
+        skills_intro = "Load a skill by reading its SKILL.md when the task matches its description."
+
     esc = (
         f'`rig send {r["reports_to"]["address"]} "<message>"`'
         if r.get("reports_to")
@@ -303,6 +330,47 @@
         )
         or "read-only git only"
     )
+    wake_str = wake.rstrip(".") if is_pilot else wake
+
+    coord_lines = [
+        "- Work arrives as openrig queue items and `rig send` messages; follow `queue-handoff` and `mission-slice-sop`.",
+        f"- Escalate blockers to {esc}.",
+        f"- Writes are confined to: {writable}. A denial from pi-permission-system is final: hand off, never work around it.",
+        "- A denial reports one blocked command and one rule -- never a capability. Never conclude a tool is unavailable from a single denial.",
+        "- One command per `bash` call: no chaining (`;`), pipes (`|`), or redirection (`>`, `<`). A chained command is denied for the chain, not for its parts -- retry the exact command bare before reporting a block.",
+        "- `rig`/`queue`/`send` access is via `bash` allow-listed commands, not `tool_search` (no rig MCP tools exist). An empty `tool_search` proves nothing about rights.",
+        "- Before reporting a blocked capability: retry bare, then read `extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl` and quote its `command` and `matchedPattern` verbatim. Evidence is raw output, never paraphrase.",
+    ]
+    if is_pilot:
+        coord_lines.extend(
+            [
+                "- Classify every pi-permission-system denial by its `matchedPattern` before acting: (a) syntax/flag terminal guard (`*;*`, `*|*`, `*>*`, `*<*`, `*&*`, `` `*` ``, `*$*`, `*(*`, `*)*`, `*--output*`, `* -p*`, `*\\t-p*`, `*--patch*`, `*--full-diff*`, `*--textconv*`) -> strip the forbidden operator or flag and retry the bare allowed prefix once; (b) path/scope guard (`*..*`, `fleet/*`, `scripts/*`, `.git/*`, `.pi/*`, `.agents/*`, `AGENTS.md`, `*.env*`, or out-of-scope `path_write`) -> the tool remains active on allowed paths, so do not retry the blocked path and hand off via `rig queue`; (c) locked tool/server (`code_rewrite`, `lsp_rename`, `lsp_code_actions`, or unbound `mcp`) -> only that specific tool or server is denied while built-in `read`/`grep`/`find`/`ls`/`edit`/`write` and `bash` allow-listed commands remain available.",
+                "- On any tool error or denial, acknowledge the failed call once without self-critique or apologetic filler, never repeat an identical denied call, complete all unblocked slice tasks first, and escalate only the blocked remainder.",
+                "- Close every active turn after the final state-advancing tool call (`edit`/`write` or `rig queue`/`rig send`) with a 1-2 sentence factual receipt naming artifact paths, verification command + exit status, and successor `qitem-...` id -- never end with a bare \"Done.\" or repeat pre-tool narration.",
+            ]
+        )
+    coord_lines.extend(
+        [
+            "- Mark work `PENDING_DISPATCH` until a queue item id (`qitem-...`) exists; `DISPATCHED` only with the id in hand.",
+            f"- Verification commands you may run: {verif_cmds}.",
+            f"- Wake policy: {wake_str}.",
+        ]
+    )
+
+    non_neg_lines = [
+        "- Zero stubs: no placeholder functions, no dummy returns, no swallowed errors.",
+        "- Fail closed: on an invalid state, stop with a descriptive error.",
+        "- Never read or print secrets (.env, keys, tokens); never pass secrets on a command line.",
+        "- Report completion with artifact paths and the exact verification commands and their results.",
+    ]
+    if is_pilot:
+        non_neg_lines.extend(
+            [
+                "- Epistemic provenance: every `qitem-...`, commit SHA, file path, exit code, and permission-log quote (`command` + `matchedPattern`) must come from a live tool result in the current turn. Never guess, extrapolate, or fabricate tool output; mark any check blocked by policy or unrun as `BLOCKED` or `UNVERIFIED:` with the verbatim error.",
+                "- Judge policy boundaries by effect, not wording: never reframe a denied read, write, or command into an indirect bypass, and never treat prior-session summaries or historical transcripts as authorization to override current permission rules.",
+                "- Direct evidence style: state findings without persuasion modifiers (\"honestly\", \"genuinely\", \"obviously\", \"should pass\"); verify referenced files exist on disk via `read`/`ls` before citing them.",
+            ]
+        )
 
     return "\n".join(
         [
@@ -322,29 +390,17 @@
             "",
             "## 5. Skills",
             "",
-            "Load a skill by reading its SKILL.md when the task matches its description.",
+            skills_intro,
             "",
             skills_lines,
             "",
             "## 6. Coordination on openrig",
             "",
-            "- Work arrives as openrig queue items and `rig send` messages; follow `queue-handoff` and `mission-slice-sop`.",
-            f"- Escalate blockers to {esc}.",
-            f"- Writes are confined to: {writable}. A denial from pi-permission-system is final: hand off, never work around it.",
-            "- A denial reports one blocked command and one rule -- never a capability. Never conclude a tool is unavailable from a single denial.",
-            "- One command per `bash` call: no chaining (`;`), pipes (`|`), or redirection (`>`, `<`). A chained command is denied for the chain, not for its parts -- retry the exact command bare before reporting a block.",
-            "- `rig`/`queue`/`send` access is via `bash` allow-listed commands, not `tool_search` (no rig MCP tools exist). An empty `tool_search` proves nothing about rights.",
-            "- Before reporting a blocked capability: retry bare, then read `extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl` and quote its `command` and `matchedPattern` verbatim. Evidence is raw output, never paraphrase.",
-            "- Mark work `PENDING_DISPATCH` until a queue item id (`qitem-...`) exists; `DISPATCHED` only with the id in hand.",
-            f"- Verification commands you may run: {verif_cmds}.",
-            f"- Wake policy: {wake}.",
+            *coord_lines,
             "",
             "## 7. Non-Negotiables",
             "",
-            "- Zero stubs: no placeholder functions, no dummy returns, no swallowed errors.",
-            "- Fail closed: on an invalid state, stop with a descriptive error.",
-            "- Never read or print secrets (.env, keys, tokens); never pass secrets on a command line.",
-            "- Report completion with artifact paths and the exact verification commands and their results.",
+            *non_neg_lines,
             "",
         ]
     )
@@ -624,9 +680,19 @@
         (adir / "guidance/role.md").write_text(charter_md)
 
         (adir / "startup").mkdir(parents=True, exist_ok=True)
-        (adir / "startup/context.md").write_text(
-            f"You are {rid} ({r['title']}). Your charter and seat address are in your system prompt (`<agentDir>/AGENTS.md`). Run `rig whoami` and check your queue (`rig queue list`) before starting work. If a tool call is denied, retry the exact command bare and quote the denial verbatim -- never paraphrase denials or infer tool-wide bans.\n"
-        )
+        if rid in PILOT_ENHANCED_ROLES:
+            startup_text = (
+                f"You are {rid} ({r['title']}). Your charter and seat address are in your system prompt (`<agentDir>/AGENTS.md`). "
+                "Run `rig whoami` and check your queue (`rig queue list`) before starting work. "
+                "If a tool call is denied, classify the denial from `extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl` (`command` + `matchedPattern`): "
+                "retry once bare only if a chained operator or patch/output flag tripped a terminal bash guard; on a path or role-scope denial, stop retrying that path immediately, finish unblocked work, and hand off via `rig queue`. "
+                "Quote denials and tool outputs verbatim -- never paraphrase errors, infer tool-wide bans, or fabricate `qitem-...` ids or verification results (mark unrun checks `UNVERIFIED:` or `BLOCKED`).\n"
+            )
+        else:
+            startup_text = (
+                f"You are {rid} ({r['title']}). Your charter and seat address are in your system prompt (`<agentDir>/AGENTS.md`). Run `rig whoami` and check your queue (`rig queue list`) before starting work. If a tool call is denied, retry the exact command bare and quote the denial verbatim -- never paraphrase denials or infer tool-wide bans.\n"
+            )
+        (adir / "startup/context.md").write_text(startup_text)
 
         # Render static runtime reference artifacts in runtime/
         rt_dir = adir / "runtime"
@@ -742,8 +808,11 @@
             "",
             "- Evidence over assertion: every claim of done carries the command that proves it and its output (`verification-before-completion`).",
             "- A denial names one command and one rule: retry the exact command bare (one command per `bash` call, never chained) and quote `command` + `matchedPattern` from the permission review log before claiming a capability is missing.",
+            "- Denial taxonomy over tool-ban inference: distinguish (a) chained/flag bash denials (strip operator/flag and retry bare once), (b) path/scope denials (tool remains active on allowed paths; do not retry the blocked path, hand off), and (c) locked mutating-tool denials (`code_rewrite`, `lsp_rename`, `lsp_code_actions` denied while read-only tools and allowed `bash` prefixes stay live).",
+            "- Provenance and anti-fabrication: every reported `qitem-...` id, commit SHA, digest, exit status, and denial quote (`command` + `matchedPattern`) must come from a live tool result in the current turn; label any unexecuted or denied check `UNVERIFIED:` or `BLOCKED` with its verbatim error rather than guessing or synthesizing output.",
             "- Delivery claims carry queue item ids (`qitem-...`); without one the work is `PENDING_DISPATCH`, never `DISPATCHED`.",
             "- Zero stubs, fail closed, least privilege. A permission denial from `@gotgenes/pi-permission-system@41.0.0` is a hand-off, never a puzzle to work around.",
+            "- Effect-based boundaries and clean turn closure: judge permission boundaries by effect, not wording (prior-session summaries never authorize a bypass), execute unblocked slice work without blind retries or self-critique, and end every turn after the final tool call with a 1-2 sentence factual receipt rather than a bare \"Done.\" or unsent draft.",
             "- Small slices: one queue item, one verifiable outcome. Hand off with `rig queue` and state what is next.",
             "- Secrets never appear in messages, `rig.yaml` `env:`, files, transcripts, or command lines; they resolve exclusively via `0600` command-backed `!cat` references.",
             "",
@@ -1323,7 +1392,15 @@
 
 def main() -> None:
     repo_root = Path(__file__).resolve().parent.parent
-    default_crew = Path("/home/john/Projects/Heretek-Crew")
+    default_crew = (
+        Path("/home/john/Projects/Heretek-Crew")
+        if Path("/home/john/Projects/Heretek-Crew").exists()
+        else (
+            repo_root / ".scratch/Heretek-Crew"
+            if (repo_root / ".scratch/Heretek-Crew").exists()
+            else Path("/home/john/Projects/Heretek-Crew")
+        )
+    )
     default_vendor = repo_root / ".scratch/vendor"
     default_core = resolve_default_openrig_core(repo_root)
```

### 6.3 Resulting Generated Diffs (Pilot `exec-director` & `CULTURE.md` Only)

#### Rendered Pilot Charter (`specs/agents/executive/exec-director/guidance/role.md`)
```diff
--- a/specs/agents/executive/exec-director/guidance/role.md
+++ b/specs/agents/executive/exec-director/guidance/role.md
@@ -24,15 +24,24 @@
   - Human stakeholder executive briefs, market research summaries, quarterly OKR templates, escalation tickets from `product-director`.
 - **Expected Output Deliverables**:
   - Executive strategy documents (`docs/executive/STRATEGY.md`), approved company OKRs (`docs/executive/OKRS.md`), signed milestone charters, delegation briefs dispatched to openrig agent queues.
+- **Decision Provenance & Tradeoff Discipline**:
+  - Frame strategic roadmaps, budget allocations, and architectural sign-offs with steelmanned competing options, explicit cost/risk tradeoffs, and unresolved empirical dependencies; decline binary pass/fail sign-offs when verification evidence from `product-director` or `system-architect` is incomplete or contested.
+  - Record only ratified Human Board mandates as committed policy in `docs/executive/STRATEGY.md`, `docs/executive/OKRS.md`, and `mcp__memory__*`; keep unapproved agent proposals, candidate roadmaps, and single-slice working state labeled as draft proposals or in mission `NOTES.md` until human decision confirmation arrives.
 
 ## 4. MCP Servers & Tool Access
 
 - `github` (GitHub `issues` toolset, read-only): tools are named `mcp__github__<tool>`.
 - `memory`: tools are named `mcp__memory__<tool>`.
+- Memory & chain-file calibration (`mcp__memory__*`, `LEARNED.md`, `NOTES.md`): read existing entries before writing or claiming a gap; update in place rather than duplicating; store only durable cross-session decisions and ratified constraints (30-day horizon), never transient slice state or unverified command outputs.
 
 ## 5. Skills
 
-Load a skill by reading its SKILL.md when the task matches its description.
+Load a skill by reading its SKILL.md via the native `read` tool when the task matches its description (never rely on pre-training memory for OpenRig/fleet workflows):
+
+- Before claiming completion, signing off, or closing a slice: read `mission-slice-sop`.
+- Before ending a turn, parking a blocker, or dispatching work: read `queue-handoff` and `delegating-work`.
+- Before escalating a decision or update to the human operator: read `messaging-the-human`.
+- On fresh boot, inherited seat, compaction restore, or context drift: read `openrig-operating-model`, `orienting-to-an-inherited-seat`, `session-compaction-and-restore`, and `refocusing`.
 
 - `openrig-operating-model`
 - `mission-slice-sop`
@@ -58,9 +67,12 @@
 - One command per `bash` call: no chaining (`;`), pipes (`|`), or redirection (`>`, `<`). A chained command is denied for the chain, not for its parts -- retry the exact command bare before reporting a block.
 - `rig`/`queue`/`send` access is via `bash` allow-listed commands, not `tool_search` (no rig MCP tools exist). An empty `tool_search` proves nothing about rights.
 - Before reporting a blocked capability: retry bare, then read `extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl` and quote its `command` and `matchedPattern` verbatim. Evidence is raw output, never paraphrase.
+- Classify every pi-permission-system denial by its `matchedPattern` before acting: (a) syntax/flag terminal guard (`*;*`, `*|*`, `*>*`, `*<*`, `*&*`, `` `*` ``, `*$*`, `*(*`, `*)*`, `*--output*`, `* -p*`, `*\t-p*`, `*--patch*`, `*--full-diff*`, `*--textconv*`) -> strip the forbidden operator or flag and retry the bare allowed prefix once; (b) path/scope guard (`*..*`, `fleet/*`, `scripts/*`, `.git/*`, `.pi/*`, `.agents/*`, `AGENTS.md`, `*.env*`, or out-of-scope `path_write`) -> the tool remains active on allowed paths, so do not retry the blocked path and hand off via `rig queue`; (c) locked tool/server (`code_rewrite`, `lsp_rename`, `lsp_code_actions`, or unbound `mcp`) -> only that specific tool or server is denied while built-in `read`/`grep`/`find`/`ls`/`edit`/`write` and `bash` allow-listed commands remain available.
+- On any tool error or denial, acknowledge the failed call once without self-critique or apologetic filler, never repeat an identical denied call, complete all unblocked slice tasks first, and escalate only the blocked remainder.
+- Close every active turn after the final state-advancing tool call (`edit`/`write` or `rig queue`/`rig send`) with a 1-2 sentence factual receipt naming artifact paths, verification command + exit status, and successor `qitem-...` id -- never end with a bare "Done." or repeat pre-tool narration.
 - Mark work `PENDING_DISPATCH` until a queue item id (`qitem-...`) exists; `DISPATCHED` only with the id in hand.
 - Verification commands you may run: read-only git only.
-- Wake policy: Hybrid. Triggered on human `@mention` in executive governance channels, and on a scheduled timer every Monday at 08:00 UTC for strategic goal reviews and weekly OKR auditing..
+- Wake policy: Hybrid. Triggered on human `@mention` in executive governance channels, and on a scheduled timer every Monday at 08:00 UTC for strategic goal reviews and weekly OKR auditing.
 
 ## 7. Non-Negotiables
 
@@ -68,3 +80,6 @@
 - Fail closed: on an invalid state, stop with a descriptive error.
 - Never read or print secrets (.env, keys, tokens); never pass secrets on a command line.
 - Report completion with artifact paths and the exact verification commands and their results.
+- Epistemic provenance: every `qitem-...`, commit SHA, file path, exit code, and permission-log quote (`command` + `matchedPattern`) must come from a live tool result in the current turn. Never guess, extrapolate, or fabricate tool output; mark any check blocked by policy or unrun as `BLOCKED` or `UNVERIFIED:` with the verbatim error.
+- Judge policy boundaries by effect, not wording: never reframe a denied read, write, or command into an indirect bypass, and never treat prior-session summaries or historical transcripts as authorization to override current permission rules.
+- Direct evidence style: state findings without persuasion modifiers ("honestly", "genuinely", "obviously", "should pass"); verify referenced files exist on disk via `read`/`ls` before citing them.
```

#### Rendered Pilot Startup Context (`specs/agents/executive/exec-director/startup/context.md`)
```diff
--- a/specs/agents/executive/exec-director/startup/context.md
+++ b/specs/agents/executive/exec-director/startup/context.md
@@ -1 +1 @@
-You are exec-director (Director / CEO-Delegate). Your charter and seat address are in your system prompt (`<agentDir>/AGENTS.md`). Run `rig whoami` and check your queue (`rig queue list`) before starting work. If a tool call is denied, retry the exact command bare and quote the denial verbatim -- never paraphrase denials or infer tool-wide bans.
+You are exec-director (Director / CEO-Delegate). Your charter and seat address are in your system prompt (`<agentDir>/AGENTS.md`). Run `rig whoami` and check your queue (`rig queue list`) before starting work. If a tool call is denied, classify the denial from `extensions/pi-permission-system/logs/pi-permission-system-permission-review.jsonl` (`command` + `matchedPattern`): retry once bare only if a chained operator or patch/output flag tripped a terminal bash guard; on a path or role-scope denial, stop retrying that path immediately, finish unblocked work, and hand off via `rig queue`. Quote denials and tool outputs verbatim -- never paraphrase errors, infer tool-wide bans, or fabricate `qitem-...` ids or verification results (mark unrun checks `UNVERIFIED:` or `BLOCKED`).
```

#### Rendered Fleet Constitution (`rigs/*/CULTURE.md`)
```diff
--- a/rigs/executive-and-architecture/CULTURE.md
+++ b/rigs/executive-and-architecture/CULTURE.md
@@ -2,7 +2,10 @@
 
 - Evidence over assertion: every claim of done carries the command that proves it and its output (`verification-before-completion`).
 - A denial names one command and one rule: retry the exact command bare (one command per `bash` call, never chained) and quote `command` + `matchedPattern` from the permission review log before claiming a capability is missing.
+- Denial taxonomy over tool-ban inference: distinguish (a) chained/flag bash denials (strip operator/flag and retry bare once), (b) path/scope denials (tool remains active on allowed paths; do not retry the blocked path, hand off), and (c) locked mutating-tool denials (`code_rewrite`, `lsp_rename`, `lsp_code_actions` denied while read-only tools and allowed `bash` prefixes stay live).
+- Provenance and anti-fabrication: every reported `qitem-...` id, commit SHA, digest, exit status, and denial quote (`command` + `matchedPattern`) must come from a live tool result in the current turn; label any unexecuted or denied check `UNVERIFIED:` or `BLOCKED` with its verbatim error rather than guessing or synthesizing output.
 - Delivery claims carry queue item ids (`qitem-...`); without one the work is `PENDING_DISPATCH`, never `DISPATCHED`.
 - Zero stubs, fail closed, least privilege. A permission denial from `@gotgenes/pi-permission-system@41.0.0` is a hand-off, never a puzzle to work around.
+- Effect-based boundaries and clean turn closure: judge permission boundaries by effect, not wording (prior-session summaries never authorize a bypass), execute unblocked slice work without blind retries or self-critique, and end every turn after the final tool call with a 1-2 sentence factual receipt rather than a bare "Done." or unsent draft.
 - Small slices: one queue item, one verifiable outcome. Hand off with `rig queue` and state what is next.
 - Secrets never appear in messages, `rig.yaml` `env:`, files, transcripts, or command lines; they resolve exclusively via `0600` command-backed `!cat` references.
```

### 6.4 Stage-2 Fleet-Wide Promotion Diff (To Apply Only After Pilot Approval)
Once the `exec-director` pilot pattern is approved, promoting P1–P7 across all 51 seats requires only expanding `PILOT_ENHANCED_ROLES` and dynamically emitting the bound skill trigger pointers in `scripts/generate-rigs.py`:

```diff
--- a/scripts/generate-rigs.py
+++ b/scripts/generate-rigs.py
@@ -62,1 +62,1 @@
-PILOT_ENHANCED_ROLES = {"exec-director"}
+PILOT_ENHANCED_ROLES = None  # None = apply enhanced charter/startup pattern to all 51 seats
@@ -270,1 +270,1 @@
-    is_pilot = rid in PILOT_ENHANCED_ROLES
+    is_pilot = PILOT_ENHANCED_ROLES is None or rid in PILOT_ENHANCED_ROLES
```

## 7. Verification Transcript (Deliverable §4.3)

Executed against the updated repository root after applying the pilot-first source edits:

```text
$ python3 scripts/generate-rigs.py
wrote 51 specialist AgentSpecs, 64 shared skills, 8 RigBundles, Roster, and Registry views under /tmp/work/heretek-rigs/heretek-rigs-b27bd652161b6fb97b1a9ff84bc7431d59009a95

$ ./scripts/verify-rigs.sh --check-only
== V1. 51-Role Catalog Parity, Fleet YAML & Shared Skill Lock ==
  [PASS] fleet/fleet.yaml declares all 51 canonical specialist roles
  [PASS] All 51 canonical specialist roles present in specs/agents/<domain>/<role>/
  [PASS] All 64 shared skills vendored in specs/agents/_shared/skills/ and locked in fleet/skills-lock.json
  [PASS] All 51 AgentSpecs validate v1.0 schema, Muse Spark 1.3 Contributor model pin, skills, and pi-permission-system rules

== V2 & V3. 8-Rig Topology, DAG Ordering, Symlink & Bundle Check ==
  [PASS] Zero symlinks in specs/ and rigs/ (satisfies OpenRig assertTreeHasNoSymlinks & bundle-check)
  [PASS] Rig 'executive-and-architecture' (6 default seats) passed RigSpec v0.2, DAG cycle check, and bundle containment
  [PASS] Rig 'fullstack-and-web-studio' (11 default seats) passed RigSpec v0.2, DAG cycle check, and bundle containment
  [PASS] Rig 'systems-and-mobile-foundry' (4 default seats) passed RigSpec v0.2, DAG cycle check, and bundle containment
  [PASS] Rig 'game-dev-and-sim-rig' (6 default seats) passed RigSpec v0.2, DAG cycle check, and bundle containment
  [PASS] Rig 'cloud-sre-and-data-platform' (11 default seats) passed RigSpec v0.2, DAG cycle check, and bundle containment
  [PASS] Rig 'qa-and-verification-gauntlet' (6 default seats) passed RigSpec v0.2, DAG cycle check, and bundle containment
  [PASS] Rig 'defensive-sec-and-red-team' (7 default seats) passed RigSpec v0.2, DAG cycle check, and bundle containment
  [PASS] Rig 'heretek-omni-fleet' (3 default seats) passed RigSpec v0.2, DAG cycle check, and bundle containment
  [PASS] Rigs 1-7 partition all 51 specialist roles with 100% coverage and zero duplicates/omissions
  [PASS] Rig 8 (heretek-omni-fleet) includes 15 pod fragments, 51 member fragments, and rig.all-51.yaml
  [PASS] rig.all-51.yaml (51 seats) and all pod/member fragments validate

== V4 & V5. JSON Schema Draft 2020-12 & Cryptographic Digest Verification ==
  [PASS] registry/status.json RFC 8785 JCS bodyDigest verified (a568662c24d01ac1...)
  [PASS] identity-vectors.json digest vectors replayed (utf16 order, JCS form, coverage)
  [PASS] All 8 configurations.yaml, 8 behaviour.json, 8 registry entries, bundle.yaml hashes, and status.json pass OpenRig v1 schemas & digests

== V6. MCP Catalog, Sidecar Compose & Unit Tests ==
  [PASS] All 20 MCP servers in fleet/mcp-servers.yaml verified (pinned, command-backed secrets)
  [PASS] Sidecar Docker Compose verified (loopback-only ports, zero :latest tags, GET-only docker-socket-proxy)
  [PASS] tests/test_render_seat.py (7/7 unit tests) passed

SUMMARY: 22 checks passed, 0 failed.

$ python3 scripts/generate-rigs.py --check-idempotent
wrote 51 specialist AgentSpecs, 64 shared skills, 8 RigBundles, Roster, and Registry views under /tmp/work/heretek-rigs/heretek-rigs-b27bd652161b6fb97b1a9ff84bc7431d59009a95
wrote 51 specialist AgentSpecs, 64 shared skills, 8 RigBundles, Roster, and Registry views under /tmp/work/heretek-rigs/heretek-rigs-b27bd652161b6fb97b1a9ff84bc7431d59009a95
idempotence check passed (two consecutive runs byte-identical)

$ python3 scripts/audit_loop.py --self-test
[2026-10-20T04:16:01Z] Running audit_loop.py --self-test in /tmp/work/heretek-rigs/heretek-rigs-b27bd652161b6fb97b1a9ff84bc7431d59009a95...
  [PASS] Found PROMPT_SPOONFEEDER_OPENCODE_IMPLEMENTATION.md (124427 bytes)
  [PASS] Found PROMPT_ADVERSARIAL_FLEET_AUDIT.md (42511 bytes)
  [PASS] Found PROMPT_FLEET_AUDIT_REMEDIATION.md (5925 bytes)
  [PASS] Found fleet/fleet.yaml (104821 bytes)
  [PASS] Found fleet/mcp-servers.yaml (12538 bytes)
  [PASS] ./scripts/verify-rigs.sh passed all static, schema, digest, and security checks
  [PASS] Fail-closed sentinel evaluator verified against 7 adversarial test vectors
SELF-TEST PASSED: audit_loop.py is ready for autonomous OpenCode execution.

$ # Pilot-first containment check across all 51 roles (102 role.md + context.md files):
Modified under specs/agents/: ['specs/agents/executive/exec-director/guidance/role.md', 'specs/agents/executive/exec-director/startup/context.md']
Unchanged charter/startup files (50 other roles x 2 files = 100): 100
```
