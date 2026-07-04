import { test, expect, backLink, trackCarsRequests } from "./helpers";

// SSR of filtered URLs must stay hydration-clean and must not double-fetch;
// deep links into a detail page must degrade to a plain "/" back link.

test("direct load of a filtered URL: SSR data, zero client listing fetches", async ({ page }) => {
  const tracker = trackCarsRequests(page);
  await page.goto("/?CarMakerNo=10065"); // BMW

  await expect(page.locator("a[data-car-id] h3").first()).toContainText("BMW", {
    timeout: 30_000,
  });
  await expect(page.getByRole("button", { name: "BMW", exact: true })).toBeVisible();
  // URL normalization must not strip the filter.
  await expect(page).toHaveURL(/CarMakerNo=10065/);

  // SSR provided the cars; the client must not refetch (hydration console
  // errors are asserted by the shared fixture).
  await page.waitForTimeout(3_000);
  expect(tracker.count()).toBe(0);
});

test("deep link into a detail page (fresh tab): back link degrades to /", async ({ page, context }) => {
  // Grab a real detail URL first.
  await page.goto("/");
  const href = await page.locator("a[data-car-id]").first().getAttribute("href");
  expect(href).toBeTruthy();

  // Fresh page = fresh sessionStorage (new tab / shared link).
  const fresh = await context.newPage();
  await fresh.goto(href!);
  const link = backLink(fresh);
  await expect(link).toBeVisible({ timeout: 30_000 });
  await expect(link).toHaveAttribute("href", "/");

  await link.click();
  await fresh.waitForURL((url) => url.pathname === "/" && !url.search);
  await expect(fresh.getByRole("button", { name: "Все марки", exact: true })).toBeVisible();
  await fresh.close();
});
