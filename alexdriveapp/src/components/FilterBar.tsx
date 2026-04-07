"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import type { FilterData, CarListingParams } from "@/lib/types";
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
import { translateSmartly } from "@/lib/translations";

interface FilterBarProps {
  filters: FilterData | null;
  appliedParams: CarListingParams;
  onApplyFilters: (params: CarListingParams) => void;
  loading?: boolean;
}

interface SelectOption {
  value: string;
  label: string;
}

const ALL_VALUE = "__all__";

const FILTER_KEYS = [
  "CarMakerNo", "CarModelNo", "CarModelDetailNo", "CarGradeNo", "CarGradeDetailNo",
  "CarYearFrom", "CarYearTo", "CarMileageFrom", "CarMileageTo", "CarPriceFrom", "CarPriceTo",
  "CarMissionNo", "CarFuelNo", "CarColorNo",
  "CarLpg", "CarInspection", "CarPhoto", "CarSalePrice", "CarLease",
  "SearchName", "SearchCarNo",
] as const;

const SORT_OPTIONS = [
  { value: "ModDt", label: "По дате" },
  { value: "CarPrice", label: "По цене" },
  { value: "CarMileage", label: "По пробегу" },
  { value: "CarYear", label: "По году" },
];

const DEFAULT_PARAMS: CarListingParams = {
  PageNow: 1,
  PageSize: 24,
  PageSort: "ModDt",
  PageAscDesc: "DESC",
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

  // 5-level cascading state
  const [selectedMaker, setSelectedMaker] = useState(appliedParams.CarMakerNo || "");
  const [selectedModel, setSelectedModel] = useState(appliedParams.CarModelNo || "");
  const [selectedModelDetail, setSelectedModelDetail] = useState(appliedParams.CarModelDetailNo || "");
  const [selectedGrade, setSelectedGrade] = useState(appliedParams.CarGradeNo || "");
  const [selectedGradeDetail, setSelectedGradeDetail] = useState(appliedParams.CarGradeDetailNo || "");

  // Sync draft from parent when appliedParams change (e.g. pagination)
  useEffect(() => {
    setDraftParams(appliedParams);
    setSelectedMaker(appliedParams.CarMakerNo || "");
    setSelectedModel(appliedParams.CarModelNo || "");
    setSelectedModelDetail(appliedParams.CarModelDetailNo || "");
    setSelectedGrade(appliedParams.CarGradeNo || "");
    setSelectedGradeDetail(appliedParams.CarGradeDetailNo || "");
  }, [appliedParams]);

  // Dirty detection
  const hasUnappliedChanges = useMemo(() => {
    return FILTER_KEYS.some(
      (k) => (draftParams[k] || "") !== (appliedParams[k] || "")
    );
  }, [draftParams, appliedParams]);

  const updateDraft = useCallback(
    (key: keyof CarListingParams, value: string) => {
      setDraftParams((prev) => ({ ...prev, [key]: value || undefined, PageNow: 1 }));
    },
    []
  );

  // 5-level cascade handlers — all from local filter data
  const handleMakerChange = (value: string) => {
    setSelectedMaker(value);
    setSelectedModel("");
    setSelectedModelDetail("");
    setSelectedGrade("");
    setSelectedGradeDetail("");
    setDraftParams((prev) => ({
      ...prev,
      CarMakerNo: value || undefined,
      CarModelNo: undefined,
      CarModelDetailNo: undefined,
      CarGradeNo: undefined,
      CarGradeDetailNo: undefined,
      PageNow: 1,
    }));
  };

  const handleModelChange = (value: string) => {
    setSelectedModel(value);
    setSelectedModelDetail("");
    setSelectedGrade("");
    setSelectedGradeDetail("");
    setDraftParams((prev) => ({
      ...prev,
      CarModelNo: value || undefined,
      CarModelDetailNo: undefined,
      CarGradeNo: undefined,
      CarGradeDetailNo: undefined,
      PageNow: 1,
    }));
  };

  const handleModelDetailChange = (value: string) => {
    setSelectedModelDetail(value);
    setSelectedGrade("");
    setSelectedGradeDetail("");
    setDraftParams((prev) => ({
      ...prev,
      CarModelDetailNo: value || undefined,
      CarGradeNo: undefined,
      CarGradeDetailNo: undefined,
      PageNow: 1,
    }));
  };

  const handleGradeChange = (value: string) => {
    setSelectedGrade(value);
    setSelectedGradeDetail("");
    setDraftParams((prev) => ({
      ...prev,
      CarGradeNo: value || undefined,
      CarGradeDetailNo: undefined,
      PageNow: 1,
    }));
  };

  const handleGradeDetailChange = (value: string) => {
    setSelectedGradeDetail(value);
    setDraftParams((prev) => ({
      ...prev,
      CarGradeDetailNo: value || undefined,
      PageNow: 1,
    }));
  };

  // Sort — instant-apply
  const handleSortChange = (value: string) => {
    const merged = { ...draftParams, PageSort: value || undefined, PageNow: 1 };
    setDraftParams(merged);
    onApplyFilters(merged);
  };

  const handleSortDirectionChange = (value: string) => {
    const merged = { ...draftParams, PageAscDesc: value, PageNow: 1 };
    setDraftParams(merged);
    onApplyFilters(merged);
  };

  // Maker options (no logos)
  const makerOptions = useMemo(
    () =>
      (filters?.makers || []).map((m) => ({
        value: String(m.MakerNo),
        label: translateSmartly(m.MakerName),
      })),
    [filters?.makers]
  );

  // Model options — filtered from local data by selected maker
  const modelOptions = useMemo(() => {
    if (!selectedMaker || !filters?.models) return [];
    const items = filters.models[selectedMaker] || [];
    return items.map((m) => ({ value: String(m.ModelNo), label: translateSmartly(m.ModelName) }));
  }, [filters?.models, selectedMaker]);

  // ModelDetail options — filtered by selected model
  const modelDetailOptions = useMemo(() => {
    if (!selectedModel || !filters?.modelDetails) return [];
    const items = filters.modelDetails[selectedModel] || [];
    return items.map((m) => ({ value: String(m.ModelDetailNo), label: translateSmartly(m.ModelDetailName) }));
  }, [filters?.modelDetails, selectedModel]);

  // Grade options — filtered by selected model detail
  const gradeOptions = useMemo(() => {
    if (!selectedModelDetail || !filters?.grades) return [];
    const items = filters.grades[selectedModelDetail] || [];
    return items.map((g) => ({ value: String(g.GradeNo), label: translateSmartly(g.GradeName) }));
  }, [filters?.grades, selectedModelDetail]);

  // GradeDetail options — filtered by selected grade
  const gradeDetailOptions = useMemo(() => {
    if (!selectedGrade || !filters?.gradeDetails) return [];
    const items = filters.gradeDetails[selectedGrade] || [];
    return items.map((g) => ({ value: String(g.GradeDetailNo), label: translateSmartly(g.GradeDetailName) }));
  }, [filters?.gradeDetails, selectedGrade]);

  const handleReset = () => {
    setSelectedMaker("");
    setSelectedModel("");
    setSelectedModelDetail("");
    setSelectedGrade("");
    setSelectedGradeDetail("");
    const resetParams: CarListingParams = { ...DEFAULT_PARAMS };
    setDraftParams(resetParams);
    onApplyFilters(resetParams);
  };

  const handleApply = () => {
    onApplyFilters({ ...draftParams, PageNow: 1 });
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
            <FilterCombobox
              options={modelOptions}
              value={selectedModel}
              onChange={handleModelChange}
              placeholder="Все модели"
              searchPlaceholder="Найти модель..."
              disabled={!selectedMaker}
            />
          </FilterField>

          <FilterField label="Модификация">
            <FilterDropdown
              options={modelDetailOptions}
              value={selectedModelDetail}
              onChange={handleModelDetailChange}
              placeholder="Все"
              disabled={!selectedModel}
            />
          </FilterField>

          <FilterField label="Комплектация">
            <FilterDropdown
              options={gradeOptions}
              value={selectedGrade}
              onChange={handleGradeChange}
              placeholder="Все"
              disabled={!selectedModelDetail}
            />
          </FilterField>

          <FilterField label="Доп. комплектация">
            <FilterDropdown
              options={gradeDetailOptions}
              value={selectedGradeDetail}
              onChange={handleGradeDetailChange}
              placeholder="Все"
              disabled={!selectedGrade}
            />
          </FilterField>

          <FilterField label="Сортировка">
            <FilterDropdown
              options={SORT_OPTIONS}
              value={draftParams.PageSort || "ModDt"}
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
              options={(filters?.fuels || []).map((f) => ({
                value: String(f.FKeyNo),
                label: translateSmartly(f.FuelName),
              }))}
              value={draftParams.CarFuelNo || ""}
              onChange={(v) => updateDraft("CarFuelNo", v)}
            />
          </FilterField>

          {/* Mission (transmission) radio group */}
          <FilterField label="КПП">
            <FilterPillGroup
              options={(filters?.missions || []).map((m) => ({
                value: String(m.MKeyNo),
                label: translateSmartly(m.MissionName),
              }))}
              value={draftParams.CarMissionNo || ""}
              onChange={(v) => updateDraft("CarMissionNo", v)}
            />
          </FilterField>

          {/* Color dropdown (no RGB data for grid) */}
          {filters?.colors && filters.colors.length > 0 && (
            <FilterField label="Цвет">
              <FilterDropdown
                options={filters.colors.map((c) => ({
                  value: String(c.CKeyNo),
                  label: translateSmartly(c.ColorName),
                }))}
                value={draftParams.CarColorNo || ""}
                onChange={(v) => updateDraft("CarColorNo", v)}
                placeholder="Все цвета"
              />
            </FilterField>
          )}

          {/* Range filters */}
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
            <RangeInput
              label="Год выпуска"
              fromValue={draftParams.CarYearFrom || ""}
              toValue={draftParams.CarYearTo || ""}
              onFromChange={(v) => updateDraft("CarYearFrom", v)}
              onToChange={(v) => updateDraft("CarYearTo", v)}
              placeholderFrom="От (2015)"
              placeholderTo="До (2024)"
            />
            <RangeInput
              label="Пробег (км)"
              fromValue={draftParams.CarMileageFrom || ""}
              toValue={draftParams.CarMileageTo || ""}
              onFromChange={(v) => updateDraft("CarMileageFrom", v)}
              onToChange={(v) => updateDraft("CarMileageTo", v)}
              placeholderFrom="От"
              placeholderTo="До"
            />
            <RangeInput
              label="Цена (만원)"
              fromValue={draftParams.CarPriceFrom || ""}
              toValue={draftParams.CarPriceTo || ""}
              onFromChange={(v) => updateDraft("CarPriceFrom", v)}
              onToChange={(v) => updateDraft("CarPriceTo", v)}
              placeholderFrom="От (напр. 1000)"
              placeholderTo="До (напр. 5000)"
            />
          </div>

          {/* Search inputs */}
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
            <FilterField label="Поиск по названию">
              <Input
                type="text"
                value={draftParams.SearchName || ""}
                onChange={(e) => updateDraft("SearchName", e.target.value)}
                placeholder="Название модели"
                className="h-9 bg-bg-elevated"
              />
            </FilterField>
            <FilterField label="Поиск по номеру">
              <Input
                type="text"
                value={draftParams.SearchCarNo || ""}
                onChange={(e) => updateDraft("SearchCarNo", e.target.value)}
                placeholder="Гос. номер"
                className="h-9 bg-bg-elevated"
              />
            </FilterField>
          </div>

          {/* Checkbox options */}
          <FilterField label="Опции">
            <div className="flex flex-wrap gap-2">
              <FilterCheckbox
                label="LPG"
                checked={draftParams.CarLpg === "1"}
                onChange={(c) => updateDraft("CarLpg", c ? "1" : "")}
              />
              <FilterCheckbox
                label="Тех. осмотр"
                checked={draftParams.CarInspection === "1"}
                onChange={(c) => updateDraft("CarInspection", c ? "1" : "")}
              />
              <FilterCheckbox
                label="С фото"
                checked={draftParams.CarPhoto === "1"}
                onChange={(c) => updateDraft("CarPhoto", c ? "1" : "")}
              />
              <FilterCheckbox
                label="Цена продажи"
                checked={draftParams.CarSalePrice === "1"}
                onChange={(c) => updateDraft("CarSalePrice", c ? "1" : "")}
              />
              <FilterCheckbox
                label="Лизинг"
                checked={draftParams.CarLease === "1"}
                onChange={(c) => updateDraft("CarLease", c ? "1" : "")}
              />
            </div>
          </FilterField>

          {/* Sort direction — instant-apply */}
          <div className="flex flex-wrap gap-3">
            <div className="ml-auto flex items-center gap-0.5 rounded-lg border border-border">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleSortDirectionChange("ASC")}
                className={cn(
                  "rounded-r-none border-0",
                  draftParams.PageAscDesc === "ASC"
                    ? "bg-gold/10 text-gold"
                    : "text-text-secondary hover:text-text-primary"
                )}
              >
                По возр.
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleSortDirectionChange("DESC")}
                className={cn(
                  "rounded-l-none border-0",
                  draftParams.PageAscDesc !== "ASC"
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
}: {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  searchPlaceholder: string;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);

  const selectedLabel = useMemo(
    () => options.find((o) => o.value === value)?.label,
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
        <span className="truncate">
          {selectedLabel || placeholder}
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
                  {opt.label}
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
