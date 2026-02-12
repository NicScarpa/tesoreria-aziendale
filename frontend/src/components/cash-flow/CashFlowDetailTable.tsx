"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CashFlowProjectionLine } from "@/types/cash-flow";
import { CASH_FLOW_SOURCE_LABELS } from "@/types/cash-flow";
import { ConfidenceBadge } from "./ConfidenceBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface CashFlowDetailTableProps {
  lines: CashFlowProjectionLine[];
  className?: string;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric" });
}

export function CashFlowDetailTable({ lines, className }: CashFlowDetailTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const toggleRow = (index: number) => {
    const next = new Set(expandedRows);
    if (next.has(index)) next.delete(index);
    else next.add(index);
    setExpandedRows(next);
  };

  if (lines.length === 0) {
    return (
      <div className={cn("rounded-lg border p-8 text-center text-muted-foreground", className)}>
        Nessun movimento previsto nel periodo selezionato
      </div>
    );
  }

  return (
    <div className={cn("overflow-auto rounded-lg border", className)}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-8" />
            <TableHead>Data</TableHead>
            <TableHead>Descrizione</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead className="text-right">Importo</TableHead>
            <TableHead>Fonte</TableHead>
            <TableHead>Confidenza</TableHead>
            <TableHead className="text-right">Saldo</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {lines.map((line, idx) => (
            <>
              <TableRow
                key={idx}
                className={cn(
                  "cursor-pointer hover:bg-muted/50",
                  line.is_realizzata && "bg-muted/20"
                )}
                onClick={() => toggleRow(idx)}
              >
                <TableCell className="w-8 p-2">
                  {expandedRows.has(idx) ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </TableCell>
                <TableCell className="whitespace-nowrap text-sm">
                  {formatDate(line.data)}
                </TableCell>
                <TableCell className="max-w-[200px] truncate text-sm">
                  {line.descrizione || "\u2014"}
                </TableCell>
                <TableCell>
                  <span
                    className={cn(
                      "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
                      line.tipo === "entrata"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    )}
                  >
                    {line.tipo === "entrata" ? "Entrata" : "Uscita"}
                  </span>
                </TableCell>
                <TableCell className={cn("text-right text-sm font-medium", line.tipo === "entrata" ? "text-green-700" : "text-red-700")}>
                  {line.tipo === "entrata" ? "+" : "-"}{formatCurrency(line.importo)}
                </TableCell>
                <TableCell>
                  <span className="inline-flex rounded bg-muted px-1.5 py-0.5 text-xs">
                    {CASH_FLOW_SOURCE_LABELS[line.fonte]}
                  </span>
                </TableCell>
                <TableCell>
                  <ConfidenceBadge level={line.confidenza} />
                </TableCell>
                <TableCell className="text-right text-sm font-medium">
                  {formatCurrency(line.saldo_progressivo)}
                </TableCell>
              </TableRow>
              {expandedRows.has(idx) && (
                <TableRow key={`${idx}-detail`}>
                  <TableCell colSpan={8} className="bg-muted/10 px-10 py-3">
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Categoria: </span>
                        {line.categoria || "Non categorizzato"}
                      </div>
                      <div>
                        <span className="text-muted-foreground">Fonte ID: </span>
                        {line.fonte_id ? (
                          <code className="rounded bg-muted px-1 text-xs">{line.fonte_id.slice(0, 8)}...</code>
                        ) : "\u2014"}
                      </div>
                      <div>
                        <span className="text-muted-foreground">Realizzata: </span>
                        {line.is_realizzata ? "Si" : "No"}
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
