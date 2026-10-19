---
name: playwright-page-object-automation
description: Authors resilient Playwright end-to-end tests using the Page Object Model and locator best practices.
---

# Playwright Page Object Automation Procedure

1. Read user story acceptance criteria.
2. Structure or update the Page Object in `tests/e2e/pages/`:
   - Use role-based and user-facing locators (`getByRole`, `getByLabel`, `getByText`).
   - Avoid brittle CSS or XPath selectors (`div > span:nth-child(2)`).
3. Author the test workflow in `tests/e2e/specs/`:
   - Include realistic user authentication and state preparation.
   - Assert visual state, navigation changes, and API network responses.
4. Run tests in headless browser: `npx playwright test`.
5. If failures occur, inspect `trace.zip` to isolate timing or locator issues.
6. Commit passing test suite to repository.
