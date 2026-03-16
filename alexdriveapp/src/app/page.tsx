import { backendFetch } from "@/lib/api";
import { CatalogContent } from "@/components/CatalogContent";
import type { FilterData, CarListing } from "@/lib/types";

const PAGE_SIZE = 20;

const VALID_PARAM_KEYS = new Set([
  "carnation",
  "CarMakerNo", "CarModelNo", "CarModelDetailNo", "CarGradeNo", "CarGradeDetailNo",
  "CarYearFrom", "CarYearTo", "CarMileageFrom", "CarMileageTo", "CarPriceFrom", "CarPriceTo",
  "CarFuelNo", "CarColorNo", "CarMissionNo", "SearchCarNo",
  "PageNow", "PageSize", "PageSort", "PageAscDesc",
]);

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function CatalogPage({ searchParams }: PageProps) {
  const rawParams = await searchParams;

  // Build backend query params from URL search params
  const backendParams = new URLSearchParams();
  for (const [key, value] of Object.entries(rawParams)) {
    if (!VALID_PARAM_KEYS.has(key) || !value || Array.isArray(value)) continue;
    backendParams.set(key, value);
  }

  // Set defaults if not present in URL
  if (!backendParams.has("PageSize")) backendParams.set("PageSize", String(PAGE_SIZE));
  if (!backendParams.has("PageSort")) backendParams.set("PageSort", "ModDt");
  if (!backendParams.has("PageAscDesc")) backendParams.set("PageAscDesc", "DESC");

  const carnation = backendParams.get("carnation") || "1";

  // Parallel server-side fetch (internal network, no CORS)
  let filters: FilterData | null = null;
  let cars: CarListing[] = [];
  let total = 0;
  let hasNext = false;

  try {
    const filterParams = new URLSearchParams({ carnation });
    const [filtersData, carsData] = await Promise.all([
      backendFetch<FilterData>("/filters", filterParams, { revalidate: 3600 }),
      backendFetch<{ listings: CarListing[]; total: number; hasNext?: boolean }>("/cars", backendParams, { revalidate: 300 }),
    ]);
    filters = filtersData;
    cars = carsData.listings;
    total = carsData.total;
    hasNext = carsData.hasNext ?? false;
  } catch (e) {
    console.error("Failed to fetch initial catalog data:", e);
  }

  return (
    <CatalogContent
      initialFilters={filters}
      initialCars={cars}
      initialTotal={total}
      initialHasNext={hasNext}
    />
  );
}
