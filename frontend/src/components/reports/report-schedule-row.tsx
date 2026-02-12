"use client";

import { Play, Trash2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ReportSchedule } from "@/types/report";
import { REPORT_FORMAT_LABELS, REPORT_FREQUENCY_LABELS } from "@/types/report";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "\u2014";
  return new Date(dateStr).toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface ReportScheduleRowProps {
  schedule: ReportSchedule;
  onToggleActive: (schedule: ReportSchedule) => void;
  onRunNow: (schedule: ReportSchedule) => void;
  onEdit: (schedule: ReportSchedule) => void;
  onDelete: (schedule: ReportSchedule) => void;
}

export function ReportScheduleRow({ schedule, onToggleActive, onRunNow, onEdit, onDelete }: ReportScheduleRowProps) {
  return (
    <TableRow>
      <TableCell>
        <p className="font-medium text-sm">{schedule.nome}</p>
      </TableCell>
      <TableCell className="text-sm">
        {REPORT_FREQUENCY_LABELS[schedule.frequenza]}
      </TableCell>
      <TableCell className="text-sm">
        {REPORT_FORMAT_LABELS[schedule.formato]}
      </TableCell>
      <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
        {formatDate(schedule.prossima_esecuzione)}
      </TableCell>
      <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
        {formatDate(schedule.ultima_esecuzione)}
      </TableCell>
      <TableCell>
        <Switch
          checked={schedule.attivo}
          onCheckedChange={() => onToggleActive(schedule)}
        />
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          <Button size="sm" variant="ghost" onClick={() => onRunNow(schedule)} title="Esegui ora">
            <Play className="h-4 w-4" />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onEdit(schedule)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="text-destructive hover:text-destructive"
            onClick={() => onDelete(schedule)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
}
