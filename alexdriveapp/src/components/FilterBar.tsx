"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import Image from "next/image";
import type { FilterData, CarListingParams, CarModel, CarSeries } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChevronsUpDown, ChevronDown, RotateCcw, Search } from "lucide-react";
import { ModelSelectorModal } from "@/components/ModelSelectorModal";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

interface FilterBarProps {
  filters: FilterData | null;
  appliedParams: CarListingParams;
  onApplyFilters: (params: CarListingParams) => void;
  loading?: boolean;
}

interface SelectOption {
  value: string;
  label: string;
  logo?: string;
}

const ALL_VALUE = "__all__";

const FILTER_KEYS = [
  "bm_no", "bo_no", "bs_no", "bd_no",
  "yearFrom", "yearTo", "mileageFrom", "mileageTo", "priceFrom", "priceTo",
  "fuel", "transmission", "color", "keyword",
  "extFlag1", "extFlag2", "extFlag3", "extFlag4", "extFlag5",
] as const;

const SORT_OPTIONS = [
  { value: "date", label: "По дате" },
  { value: "price", label: "По цене" },
  { value: "mileage", label: "По пробегу" },
  { value: "year", label: "По году" },
];

const DEFAULT_PARAMS: CarListingParams = {
  page: 1,
  page_size: 20,
  sort: "date",
  order: "desc",
};

export function FilterBar({
  filters,
  appliedParams,
  onApplyFilters,
  loading,
}: FilterBarProps) {
  const [expanded, setExpanded] = useState(false);

  // Draft state — local, uncommitted filter values
  const [draftParams, setDraftParams] = useState<CarListingParams>(appliedParams);

  // Cascading state
  const [selectedMaker, setSelectedMaker] = useState(appliedParams.bm_no || "");
  const [selectedModel, setSelectedModel] = useState(appliedParams.bo_no || "");
  const [selectedSeries, setSelectedSeries] = useState(appliedParams.bs_no || "");
  const [selectedTrim, setSelectedTrim] = useState(appliedParams.bd_no || "");

  // Async cascading data
  const [models, setModels] = useState<CarModel[]>([]);
  const [series, setSeries] = useState<CarSeries[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [seriesLoading, setSeriesLoading] = useState(false);

  // Sync draft from parent when appliedParams change (e.g. pagination)
  useEffect(() => {
    setDraftParams(appliedParams);
    setSelectedMaker(appliedParams.bm_no || "");
    setSelectedModel(appliedParams.bo_no || "");
    setSelectedSeries(appliedParams.bs_no || "");
    setSelectedTrim(appliedParams.bd_no || "");
  }, [appliedParams]);

  // Fetch models when maker changes
  useEffect(() => {
    if (!selectedMaker) {
      setModels([]);
      return;
    }
    let cancelled = false;
    setModelsLoading(true);
    fetch(`${BACKEND_URL}/api/filters/models?bm_no=${selectedMaker}`)
      .then((r) => r.json())
      .then((data) => {
        if (!cancelled) setModels(data || []);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setModelsLoading(false);
      });
    return () => { cancelled = true; };
  }, [selectedMaker]);

  // Fetch series when model changes
  useEffect(() => {
    if (!selectedModel) {
      setSeries([]);
      return;
    }
    let cancelled = false;
    setSeriesLoading(true);
    fetch(`${BACKEND_URL}/api/filters/series?bo_no=${selectedModel}`)
      .then((r) => r.json())
      .then((data) => {
        if (!cancelled) setSeries(data || []);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setSeriesLoading(false);
      });
    return () => { cancelled = true; };
  }, [selectedModel]);

  // Dirty detection
  const hasUnappliedChanges = useMemo(() => {
    return FILTER_KEYS.some(
      (k) => (draftParams[k] || "") !== (appliedParams[k] || "")
    );
  }, [draftParams, appliedParams]);

  const updateDraft = useCallback(
    (key: keyof CarListingParams, value: string) => {
      setDraftParams((prev) => ({ ...prev, [key]: value || undefined, page: 1 }));
    },
    []
  );

  const handleMakerChange = (value: string) => {
    setSelectedMaker(value);
    setSelectedModel("");
    setSelectedSeries("");
    setSelectedTrim("");
    setDraftParams((prev) => ({
      ...prev,
      bm_no: value || undefined,
      bo_no: undefined,
      bs_no: undefined,
      bd_no: undefined,
      page: 1,
    }));
  };

  const handleModelChange = (value: string) => {
    setSelectedModel(value);
    setSelectedSeries("");
    setSelectedTrim("");
    setDraftParams((prev) => ({
      ...prev,
      bo_no: value || undefined,
      bs_no: undefined,
      bd_no: undefined,
      page: 1,
    }));
  };

  const handleSeriesChange = (value: string) => {
    setSelectedSeries(value);
    setSelectedTrim("");
    setDraftParams((prev) => ({
      ...prev,
      bs_no: value || undefined,
      bd_no: undefined,
      page: 1,
    }));
  };

  const handleTrimChange = (value: string) => {
    setSelectedTrim(value);
    setDraftParams((prev) => ({
      ...prev,
      bd_no: value || undefined,
      page: 1,
    }));
  };

  // Sort — instant-apply
  const handleSortChange = (value: string) => {
    const merged = { ...draftParams, sort: value || undefined, page: 1 };
    setDraftParams(merged);
    onApplyFilters(merged);
  };

  const handleSortDirectionChange = (value: string) => {
    const merged = { ...draftParams, order: value, page: 1 };
    setDraftParams(merged);
    onApplyFilters(merged);
  };

  // Maker options with logos
  const makerOptions = useMemo(
    () =>
      (filters?.makers || []).map((m) => ({
        value: String(m.bm_no),
        label: m.bm_name,
        logo: m.bm_logoImage,
      })),
    [filters?.makers]
  );

  // Series options
  const seriesOptions = useMemo(
    () =>
      series.map((s) => ({
        value: String(s.bs_no),
        label: s.bs_name,
      })),
    [series]
  );

  // Trim options (from selected series)
  const trimOptions = useMemo(() => {
    const selectedSeriesObj = series.find((s) => String(s.bs_no) === selectedSeries);
    if (!selectedSeriesObj?.bd) return [];
    return selectedSeriesObj.bd.map((t) => ({
      value: String(t.bd_no),
      label: t.bd_name,
    }));
  }, [series, selectedSeries]);

  const handleReset = () => {
    setSelectedMaker("");
    setSelectedModel("");
    setSelectedSeries("");
    setSelectedTrim("");
    setModels([]);
    setSeries([]);
    const resetParams: CarListingParams = { ...DEFAULT_PARAMS };
    setDraftParams(resetParams);
    onApplyFilters(resetParams);
  };

  const handleApply = () => {
    onApplyFilters({ ...draftParams, page: 1 });
  };

  return (
    <div className="rounded-xl border border-border bg-bg-surface">
      {/* Main filters row */}
      <div className="p-4">
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          <FilterField label="Марка">
            <FilterCombobox
              options={makerOptions}
              value={selectedMaker}
              onChange={handleMakerChange}
              placeholder="Все марки"
              searchPlaceholder="Найти марку..."
            />
          </FilterField>

          <FilterField label="Модель">
            <ModelSelectorModal
              models={models}
              selectedModel={selectedModel}
              onSelect={handleModelChange}
              disabled={!selectedMaker}
              isLoading={modelsLoading}
            />
          </FilterField>

          <FilterField label="Серия">
            <FilterDropdown
              options={seriesOptions}
              value={selectedSeries}
              onChange={handleSeriesChange}
              placeholder="Все"
              disabled={!selectedModel}
              isLoading={seriesLoading}
            />
          </FilterField>

          <FilterField label="Комплектация">
            <FilterDropdown
              options={trimOptions}
              value={selectedTrim}
              onChange={handleTrimChange}
              placeholder="Все"
              disabled={!selectedSeries}
            />
          </FilterField>

          <FilterField label="Поиск по номеру">
            <Input
              type="text"
              value={draftParams.keyword || ""}
              onChange={(e) => updateDraft("keyword", e.target.value)}
              placeholder="Гос. номер или ключевое слово"
              className="h-9 bg-bg-elevated"
            />
          </FilterField>

          <FilterField label="Сортировка">
            <FilterDropdown
              options={SORT_OPTIONS}
              value={draftParams.sort || "date"}
              onChange={handleSortChange}
              placeholder="По дате"
              allowClear={false}
            />
          </FilterField>
        </div>

        {/* Toggle expand, Apply & Reset */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="text-text-secondary hover:text-text-primary"
          >
            <ChevronDown
              className={cn(
                "size-3.5 transition-transform",
                expanded && "rotate-180"
              )}
            />
            {expanded ? "Скрыть фильтры" : "Все фильтры"}
          </Button>

          <div className="ml-auto flex items-center gap-2">
            <Button
              size="sm"
              onClick={handleApply}
              disabled={loading}
              className={cn(
                "transition-all",
                hasUnappliedChanges
                  ? "bg-gold text-bg-base hover:bg-gold/90 shadow-[0_0_12px_rgba(212,175,55,0.3)]"
                  : "bg-bg-elevated text-text-secondary hover:bg-bg-elevated/80"
              )}
            >
              <Search className="size-3.5" />
              Найти
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="text-text-secondary hover:text-gold"
            >
              <RotateCcw className="size-3.5" />
              Сбросить
            </Button>
          </div>
        </div>
      </div>

      {/* Expanded filters */}
      {expanded && (
        <div className="border-t border-border p-4 space-y-4">
          {/* Fuel radio group */}
          <FilterField label="Топливо">
            <FilterPillGroup
              options={filters?.fuels || []}
              value={draftParams.fuel || ""}
              onChange={(v) => updateDraft("fuel", v)}
            />
          </FilterField>

          {/* Transmission radio group */}
          <FilterField label="КПП">
            <FilterPillGroup
              options={filters?.transmissions || []}
              value={draftParams.transmission || ""}
              onChange={(v) => updateDraft("transmission", v)}
            />
          </FilterField>

          {/* Color grid */}
          {filters?.colors && filters.colors.length > 0 && (
            <FilterField label="Цвет">
              <FilterColorGrid
                colors={filters.colors}
                value={draftParams.color || ""}
                onChange={(v) => updateDraft("color", v)}
              />
            </FilterField>
          )}

          {/* Range filters */}
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            <RangeInput
              label="Год выпуска"
              fromValue={draftParams.yearFrom || ""}
              toValue={draftParams.yearTo || ""}
              onFromChange={(v) => updateDraft("yearFrom", v)}
              onToChange={(v) => updateDraft("yearTo", v)}
              placeholderFrom="От (2015)"
              placeholderTo="До (2024)"
            />
            <RangeInput
              label="Пробег (км)"
              fromValue={draftParams.mileageFrom || ""}
              toValue={draftParams.mileageTo || ""}
              onFromChange={(v) => updateDraft("mileageFrom", v)}
              onToChange={(v) => updateDraft("mileageTo", v)}
              placeholderFrom="От"
              placeholderTo="До"
            />
            <RangeInput
              label="Цена (만원)"
              fromValue={draftParams.priceFrom || ""}
              toValue={draftParams.priceTo || ""}
              onFromChange={(v) => updateDraft("priceFrom", v)}
              onToChange={(v) => updateDraft("priceTo", v)}
              placeholderFrom="От (напр. 3000)"
              placeholderTo="До (напр. 5000)"
            />
          </div>

          {/* Checkbox options */}
          <FilterField label="Опции">
            <div className="flex flex-wrap gap-2">
              <FilterCheckbox
                label="Навигация"
                checked={draftParams.extFlag1 === "1"}
                onChange={(c) => updateDraft("extFlag1", c ? "1" : "")}
              />
              <FilterCheckbox
                label="Люк"
                checked={draftParams.extFlag2 === "1"}
                onChange={(c) => updateDraft("extFlag2", c ? "1" : "")}
              />
              <FilterCheckbox
                label="Умный ключ"
                checked={draftParams.extFlag3 === "1"}
                onChange={(c) => updateDraft("extFlag3", c ? "1" : "")}
              />
              <FilterCheckbox
                label="Без ДТП"
                checked={draftParams.extFlag4 === "1"}
                onChange={(c) => updateDraft("extFlag4", c ? "1" : "")}
              />
              <FilterCheckbox
                label="Тех. осмотр"
                checked={draftParams.extFlag5 === "1"}
                onChange={(c) => updateDraft("extFlag5", c ? "1" : "")}
              />
            </div>
          </FilterField>

          {/* Sort direction — instant-apply */}
          <div className="flex flex-wrap gap-3">
            <div className="ml-auto flex items-center gap-0.5 rounded-lg border border-border">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleSortDirectionChange("asc")}
                className={cn(
                  "rounded-r-none border-0",
                  draftParams.order === "asc"
                    ? "bg-gold/10 text-gold"
                    : "text-text-secondary hover:text-text-primary"
                )}
              >
                По возр.
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleSortDirectionChange("desc")}
                className={cn(
                  "rounded-l-none border-0",
                  draftParams.order !== "asc"
                    ? "bg-gold/10 text-gold"
                    : "text-text-secondary hover:text-text-primary"
                )}
              >
                По убыв.
              </Button>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="border-t border-border px-4 py-2">
          <div className="h-0.5 animate-pulse rounded-full bg-gold/30" />
        </div>
      )}
    </div>
  );
}

// --- Sub-components ---

function FilterField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[11px] font-medium uppercase tracking-wider text-text-secondary">
        {label}
      </span>
      {children}
    </div>
  );
}

function FilterCombobox({
  options,
  value,
  onChange,
  placeholder,
  searchPlaceholder,
  disabled,
  isLoading,
}: {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  searchPlaceholder: string;
  disabled?: boolean;
  isLoading?: boolean;
}) {
  const [open, setOpen] = useState(false);

  const selectedLabel = useMemo(
    () => options.find((o) => o.value === value)?.label,
    [options, value]
  );

  const selectedLogo = useMemo(
    () => options.find((o) => o.value === value)?.logo,
    [options, value]
  );

  return (
    <Popover
      open={open && !disabled}
      onOpenChange={(v) => !disabled && setOpen(v)}
    >
      <PopoverTrigger
        className={cn(
          "flex h-9 w-full items-center justify-between rounded-lg border border-input bg-bg-elevated px-3 text-sm transition-colors",
          disabled
            ? "opacity-40 cursor-not-allowed"
            : "hover:border-ring/50",
          value ? "text-text-primary" : "text-muted-foreground"
        )}
      >
        <span className="truncate flex items-center gap-2">
          {selectedLogo && (
            <Image src={selectedLogo} alt="" width={20} height={20} className="rounded-sm" unoptimized />
          )}
          {isLoading ? "Загрузка..." : selectedLabel || placeholder}
        </span>
        <ChevronsUpDown className="ml-2 size-3.5 shrink-0 text-muted-foreground" />
      </PopoverTrigger>
      <PopoverContent className="w-(--anchor-width) p-0" align="start">
        <Command>
          <CommandInput placeholder={searchPlaceholder} />
          <CommandList>
            <CommandEmpty>Не найдено</CommandEmpty>
            <CommandGroup>
              <CommandItem
                value={ALL_VALUE}
                onSelect={() => {
                  onChange("");
                  setOpen(false);
                }}
                data-checked={!value}
              >
                {placeholder}
              </CommandItem>
              {options.map((opt) => (
                <CommandItem
                  key={opt.value}
                  value={opt.label}
                  onSelect={() => {
                    onChange(opt.value);
                    setOpen(false);
                  }}
                  data-checked={value === opt.value}
                >
                  <span className="flex items-center gap-2">
                    {opt.logo && (
                      <Image src={opt.logo} alt="" width={20} height={20} className="rounded-sm" unoptimized />
                    )}
                    {opt.label}
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

function FilterDropdown({
  options,
  value,
  onChange,
  placeholder,
  disabled,
  allowClear = true,
  isLoading,
}: {
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  disabled?: boolean;
  allowClear?: boolean;
  isLoading?: boolean;
}) {
  const items = useMemo(() => {
    const all = options.map((o) => ({ value: o.value, label: o.label }));
    if (allowClear) {
      all.unshift({ value: ALL_VALUE, label: placeholder });
    }
    return all;
  }, [options, allowClear, placeholder]);

  const selectValue = value || (allowClear ? ALL_VALUE : undefined);

  return (
    <Select
      value={selectValue}
      onValueChange={(v) =>
        onChange(!v || v === ALL_VALUE ? "" : v)
      }
      disabled={disabled || isLoading}
      items={items}
    >
      <SelectTrigger
        className={cn(
          "h-9 w-full border-input bg-bg-elevated",
          (disabled || isLoading) && "opacity-40"
        )}
      >
        <SelectValue placeholder={isLoading ? "Загрузка..." : placeholder} />
      </SelectTrigger>
      <SelectContent>
        {allowClear && (
          <SelectItem value={ALL_VALUE}>{placeholder}</SelectItem>
        )}
        {options.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function FilterPillGroup({
  options,
  value,
  onChange,
}: {
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(value === opt.value ? "" : opt.value)}
          className={cn(
            "rounded-full px-3 py-1.5 text-xs font-medium transition-colors border",
            value === opt.value
              ? "bg-gold/15 text-gold border-gold/30"
              : "bg-bg-elevated text-text-secondary border-border hover:text-text-primary hover:border-border"
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function FilterColorGrid({
  colors,
  value,
  onChange,
}: {
  colors: { bc_no: string; bc_name: string; bc_rgb1: string; bc_rgb2: string }[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {colors.map((color) => {
        const isSelected = value === String(color.bc_no);
        const isTwoTone = color.bc_rgb1 !== color.bc_rgb2;
        return (
          <button
            key={color.bc_no}
            onClick={() => onChange(isSelected ? "" : String(color.bc_no))}
            className={cn(
              "group relative flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-all",
              isSelected
                ? "border-gold bg-gold/10 text-gold"
                : "border-border bg-bg-elevated text-text-secondary hover:border-border hover:text-text-primary"
            )}
            title={color.bc_name}
          >
            <span
              className="inline-block size-3.5 rounded-full border border-white/20 shrink-0"
              style={{
                background: isTwoTone
                  ? `linear-gradient(135deg, ${color.bc_rgb1} 50%, ${color.bc_rgb2} 50%)`
                  : color.bc_rgb1,
              }}
            />
            <span className="hidden sm:inline">{color.bc_name}</span>
          </button>
        );
      })}
    </div>
  );
}

function FilterCheckbox({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={cn(
        "rounded-full px-3 py-1.5 text-xs font-medium transition-colors border",
        checked
          ? "bg-gold/15 text-gold border-gold/30"
          : "bg-bg-elevated text-text-secondary border-border hover:text-text-primary"
      )}
    >
      {checked && "✓ "}
      {label}
    </button>
  );
}

function RangeInput({
  label,
  fromValue,
  toValue,
  onFromChange,
  onToChange,
  placeholderFrom,
  placeholderTo,
}: {
  label: string;
  fromValue: string;
  toValue: string;
  onFromChange: (value: string) => void;
  onToChange: (value: string) => void;
  placeholderFrom: string;
  placeholderTo: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[11px] font-medium uppercase tracking-wider text-text-secondary">
        {label}
      </span>
      <div className="flex items-center gap-2">
        <Input
          type="text"
          value={fromValue}
          onChange={(e) => onFromChange(e.target.value)}
          placeholder={placeholderFrom}
          className="h-9 bg-bg-elevated"
        />
        <span className="text-xs text-text-secondary">—</span>
        <Input
          type="text"
          value={toValue}
          onChange={(e) => onToChange(e.target.value)}
          placeholder={placeholderTo}
          className="h-9 bg-bg-elevated"
        />
      </div>
    </div>
  );
}
