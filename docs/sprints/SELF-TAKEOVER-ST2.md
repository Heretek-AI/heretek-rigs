# SELF-TAKEOVER-ST2 — Pi-extension follow-up batch (APPLIED by operator)

- Slice qitem: ST-2 (+ST-2P proposal qitem-20261021161108-108d8c8e5795762b).
- Source slice: qitem-20261021155313-fe1742ceb (self-takeover brief).
- Operator rule: qitem-20261021160234-e304e6d8e1094b9a (proposal packages).
- Fleet input: platform-dependency-patcher package
  `st2p-proposal-package-lock.json` (repo root) — pin table, seat lists,
  mirror re-verification post-ST-1, red-seat flags, 4 operator decisions.
- Human authorization: operator session 2026-10-21 ("you can apply them").
- **Implementation: OPERATOR-EXECUTED, not seat-executed.** No seat holds
  fleet/* write. The fleet specified pins + seats + evidence; the operator
  applied the hunks, regenerated, verified, and commits.

## Operator decisions on the 4 flagged items

1. **pi-web-access pin: 0.44.0.** #14 said 0.42.0, B4's note said 0.43.0;
   live npm check 2026-10-21 shows latest 0.44.0, MIT. Freshness rule:
   pin what is verified today.
2. **B2 rows 40-41 adopting seat: BOTH e2e-browser-qa AND api-contract-tester.**
   #14 rows 40-41 name exactly these seats, neither carries the extension,
   and both do web verification work where it fits. Adopted on both.
3. **pi-memory / plan-mode / usage: OUT OF SCOPE confirmed.** Named only in
   B4 (Rig-1) rows. Deferred to a Rig-1 follow-up batch, not this slice.
4. **Red seats (binary-reverse-eng, firmware-sec-analyst): REFUSED.**
   B3 zero-new-tool-grants bar holds; pi-web-access is a web-fetch extension
   (new capability surface) on locked charters. No hunk authored for either.

## Applied: 24 pins appended across 22 seats (additive only, existing kept)

- pi-lens@4.4.4 (live-verified MIT today): go-backend-eng, ui-ux-designer,
  design-system-eng, fe-perf-eng, ux-research-analyst, rust-systems-spec,
  graphics-shader-eng (7).
- pi-btw@0.8.0 (MIT): threat-modeler, compliance-auditor, ui-ux-designer,
  a11y-specialist, brand-copy-spec (5).
- pi-web-access@0.44.0 (MIT, live-verified today): mobile-web-eng,
  android-mobile-spec, ios-mobile-spec, e2e-browser-qa, api-contract-tester
  (5; red seats refused).
- pi-mcp-adapter@5.4.0 (MIT): ts-node-fullstack, design-system-eng,
  cloud-sec-auditor, tech-artist-pipeline (4).
- '@ff-labs/pi-fff@0.11.0' (MIT, B1 quoted format): engine-systems-eng,
  game-systems-dev, game-ai-dev (3).
- pi-subagents: EXCLUDED everywhere per HR-6.2 (no hunk, unchanged).

## Verification (operator-run; fleet bash-denies these tools)

- Regen + ./scripts/verify-rigs.sh --check-only, target 22/0.
- Rendered proof: each seat's rendered agent carries the new extension(s);
  no seat loses existing allows (additive-only diff).
- Results recorded below after execution.

## Results (operator-executed 2026-10-21)

- Regen: generate-rigs.py with ALLOW_DIRTY=1 (dirt was exactly the catalog hunks) → 51 AgentSpecs, 64 skills, 8 RigBundles, Roster, Registry.
- Verify: ./scripts/verify-rigs.sh --check-only → 22 checks passed, 0 failed.
- Rendered proof: 22/22 seats carry new pins in runtime policy-enforcement.json (spot-checked 5, full-swept 22, 0 missing); red seats binary-reverse-eng + firmware-sec-analyst confirmed WITHOUT pi-web-access (refusal holds in render).
- pi-web-access pinned at live-verified 0.44.0 MIT (2026-10-21 npm); pi-lens 4.4.4, pi-btw 0.8.0, pi-mcp-adapter 5.4.0, pi-fff 0.11.0 all MIT, versions match ledger.

## Deviation note

No agency-programmer/agency-qa/agency-drift-guard subagents were available
in the operator session (tool guard rejects subagent calls for role "build").
The operator applied the hunks directly under explicit human authorization,
with exact-match fail-closed editing (unique-match assertions per hunk,
24/24 pins verified in intended seats post-edit), and verifies via the
automated gate + rendered greps. Human merge review remains the gate.
