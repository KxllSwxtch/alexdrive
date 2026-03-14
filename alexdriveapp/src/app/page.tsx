import { backendFetch } from "@/lib/api";
import { CatalogContent } from "@/components/CatalogContent";
import type { FilterData, CarListing } from "@/lib/types";

const PAGE_SIZE = 20;

const PRICE_KEYS = new Set(["CarPriceFrom", "CarPriceTo"]);

const VALID_PARAM_KEYS = new Set([
  "CarMakerNo", "CarModelNo", "CarModelDetailNo", "CarGradeNo", "CarGradeDetailNo",
  "CarYearFrom", "CarYearTo", "CarMileageFrom", "CarMileageTo", "CarPriceFrom", "CarPriceTo",
  "CarFuelNo", "CarColorNo", "CarPhoto", "CarInsurance", "CarInspection", "CarLease",
  "CarMissionNo", "DanjiNo", "CarSiDoNo", "CarSiDoAreaNo", "SearchName", "SearchCarNo",
  "CarLpg", "CarSalePrice",
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
    if (PRICE_KEYS.has(key)) {
      const num = parseInt(value, 10);
      if (!isNaN(num)) {
        backendParams.set(key, String(Math.round(num / 10000)));
        continue;
      }
    }
    backendParams.set(key, value);
  }

  // Set defaults if not present in URL
  if (!backendParams.has("PageSize")) backendParams.set("PageSize", String(PAGE_SIZE));
  if (!backendParams.has("PageSort")) backendParams.set("PageSort", "ModDt");
  if (!backendParams.has("PageAscDesc")) backendParams.set("PageAscDesc", "DESC");

  // Parallel server-side fetch (internal network, no CORS)
  let filters: FilterData | null = null;
  let cars: CarListing[] = [];
  let total = 0;
  let initialStatus = "ok";

  try {
    const [filtersData, carsData] = await Promise.all([
      backendFetch<FilterData>("/filters", undefined, { revalidate: 3600 }),
      backendFetch<{ listings: CarListing[]; total: number; status?: string }>("/cars", backendParams, { revalidate: 300 }),
    ]);
    filters = filtersData;
    cars = carsData.listings;
    total = carsData.total;
    initialStatus = carsData.status || (carsData.listings.length > 0 ? "ok" : "empty");
  } catch (e) {
    console.error("Failed to fetch initial catalog data:", e);
    // Graceful degradation: client component will fall back to client-side fetch
  }

  return (
    <CatalogContent
      initialFilters={filters}
      initialCars={cars}
      initialTotal={total}
      initialStatus={initialStatus}
    />
  );
}
