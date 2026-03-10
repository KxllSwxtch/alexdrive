"use client";

import { Accordion } from "@base-ui/react/accordion";
import { ChevronDown } from "lucide-react";
import type { InspectionReport as InspectionReportType } from "@/lib/types";
import { CarBodyDiagram } from "./CarBodyDiagram";

interface InspectionReportProps {
  inspection: InspectionReportType;
}

// Field name translations
const CONDITION_LABELS: Record<string, Record<string, string>> = {
  engine: {
    _group: "Двигатель",
    oilLeakRockerArm: "Утечка масла — клапанная крышка",
    oilLeakCylinderHead: "Утечка масла — прокладка ГБЦ",
    coolantLeak: "Утечка охлаждающей жидкости",
    idleCondition: "Холостой ход",
    exhaustSystem: "Выхлопная система",
  },
  transmission: {
    _group: "Коробка передач",
    oilLeak: "Утечка масла",
    oilLevelCondition: "Уровень/состояние масла",
    idleGearShift: "АКПП — переключение на холостых",
    drivePowerShift: "АКПП — переключение на ходу",
  },
  power: {
    _group: "Силовая передача",
    clutchAssembly: "Сцепление",
  },
  electrical: {
    _group: "Электрооборудование",
    generatorOutput: "Генератор",
    starterMotor: "Стартер",
    wiperMotor: "Стеклоочистители",
    lights: "Освещение",
    windowOperation: "Стеклоподъёмники",
    interiorElectrics: "Электрика салона",
    acSystem: "Кондиционер",
    heater: "Отопитель",
    defroster: "Обогрев стёкол",
  },
  fuel: {
    _group: "Топливная система",
    fuelLeak: "Утечка топлива",
  },
  tires: {
    _group: "Шины",
    tireFrontLeft: "Передняя левая",
    tireFrontRight: "Передняя правая",
    tireRearLeft: "Задняя левая",
    tireRearRight: "Задняя правая",
  },
};

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  good: { label: "Норма", color: "text-green-400" },
  bad: { label: "Неисправно", color: "text-red-400" },
  unable: { label: "Не проверено", color: "text-text-secondary" },
};

function StatusDot({ status }: { status: string | null | undefined }) {
  const info = status ? STATUS_LABELS[status] : null;
  if (!info) return <span className="text-xs text-text-secondary">—</span>;
  return (
    <span className={`text-xs font-medium ${info.color}`}>
      {info.label}
    </span>
  );
}

function Badge({ ok, labelOk, labelBad }: { ok: boolean; labelOk: string; labelBad: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium ${
        ok
          ? "border-green-500/30 bg-green-500/10 text-green-400"
          : "border-red-500/30 bg-red-500/10 text-red-400"
      }`}
    >
      <span className={`inline-block size-1.5 rounded-full ${ok ? "bg-green-400" : "bg-red-400"}`} />
      {ok ? labelOk : labelBad}
    </span>
  );
}

export function InspectionReport({ inspection }: InspectionReportProps) {
  if (!inspection.available) return null;

  const conditionGroups = Object.entries(inspection.detailedCondition).filter(
    ([key]) => CONDITION_LABELS[key]
  );

  const hasBodyDamage =
    Object.keys(inspection.bodyDamage.exterior).length > 0 ||
    Object.keys(inspection.bodyDamage.structural).length > 0;

  return (
    <div className="rounded-xl border border-border bg-bg-surface p-5">
      {/* Header */}
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
          Отчёт о техосмотре
        </h2>
        {inspection.documentNumber && (
          <span className="text-xs text-text-secondary">
            № {inspection.documentNumber}
            {inspection.inspectionDate && ` от ${inspection.inspectionDate}`}
          </span>
        )}
      </div>

      {/* Quick status badges */}
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge
          ok={!inspection.specialHistory.flood}
          labelOk="Нет затопления"
          labelBad="Затопление"
        />
        <Badge
          ok={!inspection.specialHistory.fire}
          labelOk="Нет пожара"
          labelBad="Пожар"
        />
        <Badge
          ok={!inspection.accidentHistory.exists}
          labelOk="Нет аварий"
          labelBad="Есть аварии"
        />
        <Badge
          ok={inspection.mileage.gaugeStatus === "good"}
          labelOk="Одометр исправен"
          labelBad="Одометр неисправен"
        />
      </div>

      {/* Usage history grid */}
      <div className="mt-5 grid gap-4 grid-cols-2 sm:grid-cols-3">
        {inspection.mileage.value && (
          <div>
            <p className="text-xs text-text-secondary">Пробег</p>
            <p className="mt-0.5 text-sm font-medium text-text-primary">
              {inspection.mileage.value} км
            </p>
          </div>
        )}
        <div>
          <p className="text-xs text-text-secondary">VIN</p>
          <p className="mt-0.5 text-sm font-medium text-text-primary">
            {inspection.vinStatus === "good" ? "В порядке" : inspection.vinStatus || "—"}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">Выхлоп</p>
          <p className="mt-0.5 text-sm font-medium text-text-primary">
            {inspection.emissions.status === "pass" ? "В норме" : inspection.emissions.status === "fail" ? "Не пройден" : "—"}
            {inspection.emissions.co && ` (CO: ${inspection.emissions.co})`}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">Тюнинг</p>
          <p className="mt-0.5 text-sm font-medium text-text-primary">
            {inspection.tuning.exists ? "Есть" : "Нет"}
          </p>
        </div>
        <div>
          <p className="text-xs text-text-secondary">Отзывные кампании</p>
          <p className="mt-0.5 text-sm font-medium text-text-primary">
            {inspection.recallStatus.applicable ? "Есть" : "Нет"}
          </p>
        </div>
        {inspection.warranty.company && (
          <div>
            <p className="text-xs text-text-secondary">Гарантия</p>
            <p className="mt-0.5 text-sm font-medium text-text-primary">
              {inspection.warranty.company}
              {inspection.warranty.premium > 0 && (
                <span className="text-text-secondary">
                  {" "}({inspection.warranty.premium.toLocaleString()}₩)
                </span>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Body diagram */}
      <div className="mt-6">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
          {hasBodyDamage ? "Схема повреждений кузова" : "Состояние кузова"}
        </h3>
        <CarBodyDiagram
          exterior={inspection.bodyDamage.exterior}
          structural={inspection.bodyDamage.structural}
        />
      </div>

      {/* Detailed mechanical condition */}
      {conditionGroups.length > 0 && (
        <div className="mt-6">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
            Техническое состояние
          </h3>
          <Accordion.Root multiple keepMounted className="divide-y divide-border">
            {conditionGroups.map(([system, fields], i) => {
              const labels = CONDITION_LABELS[system];
              if (!labels) return null;
              const groupName = labels._group;
              const entries = Object.entries(fields).filter(
                ([k]) => k !== "_group" && labels[k]
              );
              if (entries.length === 0) return null;

              // Check if all items are "good"
              const allGood = entries.every(([, v]) => v === "good");

              return (
                <Accordion.Item key={system} value={i}>
                  <Accordion.Header>
                    <Accordion.Trigger className="group flex w-full cursor-pointer items-center justify-between py-3 text-xs font-semibold text-gold transition-colors hover:text-gold-light">
                      <span className="flex items-center gap-2">
                        {groupName}
                        {allGood && (
                          <span className="rounded-md bg-green-500/10 px-1.5 py-0.5 text-[10px] font-medium text-green-400">
                            OK
                          </span>
                        )}
                      </span>
                      <ChevronDown className="size-4 text-text-secondary transition-transform duration-200 group-data-[panel-open]:rotate-180" />
                    </Accordion.Trigger>
                  </Accordion.Header>
                  <Accordion.Panel data-accordion-panel>
                    <div className="space-y-2 pb-3">
                      {entries.map(([field, status]) => (
                        <div
                          key={field}
                          className="flex items-center justify-between rounded-lg bg-bg-elevated/50 px-3 py-2"
                        >
                          <span className="text-xs text-text-secondary">
                            {labels[field] || field}
                          </span>
                          <StatusDot status={status} />
                        </div>
                      ))}
                    </div>
                  </Accordion.Panel>
                </Accordion.Item>
              );
            })}
          </Accordion.Root>
        </div>
      )}

      {/* Inspection photos */}
      {inspection.photos.length > 0 && (
        <div className="mt-6">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
            Фотографии осмотра
          </h3>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {inspection.photos.map((url, i) => (
              <a
                key={i}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-shrink-0"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={url}
                  alt={`Фото осмотра ${i + 1}`}
                  className="h-20 w-28 rounded-lg border border-border object-cover transition-opacity hover:opacity-80"
                  loading="lazy"
                />
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Original report link */}
      {inspection.originalReportUrl && (
        <div className="mt-5 border-t border-border pt-4">
          <a
            href={inspection.originalReportUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-gold transition-colors hover:text-gold-light"
          >
            Посмотреть оригинальный отчёт
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </a>
        </div>
      )}
    </div>
  );
}
