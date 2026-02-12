"use client";

import { useState, useCallback, useEffect } from "react";
import { CalendarIcon, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface CashFlowFilters {
  data_inizio: string;
  data_fine: string;
  raggruppamento: string;
  includi_scadenze: boolean;
  includi_pagamenti: boolean;
  includi_ricorrenze: boolean;
}

interface CashFlowControlsProps {
  filters: CashFlowFilters;
  onChange: (filters: CashFlowFilters) => void;
  onSave?: () => void;
}

const PRESETS = [
  { label: "30gg", days: 30 },
  { label: "90gg", days: 90 },
  { label: "6 mesi", days: 180 },
  { label: "1 anno", days: 365 },
];

export function CashFlowControls({ filters, onChange, onSave }: CashFlowControlsProps) {
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);

  const updateFilter = useCallback(
    (key: keyof CashFlowFilters, value: string | boolean) => {
      const newFilters = { ...filters, [key]: value };
      if (debounceTimer) clearTimeout(debounceTimer);
      const timer = setTimeout(() => onChange(newFilters), 300);
      setDebounceTimer(timer);
    },
    [filters, onChange, debounceTimer]
  );

  const applyPreset = (days: number) => {
    const today = new Date();
    const start = new Date(today);
    start.setDate(start.getDate() - 30);
    const end = new Date(today);
    end.setDate(end.getDate() + days);
    onChange({
      ...filters,
      data_inizio: start.toISOString().split("T")[0],
      data_fine: end.toISOString().split("T")[0],
    });
  };

  useEffect(() => {
    return () => {
      if (debounceTimer) clearTimeout(debounceTimer);
    };
  }, [debounceTimer]);

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card p-3">
      <div className="flex items-center gap-2">
        <CalendarIcon className="h-4 w-4 text-muted-foreground" />
        <Input
          type="date"
          value={filters.data_inizio}
          onChange={(e) => updateFilter("data_inizio", e.target.value)}
          className="h-8 w-36"
        />
        <span className="text-sm text-muted-foreground">-</span>
        <Input
          type="date"
          value={filters.data_fine}
          onChange={(e) => updateFilter("data_fine", e.target.value)}
          className="h-8 w-36"
        />
      </div>

      <div className="flex gap-1">
        {PRESETS.map((p) => (
          <Button
            key={p.label}
            variant="outline"
            size="sm"
            className="h-8 px-2 text-xs"
            onClick={() => applyPreset(p.days)}
          >
            {p.label}
          </Button>
        ))}
      </div>

      <Select
        value={filters.raggruppamento}
        onValueChange={(v) => updateFilter("raggruppamento", v)}
      >
        <SelectTrigger className="h-8 w-32">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="giornaliero">Giornaliero</SelectItem>
          <SelectItem value="settimanale">Settimanale</SelectItem>
          <SelectItem value="mensile">Mensile</SelectItem>
        </SelectContent>
      </Select>

      {onSave && (
        <Button size="sm" className="ml-auto h-8" onClick={onSave}>
          <Save className="mr-1 h-3 w-3" />
          Salva previsione
        </Button>
      )}
    </div>
  );
}
