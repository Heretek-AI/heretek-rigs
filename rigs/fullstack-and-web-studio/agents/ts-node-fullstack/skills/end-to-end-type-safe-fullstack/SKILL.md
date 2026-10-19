---
name: end-to-end-type-safe-fullstack
description: Implements end-to-end type-safe features connecting React Server Components, tRPC/Zod routers, and database queries.
---

# End-to-End Type-Safe Fullstack Procedure

1. Read feature specification and define Zod validation schemas.
2. Implement backend router/server action with database query (Drizzle/Prisma).
3. Connect frontend React Server Component and client interactivity hook.
4. Verify optimistic updates and rollback on error.
5. Run TypeScript compiler: `npx tsc --noEmit`.
6. Run unit and integration tests: `npx vitest run`.
7. Verify production build: `npm run build`.
