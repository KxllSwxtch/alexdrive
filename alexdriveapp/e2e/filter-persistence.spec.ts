import {
  test,
  expect,
  applyMakerFilter,
  expectFilteredCatalog,
  openCar,
  backLink,
  gotoPage,
  trackCarsRequests,
} from "./helpers";

// Core bug (reproduced on prod 2026-07-04): filters were wiped when returning
// from a car detail page, via the «Назад в каталог» button AND via browser back.

test("@smoke button path: «Назад в каталог» restores the filtered catalog", async ({ page }) => {
  await page.goto("/");
  await applyMakerFilter(page, "BMW");
  await openCar(page);

  await backLink(page).click();

  await expectFilteredCatalog(page, "BMW");
  await expect(page.getByRole("button", { name: "BMW", exact: true })).toBeVisible();
});

test("@smoke browser back: address bar keeps ?CarMakerNo and results stay filtered", async ({ page }) => {
  await page.goto("/");
  await applyMakerFilter(page, "BMW");
  await openCar(page);

  const tracker = trackCarsRequests(page);
  await page.goBack();

  // The wipe regression trap: the query string must survive the round-trip.
  await page.waitForURL(/CarMakerNo=\d+/);
  await expectFilteredCatalog(page, "BMW");
  await expect(page.getByRole("button", { name: "BMW", exact: true })).toBeVisible();

  // At most one recovery fetch (zero if the browser restored from bfcache).
  await page.waitForTimeout(1_500);
  expect(tracker.count()).toBeLessThanOrEqual(1);
});

test("@smoke pagination + filter survive the round-trip (both paths)", async ({ page }) => {
  await page.goto("/");
  await applyMakerFilter(page, "BMW");
  await gotoPage(page, 2);
  await openCar(page);

  // Button path
  await backLink(page).click();
  await page.waitForURL(/CarMakerNo=\d+.*PageNow=2|PageNow=2.*CarMakerNo=\d+/);
  await expectFilteredCatalog(page, "BMW");

  // Browser-back path: detail again, then goBack
  await openCar(page);
  await page.goBack();
  await page.waitForURL(/CarMakerNo=\d+.*PageNow=2|PageNow=2.*CarMakerNo=\d+/);
  await expectFilteredCatalog(page, "BMW");
});

test("@smoke «Сбросить» round-trip stays unfiltered", async ({ page }) => {
  await page.goto("/");
  await applyMakerFilter(page, "BMW");
  await page.getByRole("button", { name: "Сбросить" }).click();
  await page.waitForURL((url) => url.searchParams.get("CarMakerNo") === null);

  await openCar(page);
  await backLink(page).click();

  await page.waitForURL((url) => !url.search);
  await expect(page.getByRole("button", { name: "Все марки", exact: true })).toBeVisible();
});

test("sort selection survives the round-trip", async ({ page }) => {
  await page.goto("/");
  await page.getByText("По дате").first().click();
  await page.getByRole("option", { name: "По цене" }).click();
  await page.waitForURL(/PageSort=CarPrice/);
  await expect(page.locator("a[data-car-id]").first()).toBeVisible({ timeout: 30_000 });

  await openCar(page);
  await backLink(page).click();

  await page.waitForURL(/PageSort=CarPrice/);
  await expect(page.getByText("По цене").first()).toBeVisible();
});

test("scroll restore: the clicked card is back in the viewport (both paths)", async ({ page }) => {
  await page.goto("/");
  await applyMakerFilter(page, "BMW");

  // A card far enough down that the list top would not show it.
  const carId = await openCar(page, 8);

  await backLink(page).click();
  await expectFilteredCatalog(page, "BMW");
  await expect(page.locator(`a[data-car-id="${carId}"]`)).toBeInViewport({ timeout: 15_000 });

  const carId2 = await openCar(page, 10);
  await page.goBack();
  await expectFilteredCatalog(page, "BMW");
  await expect(page.locator(`a[data-car-id="${carId2}"]`)).toBeInViewport({ timeout: 15_000 });
});
