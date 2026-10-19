---
name: planning-with-files
description: Disk-persisted hierarchical task plan and progress ledger surviving context compaction in long-running assignments.
license: MIT
---

# Planning-With-Files Operational Protocol

When executing multi-step sprints or long-running tasks, maintain operational state directly on disk to prevent context degradation across compaction cycles:

1. **Sprint Initialization**:
   On ticket assignment, establish three ledger files in the working directory:
   - `task_plan.md`: Encodes the primary goal, hard constraints, architectural decisions, and Definition of Done (DoD) checklist.
   - `findings.md`: Records verified technical facts, discovered API signatures, reproduction steps, and benchmark metrics.
   - `progress.md`: Timestamped log of executed steps, verified diffs, and current blocking issues.

2. **Per-Turn Execution Loop**:
   - Begin every turn by reading `task_plan.md` and `progress.md`.
   - Update the current task status (PENDING $\rightarrow$ IN-PROGRESS $\rightarrow$ VERIFIED).
   - Append new technical discoveries to `findings.md`. Never rewrite historical entries.

3. **Compaction Resilience**:
   - When context windows approach limits, rely on the on-disk markdown files as the definitive source of truth.
   - Summarize transient scratch notes into `progress.md`.

4. **Definition of Done Verification Gate**:
   - Before completing an assignment or handing off to another agent, confirm that every checklist item in `task_plan.md` has corresponding test results and passing verification logs.
