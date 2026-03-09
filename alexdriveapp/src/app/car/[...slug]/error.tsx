"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function CarDetailError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Car detail page error:", error);
  }, [error]);

  return (
    <div className="px-4 py-20 text-center sm:px-6 lg:px-8">
      <div className="mx-auto max-w-md space-y-6">
        <svg
          width="48"
          height="48"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="mx-auto text-text-secondary"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
        </svg>

        <div>
          <h2 className="text-lg font-semibold text-text-primary">
            Не удалось загрузить данные
          </h2>
          <p className="mt-2 text-sm text-text-secondary">
            Произошла ошибка при загрузке страницы автомобиля. Попробуйте
            обновить страницу или вернитесь в каталог.
          </p>
        </div>

        <div className="flex items-center justify-center gap-3">
          <button
            onClick={reset}
            className="rounded-xl bg-gold px-5 py-2.5 text-sm font-semibold text-bg-primary transition-colors hover:bg-gold-light"
          >
            Попробовать снова
          </button>
          <Link
            href="/"
            className="rounded-xl border border-border px-5 py-2.5 text-sm font-medium text-text-secondary transition-colors hover:text-text-primary"
          >
            В каталог
          </Link>
        </div>
      </div>
    </div>
  );
}
