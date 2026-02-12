"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface Header {
  name: string;
  label: string;
  align?: string;
  format?: string;
}

interface ReportPreviewTableProps {
  headers: Header[];
  rows: Record<string, unknown>[];
  totals?: Record<string, unknown>;
  maxRows?: number;
}

function formatValue(val: unknown, format?: string): string {
  if (val == null) return "";
  if (typeof val === "number") {
    if (format === "currency") {
      return new Intl.NumberFormat("it-IT", {
        style: "currency",
        currency: "EUR",
      }).format(val);
    }
    if (format === "percentage") return `${val}%`;
    return String(val);
  }
  if (typeof val === "string" && format === "date") {
    try {
      return new Date(val).toLocaleDateString("it-IT");
    } catch {
      return val;
    }
  }
  return String(val);
}

export function ReportPreviewTable({
  headers,
  rows,
  totals,
  maxRows = 50,
}: ReportPreviewTableProps) {
  const displayRows = rows.slice(0, maxRows);
  const hasMore = rows.length > maxRows;

  return (
    <div className="rounded-md border overflow-auto max-h-[400px]">
      <Table>
        <TableHeader>
          <TableRow>
            {headers.map((h) => (
              <TableHead
                key={h.name}
                className={
                  h.align === "right"
                    ? "text-right"
                    : h.align === "center"
                    ? "text-center"
                    : ""
                }
              >
                {h.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayRows.map((row, idx) => (
            <TableRow key={idx}>
              {headers.map((h) => (
                <TableCell
                  key={h.name}
                  className={
                    h.align === "right"
                      ? "text-right font-mono text-sm"
                      : h.align === "center"
                      ? "text-center text-sm"
                      : "text-sm"
                  }
                >
                  {formatValue(row[h.name], h.format)}
                </TableCell>
              ))}
            </TableRow>
          ))}
          {totals && Object.keys(totals).length > 0 && (
            <TableRow className="font-bold bg-muted/50">
              {headers.map((h) => (
                <TableCell
                  key={h.name}
                  className={
                    h.align === "right"
                      ? "text-right font-mono text-sm font-bold"
                      : "text-sm font-bold"
                  }
                >
                  {formatValue(totals[h.name], h.format)}
                </TableCell>
              ))}
            </TableRow>
          )}
        </TableBody>
      </Table>
      {hasMore && (
        <p className="text-xs text-muted-foreground text-center py-2">
          Mostrate {maxRows} di {rows.length} righe
        </p>
      )}
    </div>
  );
}
