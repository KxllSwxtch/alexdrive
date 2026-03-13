import { ContactCard } from "@/components/ContactCard";

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-bg-elevated ${className ?? ""}`} />;
}

export function CarDetailSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-[1fr_320px] lg:grid-cols-[1fr_300px]">
      {/* Left column */}
      <div className="min-w-0 space-y-6">
        {/* Gallery placeholder */}
        <div>
          <Skeleton className="aspect-[4/3] w-full rounded-xl" />
          <div className="mt-2 flex gap-2 overflow-hidden">
            {Array.from({ length: 7 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-20 md:h-20 md:w-28 shrink-0 rounded-lg" />
            ))}
          </div>
        </div>

        {/* Title & Price */}
        <div>
          <Skeleton className="h-8 w-3/4 sm:h-9" />
          <Skeleton className="mt-3 h-8 w-40" />
        </div>

        {/* Specs grid */}
        <div className="rounded-xl border border-border bg-bg-surface p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
            Характеристики
          </h2>
          <div className="mt-4 grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i}>
                <Skeleton className="h-3 w-16" />
                <Skeleton className="mt-2 h-4 w-24" />
              </div>
            ))}
          </div>
        </div>

        {/* Inspection link placeholder */}
        <Skeleton className="h-5 w-64" />

        {/* Options placeholder */}
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-xl" />
          ))}
        </div>
      </div>

      {/* Right column — real contact card, interactive immediately */}
      <div className="hidden md:block md:sticky md:top-20 md:self-start space-y-4">
        <ContactCard />
      </div>
    </div>
  );
}
