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

  // allSettled, not all: these two fetches are independent, and Promise.all is
  // all-or-nothing. When /cars was slow the already-resolved filter tree was thrown
  // away too, so one slow backend call blanked the entire filter UI and pushed every
  // visitor's browser into refetching the ~2.9MB /api/filters payload client-side.
  const [filtersResult, carsResult, healthResult] = await Promise.allSettled([
    fetchFiltersCached<FilterData>(),
    backendFetch<{ listings: CarListing[]; total: number; hasNext?: boolean }>("/cars", backendParams, { revalidate: 300 }),
    // Cheap (in-memory read, ~30ms) and cached, so it adds no meaningful latency.
    backendFetch<{ status: string }>("/health", undefined, { revalidate: 60 }),
  ]);

  if (filtersResult.status === "fulfilled") {
    filters = filtersResult.value;
  } else {
    console.error("Failed to fetch filters:", filtersResult.reason);
  }

  // Fail-safe: if the health probe itself fails we show NO notice rather than
  // guessing. A false "everything is fine" is better here than a false alarm on
  // every page for a probe that is merely unreachable.
  const degraded =
    healthResult.status === "fulfilled" && healthResult.value?.status !== "ok";

  if (carsResult.status === "fulfilled") {
    cars = carsResult.value.listings;
    total = carsResult.value.total;
    hasNext = carsResult.value.hasNext ?? false;
  } else {
    console.error("Failed to fetch initial cars:", carsResult.reason);
  }

  return (
    <CatalogContent
      initialFilters={filters}
      initialCars={cars}
      initialTotal={total}
      initialHasNext={hasNext}
      initialParams={initialParams}
      degraded={degraded}
    />
  );
}
