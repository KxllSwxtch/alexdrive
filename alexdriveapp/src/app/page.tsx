"use client";

import { useState, useEffect } from "react";
import { FilterBar } from "@/components/FilterBar";
import { CarGrid } from "@/components/CarGrid";
import { Pagination } from "@/components/Pagination";
import type { FilterData, CarListing, CarListingParams } from "@/lib/types";

const PAGE_SIZE = 20;
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

export default function CatalogPage() {
  const [filters, setFilters] = useState<FilterData | null>(null);
  const [cars, setCars] = useState<CarListing[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [params, setParams] = useState<CarListingParams>({
    PageNow: 1,
    PageSize: PAGE_SIZE,
    PageSort: "ModDt",
    PageAscDesc: "DESC",
  });

  // Debounce params changes before fetching
  const [debouncedParams, setDebouncedParams] = useState(params);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedParams(params), 500);
    return () => clearTimeout(timer);
  }, [params]);

  // Load filter data once
  useEffect(() => {
    let ignore = false;
    fetch(`${BACKEND_URL}/api/filters`)
      .then((r) => r.json())
      .then((data) => {
        if (!ignore && data && data.makers) setFilters(data);
      })
      .catch(console.error);
    return () => { ignore = true; };
  }, []);

  // Load cars when debounced params change
  useEffect(() => {
    let ignore = false;
    setLoading(true);

    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(debouncedParams)) {
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
  }, [debouncedParams]);

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
        params={params}
        onParamsChange={setParams}
        loading={loading}
      />

      {/* Results */}
      <div className="mt-6">
        {loading && cars.length === 0 ? (
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
          onPageChange={(page) =>
            setParams((prev) => ({ ...prev, PageNow: page }))
          }
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
