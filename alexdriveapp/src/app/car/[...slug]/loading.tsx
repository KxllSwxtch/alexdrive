export default function CarDetailLoading() {
  return (
    <div className="px-4 py-6 pb-20 md:pb-6 sm:px-6 lg:px-8 animate-pulse">
      {/* Back link placeholder */}
      <div className="mb-6 h-5 w-36 rounded bg-bg-elevated" />

      <div className="grid gap-6 md:grid-cols-[1fr_320px] lg:grid-cols-[1fr_300px]">
        {/* Left column */}
        <div className="min-w-0 space-y-6">
          {/* Gallery placeholder */}
          <div className="aspect-[16/10] rounded-xl border border-border bg-bg-surface" />

          {/* Thumbnails */}
          <div className="flex gap-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="h-16 w-24 md:h-20 md:w-28 flex-shrink-0 rounded-lg bg-bg-surface"
              />
            ))}
          </div>

          {/* Title & Price */}
          <div>
            <div className="h-8 w-3/4 rounded bg-bg-elevated" />
            <div className="mt-2 h-7 w-40 rounded bg-bg-elevated" />
          </div>

          {/* Specs grid */}
          <div className="rounded-xl border border-border bg-bg-surface p-5">
            <div className="h-4 w-32 rounded bg-bg-elevated" />
            <div className="mt-4 grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i}>
                  <div className="h-3 w-20 rounded bg-bg-elevated" />
                  <div className="mt-1.5 h-4 w-28 rounded bg-bg-elevated" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column - sidebar placeholder (desktop only) */}
        <div className="hidden md:block space-y-4">
          <div className="rounded-xl border border-border bg-bg-surface p-5 h-48" />
          <div className="rounded-xl border border-border bg-bg-surface p-5 h-14" />
        </div>
      </div>
    </div>
  );
}
