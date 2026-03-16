"use client";

import { useState, useMemo } from "react";
import Image from "next/image";
import type { CarModel } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { ChevronsUpDown, Search } from "lucide-react";

interface ModelSelectorModalProps {
  models: CarModel[];
  selectedModel: string;
  onSelect: (boNo: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

function formatYearRange(start?: string, end?: string): string {
  if (!start) return "";
  const s = start.length >= 7 ? start.substring(0, 7) : start.substring(0, 4);
  if (!end) return `${s} ~`;
  const e = end.length >= 7 ? end.substring(0, 7) : end.substring(0, 4);
  return `${s} ~ ${e}`;
}

function CarSilhouette() {
  return (
    <svg
      viewBox="0 0 120 60"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="h-full w-full opacity-20"
    >
      <path
        d="M15 42h90M20 42c0-3 0-6-1-8l-4-8c-2-3-4-5-7-5H6c-2 0-3 1-3 3v7c0 2 1 3 3 3h9m90 0c0-3 0-6 1-8l4-8c2-3 4-5 7-5h2c2 0 3 1 3 3v7c0 2-1 3-3 3h-9M30 42v-20c0-2 2-5 5-7l15-8c3-2 7-2 10 0l15 8c3 2 5 5 5 7v20"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="30" cy="44" r="6" stroke="currentColor" strokeWidth="2" />
      <circle cx="90" cy="44" r="6" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

export function ModelSelectorModal({
  models,
  selectedModel,
  onSelect,
  disabled,
  isLoading,
}: ModelSelectorModalProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const selectedModelName = useMemo(
    () => models.find((m) => String(m.bo_no) === selectedModel)?.bo_name,
    [models, selectedModel]
  );

  const groupedModels = useMemo(() => {
    const query = search.toLowerCase().trim();
    const filtered = query
      ? models.filter((m) => m.bo_name.toLowerCase().includes(query))
      : models;

    const groups = new Map<string, CarModel[]>();
    for (const model of filtered) {
      const groupName = model.bo_group || model.bo_name;
      const existing = groups.get(groupName);
      if (existing) {
        existing.push(model);
      } else {
        groups.set(groupName, [model]);
      }
    }

    // Sort groups alphabetically, sort models within each group by startDate
    return Array.from(groups.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([name, items]) => ({
        name,
        items: items.sort((a, b) =>
          (a.bo_startDate || "").localeCompare(b.bo_startDate || "")
        ),
      }));
  }, [models, search]);

  const handleSelect = (boNo: string) => {
    onSelect(boNo);
    setOpen(false);
    setSearch("");
  };

  return (
    <Dialog
      open={open && !disabled}
      onOpenChange={(v) => {
        if (!disabled) {
          setOpen(v);
          if (!v) setSearch("");
        }
      }}
    >
      <DialogTrigger
        className={cn(
          "flex h-9 w-full items-center justify-between rounded-lg border border-input bg-bg-elevated px-3 text-sm transition-colors",
          disabled
            ? "opacity-40 cursor-not-allowed"
            : "hover:border-ring/50",
          selectedModel ? "text-text-primary" : "text-muted-foreground"
        )}
      >
        <span className="truncate">
          {isLoading
            ? "Загрузка..."
            : selectedModelName || "Все модели"}
        </span>
        <ChevronsUpDown className="ml-2 size-3.5 shrink-0 text-muted-foreground" />
      </DialogTrigger>

      <DialogContent
        className="sm:max-w-3xl lg:max-w-5xl max-h-[85vh] flex flex-col"
        showCloseButton
      >
        <DialogHeader>
          <DialogTitle>Выбрать модель</DialogTitle>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Найти модель..."
              className="pl-9 h-9 bg-bg-elevated"
              autoFocus
            />
          </div>
        </DialogHeader>

        <ScrollArea className="flex-1 -mx-4 px-4 overflow-y-auto max-h-[calc(85vh-8rem)]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12 text-text-secondary text-sm">
              Загрузка моделей...
            </div>
          ) : groupedModels.length === 0 && search ? (
            <div className="flex items-center justify-center py-12 text-text-secondary text-sm">
              Не найдено
            </div>
          ) : (
            <div className="space-y-4 pb-2">
              {/* "All models" card */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                <button
                  onClick={() => handleSelect("")}
                  className={cn(
                    "flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-3 transition-colors cursor-pointer min-h-[100px]",
                    !selectedModel
                      ? "border-gold bg-gold/10 text-gold"
                      : "border-border text-text-secondary hover:border-gold/40 hover:bg-gold/5"
                  )}
                >
                  <span className="text-sm font-medium">Все модели</span>
                </button>
              </div>

              {groupedModels.map((group) => (
                <div key={group.name}>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-gold mb-2">
                    {group.name}
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                    {group.items.map((model) => {
                      const isSelected =
                        String(model.bo_no) === selectedModel;
                      const yearRange = formatYearRange(
                        model.bo_startDate,
                        model.bo_endDate
                      );
                      return (
                        <button
                          key={model.bo_no}
                          onClick={() => handleSelect(String(model.bo_no))}
                          className={cn(
                            "flex flex-col items-center gap-1.5 rounded-xl border p-3 transition-colors cursor-pointer min-h-[100px]",
                            isSelected
                              ? "border-gold bg-gold/10 ring-1 ring-gold/30"
                              : "border-border bg-bg-elevated hover:border-gold/40 hover:bg-gold/5"
                          )}
                        >
                          <div className="h-16 w-full flex items-center justify-center">
                            {model.bo_faceImage ? (
                              <Image
                                src={model.bo_faceImage}
                                alt={model.bo_name}
                                width={120}
                                height={64}
                                className="h-16 w-full object-contain"
                                unoptimized
                              />
                            ) : (
                              <div className="h-12 w-20 text-text-secondary">
                                <CarSilhouette />
                              </div>
                            )}
                          </div>
                          <span className="text-sm font-medium text-text-primary text-center line-clamp-2 leading-tight">
                            {model.bo_name}
                          </span>
                          {yearRange && (
                            <span className="text-xs text-text-secondary">
                              {yearRange}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
