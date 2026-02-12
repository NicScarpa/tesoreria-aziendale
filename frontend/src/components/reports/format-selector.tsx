"use client";

import { FileText, FileSpreadsheet, FileDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReportFormat } from "@/types/report";

const FORMAT_OPTIONS: { value: ReportFormat; label: string; icon: typeof FileText; description: string }[] = [
  { value: "pdf", label: "PDF", icon: FileText, description: "Documento professionale" },
  { value: "xlsx", label: "Excel", icon: FileSpreadsheet, description: "Foglio di calcolo" },
  { value: "csv", label: "CSV", icon: FileDown, description: "Dati grezzi" },
];

interface FormatSelectorProps {
  value: ReportFormat;
  onChange: (value: ReportFormat) => void;
  disabled?: boolean;
}

export function FormatSelector({ value, onChange, disabled }: FormatSelectorProps) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {FORMAT_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          disabled={disabled}
          onClick={() => onChange(opt.value)}
          className={cn(
            "flex flex-col items-center gap-1 rounded-lg border p-3 text-sm transition-colors",
            value === opt.value
              ? "border-primary bg-primary/5 text-primary"
              : "border-border hover:border-primary/50 text-muted-foreground",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          <opt.icon className="h-5 w-5" />
          <span className="font-medium">{opt.label}</span>
          <span className="text-xs">{opt.description}</span>
        </button>
      ))}
    </div>
  );
}
