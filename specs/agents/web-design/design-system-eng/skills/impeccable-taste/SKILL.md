---
name: impeccable-taste
description: Deterministic UI polish, typography scale, and art-direction check with headless browser screenshot verification.
license: Apache-2.0 (impeccable) + MIT (taste-skill)
---

# Impeccable-Taste Design Verification Procedure

Follow this strict procedure when building, refining, or auditing user interface components and layouts:

1. **Specification Truth**: Read design requirements and token variables from `tokens/` or component specifications. Establish exact viewport breakpoints (e.g., 390px mobile, 1440px desktop).
2. **Deterministic Quality Audit**:
   - Check against visual anti-patterns: generic purple gradients, centered text blocks longer than 3 lines, unstyled browser default form controls, and low-contrast borders.
   - Enforce harmonic type scales (e.g. Minor Third 1.2 or Major Third 1.25) and consistent 4px/8px spatial spacing intervals.
3. **Headless Visual Evidence**:
   - Capture rendered component screenshots at 390px and 1440px using the containerized browserless sidecar:
     `ws://browserless:3000?stealth=true`
   - Inspect element bounding boxes, padding alignment, and contrast ratios.
4. **Deterministic Linting**:
   - Run layout and styling verification rules before invoking subjective LLM critique passes.
   - Address all accessibility (WCAG 2.2 AA) contrast violations (minimum 4.5:1 for body copy).
5. **Artifact Export & Handoff**:
   - Export vector diagrams and state charts as self-contained HTML+SVG artifacts.
   - Store visual evidence screenshots in persistent storage for QA acceptance review.
