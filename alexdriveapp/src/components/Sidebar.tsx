"use client"

import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const STORAGE_KEY = "alexdrive-sidebar-collapsed"

const navLinks = [
  {
    href: "/",
    label: "Каталог",
    icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1",
  },
  {
    href: "/about",
    label: "О нас",
    icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  },
  {
    href: "/contacts",
    label: "Контакты",
    icon: "M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z",
  },
  {
    href: "/calculator",
    label: "Калькулятор",
    icon: "M9 7h6m-6 4h6m-4 4h2M5 3h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2z",
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored === "true") setCollapsed(true)
    } catch {}
  }, [])

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev
      try {
        localStorage.setItem(STORAGE_KEY, String(next))
      } catch {}
      return next
    })
  }, [])

  return (
    <aside
      className="hidden lg:flex flex-col sticky top-16 h-[calc(100vh-4rem)] border-r border-border bg-bg-surface shrink-0 overflow-hidden transition-[width] duration-300 ease-in-out"
      style={{ width: collapsed ? 64 : 268 }}
    >
      {/* Header with toggle */}
      <div className={cn("flex items-center pt-6 pb-4", collapsed ? "justify-center px-2" : "justify-between px-6")}>
        {!collapsed && (
          <p className="font-heading text-sm font-semibold uppercase tracking-wider text-text-secondary">
            Меню
          </p>
        )}
        <button
          onClick={toggleCollapsed}
          className="flex h-8 w-8 items-center justify-center rounded-md text-text-secondary transition-colors hover:bg-bg-elevated hover:text-text-primary"
          aria-label={collapsed ? "Развернуть меню" : "Свернуть меню"}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn("transition-transform duration-300", collapsed && "rotate-180")}
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
      </div>

      {/* Nav items */}
      <nav className={cn("flex flex-col gap-1", collapsed ? "px-2" : "px-4")}>
        {navLinks.map((link) => {
          const isActive =
            link.href === "/"
              ? pathname === "/"
              : pathname.startsWith(link.href)

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "group relative flex items-center rounded-lg text-sm font-medium transition-colors",
                collapsed ? "justify-center px-0 py-3" : "gap-3 px-4 py-3",
                isActive
                  ? "bg-gold text-bg-primary"
                  : "text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
              )}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="shrink-0"
              >
                <path d={link.icon} />
              </svg>
              {!collapsed && <span>{link.label}</span>}
              {/* Tooltip in collapsed mode */}
              {collapsed && (
                <span className="pointer-events-none absolute left-full ml-2 whitespace-nowrap rounded-md bg-bg-elevated px-2.5 py-1.5 text-xs font-medium text-text-primary opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                  {link.label}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* Bottom section */}
      <div className={cn("mt-auto border-t border-border", collapsed ? "p-2" : "p-4")}>
        <a
          href="https://wa.me/821039086050"
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            "flex items-center justify-center rounded-lg bg-gold font-semibold text-bg-primary transition-colors hover:bg-gold-light",
            collapsed ? "h-10 w-10 mx-auto" : "w-full gap-2 px-4 py-3 text-sm"
          )}
          aria-label="WhatsApp"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" className="shrink-0">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
          </svg>
          {!collapsed && <span>WhatsApp</span>}
        </a>

        {!collapsed && (
          <div className="mt-3 text-center text-xs text-text-secondary">
            <p className="font-medium text-text-primary">Кан Алексей</p>
            <a
              href="tel:+821039086050"
              className="text-gold hover:text-gold-light"
            >
              +82-10-3908-6050
            </a>
          </div>
        )}
      </div>
    </aside>
  )
}
