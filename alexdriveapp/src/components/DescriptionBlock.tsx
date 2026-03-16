"use client";

import { useState, useRef, useEffect } from "react";

const MAX_HEIGHT = 160; // px before truncation

export function DescriptionBlock({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  const [needsTruncation, setNeedsTruncation] = useState(false);
  const contentRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (contentRef.current && contentRef.current.scrollHeight > MAX_HEIGHT) {
      setNeedsTruncation(true);
    }
  }, [text]);

  return (
    <div className="rounded-xl border border-border bg-bg-surface p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
        Описание
      </h2>
      <div className="relative mt-3">
        <p
          ref={contentRef}
          className="text-sm text-text-primary whitespace-pre-line leading-relaxed overflow-hidden transition-[max-height] duration-300"
          style={{ maxHeight: expanded || !needsTruncation ? "none" : `${MAX_HEIGHT}px` }}
        >
          {text}
        </p>
        {needsTruncation && !expanded && (
          <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-bg-surface to-transparent" />
        )}
      </div>
      {needsTruncation && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 text-xs font-medium text-gold hover:text-gold-light transition-colors"
        >
          {expanded ? "Свернуть" : "Показать полностью"}
        </button>
      )}
    </div>
  );
}
