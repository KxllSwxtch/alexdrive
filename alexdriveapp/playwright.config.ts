import { defineConfig, devices } from "@playwright/test";

// E2E for catalog filter persistence. MUST run against a production build:
// `next dev` re-renders the current URL on back-navigation, so the Router-Cache
// behavior these tests exist to cover never reproduces there.
//
// Local (default):  starts `next build && next start` on :3000; the FastAPI
//                   backend must already be running on :3001.
// Prod smoke:       E2E_BASE_URL=https://alexdrive.kr npx playwright test --grep @smoke
const baseURL = process.env.E2E_BASE_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 15_000 },
  retries: 1,
  // Single worker: specs share one Next server + one throttled scraper backend,
  // and history-stack assertions are order-sensitive.
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
  },
  projects: [
    { name: "mobile-safari", use: { ...devices["iPhone 13"] } },
    { name: "desktop-chrome", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: "npm run build && npm run start",
        url: "http://localhost:3000",
        reuseExistingServer: true,
        timeout: 300_000,
      },
});
