"use client";

import { Download, Trash2, Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TableCell, TableRow } from "@/components/ui/table";
import type { ReportExecution } from "@/types/report";
import {
  REPORT_EXECUTION_STATUS_LABELS,
  REPORT_FORMAT_LABELS,
  REPORT_STATUS_COLORS,
} from "@/types/report";

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

function formatFileSize(bytes: number | null): string {
  if (!bytes) return "\u2014";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface ReportExecutionRowProps {
  execution: ReportExecution;
  onDownload: (execution: ReportExecution) => void;
  onDelete: (execution: ReportExecution) => void;
}

export function ReportExecutionRow({ execution, onDownload, onDelete }: ReportExecutionRowProps) {
  const isLoading = execution.stato === "in_coda" || execution.stato === "in_generazione";
  const isComplete = execution.stato === "completato";
  const isError = execution.stato === "errore";

  return (
    <TableRow>
      <TableCell>
        <div>
          <p className="font-medium text-sm">{execution.nome}</p>
          {execution.righe_totali != null && (
            <p className="text-xs text-muted-foreground">{execution.righe_totali} righe</p>
          )}
        </div>
      </TableCell>
      <TableCell className="text-sm">
        {REPORT_FORMAT_LABELS[execution.formato]}
      </TableCell>
      <TableCell>
        <Badge className={REPORT_STATUS_COLORS[execution.stato]}>
          {isLoading && <Loader2 className="h-3 w-3 mr-1 animate-spin" />}
          {isError && <AlertCircle className="h-3 w-3 mr-1" />}
          {REPORT_EXECUTION_STATUS_LABELS[execution.stato]}
        </Badge>
      </TableCell>
      <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
        {formatDate(execution.data_generazione)}
      </TableCell>
      <TableCell className="text-sm text-muted-foreground">
        {formatFileSize(execution.file_size)}
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          {isComplete && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onDownload(execution)}
            >
              <Download className="h-4 w-4" />
            </Button>
          )}
          <Button
            size="sm"
            variant="ghost"
            className="text-destructive hover:text-destructive"
            onClick={() => onDelete(execution)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
}
