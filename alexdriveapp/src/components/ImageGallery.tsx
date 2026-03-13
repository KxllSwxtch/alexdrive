"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Image from "next/image";

interface ImageGalleryProps {
  images: string[];
  alt: string;
  blurDataUrl?: string;
}

export function ImageGallery({ images, alt, blurDataUrl }: ImageGalleryProps) {
  const [current, setCurrent] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const triggerRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);
  const fullscreenThumbnailRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const touchStartX = useRef(0);

  if (images.length === 0) {
    return (
      <div className="flex aspect-[16/10] items-center justify-center rounded-xl border border-border bg-bg-surface">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-text-secondary opacity-30">
          <path d="M5 17h14M5 17l1.5-6h11L19 17M5 17H3l1-4M19 17h2l-1-4M6.5 11L8 7h8l1.5 4M9 14h.01M15 14h.01" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    );
  }

  const goTo = (idx: number) => {
    setCurrent((idx + images.length) % images.length);
  };

  const openFullscreen = () => setIsFullscreen(true);
  const closeFullscreen = useCallback(() => {
    setIsFullscreen(false);
    triggerRef.current?.focus();
  }, []);

  // Keyboard navigation + body scroll lock
  useEffect(() => {
    if (!isFullscreen) return;
    document.body.style.overflow = "hidden";
    overlayRef.current?.focus();

    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeFullscreen();
      else if (e.key === "ArrowLeft") goTo(current - 1);
      else if (e.key === "ArrowRight") goTo(current + 1);
    };
    window.addEventListener("keydown", handler);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handler);
    };
  }, [isFullscreen, current, closeFullscreen]);

  // Auto-scroll active fullscreen thumbnail into view
  useEffect(() => {
    if (isFullscreen) {
      fullscreenThumbnailRefs.current[current]?.scrollIntoView({
        behavior: "smooth",
        inline: "center",
      });
    }
  }, [current, isFullscreen]);

  const onTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };
  const onTouchEnd = (e: React.TouchEvent) => {
    const delta = e.changedTouches[0].clientX - touchStartX.current;
    if (Math.abs(delta) > 50) {
      goTo(delta > 0 ? current - 1 : current + 1);
    }
  };

  return (
    <div className="space-y-3">
      {/* Main image */}
      <div
        ref={triggerRef}
        tabIndex={-1}
        onClick={openFullscreen}
        className="group relative aspect-[16/10] max-h-[70vh] cursor-zoom-in overflow-hidden rounded-xl border border-border bg-bg-surface"
      >
        <Image
          src={images[current]}
          alt={`${alt} - фото ${current + 1}`}
          fill
          sizes="(max-width: 1024px) 100vw, 60vw"
          className="object-cover"
          priority
          placeholder={blurDataUrl ? "blur" : "empty"}
          blurDataURL={blurDataUrl}
        />

        {images.length > 1 && (
          <>
            {/* Prev */}
            <button
              onClick={(e) => { e.stopPropagation(); goTo(current - 1); }}
              className="absolute left-3 top-1/2 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-bg-primary/60 text-text-primary backdrop-blur-sm transition-opacity opacity-0 group-hover:opacity-100"
              aria-label="Предыдущее фото"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            {/* Next */}
            <button
              onClick={(e) => { e.stopPropagation(); goTo(current + 1); }}
              className="absolute right-3 top-1/2 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full bg-bg-primary/60 text-text-primary backdrop-blur-sm transition-opacity opacity-0 group-hover:opacity-100"
              aria-label="Следующее фото"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 18l6-6-6-6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            {/* Counter */}
            <div className="absolute bottom-3 right-3 rounded-lg bg-bg-primary/60 px-2.5 py-1 text-xs font-medium text-text-primary backdrop-blur-sm">
              {current + 1} / {images.length}
            </div>
          </>
        )}
      </div>

      {/* Thumbnails */}
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {images.map((src, i) => (
            <button
              key={i}
              onClick={() => setCurrent(i)}
              className={`relative h-16 w-24 md:h-20 md:w-28 flex-shrink-0 overflow-hidden rounded-lg border-2 transition-colors ${
                i === current
                  ? "border-gold"
                  : "border-transparent opacity-60 hover:opacity-100"
              }`}
            >
              <Image
                src={src}
                alt={`${alt} - миниатюра ${i + 1}`}
                fill
                sizes="96px"
                className="object-cover"
                loading="lazy"
              />
            </button>
          ))}
        </div>
      )}

      {/* Fullscreen overlay */}
      {isFullscreen && (
        <div
          ref={overlayRef}
          role="dialog"
          aria-modal="true"
          aria-label="Галерея фотографий"
          tabIndex={-1}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/95 outline-none"
          onClick={(e) => { if (e.target === e.currentTarget) closeFullscreen(); }}
        >
          {/* Close button */}
          <button
            onClick={closeFullscreen}
            className="absolute top-4 right-4 z-10 flex h-10 w-10 items-center justify-center rounded-full text-white/70 transition-colors hover:text-white hover:bg-white/10"
            aria-label="Закрыть галерею"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          {/* Image area */}
          <div
            className="relative flex w-full max-w-[90vw] flex-1 items-center justify-center"
            onTouchStart={onTouchStart}
            onTouchEnd={onTouchEnd}
          >
            {/* Prev arrow */}
            {images.length > 1 && (
              <button
                onClick={() => goTo(current - 1)}
                className="absolute left-2 z-10 flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-sm transition-colors hover:bg-white/20"
                aria-label="Предыдущее фото"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            )}

            {/* Fullscreen image */}
            <div className="relative h-[75vh] w-full">
              <Image
                src={images[current]}
                alt={`${alt} - фото ${current + 1}`}
                fill
                sizes="90vw"
                className="object-contain"
                loading="eager"
              />
            </div>

            {/* Next arrow */}
            {images.length > 1 && (
              <button
                onClick={() => goTo(current + 1)}
                className="absolute right-2 z-10 flex h-12 w-12 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-sm transition-colors hover:bg-white/20"
                aria-label="Следующее фото"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 18l6-6-6-6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            )}
          </div>

          {/* Counter */}
          {images.length > 1 && (
            <div className="py-2 text-sm font-medium text-white/80">
              {current + 1} / {images.length}
            </div>
          )}

          {/* Fullscreen thumbnails */}
          {images.length > 1 && (
            <div className="flex max-w-[90vw] gap-2 overflow-x-auto px-4 pb-4">
              {images.map((src, i) => {
                const inWindow = Math.abs(i - current) <= 5;
                return (
                  <button
                    key={i}
                    ref={(el) => { fullscreenThumbnailRefs.current[i] = el; }}
                    onClick={() => setCurrent(i)}
                    className={`relative h-14 w-20 flex-shrink-0 overflow-hidden rounded-lg border-2 transition-all ${
                      i === current
                        ? "border-gold"
                        : "border-transparent opacity-50 hover:opacity-80"
                    }`}
                  >
                    {inWindow ? (
                      <Image
                        src={src}
                        alt={`${alt} - миниатюра ${i + 1}`}
                        fill
                        sizes="80px"
                        className="object-cover"
                      />
                    ) : (
                      <div className="absolute inset-0 bg-bg-elevated" />
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
