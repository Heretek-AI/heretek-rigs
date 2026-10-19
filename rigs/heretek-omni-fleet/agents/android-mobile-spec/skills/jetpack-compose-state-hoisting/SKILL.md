---
name: jetpack-compose-state-hoisting
description: Builds responsive Jetpack Compose screens using unidirectional data flow, state hoisting, and Material 3 design tokens.
---

# Jetpack Compose State Hoisting Procedure

1. Read mobile feature requirements and inspect existing ViewModel architecture.
2. Design Composable functions with clean state hoisting (separate stateless UI from stateful containers).
3. Connect UI to ViewModel exposing UIState via `StateFlow` and `collectAsStateWithLifecycle()`.
4. Ensure all database operations are offloaded to `Dispatchers.IO` using Room coroutines.
5. Author unit tests for ViewModel business logic and Compose UI tests.
6. Run Ktlint: `./gradlew ktlintCheck`.
7. Execute unit tests: `./gradlew testDebugUnitTest`.
