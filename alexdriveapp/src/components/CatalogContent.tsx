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

// Pure: build the canonical catalog URL (default params omitted). No side effects.
function buildCanonicalUrl(params: CarListingParams): string {
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
  return qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
}

interface CatalogContentProps {
  initialFilters: FilterData | null;
  initialCars: CarListing[];
  initialTotal: number;
  initialHasNext?: boolean;
}

const MAX_CLIENT_RETRIES = 1;
const MAX_RETRY_COUNTDOWN_SECS = 30;

export function CatalogContent({ initialFilters, initialCars, initialTotal, initialHasNext }: CatalogContentProps) {
  const isInitialMount = useRef(true);

  const [filters, setFilters] = useState<FilterData | null>(initialFilters);
  const [cars, setCars] = useState<CarListing[]>(initialCars);
  const [total, setTotal] = useState(initialTotal);
  const [hasNext, setHasNext] = useState(initialHasNext ?? false);
  const [loading, setLoading] = useState(false);
  const [rateLimited, setRateLimited] = useState(false);
  const [retryCountdown, setRetryCountdown] = useState(0);
  const [retryExhausted, setRetryExhausted] = useState(false);
  const [hardFailure, setHardFailure] = useState(false);
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
    setRetryExhausted(false);
    setHardFailure(false);
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

  // Forward navigation: create ONE real history entry per filter/page state.
  // Next.js patches history.pushState so this updates the router URL WITHOUT a
  // server round-trip or re-render (this component does not read useSearchParams).
  // The equality guard avoids a dead duplicate entry (e.g. re-clicking "Найти"
  // with unchanged filters), which would make one BACK press appear to do nothing.
  const pushParamsToURL = useCallback((p: CarListingParams) => {
    const url = buildCanonicalUrl(p);
    if (url !== window.location.pathname + window.location.search) {
      window.history.pushState(null, "", url);
    }
  }, []);

  // Prefetch: warm backend cache before user clicks "Найти"
  const preloadAbortRef = useRef<AbortController | null>(null);
  const handlePreload = useCallback((p: CarListingParams) => {
    if (preloadAbortRef.current) preloadAbortRef.current.abort();
    const controller = new AbortController();
    preloadAbortRef.current = controller;
    const searchParams = buildSearchParams(p);
    fetch(`${BACKEND_URL}/api/cars?${searchParams.toString()}`, {
      signal: controller.signal,
    }).catch(() => {}); // fire-and-forget, ignore errors
  }, [buildSearchParams]);

  const fetchCars = useCallback(async (p: CarListingParams, signal?: AbortSignal): Promise<{ ok: boolean; retryAfter?: number; hardFailure?: boolean }> => {
    const searchParams = buildSearchParams(p);
    const timeoutSignal = AbortSignal.timeout(15_000);
    const combinedSignal = signal
      ? AbortSignal.any([signal, timeoutSignal])
      : timeoutSignal;
    const res = await fetch(`${BACKEND_URL}/api/cars?${searchParams.toString()}`, { signal: combinedSignal });
    const data = await res.json();

    // Rate-limit / transient overload — keep auto-retrying with the countdown banner.
    if (res.status === 429 || data.status === "rate_limited") {
      const retryAfter = parseInt(res.headers.get("Retry-After") || "0", 10)
                         || data.retry_after || 30;
      return { ok: false, retryAfter };
    }

    // Pagination soft-fail: empty page but pagination/UI still valid via fallback total.
    if (data.status === "scrape_failed") {
      setCars([]);
      setTotal(data.total || 0);
      setHasNext(false);
      const retryAfter = parseInt(res.headers.get("Retry-After") || "0", 10) || 5;
      return { ok: false, retryAfter };
    }

    // Deterministic parser/empty failure — auto-retry would just fail the same way.
    if (data.status === "parse_failure" || data.status === "empty" || (res.status === 503 && !data.listings?.length)) {
      setCars([]);
      setTotal(0);
      setHasNext(false);
      return { ok: false, hardFailure: true };
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
          setRetryExhausted(true);
          setLoading(false);
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
      // Normalize the landing URL in place — no new history entry, no fetch
      // (initial cars came from the server render).
      window.history.replaceState(null, "", buildCanonicalUrl(params));
      return;
    }

    clearRetryState();
    const abortController = new AbortController();
    setLoading(true);

    fetchCars(params, abortController.signal)
      .then((result) => {
        if (abortController.signal.aborted) return;
        if (result.hardFailure) {
          setHardFailure(true);
          setLoading(false);
          return;
        }
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

  // Browser back/forward: re-sync params from the URL so the displayed results
  // match the address bar. This path only READS history (forward pushes live in
  // the user-action handlers below), so the history stack stays intact; the fetch
  // effect above then re-fetches for the restored params (aborting any in-flight
  // request via its cleanup). parseParamsFromURL + setParams are stable → [] deps.
  useEffect(() => {
    function handlePopState() {
      setParams(parseParamsFromURL(new URLSearchParams(window.location.search)));
    }
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

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
          if (preloadAbortRef.current) preloadAbortRef.current.abort();
          pushParamsToURL(newParams);
          window.scrollTo({ top: 0, behavior: "instant" });
          setParams(newParams);
        }}
        onPreload={handlePreload}
        loading={loading}
      />

      {/* Results */}
      {rateLimited && (
        <RateLimitBanner
          countdown={retryCountdown}
          exhausted={retryExhausted}
          onRetry={() => {
            clearRetryState();
            setParams((p) => ({ ...p }));
          }}
        />
      )}
      {hardFailure && !rateLimited && (
        <HardFailureBanner
          onRetry={() => {
            clearRetryState();
            setLoading(true);
            setParams((p) => ({ ...p }));
          }}
        />
      )}
      <div className={`mt-6 ${loading && cars.length > 0 ? "opacity-60 pointer-events-none" : ""}`}>
        {!rateLimited && !hardFailure && loading && cars.length === 0 ? (
          <LoadingSkeleton />
        ) : rateLimited && cars.length === 0 ? (
          <RateLimitFullPage countdown={retryCountdown} exhausted={retryExhausted} />
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
            const next = { ...params, PageNow: page };
            pushParamsToURL(next);
            window.scrollTo({ top: 0, behavior: "instant" });
            setLoading(true);
            setParams(next);
          }}
          disabled={loading}
        />
      )}
    </div>
  );
}

function RateLimitBanner({
  countdown,
  exhausted,
  onRetry,
}: {
  countdown: number;
  exhausted: boolean;
  onRetry: () => void;
}) {
  return (
    <div className="mt-4 flex items-center justify-between gap-3 rounded-lg border border-accent/30 bg-accent/10 px-4 py-3 text-sm">
      <div className="flex items-center gap-3">
        {!exhausted && (
          <svg
            className="h-5 w-5 animate-spin text-accent"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        <span className="text-text-primary">
          {exhausted
            ? "Не удалось загрузить страницу."
            : countdown > 0
              ? `Сервер временно перегружен. Повторная попытка через ${countdown} сек...`
              : "Повторная попытка..."}
        </span>
      </div>
      {exhausted && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-md border border-accent bg-accent/10 px-3 py-1 text-xs font-medium text-accent hover:bg-accent/20"
        >
          Обновить
        </button>
      )}
    </div>
  );
}

function RateLimitFullPage({ countdown, exhausted }: { countdown: number; exhausted: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {!exhausted && (
        <svg
          className="mb-4 h-10 w-10 animate-spin text-accent"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      <p className="text-lg font-medium text-text-primary">
        {exhausted ? "Не удалось загрузить" : "Сервер временно перегружен"}
      </p>
      <p className="mt-2 text-sm text-text-secondary">
        {exhausted
          ? "Попробуйте обновить страницу."
          : countdown > 0
            ? `Повторная попытка через ${countdown} сек...`
            : "Повторная попытка..."}
      </p>
    </div>
  );
}

function HardFailureBanner({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="mt-4 flex items-center justify-between gap-3 rounded-lg border border-border bg-bg-surface px-4 py-3 text-sm">
      <span className="text-text-primary">
        Не удалось загрузить эту категорию. Попробуйте другой фильтр или повторите попытку.
      </span>
      <button
        type="button"
        onClick={onRetry}
        className="rounded-md border border-accent bg-accent/10 px-3 py-1 text-xs font-medium text-accent hover:bg-accent/20"
      >
        Попробовать снова
      </button>
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
