---
name: behavior-tree-authoring
description: Authors, evaluates, and tests hierarchical Behavior Trees and blackboard state memory for intelligent NPC agents.
---

# Behavior Tree Authoring Procedure

1. Read NPC design requirements to identify behaviors (e.g., Patrol, Investigate, Engage, Flee).
2. Model behavior hierarchy using Composite nodes (Selector, Sequence) and Decorators (Cooldown, Inverter).
3. Connect sensory inputs to the NPC Blackboard (target position, alert level).
4. Implement fail-safe fallback nodes for edge cases (e.g., target lost, path blocked).
5. Author headless simulation tests with simulated world states.
6. Verify AI decision time remains well within the AI tick slice (< 1ms per NPC).
