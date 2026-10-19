---
name: tailwind-ui-prototyping
description: Translates product requirements into modern, accessible, responsive UI layouts using Tailwind CSS utility classes and semantic HTML5.
---

# Tailwind UI Prototyping Procedure

1. Read user story and layout hierarchy from PRD.
2. Structure component hierarchy with semantic HTML (`<main>`, `<header>`, `<nav>`, `<article>`).
3. Apply Tailwind CSS classes following mobile-first responsive breakpoints (`sm:`, `md:`, `lg:`, `xl:`).
4. Verify typography hierarchy, contrast ratios, and interactive states (`hover:`, `focus-visible:`, `active:`).
5. Render component in headless browser via `chrome-devtools-mcp` and capture screenshot for visual verification.
6. Commit prototype components and open PR for design system integration.
