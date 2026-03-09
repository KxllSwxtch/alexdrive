"use client";

import { useMemo, useState } from "react";
import { calculateCredit } from "@/lib/credit-math";
import { formatKrw } from "@/lib/format";
import { cn } from "@/lib/utils";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TERM_OPTIONS = [3, 6, 12, 18, 24, 30, 36, 48, 60, 72];

function termLabel(months: number): string {
  if (months >= 12) {
    const years = Math.floor(months / 12);
    const rem = months % 12;
    return rem > 0
      ? `${months} мес. (${years} г. ${rem} мес.)`
      : `${months} мес. (${years} ${years === 1 ? "год" : years < 5 ? "года" : "лет"})`;
  }
  return `${months} мес.`;
}

interface CreditCalculatorProps {
  initialCarPrice?: number;
}

export function CreditCalculator({ initialCarPrice }: CreditCalculatorProps) {
  const [carPrice, setCarPrice] = useState(
    initialCarPrice ? String(initialCarPrice) : ""
  );
  const [termMonths, setTermMonths] = useState(36);
  const [annualRate, setAnnualRate] = useState("5.9");
  const [showSchedule, setShowSchedule] = useState(false);

  const result = useMemo(() => {
    const price = parseInt(carPrice, 10);
    const rate = parseFloat(annualRate);
    if (!price || isNaN(rate)) return null;
    return calculateCredit({
      carPrice: price,
      termMonths,
      annualRate: rate,
    });
  }, [carPrice, termMonths, annualRate]);

  const handlePriceChange = (raw: string) => {
    setCarPrice(raw.replace(/[^\d]/g, ""));
  };
  const handleRateChange = (raw: string) => {
    setAnnualRate(raw.replace(/[^\d.]/g, ""));
  };

  const principalPercent = result
    ? Math.round((result.loanAmount / result.totalPayment) * 100)
    : 0;
  const interestPercent = result ? 100 - principalPercent : 0;

  return (
    <div className="space-y-6">
      {/* Input fields */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label>Сумма кредита</Label>
          <InputGroup>
            <InputGroupAddon align="inline-start">₩</InputGroupAddon>
            <InputGroupInput
              type="text"
              inputMode="numeric"
              placeholder="10,000,000"
              value={carPrice ? formatKrw(parseInt(carPrice, 10) || 0) : ""}
              onChange={(e) => handlePriceChange(e.target.value)}
            />
          </InputGroup>
        </div>

        <div className="space-y-1.5">
          <Label>Срок кредита</Label>
          <Select value={termMonths} onValueChange={(val) => setTermMonths(val as number)}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TERM_OPTIONS.map((m) => (
                <SelectItem key={m} value={m}>
                  {termLabel(m)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Процентная ставка</Label>
          <InputGroup>
            <InputGroupInput
              type="text"
              inputMode="decimal"
              placeholder="5.9"
              value={annualRate}
              onChange={(e) => handleRateChange(e.target.value)}
            />
            <InputGroupAddon align="inline-end">%</InputGroupAddon>
          </InputGroup>
        </div>
      </div>

      {/* C. Results summary */}
      {result ? (
        <div className="rounded-xl border border-border bg-bg-surface p-5 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs text-text-secondary">Сумма кредита</p>
              <p className="mt-0.5 text-sm font-medium text-text-primary">
                ₩{formatKrw(result.loanAmount)}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-secondary">Ежемесячный платёж</p>
              <p className="mt-0.5 text-xl font-bold text-gold">
                ₩{formatKrw(result.monthlyPayment)}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-secondary">Общая сумма процентов</p>
              <p className="mt-0.5 text-sm font-medium text-text-secondary">
                ₩{formatKrw(result.totalInterest)}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-secondary">Общая сумма выплат</p>
              <p className="mt-0.5 text-sm font-medium text-text-primary">
                ₩{formatKrw(result.totalPayment)}
              </p>
            </div>
          </div>

          {/* D. Principal vs Interest bar */}
          <div>
            <div className="rounded-full overflow-hidden h-4 bg-bg-elevated flex">
              <div
                className="bg-gold transition-all duration-300"
                style={{ width: `${principalPercent}%` }}
              />
            </div>
            <div className="mt-1.5 flex justify-between text-xs text-text-secondary">
              <span>Основной долг: {principalPercent}%</span>
              <span>Проценты: {interestPercent}%</span>
            </div>
          </div>
        </div>
      ) : (
        carPrice && (
          <div className="rounded-xl border border-border bg-bg-surface p-5 text-center text-sm text-text-secondary">
            Введите корректные данные для расчёта
          </div>
        )
      )}

      {/* E. Amortization schedule */}
      {result && (
        <div>
          <button
            type="button"
            onClick={() => setShowSchedule(!showSchedule)}
            className="flex items-center gap-2 text-sm font-medium text-text-secondary transition-colors hover:text-text-primary"
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
              className={cn(
                "transition-transform",
                showSchedule && "rotate-90"
              )}
            >
              <path d="M9 18l6-6-6-6" />
            </svg>
            {showSchedule
              ? "Скрыть график платежей"
              : `Показать график платежей (${result.schedule.length} мес.)`}
          </button>

          {showSchedule && (
            <div className="mt-3 overflow-x-auto rounded-xl border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-bg-surface">
                    <th className="px-3 py-2.5 text-left text-[11px] font-medium uppercase tracking-wider text-text-secondary">
                      №
                    </th>
                    <th className="px-3 py-2.5 text-right text-[11px] font-medium uppercase tracking-wider text-text-secondary">
                      Основной долг
                    </th>
                    <th className="px-3 py-2.5 text-right text-[11px] font-medium uppercase tracking-wider text-text-secondary">
                      Проценты
                    </th>
                    <th className="px-3 py-2.5 text-right text-[11px] font-medium uppercase tracking-wider text-text-secondary">
                      Платёж
                    </th>
                    <th className="px-3 py-2.5 text-right text-[11px] font-medium uppercase tracking-wider text-text-secondary">
                      Остаток
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {result.schedule.map((row) => (
                    <tr
                      key={row.month}
                      className="border-b border-border/50 even:bg-bg-elevated/30"
                    >
                      <td className="px-3 py-2 text-text-secondary">
                        {row.month}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums text-text-primary">
                        ₩{formatKrw(row.principalPaid)}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums text-text-secondary">
                        ₩{formatKrw(row.interestPaid)}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums font-medium text-text-primary">
                        ₩{formatKrw(row.payment)}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums text-text-secondary">
                        ₩{formatKrw(row.remainingBalance)}
                      </td>
                    </tr>
                  ))}
                  {/* Summary row */}
                  <tr className="border-t-2 border-gold/30 font-semibold">
                    <td className="px-3 py-2.5 text-text-secondary">Итого</td>
                    <td className="px-3 py-2.5 text-right tabular-nums text-text-primary">
                      ₩{formatKrw(result.loanAmount)}
                    </td>
                    <td className="px-3 py-2.5 text-right tabular-nums text-text-secondary">
                      ₩{formatKrw(result.totalInterest)}
                    </td>
                    <td className="px-3 py-2.5 text-right tabular-nums text-text-primary">
                      ₩{formatKrw(result.totalPayment)}
                    </td>
                    <td className="px-3 py-2.5 text-right tabular-nums text-text-secondary">
                      ₩0
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
