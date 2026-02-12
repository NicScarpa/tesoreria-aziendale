"use client";

import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  PAYMENT_LINE_STATUS_LABELS,
  type PaymentOrderLine,
  type PaymentLineStatus,
} from "@/types/payment";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

const LINE_STATUS_COLORS: Record<PaymentLineStatus, string> = {
  inclusa: "bg-blue-100 text-blue-700",
  eseguita: "bg-green-100 text-green-700",
  rifiutata: "bg-red-100 text-red-700",
  esclusa: "bg-gray-100 text-gray-500",
};

interface PaymentLineTableProps {
  lines: PaymentOrderLine[];
  isEditable?: boolean;
  onEdit?: (line: PaymentOrderLine) => void;
  onDelete?: (lineId: string) => void;
}

export function PaymentLineTable({
  lines,
  isEditable = false,
  onEdit,
  onDelete,
}: PaymentLineTableProps) {
  const total = lines.reduce((sum, line) => sum + line.importo, 0);

  if (lines.length === 0) {
    return (
      <div className="rounded-md border p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Nessuna riga di pagamento presente.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Beneficiario</TableHead>
            <TableHead>IBAN</TableHead>
            <TableHead className="text-right">Importo</TableHead>
            <TableHead>Causale</TableHead>
            <TableHead>Stato</TableHead>
            {isEditable && <TableHead className="w-[100px]">Azioni</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {lines.map((line) => (
            <TableRow key={line.id}>
              <TableCell className="font-medium">
                {line.beneficiario_nome}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground font-mono">
                {line.beneficiario_iban || "-"}
              </TableCell>
              <TableCell className="text-right font-medium">
                {formatCurrency(line.importo)}
              </TableCell>
              <TableCell className="max-w-[200px] truncate text-sm text-muted-foreground">
                {line.causale || "-"}
              </TableCell>
              <TableCell>
                <Badge
                  variant="secondary"
                  className={cn(LINE_STATUS_COLORS[line.stato])}
                >
                  {PAYMENT_LINE_STATUS_LABELS[line.stato]}
                </Badge>
              </TableCell>
              {isEditable && (
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => onEdit?.(line)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => onDelete?.(line.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell colSpan={2} className="font-semibold">
              Totale ({lines.length} {lines.length === 1 ? "riga" : "righe"})
            </TableCell>
            <TableCell className="text-right font-bold">
              {formatCurrency(total)}
            </TableCell>
            <TableCell colSpan={isEditable ? 3 : 2} />
          </TableRow>
        </TableFooter>
      </Table>
    </div>
  );
}
