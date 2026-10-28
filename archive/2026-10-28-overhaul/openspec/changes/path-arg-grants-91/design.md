# Design: path-arg-grants-91 (prove enforcement, then scope)

## Why M0 comes first
Every prior wave verified against repo gates, never against the installed enforcer. §4 shows that strategy can produce verified-but-dead policy: the list overlay is well-formed per our spec yet plausibly unparsed by pps's zod record. M0 inverts the order — enforcer behavior first, implementation second — for the price of one hostile-corpus run. If the list form already enforces, M0 is cheap and the wave proceeds list-only; if only the map enforces, we emit both; if neither, we stop before writing dead grants fleet-wide.

## Why native-map + descriptor-list (expected outcome)
The map form is what pps folds (`foldDeclaredCommandEffects` per layer); the list form is what humans audit (ids, scopes, constraints, red-proof references). Emitting both keeps each layer's strength: enforcement correctness from the native shape, reviewability from ours. The V-number block asserts both are present and consistent (same tool set, same scope roots).

## Why argv-slot exception, not deny re-scope (Q6)
Re-scoping `* -c *`/`* -W*` would weaken every role's protection against `sh -c` flag smuggling for the sake of two roles' compilers. Slot-scoped precedence keeps the deny byte-identical (auditors diff clean) while making the grant effective exactly where the compiler's path operand sits. The `-c` flag itself still matches the deny outside the slot — proven by red-proof.

## Why two roles (Q7)
Compile capability is the sharpest tool class in the fleet (arbitrary code execution by design). cpp-lowlevel-eng already owns the C++ mission surface; engine-systems-eng owns the engine tree that #91's live proof centers on. Every additional role multiplies the hostile-corpus burden; expansion is a future principal call with its own wave.

## Failure modes
- M0 shows list-form enforces: drop the map emission, wave simplifies (record, proceed).
- M0 shows neither enforces: halt, re-plan (possible pps upgrade or wrapper-script fallback per Q2's runner-up).
- `go ./...` vs `..` escape: package-pattern branch must reject any arg containing `/../` or leading `../` before pattern classification.
- `cmake -S` pointing outside the seat tree: flag-value pairing resolves values against scope roots like any path operand.
