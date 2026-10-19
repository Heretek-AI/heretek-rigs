---
name: worktree-rebase-orchestration
description: Creates isolated git worktrees for parallel agent execution and cleanly rebases feature branches onto main.
---

# Worktree Rebase Orchestration Procedure

1. Read active agent task and create dedicated isolated worktree:
   `git worktree add /paperclip/workspaces/<task-id> -b feature/<task-id> origin/main`.
2. Monitor branch drift: Compute merge-base against `origin/main`.
3. If branch is behind:
   - Perform clean rebase: `git rebase origin/main`.
   - If mechanical conflicts occur (e.g. formatting, imports): Resolve using standard patterns and continue.
   - If semantic logic conflicts occur: Halt, create conflict summary, and notify feature author.
4. Verify tests pass after rebase.
5. When task is merged: Prune worktree with `git worktree remove` and delete stale remote branch.
