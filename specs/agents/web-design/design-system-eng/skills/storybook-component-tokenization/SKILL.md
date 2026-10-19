---
name: storybook-component-tokenization
description: Refactors prototype components into production-grade design system components with Storybook stories and token bindings.
---

# Storybook Component Tokenization Procedure

1. Read target component prototype from `src/components/prototypes/`.
2. Extract all colors, dimensions, and typography into semantic design tokens.
3. Author the production component with:
   - Strict TypeScript prop interfaces and JSDoc documentation.
   - Forwarded refs (`React.forwardRef`) and accessible ARIA attributes.
   - Comprehensive variant support using `cva` (class-variance-authority).
4. Create a comprehensive Storybook file (`<Component>.stories.tsx`) covering:
   - Default, Active, Disabled, Loading, and Error states.
   - Mobile and Desktop viewport variations.
5. Execute Storybook test runner (`npm run test-storybook`).
6. Verify component passes zero-prop console errors.
