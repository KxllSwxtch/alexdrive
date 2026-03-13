import Link from "next/link";
import { CarDetailSkeleton } from "@/components/CarDetailSkeleton";
import { MobileContactBar } from "@/components/MobileContactBar";

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

      <CarDetailSkeleton />
      <MobileContactBar />
    </div>
  );
}
