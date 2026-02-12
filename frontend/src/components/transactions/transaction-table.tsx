"use client";

import { CheckCircle2, Circle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Transaction } from "@/types/transaction";

function formatCurrency(value: number, currency = "EUR"): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency }).format(value);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

const TX_TYPE_LABELS: Record<string, string> = {
  credit_transfer: "Bonifico",
  direct_debit: "Addebito diretto",
  card_payment: "Carta",
  cash: "Contante",
  fee: "Commissione",
  interest: "Interesse",
  tax: "Tasse",
  other: "Altro",
};

interface Props {
  transactions: Transaction[];
  onSelect: (transaction: Transaction) => void;
  onToggleVerified?: (transaction: Transaction) => void;
}

export function TransactionTable({ transactions, onSelect, onToggleVerified }: Props) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-8" />
            <TableHead>Data</TableHead>
            <TableHead>Descrizione</TableHead>
            <TableHead>Controparte</TableHead>
            <TableHead>Categoria</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead className="text-right">Importo</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                Nessun movimento trovato.
              </TableCell>
            </TableRow>
          ) : (
            transactions.map((tx) => (
              <TableRow
                key={tx.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => onSelect(tx)}
              >
                <TableCell>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleVerified?.(tx);
                    }}
                    className="p-0.5"
                  >
                    {tx.verified ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <Circle className="h-4 w-4 text-muted-foreground/30" />
                    )}
                  </button>
                </TableCell>
                <TableCell className="whitespace-nowrap text-sm">
                  {formatDate(tx.transaction_date)}
                </TableCell>
                <TableCell className="max-w-[300px] truncate text-sm">
                  {tx.description || "—"}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {tx.counterpart_name || "—"}
                </TableCell>
                <TableCell>
                  {tx.category ? (
                    <Badge
                      variant="outline"
                      className="text-xs"
                      style={{
                        borderColor: tx.category.color,
                        color: tx.category.color,
                      }}
                    >
                      {tx.category.name}
                    </Badge>
                  ) : tx.allocations.length > 0 ? (
                    <Badge variant="outline" className="text-xs">
                      Split ({tx.allocations.length})
                    </Badge>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {TX_TYPE_LABELS[tx.transaction_type] || tx.transaction_type}
                </TableCell>
                <TableCell className="text-right font-mono text-sm font-medium whitespace-nowrap">
                  <span className={tx.amount >= 0 ? "text-emerald-600" : "text-red-600"}>
                    {formatCurrency(tx.amount, tx.currency)}
                  </span>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
