"use client";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { BankAccountBalance } from "@/types/bank-account";

function formatCurrency(value: number | null): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

const SOURCE_LABELS: Record<string, string> = {
  manual: "Manuale",
  open_banking: "Open Banking",
  import: "Import",
  calculated: "Calcolato",
};

interface Props {
  balances: BankAccountBalance[];
  loading?: boolean;
}

export function BalanceHistoryTable({ balances, loading }: Props) {
  if (loading) {
    return <div className="h-48 animate-pulse rounded bg-muted" />;
  }

  if (balances.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
        Nessun storico saldi disponibile
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Data</TableHead>
          <TableHead className="text-right">Saldo contabile</TableHead>
          <TableHead className="text-right">Saldo disponibile</TableHead>
          <TableHead>Fonte</TableHead>
          <TableHead>Note</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {balances.map((b) => (
          <TableRow key={b.id}>
            <TableCell>
              {new Date(b.balance_date).toLocaleDateString("it-IT")}
            </TableCell>
            <TableCell className="text-right font-mono">
              {formatCurrency(b.current_balance)}
            </TableCell>
            <TableCell className="text-right font-mono">
              {formatCurrency(b.available_balance)}
            </TableCell>
            <TableCell>
              <Badge variant="outline" className="text-xs">
                {SOURCE_LABELS[b.source] || b.source}
              </Badge>
            </TableCell>
            <TableCell className="text-muted-foreground text-sm max-w-[200px] truncate">
              {b.notes || "—"}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
