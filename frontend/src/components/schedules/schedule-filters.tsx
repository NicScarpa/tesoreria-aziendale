"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ScheduleFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: string;
  onStatusChange: (value: string) => void;
  typeFilter: string;
  onTypeChange: (value: string) => void;
  priorityFilter: string;
  onPriorityChange: (value: string) => void;
}

export function ScheduleFilters({
  search,
  onSearchChange,
  statusFilter,
  onStatusChange,
  typeFilter,
  onTypeChange,
  priorityFilter,
  onPriorityChange,
}: ScheduleFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="relative flex-1 min-w-[200px] max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Cerca per descrizione, controparte, documento..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>

      <Select value={statusFilter} onValueChange={onStatusChange}>
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="Stato" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tutti gli stati</SelectItem>
          <SelectItem value="aperta">Aperte</SelectItem>
          <SelectItem value="parzialmente_pagata">Parziali</SelectItem>
          <SelectItem value="pagata">Pagate</SelectItem>
          <SelectItem value="scaduta">Scadute</SelectItem>
          <SelectItem value="annullata">Annullate</SelectItem>
        </SelectContent>
      </Select>

      <Select value={typeFilter} onValueChange={onTypeChange}>
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="Tipo" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tutti i tipi</SelectItem>
          <SelectItem value="attiva">Da incassare</SelectItem>
          <SelectItem value="passiva">Da pagare</SelectItem>
        </SelectContent>
      </Select>

      <Select value={priorityFilter} onValueChange={onPriorityChange}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Priorita" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tutte</SelectItem>
          <SelectItem value="urgente">Urgente</SelectItem>
          <SelectItem value="alta">Alta</SelectItem>
          <SelectItem value="normale">Normale</SelectItem>
          <SelectItem value="bassa">Bassa</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
