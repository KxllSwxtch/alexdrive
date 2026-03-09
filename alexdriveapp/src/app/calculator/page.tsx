import type { Metadata } from "next";
import { CreditCalculator } from "@/components/CreditCalculator";

export const metadata: Metadata = {
  title: "Кредитный калькулятор - AlexDrive",
  description: "Рассчитайте ежемесячный платёж по автокредиту в Южной Корее",
};

export default async function CalculatorPage({
  searchParams,
}: {
  searchParams: Promise<{ price?: string }>;
}) {
  const { price } = await searchParams;
  const initialCarPrice = price ? parseInt(price, 10) || undefined : undefined;

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        <h1 className="font-heading text-2xl font-bold tracking-tight sm:text-3xl">
          Кредитный калькулятор
        </h1>
        <p className="mt-2 text-sm text-text-secondary">
          Рассчитайте ежемесячный платёж по автокредиту
        </p>
        <div className="mt-6">
          <CreditCalculator initialCarPrice={initialCarPrice} />
        </div>
      </div>
    </div>
  );
}
