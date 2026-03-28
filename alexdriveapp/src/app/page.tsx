import { backendFetch, fetchFiltersCached } from "@/lib/api";
import { CatalogContent } from "@/components/CatalogContent";
import type { FilterData, CarListing } from "@/lib/types";

const PAGE_SIZE = 20;

const VALID_PARAM_KEYS = new Set([
  "CarMakerNo", "CarModelNo", "CarModelDetailNo", "CarGradeNo", "CarGradeDetailNo",
  "CarYearFrom", "CarYearTo", "CarMileageFrom", "CarMileageTo", "CarPriceFrom", "CarPriceTo",
  "CarMissionNo", "CarFuelNo", "CarColorNo", "DanjiNo",
  "CarLpg", "CarInspection", "CarPhoto", "CarSalePrice", "CarLease",
  "SearchName", "SearchCarNo",
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

  // Parallel server-side fetch (internal network, no CORS)
  let filters: FilterData | null = null;
  let cars: CarListing[] = [];
  let total = 0;
  let hasNext = false;

  try {
    const [filtersData, carsData] = await Promise.all([
      fetchFiltersCached<FilterData>(),
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
