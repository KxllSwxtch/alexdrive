"use client";

import { Accordion } from "@base-ui/react/accordion";
import { ChevronDown } from "lucide-react";

interface CarOptionsProps {
  options: { group: string; items: string[] }[];
}

export function CarOptions({ options }: CarOptionsProps) {
  return (
    <div className="rounded-xl border border-border bg-bg-surface p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
        Опции и комплектация
      </h2>
      <Accordion.Root multiple keepMounted className="mt-4 divide-y divide-border">
        {options.map((group, i) => (
          <Accordion.Item key={i} value={i}>
            <Accordion.Header>
              <Accordion.Trigger className="group flex w-full cursor-pointer items-center justify-between py-3 text-xs font-semibold text-gold transition-colors hover:text-gold-light">
                {group.group}
                <ChevronDown className="size-4 text-text-secondary transition-transform duration-200 group-data-[panel-open]:rotate-180" />
              </Accordion.Trigger>
            </Accordion.Header>
            <Accordion.Panel data-accordion-panel>
              <div className="flex flex-wrap gap-2 pb-3">
                {group.items.map((item, j) => (
                  <span
                    key={j}
                    className="inline-flex rounded-lg border border-border bg-bg-elevated px-3 py-1.5 text-xs text-text-secondary"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion.Root>
    </div>
  );
}
