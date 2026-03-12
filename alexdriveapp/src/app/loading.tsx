export default function Loading() {
  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mb-6">
        <div className="h-8 w-64 rounded bg-bg-elevated animate-pulse" />
        <div className="mt-2 h-4 w-40 rounded bg-bg-elevated animate-pulse" />
      </div>
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
    </div>
  );
}
