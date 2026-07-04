import { expect, test as base, type Page } from "@playwright/test";

// Every test fails if React logs a hydration error (the class of bug the
// 2026-06 fixes addressed) or a minified React invariant.
const REACT_ERROR = /hydrat|Minified React error #(418|423|425)/i;

export const test = base.extend<{ consoleErrors: string[] }>({
  consoleErrors: [
    async ({ page }, use) => {
      const errors: string[] = [];
      page.on("console", (msg) => {
        if (msg.type() === "error") errors.push(msg.text());
      });
      page.on("pageerror", (err) => errors.push(String(err)));
      await use(errors);
      const react = errors.filter((e) => REACT_ERROR.test(e));
      expect(react, `React errors in console:\n${react.join("\n")}`).toEqual([]);
    },
    { auto: true },
  ],
});

export { expect };

// Client-side catalog listing fetches (excludes /api/cars/prefetch and
// /api/cars/detail — "?" must follow "cars" directly).
const CARS_API = /\/api\/cars\?/;

export function trackCarsRequests(page: Page) {
  let count = 0;
  page.on("request", (req) => {
    if (req.method() === "GET" && CARS_API.test(req.url())) count++;
  });
  return {
    count: () => count,
    reset: () => {
      count = 0;
    },
  };
}

export async function applyMakerFilter(page: Page, maker: string, currentLabel = "Все марки") {
  // The maker combobox button shows the current selection («Все марки» or a maker).
  await page.getByRole("button", { name: currentLabel, exact: true }).first().click();
  await page.getByRole("option", { name: maker, exact: true }).click();
  await Promise.all([
    page.waitForResponse((r) => CARS_API.test(r.url()) && r.url().includes("CarMakerNo")),
    page.getByRole("button", { name: "Найти" }).click(),
  ]);
  await page.waitForURL(/CarMakerNo=\d+/);
  await expect(page.locator("a[data-car-id] h3").first()).toContainText(maker, {
    timeout: 30_000,
  });
}

export async function expectFilteredCatalog(page: Page, maker: string) {
  await expect(page).toHaveURL(/CarMakerNo=\d+/);
  await expect(page.locator("a[data-car-id] h3").first()).toContainText(maker, {
    timeout: 30_000,
  });
}

export async function openCar(page: Page, nth = 0): Promise<string> {
  const card = page.locator("a[data-car-id]").nth(nth);
  const carId = await card.getAttribute("data-car-id");
  await card.click();
  await page.waitForURL(/\/car\//);
  await expect(backLink(page)).toBeVisible({ timeout: 30_000 });
  return carId!;
}

export function backLink(page: Page) {
  return page.getByRole("link", { name: "Назад в каталог" }).first();
}

export async function gotoPage(page: Page, pageNumber: number) {
  await Promise.all([
    page.waitForResponse((r) => CARS_API.test(r.url()) && r.url().includes(`PageNow=${pageNumber}`)),
    page.getByRole("button", { name: String(pageNumber), exact: true }).click(),
  ]);
  await page.waitForURL(new RegExp(`PageNow=${pageNumber}`));
}
