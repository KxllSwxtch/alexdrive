"use client";

import dynamic from "next/dynamic";

const CreditCalculatorCompact = dynamic(
  () =>
    import("@/components/CreditCalculatorCompact").then((m) => ({
      default: m.CreditCalculatorCompact,
    })),
  {
    ssr: false,
    loading: () => (
      <div className="rounded-xl border border-border bg-bg-surface overflow-hidden">
        <div className="flex w-full items-center justify-between p-4">
          <span className="text-sm font-semibold text-text-primary">
            Кредитный калькулятор
          </span>
        </div>
      </div>
    ),
  },
);

export function CreditCalculatorLazy({ initialPrice }: { initialPrice: number }) {
  return <CreditCalculatorCompact initialPrice={initialPrice} />;
}
