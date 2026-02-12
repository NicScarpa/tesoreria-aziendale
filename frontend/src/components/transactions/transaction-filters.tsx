"use client";

import { useState } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BankAccountSelector } from "@/components/shared/bank-account-selector";
import type { Category } from "@/types/category";

export interface TransactionFilters {
  bank_account_id: string | null;
  date_from: string;
  date_to: string;
  amount_min: string;
  amount_max: string;
  direction: string;
  category_id: string;
  search: string;
  status: string;
  uncategorized: string;
  verified: string;
  counterpart_name: string;
}

export const defaultFilters: TransactionFilters = {
  bank_account_id: null,
  date_from: "",
  date_to: "",
  amount_min: "",
  amount_max: "",
  direction: "",
  category_id: "",
  search: "",
  status: "",
  uncategorized: "",
  verified: "",
  counterpart_name: "",
};

interface Props {
  filters: TransactionFilters;
  onChange: (filters: TransactionFilters) => void;
  categories: Category[];
}

export function TransactionFiltersBar({ filters, onChange, categories }: Props) {
  const [expanded, setExpanded] = useState(false);

  const update = (key: keyof TransactionFilters, value: string | null) => {
    onChange({ ...filters, [key]: value });
  };

  const clearAll = () => onChange(defaultFilters);

  const hasActiveFilters = Object.entries(filters).some(
    ([key, value]) => value !== "" && value !== null && key !== "bank_account_id"
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <BankAccountSelector
          value={filters.bank_account_id}
          onChange={(v) => update("bank_account_id", v)}
          className="w-[250px]"
        />
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Cerca movimenti..."
            value={filters.search}
            onChange={(e) => update("search", e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={filters.direction} onValueChange={(v) => update("direction", v === "all" ? "" : v)}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Direzione" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tutte</SelectItem>
            <SelectItem value="inflow">Entrate</SelectItem>
            <SelectItem value="outflow">Uscite</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          className="gap-1"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filtri
        </Button>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearAll} className="gap-1">
            <X className="h-4 w-4" />
            Reset
          </Button>
        )}
      </div>

      {expanded && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 border rounded-lg bg-muted/30">
          <div>
            <label className="text-xs text-muted-foreground">Data da</label>
            <Input
              type="date"
              value={filters.date_from}
              onChange={(e) => update("date_from", e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Data a</label>
            <Input
              type="date"
              value={filters.date_to}
              onChange={(e) => update("date_to", e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Importo min</label>
            <Input
              type="number"
              placeholder="0.00"
              value={filters.amount_min}
              onChange={(e) => update("amount_min", e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Importo max</label>
            <Input
              type="number"
              placeholder="0.00"
              value={filters.amount_max}
              onChange={(e) => update("amount_max", e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Categoria</label>
            <Select value={filters.category_id} onValueChange={(v) => update("category_id", v === "all" ? "" : v)}>
              <SelectTrigger>
                <SelectValue placeholder="Tutte" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutte</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id}>
                    <span className="flex items-center gap-2">
                      <span
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: cat.color }}
                      />
                      {cat.name}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Stato</label>
            <Select value={filters.status} onValueChange={(v) => update("status", v === "all" ? "" : v)}>
              <SelectTrigger>
                <SelectValue placeholder="Tutti" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti</SelectItem>
                <SelectItem value="booked">Contabilizzato</SelectItem>
                <SelectItem value="pending">In sospeso</SelectItem>
                <SelectItem value="rejected">Rifiutato</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Verificato</label>
            <Select value={filters.verified} onValueChange={(v) => update("verified", v === "all" ? "" : v)}>
              <SelectTrigger>
                <SelectValue placeholder="Tutti" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti</SelectItem>
                <SelectItem value="true">Verificati</SelectItem>
                <SelectItem value="false">Non verificati</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Controparte</label>
            <Input
              placeholder="Nome controparte..."
              value={filters.counterpart_name}
              onChange={(e) => update("counterpart_name", e.target.value)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
