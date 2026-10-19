---
name: core-web-vitals-profiling
description: Runs automated Chrome DevTools performance profiling to identify render-blocking resources, long tasks, and layout shifts.
---

# Core Web Vitals Profiling Procedure

1. Launch staging URL in headless Chrome via `chrome-devtools-mcp` with simulated 4G network and 4x CPU throttling.
2. Record performance trace covering initial navigation and user interaction.
3. Extract metrics:
   - First Contentful Paint (FCP) and Largest Contentful Paint (LCP).
   - Total Blocking Time (TBT) and Interaction to Next Paint (INP).
   - Cumulative Layout Shift (CLS).
4. Identify render-blocking `<script>` and `<link>` tags; configure `async`/`defer` or font preload headers.
5. Inspect bundle analyzer to identify bloated dependencies for code-splitting.
6. Verify optimization brings all Core Web Vitals into the "Good" green threshold.
