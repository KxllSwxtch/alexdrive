"use client";

import Link from "next/link";
import Image from "next/image";
import { useState, useCallback } from "react";

import type { CarListing } from "@/lib/types";
import { formatMileage, formatPriceKrw } from "@/lib/format";
import { buildCarDetailPath } from "@/lib/url";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

interface CarCardProps {
  car: CarListing;
  index?: number;
}

export function CarCard({ car, index }: CarCardProps) {
  const [prefetchActive, setPrefetchActive] = useState(false);

  const onHover = useCallback(() => {
    if (!prefetchActive) {
      setPrefetchActive(true);
      fetch(`${BACKEND_URL}/api/cars/prefetch?id=${encodeURIComponent(car.encryptedId)}`, {
        method: "POST",
      }).catch(() => {});
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefetchActive, car.encryptedId]);

  return (
    <Link
      href={buildCarDetailPath(car.name, car.year, car.encryptedId)}
      prefetch={prefetchActive ? null : false}
      onMouseEnter={onHover}
      onTouchStart={onHover}
      className="group flex flex-col overflow-hidden rounded-xl border border-border bg-bg-surface transition-all duration-300 hover:border-gold/30 hover:shadow-[0_0_30px_rgba(212,175,55,0.06)]"
    >
      {/* Image */}
      <div className="relative aspect-[16/10] overflow-hidden bg-bg-elevated">
        {car.imageUrl ? (
          <Image
            src={car.imageUrl}
            alt={car.name}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            className="object-cover transition-transform duration-500 group-hover:scale-105"
            loading={index !== undefined && index < 3 ? "eager" : "lazy"}
            priority={index !== undefined && index < 3}
            unoptimized
          />
        ) : (
          <div className="flex h-full items-center justify-center text-text-secondary">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="opacity-30">
              <path d="M5 17h14M5 17l1.5-6h11L19 17M5 17H3l1-4M19 17h2l-1-4M6.5 11L8 7h8l1.5 4M9 14h.01M15 14h.01" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex flex-1 flex-col p-4">
        {/* Price */}
        {car.priceMl ? (
          <p className="text-lg font-bold text-gold">
            {formatPriceKrw(car.priceMl)}
          </p>
        ) : null}

        {/* Name */}
        <h3 className="mt-1.5 line-clamp-2 text-sm font-semibold leading-snug text-text-primary group-hover:text-gold transition-colors">
          {car.name}
        </h3>

        {/* Specs */}
        <div className="mt-3 flex flex-col gap-1 text-xs text-text-secondary">
          {car.year && (
            <span className="inline-flex items-center gap-1">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
              </svg>
              {car.year}
            </span>
          )}
          {car.mileage && (
            <span className="inline-flex items-center gap-1">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" /><path d="M12 6v6l4 2" />
              </svg>
              {formatMileage(car.mileage)}
            </span>
          )}
          {car.transmission && (
            <span className="inline-flex items-center gap-1">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3" /><path d="M3 12h6m6 0h6" /><path d="M12 3v6m0 6v6" /><path d="m5.6 5.6 4.25 4.25m4.3 4.3 4.25 4.25" /><path d="m18.4 5.6-4.25 4.25m-4.3 4.3L5.6 18.4" />
              </svg>
              {car.transmission}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
