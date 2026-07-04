import { backendFetch, fetchFiltersCached } from "@/lib/api";
import { CatalogContent } from "@/components/CatalogContent";
import type { FilterData, CarListing } from "@/lib/types";
import { parseParamsFromRecord } from "@/lib/catalogParams";

interface PageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function CatalogPage({ searchParams }: PageProps) {
  const rawParams = await searchParams;

  // Parse initial params from the URL on the server so CatalogContent hydrates
  // with the exact same params the client would derive — prevents a hydration
  // mismatch when a filtered URL is loaded directly or restored via back/forward.
  const initialParams = parseParamsFromRecord(rawParams);

  // Build the backend query from the parsed params (defaults + URL overrides) so
  // the server fetches with the SAME param set the client sends — otherwise the
  // canonical URL's omitted defaults (PageSort=ModDt, PageAscDesc=DESC) fall back
  // to a different backend ordering than the one displayed in the UI.
  const backendParams = new URLSearchParams();
  for (const [key, value] of Object.entries(initialParams)) {
    if (value !== undefined && value !== "") backendParams.set(key, String(value));
  }

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
      initialParams={initialParams}
    />
  );
}
