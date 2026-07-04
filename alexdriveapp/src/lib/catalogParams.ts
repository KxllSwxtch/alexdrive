import type { CarListingParams } from "@/lib/types";

// Shared catalog query-param logic used by BOTH the server component (app/page.tsx)
// and the client component (components/CatalogContent.tsx). Keeping a single source
// of truth guarantees the server and client derive identical initial params, which
// is required to avoid a hydration mismatch when a filtered URL is loaded directly.

export const PAGE_SIZE = 24;

// sessionStorage keys shared by CatalogContent (writer) and the detail page's
// BackToCatalogLink / CarCard (readers).
export const CATALOG_URL_KEY = "alexdrive:catalogUrl";
export const LAST_CAR_KEY = "alexdrive:lastCarId";

// Safe sessionStorage access — embedded webviews (e.g. messenger in-app
// browsers with cookies blocked) can throw on any storage access.
export function readSession(key: string): string | null {
  try {
    return sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

export function writeSession(key: string, value: string): void {
  try {
    sessionStorage.setItem(key, value);
  } catch {}
}

export function removeSession(key: string): void {
  try {
    sessionStorage.removeItem(key);
  } catch {}
}

export const VALID_PARAM_KEYS = new Set([
  "CarMakerNo", "CarModelNo", "CarModelDetailNo", "CarGradeNo", "CarGradeDetailNo",
  "CarYearFrom", "CarYearTo", "CarMileageFrom", "CarMileageTo", "CarPriceFrom", "CarPriceTo",
  "CarMissionNo", "CarFuelNo", "CarColorNo", "DanjiNo",
  "CarLpg", "CarInspection", "CarPhoto", "CarSalePrice", "CarLease",
  "SearchName", "SearchCarNo",
  "PageNow", "PageSize", "PageSort", "PageAscDesc",
]);

export const NUMBER_KEYS = new Set(["PageNow", "PageSize"]);

export const DEFAULT_PARAMS: CarListingParams = {
  PageNow: 1,
  PageSize: PAGE_SIZE,
  PageSort: "ModDt",
  PageAscDesc: "DESC",
};

// Parse a URLSearchParams (or any iterable query) into validated CarListingParams,
// starting from the defaults. Deterministic — same input always yields same output,
// so the server and client produce byte-identical params for the same URL.
export function parseParamsFromURL(searchParams: URLSearchParams): CarListingParams {
  const parsed: CarListingParams = { ...DEFAULT_PARAMS };
  searchParams.forEach((value, key) => {
    if (!VALID_PARAM_KEYS.has(key) || !value) return;
    if (NUMBER_KEYS.has(key)) {
      const num = parseInt(value, 10);
      if (!isNaN(num)) (parsed as Record<string, unknown>)[key] = num;
    } else {
      (parsed as Record<string, unknown>)[key] = value;
    }
  });
  return parsed;
}

// Server-side helper: build initial params from Next.js' raw searchParams record.
export function parseParamsFromRecord(
  rawParams: Record<string, string | string[] | undefined>,
): CarListingParams {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(rawParams)) {
    if (typeof value === "string") sp.set(key, value);
  }
  return parseParamsFromURL(sp);
}
