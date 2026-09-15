// Playwright config for the Phase 1 e2e suite (tests/CLAUDE.md "/e2e").
//
// REALITY CHECK (see docs/STATUS.md — "nothing is deployed to AWS yet"):
// tests/CLAUDE.md describes /e2e as running against "a real browser,
// staging environment." There is no staging environment — no real Cognito
// user pool, no real Aurora database, nothing deployed. What DOES exist and
// IS real: the Next.js frontend, runnable locally via `npm run dev`
// (frontend/package.json), against whatever `NEXT_PUBLIC_API_URL` happens
// to be set to (unset here — see below).
//
// This config drives that local dev server, not a staging deployment. Specs
// that need a live backend/real Cognito session are `test.skip`/
// `test.fixme` with a comment naming exactly what's missing — see each
// spec file. Nothing here fakes a staging environment that doesn't exist.
//
// NEXT_PUBLIC_API_URL is deliberately left UNSET for this webServer: with
// no backend deployed there is nothing real to point it at, and leaving it
// unset drives the exact code path this suite actually asserts on — see
// frontend/src/lib/api/client.ts's `apiFetch`, which throws immediately
// (no network call) when the var is missing. Homepage/search "Popular near
// you"/"Search results" both catch this broadly and render a graceful
// InfoPanel empty/error state (frontend/src/components/home/PopularNearYou.tsx,
// frontend/src/components/search/SearchResults.tsx). The restaurant detail
// page's data loader only catches a 404 ApiError and re-throws everything
// else (frontend/src/app/restaurant/[slug]/page.tsx), so any slug there
// currently surfaces the app/error.tsx boundary instead — see
// test_public_listing.spec.ts for exactly why, and why that's actually a
// useful, deterministic way to exercise the error boundary today.
import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const FRONTEND_DIR = path.resolve(__dirname, "../frontend");
const PORT = 3100; // avoid clashing with a developer's own `npm run dev` on 3000
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [["html", { open: "never" }], ["list"]],
  // Next.js dev server compiles each route on first request (no production
  // build here) — a cold hit on a route plus React's dev-mode error-boundary
  // retry cycle (see test_public_listing.spec.ts's restaurant-detail test)
  // can comfortably exceed the 5s Playwright default. Generous timeouts
  // reflect dev-server reality, not flakiness being papered over.
  timeout: 45_000,
  expect: { timeout: 10_000 },

  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      // Phase 1 checklist requires "Mobile viewport (375px): no horizontal
      // scroll on any Phase 1 page" — a dedicated project makes that
      // coverage explicit and separately reportable rather than bolted on
      // via ad hoc setViewportSize calls in desktop tests.
      name: "mobile-375",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 375, height: 812 },
      },
      testMatch: /test_mobile_viewport\.spec\.ts/,
    },
  ],

  webServer: {
    command: "npm run dev -- --port " + PORT,
    cwd: FRONTEND_DIR,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    env: {
      // Playwright's webServer.env REPLACES the process env rather than
      // extending it, so PATH (needed to resolve `npm` itself) must be
      // included explicitly — spread the real env first, then layer test
      // values on top.
      ...process.env,
      // Deliberately no NEXT_PUBLIC_API_URL — see file header comment.
      NEXT_PUBLIC_COGNITO_USER_POOL_ID: "us-east-1_test000000",
      NEXT_PUBLIC_COGNITO_CLIENT_ID: "test-client-id-not-real",
    },
  },
});
