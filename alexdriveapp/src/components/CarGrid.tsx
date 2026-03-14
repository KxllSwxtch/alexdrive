import type { CarListing } from "@/lib/types";
import { CarCard } from "./CarCard";

interface CarGridProps {
  cars: CarListing[];
  status?: string;
}

export function CarGrid({ cars, status }: CarGridProps) {
  if (cars.length === 0) {
    if (status === "rate_limited") {
      return (
        <div className="flex flex-col items-center justify-center rounded-xl border border-amber-500/30 bg-amber-500/5 px-6 py-20 text-center">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-amber-400 opacity-70">
            <path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <p className="mt-4 text-base font-medium text-text-secondary">
            Сервис временно недоступен
          </p>
          <p className="mt-1 text-sm text-text-secondary/70">
            Попробуйте позже
          </p>
        </div>
      );
    }
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-bg-surface px-6 py-20 text-center">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-text-secondary opacity-40">
          <path d="M5 17h14M5 17l1.5-6h11L19 17M5 17H3l1-4M19 17h2l-1-4M6.5 11L8 7h8l1.5 4M9 14h.01M15 14h.01" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <p className="mt-4 text-base font-medium text-text-secondary">
          Автомобили не найдены
        </p>
        <p className="mt-1 text-sm text-text-secondary/70">
          Попробуйте изменить параметры поиска
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
      {cars.map((car, i) => (
        <CarCard key={car.encryptedId} car={car} index={i} />
      ))}
    </div>
  );
}
