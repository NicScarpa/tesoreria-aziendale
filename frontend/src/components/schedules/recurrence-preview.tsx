"use client";

import { RefreshCcw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { RecurrenceType } from "@/types/schedule";
import { RECURRENCE_LABELS } from "@/types/schedule";

interface RecurrencePreviewProps {
  isRicorrente: boolean;
  ricorrenzaTipo: RecurrenceType | null;
  ricorrenzaAttiva: boolean;
  ricorrenzaProssimaGenerazione: string | null;
}

export function RecurrencePreview({
  isRicorrente,
  ricorrenzaTipo,
  ricorrenzaAttiva,
  ricorrenzaProssimaGenerazione,
}: RecurrencePreviewProps) {
  if (!isRicorrente) return null;

  return (
    <div className="flex items-center gap-2 text-sm">
      <RefreshCcw className="h-3.5 w-3.5 text-muted-foreground" />
      <span className="text-muted-foreground">
        {ricorrenzaTipo ? RECURRENCE_LABELS[ricorrenzaTipo] : "Ricorrente"}
      </span>
      {!ricorrenzaAttiva && (
        <Badge variant="secondary" className="text-xs">
          Disattivata
        </Badge>
      )}
      {ricorrenzaAttiva && ricorrenzaProssimaGenerazione && (
        <span className="text-xs text-muted-foreground">
          Prossima: {new Date(ricorrenzaProssimaGenerazione).toLocaleDateString("it-IT")}
        </span>
      )}
    </div>
  );
}
