---
name: actionable-microcopy-refactoring
description: Audits UI microcopy, replacing cryptic errors and generic labels with clear, empathetic, and actionable copy.
---

# Actionable Microcopy Refactoring Procedure

1. Scan codebase for hardcoded English strings or uninformative error messages (e.g., "Error: Request failed").
2. Replace with semantic i18n translation keys using hierarchical namespace (`errors.network.timeout`).
3. Author the copy in `locales/en.json` following the 3-part microcopy rule:
   - What happened (plain, jargon-free English).
   - Why it happened (contextual reason).
   - What the user can do next (clear action or button label).
4. Verify readability score (Flesch-Kincaid Grade Level <= 7).
5. Ensure copy respects character length limits for mobile buttons.
6. Commit updated locale JSON files.
