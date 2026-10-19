---
name: mobile-viewport-emulation-audit
description: Tests web applications across mobile device viewport profiles, validating touch targets, safe-areas, and virtual keyboard behavior.
---

# Mobile Viewport Emulation Audit Procedure

1. Configure Playwright emulation matrix: iPhone 15, Pixel 8, and Galaxy Fold (narrow screen 320px).
2. Emulate touch events and device pixel ratios (2x/3x Retina).
3. Validate:
   - Touch targets meet minimum 48x48px size with adequate padding.
   - Fixed headers and bottom navigation respect `safe-area-inset`.
   - Dynamic viewport height units (`100dvh`) prevent mobile browser address bar clipping.
   - Text remains readable without horizontal overflow or pinch-zoom triggers.
4. Capture full-page screenshots at each breakpoint.
5. Commit mobile layout fixes and automated regression tests.
