---
name: wcag-axe-audit-automation
description: Runs automated axe-core audits against web viewports, asserting zero critical or serious WCAG 2.2 violations.
---

# WCAG Axe Audit Automation Procedure

1. Launch target web view in headless browser via Playwright MCP.
2. Inject `@axe-core/playwright` scanner into the active DOM.
3. Run scan targeting WCAG 2.1 and WCAG 2.2 Level AA rulesets.
4. Verify:
   - Color contrast ratio >= 4.5:1 for normal text, >= 3:1 for large text.
   - Every interactive element has an accessible name and discernible focus ring.
   - Screen reader landmarks (`role="main"`, `<nav>`, `<header>`) are present.
   - Form inputs have associated `<label>` elements.
5. If violations exist, generate an actionable report detailing DOM selector and remediation steps.
6. Commit automated test to `tests/a11y/`.
