"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
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

interface CreditCalculatorCompactProps {
  initialPrice: number;
}

export function CreditCalculatorCompact({
  initialPrice,
}: CreditCalculatorCompactProps) {
  const [expanded, setExpanded] = useState(false);
  const [carPrice, setCarPrice] = useState(String(initialPrice));
  const [editingPrice, setEditingPrice] = useState(false);
  const [termMonths, setTermMonths] = useState(36);
  const [annualRate, setAnnualRate] = useState("5.9");

  const priceNum = parseInt(carPrice, 10) || 0;

  const result = useMemo(() => {
    const rate = parseFloat(annualRate);
    if (!priceNum || isNaN(rate)) return null;
    return calculateCredit({
      carPrice: priceNum,
      termMonths,
      annualRate: rate,
    });
  }, [priceNum, termMonths, annualRate]);

  return (
    <div className="rounded-xl border border-border bg-bg-surface overflow-hidden">
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-4 text-left transition-colors hover:bg-bg-elevated/50"
      >
        <span className="text-sm font-semibold text-text-primary">
          Кредитный калькулятор
        </span>
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
            "text-text-secondary transition-transform",
            expanded && "rotate-180"
          )}
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-border p-4 space-y-4">
          {/* Loan amount display */}
          <div className="space-y-1.5">
            <Label className="text-xs">Сумма кредита</Label>
            {editingPrice ? (
              <InputGroup>
                <InputGroupAddon align="inline-start">₩</InputGroupAddon>
                <InputGroupInput
                  type="text"
                  inputMode="numeric"
                  value={carPrice ? formatKrw(parseInt(carPrice, 10) || 0) : ""}
                  onChange={(e) =>
                    setCarPrice(e.target.value.replace(/[^\d]/g, ""))
                  }
                  onBlur={() => setEditingPrice(false)}
                  autoFocus
                />
              </InputGroup>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-text-primary">
                  ₩{formatKrw(priceNum)}
                </span>
                <button
                  type="button"
                  onClick={() => setEditingPrice(true)}
                  className="text-text-secondary transition-colors hover:text-text-primary"
                  aria-label="Изменить цену"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                </button>
              </div>
            )}
          </div>

          {/* Inputs */}
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Срок кредита</Label>
              <Select
                value={termMonths}
                onValueChange={(val) => setTermMonths(val as number)}
              >
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
              <Label className="text-xs">Процентная ставка</Label>
              <InputGroup>
                <InputGroupInput
                  type="text"
                  inputMode="decimal"
                  placeholder="5.9"
                  value={annualRate}
                  onChange={(e) =>
                    setAnnualRate(e.target.value.replace(/[^\d.]/g, ""))
                  }
                />
                <InputGroupAddon align="inline-end">%</InputGroupAddon>
              </InputGroup>
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className="rounded-lg bg-bg-elevated/50 p-3 space-y-1">
              <div>
                <p className="text-xs text-text-secondary">
                  Ежемесячный платёж
                </p>
                <p className="text-lg font-bold text-gold">
                  ₩{formatKrw(result.monthlyPayment)}
                </p>
              </div>
              <p className="text-xs text-text-secondary">
                Переплата: ₩{formatKrw(result.totalInterest)}
              </p>
            </div>
          )}

          {/* Link to full calculator */}
          <Link
            href={`/calculator${priceNum ? `?price=${priceNum}` : ""}`}
            className="flex items-center gap-1 text-xs font-medium text-gold transition-colors hover:text-gold-light"
          >
            Подробный расчёт
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </Link>
        </div>
      )}
    </div>
  );
}
