"use client";

import Link from "next/link";
import { useSyncExternalStore } from "react";
import { CATALOG_URL_KEY, readSession } from "@/lib/catalogParams";

// "Назад в каталог" for detail pages: returns to the catalog exactly as the
// user left it (filters, page, sort) via the canonical URL that CatalogContent
// persists in sessionStorage. Falls back to "/" for deep links and new tabs,
// where no catalog state exists in this tab.
const subscribe = () => () => {};
const getHref = () => readSession(CATALOG_URL_KEY) || "/";
const getServerHref = () => "/";

export function BackToCatalogLink({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  const href = useSyncExternalStore(subscribe, getHref, getServerHref);

  return (
    <Link href={href} className={className}>
      {children}
    </Link>
  );
}
