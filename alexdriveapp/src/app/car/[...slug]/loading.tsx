import Link from "next/link";

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-bg-elevated ${className ?? ""}`} />;
}

export default function CarDetailLoading() {
  return (
    <div className="px-4 py-6 pb-20 md:pb-6 sm:px-6 lg:px-8">
      {/* Back link — real, interactive immediately */}
      <Link
        href="/"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-gold"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Назад в каталог
      </Link>

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
          <div className="rounded-xl border border-border bg-bg-surface p-5">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
              Контакт
            </h3>
            <div className="mt-4 space-y-3">
              <div>
                <p className="text-lg font-bold text-text-primary">Кан Алексей</p>
                <p className="text-sm text-text-secondary">Менеджер по продажам</p>
              </div>
              <a
                href="tel:+821039086050"
                className="flex items-center gap-2.5 text-sm text-text-primary transition-colors hover:text-gold"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-bg-elevated">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                +82-10-3908-6050
              </a>
              <a
                href="https://wa.me/821039086050"
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-gold py-3 text-sm font-semibold text-bg-primary transition-colors hover:bg-gold-light"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                </svg>
                Написать в WhatsApp
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile sticky contact bar — real, interactive immediately */}
      <div className="fixed bottom-0 left-0 right-0 z-40 flex items-center gap-3 border-t border-border bg-bg-primary px-4 py-3 md:hidden">
        <a
          href="tel:+821039086050"
          className="flex h-11 w-11 items-center justify-center rounded-xl border border-border bg-bg-surface text-text-primary transition-colors hover:text-gold"
          aria-label="Позвонить"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </a>
        <a
          href="https://wa.me/821039086050"
          target="_blank"
          rel="noopener noreferrer"
          className="flex h-11 flex-1 items-center justify-center gap-2 rounded-xl bg-gold text-sm font-semibold text-bg-primary transition-colors hover:bg-gold-light"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
          </svg>
          Написать в WhatsApp
        </a>
      </div>
    </div>
  );
}
