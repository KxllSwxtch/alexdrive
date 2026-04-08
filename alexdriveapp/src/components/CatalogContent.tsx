"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { FilterBar } from "@/components/FilterBar";
import { CarGrid } from "@/components/CarGrid";
import { Pagination } from "@/components/Pagination";
import type { FilterData, CarListing, CarListingParams } from "@/lib/types";

const PAGE_SIZE = 24;
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

const VALID_PARAM_KEYS = new Set([
  "CarMakerNo", "CarModelNo", "CarModelDetailNo", "CarGradeNo", "CarGradeDetailNo",
  "CarYearFrom", "CarYearTo", "CarMileageFrom", "CarMileageTo", "CarPriceFrom", "CarPriceTo",
  "CarMissionNo", "CarFuelNo", "CarColorNo", "DanjiNo",
  "CarLpg", "CarInspection", "CarPhoto", "CarSalePrice", "CarLease",
  "SearchName", "SearchCarNo",
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
  initialHasNext?: boolean;
}

const MAX_CLIENT_RETRIES = 1;
const MAX_RETRY_COUNTDOWN_SECS = 120;

export function CatalogContent({ initialFilters, initialCars, initialTotal, initialHasNext }: CatalogContentProps) {
  const isInitialMount = useRef(true);

  const [filters, setFilters] = useState<FilterData | null>(initialFilters);
  const [cars, setCars] = useState<CarListing[]>(initialCars);
  const [total, setTotal] = useState(initialTotal);
  const [hasNext, setHasNext] = useState(initialHasNext ?? false);
  const [loading, setLoading] = useState(false);
  const [rateLimited, setRateLimited] = useState(false);
  const [retryCountdown, setRetryCountdown] = useState(0);
  const [params, setParams] = useState<CarListingParams>(() => {
    if (typeof window !== "undefined") {
      return parseParamsFromURL(new URLSearchParams(window.location.search));
    }
    return DEFAULT_PARAMS;
  });

  const retryCountRef = useRef(0);
  const countdownTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearRetryState = useCallback(() => {
    setRateLimited(false);
    setRetryCountdown(0);
    retryCountRef.current = 0;
    if (countdownTimerRef.current) {
      clearInterval(countdownTimerRef.current);
      countdownTimerRef.current = null;
    }
  }, []);

  const buildSearchParams = useCallback((p: CarListingParams) => {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(p)) {
      if (value !== undefined && value !== "") {
        searchParams.set(key, String(value));
      }
    }
    return searchParams;
  }, []);

  const fetchCars = useCallback(async (p: CarListingParams, signal?: AbortSignal): Promise<{ ok: boolean; retryAfter?: number }> => {
    const searchParams = buildSearchParams(p);
    const timeoutSignal = AbortSignal.timeout(15_000);
    const combinedSignal = signal
      ? AbortSignal.any([signal, timeoutSignal])
      : timeoutSignal;
    const res = await fetch(`${BACKEND_URL}/api/cars?${searchParams.toString()}`, { signal: combinedSignal });
    const data = await res.json();

    if (res.status === 429 || res.status === 503 || data.status === "rate_limited") {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "0", 10)
                         || data.retry_after || 30;
      return { ok: false, retryAfter };
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    setCars(data.listings || []);
    setTotal(data.total || 0);
    setHasNext(data.hasNext ?? false);
    clearRetryState();
    return { ok: true };
  }, [buildSearchParams, clearRetryState]);

  const startRetryCountdown = useCallback((p: CarListingParams, abortController: AbortController, retryAfterSecs: number) => {
    const countdown = Math.min(retryAfterSecs, MAX_RETRY_COUNTDOWN_SECS);
    setRateLimited(true);
    setRetryCountdown(countdown);

    if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);

    let remaining = countdown;
    countdownTimerRef.current = setInterval(async () => {
      remaining--;
      setRetryCountdown(remaining);

      if (remaining <= 0) {
        if (countdownTimerRef.current) {
          clearInterval(countdownTimerRef.current);
          countdownTimerRef.current = null;
        }

        retryCountRef.current++;
        if (retryCountRef.current > MAX_CLIENT_RETRIES) {
          setRateLimited(false);
          setLoading(false);
          setCars([]);
          setTotal(0);
          return;
        }

        try {
          const result = await fetchCars(p, abortController.signal);
          if (!result.ok) {
            startRetryCountdown(p, abortController, result.retryAfter ?? 60);
          } else {
            setLoading(false);
          }
        } catch {
          setRateLimited(false);
          setLoading(false);
        }
      }
    }, 1000);
  }, [fetchCars]);

  // Load filter data — only if server didn't provide them
  useEffect(() => {
    if (initialFilters) return;
    (async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/filters`);
        const data = await res.json();
        if (data && data.makers) setFilters(data);
      } catch (e) {
        console.error("Failed to fetch filters:", e);
      }
    })();
  }, [initialFilters]);

  // Load cars when params change — skip on initial mount
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      syncParamsToURL(params);
      return;
    }

    clearRetryState();
    const abortController = new AbortController();
    setLoading(true);

    fetchCars(params, abortController.signal)
      .then((result) => {
        if (abortController.signal.aborted) return;
        if (!result.ok) {
          startRetryCountdown(params, abortController, result.retryAfter ?? 60);
        } else {
          setLoading(false);
        }
      })
      .catch((error) => {
        if (abortController.signal.aborted) return;
        if (error.name === "TimeoutError") {
          console.warn("Search request timed out after 15s");
          setLoading(false);
          return;
        }
        console.error("Failed to fetch cars:", error);
        setCars([]);
        setTotal(0);
        setLoading(false);
      });

    return () => {
      abortController.abort();
      if (countdownTimerRef.current) {
        clearInterval(countdownTimerRef.current);
        countdownTimerRef.current = null;
      }
    };
  }, [params, fetchCars, clearRetryState, startRetryCountdown]);

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
          {total > 0 ? `${total.toLocaleString("ru-RU")} авто` : "загрузка..."}
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
      <div className={`mt-6 ${loading && !rateLimited && cars.length > 0 ? "opacity-50 pointer-events-none" : ""}`}>
        {rateLimited ? (
          <RateLimitMessage countdown={retryCountdown} />
        ) : loading && cars.length === 0 ? (
          <LoadingSkeleton />
        ) : (
          <CarGrid cars={cars} />
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

function RateLimitMessage({ countdown }: { countdown: number }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <svg
        className="mb-4 h-10 w-10 animate-spin text-accent"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <p className="text-lg font-medium text-text-primary">
        Сервер временно перегружен
      </p>
      <p className="mt-2 text-sm text-text-secondary">
        {countdown > 0
          ? `Повторная попытка через ${countdown} сек...`
          : "Повторная попытка..."}
      </p>
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
