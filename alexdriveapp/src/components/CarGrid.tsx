import type { CarListing } from "@/lib/types";
import { CarCard } from "./CarCard";

interface CarGridProps {
  cars: CarListing[];
}

export function CarGrid({ cars }: CarGridProps) {
  if (cars.length === 0) {
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
        <CarCard key={car.encryptedId || i} car={car} index={i} />
      ))}
    </div>
  );
}
