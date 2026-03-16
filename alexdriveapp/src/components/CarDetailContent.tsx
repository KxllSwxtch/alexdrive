import { cache } from "react";
import Link from "next/link";
import { backendFetch } from "@/lib/api";
import type { CarDetail } from "@/lib/types";
import { translateSmartly } from "@/lib/translations";
import { formatPrice, priceStringToKrw } from "@/lib/format";
import { ImageGallery } from "@/components/ImageGallery";
import { ContactCard } from "@/components/ContactCard";
import { CarOptions } from "@/components/CarOptions";
import { CreditCalculatorLazy } from "@/components/CreditCalculatorLazy";
import { ShareButton } from "@/components/ShareButton";

/** Fetch car detail by seq ID (deduplicated across generateMetadata + page) */
export const fetchCar = cache(async (id: string): Promise<CarDetail> => {
  return backendFetch<CarDetail>(
    "/cars/detail",
    new URLSearchParams({ id }),
    { revalidate: 600 },
  );
});

export async function CarDetailContent({ id }: { id: string }) {
  let car: CarDetail;
  try {
    car = await fetchCar(id);
  } catch (error) {
    console.error("Failed to load car:", error);
    return (
      <div className="col-span-full px-4 py-20 text-center sm:px-6 lg:px-8">
        <p className="text-lg text-text-secondary">
          Не удалось загрузить данные автомобиля
        </p>
        <Link
          href="/"
          className="mt-4 inline-flex items-center gap-2 text-gold hover:text-gold-light"
        >
          &larr; Вернуться в каталог
        </Link>
      </div>
    );
  }

  const translatedName = translateSmartly(car.name);
  const translatedFuel = car.fuel ? translateSmartly(car.fuel) : "";
  const translatedTransmission = car.transmission ? translateSmartly(car.transmission) : "";
  const translatedColor = car.color ? translateSmartly(car.color) : "";

  const carPriceKrw = car.price ? priceStringToKrw(car.price) : 0;
  const shareTitle = `${translatedName} ${car.year}${car.price ? ` - ${formatPrice(car.price)}` : ""}`;

  const specs = [
    { label: "Год выпуска", value: car.year },
    { label: "Пробег", value: car.mileage },
    { label: "Топливо", value: translatedFuel },
    { label: "КПП", value: translatedTransmission },
    { label: "Цвет", value: translatedColor },
    { label: "Номер авто", value: car.carNumber },
  ].filter((s) => s.value);

  return (
    <>
      {/* Left column */}
      <div className="min-w-0 space-y-6">
        {/* Gallery */}
        <ImageGallery images={car.images} alt={translatedName} blurDataUrl={car.blurDataUrl} />

        {/* Title & Price + Share */}
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="font-heading text-2xl font-bold tracking-tight sm:text-3xl">
              {translatedName}
            </h1>
            {car.price && (
              <p className="mt-2 text-2xl font-bold text-gold">
                {formatPrice(car.price)}
              </p>
            )}
          </div>
          <ShareButton title={shareTitle} />
        </div>

        {/* Specs grid */}
        {specs.length > 0 && (
          <div className="rounded-xl border border-border bg-bg-surface p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
              Характеристики
            </h2>
            <div className="mt-4 grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3">
              {specs.map((spec) => (
                <div key={spec.label}>
                  <p className="text-xs text-text-secondary">{spec.label}</p>
                  <p className="mt-0.5 text-sm font-medium text-text-primary">
                    {spec.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Diagnostics report link */}
        {car.diagnosticsUrl && (
          <a
            href={car.diagnosticsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-sm text-gold transition-colors hover:text-gold-light"
          >
            Посмотреть диагностику авто
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M15 3h6v6" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M10 14L21 3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </a>
        )}

        {/* Compact calculator - mobile only */}
        {carPriceKrw > 0 && (
          <div className="md:hidden">
            <CreditCalculatorLazy initialPrice={carPriceKrw} />
          </div>
        )}

        {/* Options */}
        {car.options.length > 0 && (
          <CarOptions
            options={car.options.map((group) => ({
              group: translateSmartly(group.group) || "Опции",
              items: group.items.map((item) => translateSmartly(item)),
            }))}
          />
        )}
      </div>

      {/* Right column - sticky contact card (hidden on mobile) */}
      <div className="hidden md:block md:sticky md:top-20 md:self-start space-y-4">
        <ContactCard />
        {carPriceKrw > 0 && (
          <CreditCalculatorLazy initialPrice={carPriceKrw} />
        )}
      </div>

      {/* Mobile sticky contact bar with share button */}
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
        <ShareButton title={shareTitle} compact />
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
    </>
  );
}
