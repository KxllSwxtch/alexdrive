"use client";

import { useState } from "react";
import Image from "next/image";

// ── Types ────────────────────────────────────────────────────

type Severity = "good" | "warn" | "bad";
type ValueMap = Record<string, { label: string; severity: Severity }>;

interface FieldDef {
  key: string;
  label: string;
  values: ValueMap;
}

interface SectionDef {
  title: string;
  fields: { key: string; label: string; type: keyof typeof VALUE_TYPES }[];
}

// ── Pill severity classes ────────────────────────────────────

const SEVERITY_CLASSES: Record<Severity | "inactive", string> = {
  good: "bg-green-950/60 text-green-400 border border-green-800",
  warn: "bg-amber-950/60 text-amber-400 border border-amber-800",
  bad: "bg-red-950/60 text-red-400 border border-red-800",
  inactive: "text-text-secondary opacity-30 border border-border",
};

// ── Section A: Overview fields ───────────────────────────────

const OVERVIEW_FIELDS: { key: string; label: string }[] = [
  { key: "vin", label: "VIN" },
  { key: "mileage", label: "Пробег" },
  { key: "inspection_date", label: "Дата осмотра" },
  { key: "engine_type", label: "Тип двигателя" },
  { key: "warranty", label: "Гарантия" },
  { key: "inspection_validity", label: "Действителен до" },
  { key: "emissions", label: "Выбросы" },
  { key: "insurance_premium", label: "Страховая премия" },
];

// ── Section B: Basic Condition ───────────────────────────────

const BASIC_CONDITION_FIELDS: FieldDef[] = [
  {
    key: "11",
    label: "Состояние одометра",
    values: {
      "1": { label: "Норма", severity: "good" },
      "2": { label: "Неисправен", severity: "bad" },
    },
  },
  {
    key: "12",
    label: "Уровень пробега",
    values: {
      "1": { label: "Большой", severity: "warn" },
      "2": { label: "Средний", severity: "good" },
      "3": { label: "Малый", severity: "good" },
    },
  },
  {
    key: "2",
    label: "Маркировка VIN",
    values: {
      "1": { label: "Норма", severity: "good" },
      "2": { label: "Коррозия", severity: "bad" },
      "3": { label: "Повреждена", severity: "bad" },
      "4": { label: "Не совпадает", severity: "bad" },
      "5": { label: "Изменена", severity: "bad" },
      "6": { label: "Стёрта", severity: "bad" },
    },
  },
  {
    key: "3",
    label: "Тюнинг",
    values: {
      "1": { label: "Нет", severity: "good" },
      "2": { label: "Есть", severity: "warn" },
    },
  },
  {
    key: "4",
    label: "Особая история",
    values: {
      "1": { label: "Нет", severity: "good" },
      "2": { label: "Есть", severity: "bad" },
    },
  },
  {
    key: "5",
    label: "Смена назначения",
    values: {
      "1": { label: "Нет", severity: "good" },
      "2": { label: "Изменено", severity: "warn" },
    },
  },
  {
    key: "81",
    label: "Отзывная кампания",
    values: {
      "1": { label: "Подлежит", severity: "warn" },
      "2": { label: "Не подлежит", severity: "good" },
    },
  },
];

// ── Section C: Detailed Condition value types ────────────────

const VALUE_TYPES = {
  binary: {
    "1": { label: "Норма", severity: "good" as Severity },
    "2": { label: "Неисправно", severity: "bad" as Severity },
  },
  presence: {
    "1": { label: "Нет", severity: "good" as Severity },
    "2": { label: "Есть", severity: "bad" as Severity },
  },
  oilLeak: {
    "1": { label: "Нет", severity: "good" as Severity },
    "2": { label: "Незначительная", severity: "warn" as Severity },
    "3": { label: "Течь", severity: "bad" as Severity },
  },
  coolantLeak: {
    "1": { label: "Нет", severity: "good" as Severity },
    "2": { label: "Незначительная", severity: "warn" as Severity },
    "3": { label: "Течь", severity: "bad" as Severity },
  },
  oilLevel: {
    "1": { label: "Норма", severity: "good" as Severity },
    "2": { label: "Недостаточно", severity: "warn" as Severity },
    "3": { label: "Избыток", severity: "warn" as Severity },
  },
  coolantLevel: {
    "1": { label: "Норма", severity: "good" as Severity },
    "2": { label: "Недостаточно", severity: "warn" as Severity },
  },
} as const;

const DETAILED_SECTIONS: SectionDef[] = [
  {
    title: "Самодиагностика",
    fields: [
      { key: "11", label: "Двигатель", type: "binary" },
      { key: "12", label: "КПП", type: "binary" },
    ],
  },
  {
    title: "Двигатель",
    fields: [
      { key: "21", label: "Работа на холостом ходу", type: "binary" },
      { key: "221", label: "Масло: крышка цилиндра", type: "oilLeak" },
      { key: "222", label: "Масло: головка блока", type: "oilLeak" },
      { key: "223", label: "Масло: блок/поддон", type: "oilLeak" },
      { key: "23", label: "Уровень масла", type: "oilLevel" },
      { key: "231", label: "Антифриз: головка/прокладка", type: "coolantLeak" },
      { key: "232", label: "Антифриз: помпа", type: "coolantLeak" },
      { key: "233", label: "Антифриз: радиатор", type: "coolantLeak" },
      { key: "234", label: "Уровень антифриза", type: "coolantLevel" },
      { key: "24", label: "Common Rail дизель", type: "binary" },
    ],
  },
  {
    title: "КПП (автомат)",
    fields: [
      { key: "311", label: "Течь масла", type: "oilLeak" },
      { key: "312", label: "Уровень масла", type: "oilLevel" },
      { key: "313", label: "Работа на холостом ходу", type: "binary" },
    ],
  },
  {
    title: "КПП (механика)",
    fields: [
      { key: "321", label: "Течь масла", type: "oilLeak" },
      { key: "322", label: "Переключение передач", type: "binary" },
      { key: "323", label: "Уровень масла", type: "oilLevel" },
      { key: "324", label: "Работа на холостом ходу", type: "binary" },
    ],
  },
  {
    title: "Привод",
    fields: [
      { key: "41", label: "Сцепление", type: "binary" },
      { key: "42", label: "ШРУС", type: "binary" },
      { key: "43", label: "Кардан и подшипник", type: "binary" },
      { key: "44", label: "Дифференциал", type: "binary" },
    ],
  },
  {
    title: "Рулевое управление",
    fields: [
      { key: "51", label: "Масло ГУР", type: "oilLeak" },
      { key: "521", label: "Рулевой механизм MDPS", type: "binary" },
      { key: "522", label: "Насос ГУР", type: "binary" },
      { key: "523", label: "Рулевые наконечники", type: "binary" },
      { key: "524", label: "Рулевой шарнир", type: "binary" },
      { key: "525", label: "Шланг ГУР", type: "binary" },
    ],
  },
  {
    title: "Тормоза",
    fields: [
      { key: "61", label: "Масло гл. цилиндра", type: "oilLeak" },
      { key: "62", label: "Течь тормозной жидкости", type: "oilLeak" },
      { key: "63", label: "Вакуумный усилитель", type: "binary" },
    ],
  },
  {
    title: "Электрика",
    fields: [
      { key: "71", label: "Генератор", type: "binary" },
      { key: "72", label: "Стартер", type: "binary" },
      { key: "73", label: "Мотор дворников", type: "binary" },
      { key: "74", label: "Вентилятор салона", type: "binary" },
      { key: "75", label: "Вентилятор радиатора", type: "binary" },
      { key: "76", label: "Стеклоподъёмники", type: "binary" },
    ],
  },
  {
    title: "Высоковольтная система (EV/Hybrid)",
    fields: [
      { key: "91", label: "Изоляция зарядного порта", type: "binary" },
      { key: "92", label: "Изоляция тяговой батареи", type: "binary" },
      { key: "93", label: "Высоковольтная проводка", type: "binary" },
    ],
  },
  {
    title: "Топливная система",
    fields: [
      { key: "81", label: "Утечка топлива вкл. LPG", type: "presence" },
    ],
  },
];

// ── Pill component ───────────────────────────────────────────

function Pill({
  label,
  severity,
  active,
}: {
  label: string;
  severity: Severity;
  active: boolean;
}) {
  const cls = active ? SEVERITY_CLASSES[severity] : SEVERITY_CLASSES.inactive;
  return (
    <span className={`inline-flex rounded-md px-2.5 py-1 text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}

function PillRow({
  label,
  currentValue,
  valueMap,
}: {
  label: string;
  currentValue: string;
  valueMap: ValueMap;
}) {
  const isUnchecked = currentValue === "0";
  return (
    <div className="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between sm:gap-4 py-2.5 border-b border-border/40 last:border-b-0">
      <span className="text-xs text-text-secondary shrink-0">{label}</span>
      <div className="flex flex-wrap gap-1.5">
        {Object.entries(valueMap).map(([val, def]) => (
          <Pill
            key={val}
            label={def.label}
            severity={def.severity}
            active={!isUnchecked && String(currentValue) === val}
          />
        ))}
      </div>
    </div>
  );
}

// ── Section A: Overview + Accident History ───────────────────

function OverviewSection({ data }: { data: Record<string, unknown> }) {
  const hasAccident = data.has_accident;
  const hasSimpleRepair = data.has_simple_repair;
  const inspectorNotes = data.inspector_notes;
  const inspectorName = data.inspector_name;

  const formatValue = (key: string, value: unknown): string => {
    if (value == null || value === "") return "";
    if (key === "insurance_premium" && typeof value === "number") {
      return `₩${value.toLocaleString("en-US")}`;
    }
    return String(value);
  };

  const overviewRows = OVERVIEW_FIELDS.filter((f) => {
    const v = data[f.key];
    return v != null && v !== "";
  });

  if (overviewRows.length === 0 && hasAccident == null && hasSimpleRepair == null) return null;

  return (
    <div className="grid gap-5 md:grid-cols-2">
      {/* Left: Overview table */}
      {overviewRows.length > 0 && (
        <div>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
            Отчёт осмотра
          </h3>
          <div className="space-y-0">
            {overviewRows.map((field) => (
              <div
                key={field.key}
                className="flex justify-between gap-3 border-b border-border/40 py-2 last:border-b-0"
              >
                <span className="text-xs text-text-secondary">{field.label}</span>
                <span className="text-xs font-medium text-text-primary text-right">
                  {formatValue(field.key, data[field.key])}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Right: Accident history */}
      {(hasAccident != null || hasSimpleRepair != null) && (
        <div>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
            История ДТП
          </h3>
          <div className="flex flex-wrap gap-2">
            {hasAccident != null && (
              <Pill
                label={`ДТП: ${hasAccident === true || hasAccident === "true" || hasAccident === "Да" ? "Да" : "Нет"}`}
                severity={hasAccident === true || hasAccident === "true" || hasAccident === "Да" ? "bad" : "good"}
                active
              />
            )}
            {hasSimpleRepair != null && (
              <Pill
                label={`Простой ремонт: ${hasSimpleRepair === true || hasSimpleRepair === "true" || hasSimpleRepair === "Да" ? "Да" : "Нет"}`}
                severity={hasSimpleRepair === true || hasSimpleRepair === "true" || hasSimpleRepair === "Да" ? "warn" : "good"}
                active
              />
            )}
          </div>
          {inspectorNotes != null && inspectorNotes !== "" && (
            <p className="mt-3 text-xs text-text-secondary leading-relaxed">
              {String(inspectorNotes)}
            </p>
          )}
          {inspectorName != null && inspectorName !== "" && (
            <p className="mt-2 text-[11px] text-text-secondary/70">
              Инспектор: {String(inspectorName)}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ── Section B: Basic Condition ───────────────────────────────

function BasicConditionSection({ data }: { data: Record<string, unknown> }) {
  const rows = BASIC_CONDITION_FIELDS.filter((f) => data[f.key] != null);
  if (rows.length === 0) return null;

  return (
    <div>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-secondary">
        Общее состояние
      </h3>
      <div>
        {rows.map((field) => (
          <PillRow
            key={field.key}
            label={field.label}
            currentValue={String(data[field.key])}
            valueMap={field.values}
          />
        ))}
      </div>
    </div>
  );
}

// ── Section C: Detailed Condition ────────────────────────────

function DetailedConditionSection({ data }: { data: Record<string, unknown> }) {
  const activeSections = DETAILED_SECTIONS.filter((section) =>
    section.fields.some((f) => data[f.key] != null),
  );
  if (activeSections.length === 0) return null;

  return (
    <div>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
        Детальное состояние
      </h3>
      <div className="grid gap-5 md:grid-cols-2">
        {activeSections.map((section) => {
          const activeFields = section.fields.filter((f) => data[f.key] != null);
          return (
            <div key={section.title} className="rounded-lg border border-border/60 bg-bg-primary/40 p-3">
              <h4 className="mb-1.5 text-xs font-semibold text-gold">
                {section.title}
              </h4>
              {activeFields.map((field) => (
                <PillRow
                  key={field.key}
                  label={field.label}
                  currentValue={String(data[field.key])}
                  valueMap={VALUE_TYPES[field.type]}
                />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Section D: Inspection Photos ─────────────────────────────

function InspectionPhotos({
  photos,
  stampUrl,
}: {
  photos?: unknown[];
  stampUrl?: string;
}) {
  const [fullscreenSrc, setFullscreenSrc] = useState<string | null>(null);
  const validPhotos = (photos || []).filter(
    (p): p is string => typeof p === "string" && p.length > 0,
  );
  if (validPhotos.length === 0 && !stampUrl) return null;

  return (
    <>
      <div>
        {validPhotos.length > 0 && (
          <>
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Фото осмотра
            </h3>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {validPhotos.map((src, i) => (
                <button
                  key={i}
                  onClick={() => setFullscreenSrc(src)}
                  className="relative h-20 w-28 flex-shrink-0 cursor-zoom-in overflow-hidden rounded-lg border border-border transition-colors hover:border-gold"
                >
                  <Image
                    src={src}
                    alt={`Фото осмотра ${i + 1}`}
                    fill
                    sizes="112px"
                    className="object-cover"
                    loading="lazy"
                    unoptimized
                  />
                </button>
              ))}
            </div>
          </>
        )}

        {stampUrl && (
          <div className="mt-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Печать осмотра
            </h3>
            <button
              onClick={() => setFullscreenSrc(stampUrl)}
              className="relative h-24 w-24 cursor-zoom-in overflow-hidden rounded-lg border border-border transition-colors hover:border-gold"
            >
              <Image
                src={stampUrl}
                alt="Печать осмотра"
                fill
                sizes="96px"
                className="object-contain"
                loading="lazy"
                unoptimized
              />
            </button>
          </div>
        )}
      </div>

      {/* Fullscreen overlay */}
      {fullscreenSrc && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/95"
          onClick={() => setFullscreenSrc(null)}
        >
          <button
            onClick={() => setFullscreenSrc(null)}
            className="absolute top-4 right-4 z-10 flex h-10 w-10 items-center justify-center rounded-full text-white/70 transition-colors hover:text-white hover:bg-white/10"
            aria-label="Закрыть"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <div className="relative h-[80vh] w-[90vw]">
            <Image
              src={fullscreenSrc}
              alt="Фото осмотра"
              fill
              sizes="90vw"
              className="object-contain"
              loading="eager"
              unoptimized
            />
          </div>
        </div>
      )}
    </>
  );
}

// ── Main export ──────────────────────────────────────────────

interface InspectionReportProps {
  inspection: Record<string, unknown>;
}

export function InspectionReport({ inspection }: InspectionReportProps) {
  const basicCondition = inspection.basic_condition as Record<string, unknown> | undefined;
  const detailedCondition = inspection.detailed_condition as Record<string, unknown> | undefined;
  const photos = inspection.photos as unknown[] | undefined;
  const stampUrl = inspection.stamp_url as string | undefined;

  return (
    <div className="rounded-xl border border-border bg-bg-surface p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-text-secondary">
        Отчёт о проверке
      </h2>
      <div className="mt-4 space-y-6">
        <OverviewSection data={inspection} />
        {basicCondition && <BasicConditionSection data={basicCondition} />}
        {detailedCondition && <DetailedConditionSection data={detailedCondition} />}
        <InspectionPhotos photos={photos} stampUrl={stampUrl} />
      </div>
    </div>
  );
}
