---
name: gameplay-state-machine-implementation
description: Designs and implements deterministic hierarchical state machines for player states, game phases, and quest logic.
---

# Gameplay State Machine Implementation Procedure

1. Read the gameplay specification to define all states (e.g., Idle, Run, Jump, Attack, Stunned).
2. Trace existing state transitions using `codebase-memory-mcp` (`search_graph` for state handlers).
3. Implement explicit transition guards and entry/exit actions:
   - Ensure transitions are deterministic and frame-independent.
   - Enforce tick-rate safety (avoid floating-point drift in discrete states).
4. Implement telemetry and debug logging for state changes.
5. Author unit tests covering 100% of valid transitions and asserting rejection of illegal transitions.
6. Run local game test harness to verify zero regressions.
