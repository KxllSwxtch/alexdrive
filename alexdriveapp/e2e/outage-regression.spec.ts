import { test, expect, openCar } from "./helpers";

// Regression cover for the 2026-08 outage: the scraper died for 6+ days while the
// site kept serving stale cache, and uncached queries hung until the connection pool
// timed out. These assert the USER-VISIBLE half of that failure; the API-level half
// lives in scripts/verify-production.sh.

test("@smoke catalog renders real cars, not the empty state", async ({ page }) => {
  await page.goto("/");

  // The failure mode was a 200 response with an empty grid.
  await expect(page.locator("a[data-car-id]").first()).toBeVisible({ timeout: 45_000 });
  const count = await page.locator("a[data-car-id]").count();
  expect(count, "catalog rendered zero cars").toBeGreaterThan(0);
  await expect(page.getByText("Автомобили не найдены")).toHaveCount(0);
});

test("@smoke filter bar is populated (filters survived the server render)", async ({ page }) => {
  await page.goto("/");

  // When /cars was slow, Promise.all discarded the resolved filter tree and the
  // maker dropdown came back empty -- which also pushed the browser into
  // refetching the ~2.9MB /api/filters payload client-side.
  const makerButton = page.getByRole("button", { name: "Все марки", exact: true }).first();
  await expect(makerButton).toBeVisible({ timeout: 45_000 });
  await makerButton.click();
  const options = page.getByRole("option");
  await expect(options.first()).toBeVisible({ timeout: 15_000 });
  expect(await options.count(), "maker list is empty -- filters failed to load").toBeGreaterThan(5);
});

test("@smoke the catalog does not sit behind the 30s backend timeout", async ({ page }) => {
  const started = Date.now();
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.locator("a[data-car-id]").first()).toBeVisible({ timeout: 45_000 });
  const elapsed = Date.now() - started;
  // Pre-fix this was pinned at ~30s (httpx pool timeout) or 60s (nginx 504).
  expect(elapsed, `catalog took ${elapsed}ms to show cars`).toBeLessThan(25_000);
});

test("@smoke a car detail page loads from the catalog", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("a[data-car-id]").first()).toBeVisible({ timeout: 45_000 });
  const carId = await openCar(page);
  expect(carId).toBeTruthy();
  await expect(page).toHaveURL(/\/car\//);
});

test("@smoke no backend 5xx while loading the catalog", async ({ page }) => {
  const bad: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/api/") && r.status() >= 500) bad.push(`${r.status()} ${r.url()}`);
  });
  await page.goto("/");
  await expect(page.locator("a[data-car-id]").first()).toBeVisible({ timeout: 45_000 });
  await page.waitForTimeout(3_000);
  expect(bad, `backend 5xx responses:\n${bad.join("\n")}`).toEqual([]);
});
