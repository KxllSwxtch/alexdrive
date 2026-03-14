"use client";

import { useState, useEffect, useRef } from "react";
import { FilterBar } from "@/components/FilterBar";
import { CarGrid } from "@/components/CarGrid";
import { Pagination } from "@/components/Pagination";
import type { FilterData, CarListing, CarListingParams } from "@/lib/types";

const PAGE_SIZE = 20;
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

const VALID_PARAM_KEYS = new Set([
  "CarMakerNo", "CarModelNo", "CarModelDetailNo", "CarGradeNo", "CarGradeDetailNo",
  "CarYearFrom", "CarYearTo", "CarMileageFrom", "CarMileageTo", "CarPriceFrom", "CarPriceTo",
  "CarFuelNo", "CarColorNo", "CarPhoto", "CarInsurance", "CarInspection", "CarLease",
  "CarMissionNo", "DanjiNo", "CarSiDoNo", "CarSiDoAreaNo", "SearchName", "SearchCarNo",
  "CarLpg", "CarSalePrice",
  "PageNow", "PageSize", "PageSort", "PageAscDesc",
]);

const NUMBER_KEYS = new Set(["PageNow", "PageSize"]);

const DEFAULT_PARAMS: CarListingParams = {
  PageNow: 1,
  PageSize: PAGE_SIZE,
  PageSort: "ModDt",
  PageAscDesc: "DESC",
};

function parseParamsFromURL(searchParams: URLSearchParams): CarListingParams {
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

function syncParamsToURL(params: CarListingParams) {
  const urlParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    if (key === "PageNow" && value === 1) continue;
    if (key === "PageSize" && value === PAGE_SIZE) continue;
    if (key === "PageSort" && value === "ModDt") continue;
    if (key === "PageAscDesc" && value === "DESC") continue;
    urlParams.set(key, String(value));
  }
  const qs = urlParams.toString();
  const newUrl = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  window.history.replaceState(null, "", newUrl);
}

interface CatalogContentProps {
  initialFilters: FilterData | null;
  initialCars: CarListing[];
  initialTotal: number;
  initialStatus?: string;
}

export function CatalogContent({ initialFilters, initialCars, initialTotal, initialStatus }: CatalogContentProps) {
  const isInitialMount = useRef(true);

  const [filters, setFilters] = useState<FilterData | null>(initialFilters);
  const [cars, setCars] = useState<CarListing[]>(initialCars);
  const [total, setTotal] = useState(initialTotal);
  const [status, setStatus] = useState<string>(initialStatus || "ok");
  const [loading, setLoading] = useState(false);
  const [params, setParams] = useState<CarListingParams>(() => {
    if (typeof window !== "undefined") {
      return parseParamsFromURL(new URLSearchParams(window.location.search));
    }
    return DEFAULT_PARAMS;
  });

  // Load filter data — only if server didn't provide them
  useEffect(() => {
    if (initialFilters) return;
    let ignore = false;
    fetch(`${BACKEND_URL}/api/filters`)
      .then((r) => r.json())
      .then((data) => {
        if (!ignore && data && data.makers) setFilters(data);
      })
      .catch(console.error);
    return () => { ignore = true; };
  }, [initialFilters]);

  // Load cars when params change — skip on initial mount (server already provided data)
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      syncParamsToURL(params);
      return;
    }

    let ignore = false;
    setLoading(true);

    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        if (key === "CarPriceFrom" || key === "CarPriceTo") {
          const num = parseInt(String(value), 10);
          if (!isNaN(num)) {
            searchParams.set(key, String(Math.round(num / 10000)));
            continue;
          }
        }
        searchParams.set(key, String(value));
      }
    }

    fetch(`${BACKEND_URL}/api/cars?${searchParams.toString()}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!ignore) {
          setCars(data.listings || []);
          setTotal(data.total || 0);
          setStatus(data.status || "ok");
        }
      })
      .catch((error) => {
        console.error("Failed to fetch cars:", error);
        if (!ignore) {
          setCars([]);
          setTotal(0);
        }
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });

    return () => { ignore = true; };
  }, [params]);

  // Sync params to URL on subsequent changes
  useEffect(() => {
    if (!isInitialMount.current) {
      syncParamsToURL(params);
    }
  }, [params]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      {/* Page title */}
      <div className="mb-6">
        <h1 className="font-heading text-2xl font-bold tracking-tight sm:text-3xl">
          Каталог автомобилей
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Сувон, Кёнги &mdash; {total > 0 ? `${total.toLocaleString("ru-RU")} авто` : "загрузка..."}
        </p>
      </div>

      {/* Filters */}
      <FilterBar
        filters={filters}
        appliedParams={params}
        onApplyFilters={(newParams) => {
          window.scrollTo({ top: 0, behavior: "instant" });
          setParams(newParams);
        }}
        loading={loading}
      />

      {/* Results */}
      <div className={`mt-6 ${loading && cars.length > 0 ? "opacity-50 pointer-events-none" : ""}`}>
        {loading && cars.length === 0 ? (
          <LoadingSkeleton />
        ) : (
          <CarGrid cars={cars} status={status} />
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={params.PageNow || 1}
          totalPages={totalPages}
          onPageChange={(page) => {
            if (page === (params.PageNow || 1)) return;
            window.scrollTo({ top: 0, behavior: "instant" });
            setLoading(true);
            setParams((prev) => ({ ...prev, PageNow: page }));
          }}
          disabled={loading}
        />
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse overflow-hidden rounded-xl border border-border bg-bg-surface"
        >
          <div className="aspect-[16/10] bg-bg-elevated" />
          <div className="p-4 space-y-3">
            <div className="h-5 w-24 rounded bg-bg-elevated" />
            <div className="h-4 w-full rounded bg-bg-elevated" />
            <div className="flex gap-3">
              <div className="h-3 w-16 rounded bg-bg-elevated" />
              <div className="h-3 w-16 rounded bg-bg-elevated" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
