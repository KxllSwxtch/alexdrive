import {
  test,
  expect,
  applyMakerFilter,
  expectFilteredCatalog,
  openCar,
  gotoPage,
} from "./helpers";

// Regression guard for the 2026-06-27 fix: every filter/pagination action is
// ONE history entry, so back unwinds the journey instead of exiting the site.

test("@smoke back unwinds page3 → page2 → maker B → maker A → unfiltered", async ({ page }) => {
  await page.goto("/");
  await applyMakerFilter(page, "BMW");
  await applyMakerFilter(page, "Audi", "BMW");
  await gotoPage(page, 2);
  await gotoPage(page, 3);

  await page.goBack();
  await page.waitForURL(/PageNow=2/);
  await expect(page).toHaveURL(/CarMakerNo=\d+/);

  await page.goBack();
  await page.waitForURL((url) => url.searchParams.get("PageNow") === null);
  await expect(page).toHaveURL(/CarMakerNo=\d+/);
  await expect(page.getByRole("button", { name: "Audi", exact: true })).toBeVisible();

  await page.goBack();
  await expect(page.getByRole("button", { name: "BMW", exact: true })).toBeVisible({
    timeout: 30_000,
  });

  await page.goBack();
  await page.waitForURL((url) => !url.search);
  await expect(page.getByRole("button", { name: "Все марки", exact: true })).toBeVisible();
  // Still on the catalog — back never exited the site.
  await expect(page.getByRole("heading", { name: "Каталог автомобилей" })).toBeVisible();
});

test("rapid back/forward across the detail boundary settles consistently", async ({ page }) => {
  await page.goto("/");
  await applyMakerFilter(page, "BMW");
  await openCar(page);

  await page.goBack();
  await page.goForward();
  await page.waitForURL(/\/car\//);
  await page.goBack();

  await page.waitForURL(/CarMakerNo=\d+/);
  await expectFilteredCatalog(page, "BMW");
  await expect(page.getByRole("button", { name: "BMW", exact: true })).toBeVisible();
});
