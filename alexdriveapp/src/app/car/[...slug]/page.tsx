import { Suspense } from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { permanentRedirect } from "next/navigation";
import type { CarDetail } from "@/lib/types";
import { buildCarDetailPath, fromUrlSafeId } from "@/lib/url";
import { CarDetailContent, fetchCar } from "@/components/CarDetailContent";
import { CarDetailSkeleton } from "@/components/CarDetailSkeleton";
import { MobileContactBar } from "@/components/MobileContactBar";

export const revalidate = 600; // ISR: 10 minutes

interface PageProps {
  params: Promise<{ slug: string[] }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  try {
    const slugParts = (await params).slug;
    const rawId = slugParts[slugParts.length - 1];
    const id = fromUrlSafeId(rawId);

    // Race: if cache hit, return rich metadata; if cold, return generic quickly
    const car = await Promise.race([
      fetchCar(id),
      new Promise<null>((resolve) => setTimeout(() => resolve(null), 200)),
    ]);

    if (!car) return { title: "Автомобиль - AlexDrive" };

    return {
      title: `${car.name} ${car.year} - AlexDrive`,
      description: `${car.name} ${car.year}, ${car.mileage}, ${car.price} - купить в AlexDrive, Сувон`,
      openGraph: {
        title: `${car.name} ${car.year} - AlexDrive`,
        description: `${car.name} - ${car.price}`,
        images: car.images[0] ? [car.images[0]] : [],
      },
    };
  } catch {
    return { title: "Автомобиль - AlexDrive" };
  }
}

export default async function CarDetailPage({ params }: PageProps) {
  const slugParts = (await params).slug;

  // OLD URL: /car/ENCODED_ID → 301 redirect to new SEO-friendly URL
  if (slugParts.length === 1) {
    const rawSegment = slugParts[0];
    const id = fromUrlSafeId(rawSegment);
    let car: CarDetail;

    try {
      car = await fetchCar(id);
    } catch {
      return <ErrorState />;
    }

    const newPath = buildCarDetailPath(
      car.name,
      car.year,
      car.id,
    );
    permanentRedirect(newPath);
  }

  // NEW URL: /car/slug/id
  const rawId = slugParts[slugParts.length - 1];
  const id = fromUrlSafeId(rawId);

  return (
    <div className="px-4 py-6 pb-20 md:pb-6 sm:px-6 lg:px-8">
      {/* Back link — instant */}
      <Link
        href="/"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-text-secondary transition-colors hover:text-gold"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Назад в каталог
      </Link>

      <Suspense fallback={
        <>
          <CarDetailSkeleton />
          {/* Basic mobile contact bar while loading */}
          <MobileContactBar />
        </>
      }>
        <div className="grid gap-6 md:grid-cols-[1fr_320px] lg:grid-cols-[1fr_300px]">
          <CarDetailContent id={id} />
        </div>
      </Suspense>
    </div>
  );
}

function ErrorState() {
  return (
    <div className="px-4 py-20 text-center sm:px-6 lg:px-8">
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
