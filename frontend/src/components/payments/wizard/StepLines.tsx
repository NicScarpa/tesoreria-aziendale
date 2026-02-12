"use client";

import { useState } from "react";
import { Plus, CalendarDays, Trash2 } from "lucide-react";
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
import { PaymentLineForm } from "@/components/payments/PaymentLineForm";
import { SchedulePickerDialog } from "@/components/payments/SchedulePickerDialog";
import type { PaymentOrderLine, PaymentOrderType } from "@/types/payment";
import type { CreatePaymentLineInput } from "@/lib/validations/payment";
import type { BankAccount } from "@/types/bank-account";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

interface StepLinesProps {
  lines: PaymentOrderLine[];
  tipo: PaymentOrderType;
  onAddLine: (line: CreatePaymentLineInput) => void;
  onRemoveLine: (index: number) => void;
  bankAccounts: BankAccount[];
}

export function StepLines({
  lines,
  tipo,
  onAddLine,
  onRemoveLine,
  bankAccounts,
}: StepLinesProps) {
  const [lineFormOpen, setLineFormOpen] = useState(false);
  const [schedulePickerOpen, setSchedulePickerOpen] = useState(false);

  const total = lines.reduce((sum, line) => sum + line.importo, 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setLineFormOpen(true)}
        >
          <Plus className="mr-2 h-4 w-4" />
          Aggiungi Riga
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSchedulePickerOpen(true)}
        >
          <CalendarDays className="mr-2 h-4 w-4" />
          Da Scadenze
        </Button>
      </div>

      {lines.length === 0 ? (
        <div className="rounded-md border p-8 text-center">
          <p className="text-sm text-muted-foreground">
            Nessuna riga aggiunta. Usa i pulsanti sopra per aggiungere righe di
            pagamento.
          </p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Beneficiario</TableHead>
                <TableHead>IBAN</TableHead>
                <TableHead className="text-right">Importo</TableHead>
                <TableHead>Causale</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {lines.map((line, index) => (
                <TableRow key={line.id || index}>
                  <TableCell className="text-muted-foreground">
                    {index + 1}
                  </TableCell>
                  <TableCell className="font-medium">
                    {line.beneficiario_nome}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground font-mono">
                    {line.beneficiario_iban || "-"}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(line.importo)}
                  </TableCell>
                  <TableCell className="max-w-[150px] truncate text-sm text-muted-foreground">
                    {line.causale || "-"}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => onRemoveLine(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
            <TableFooter>
              <TableRow>
                <TableCell colSpan={3} className="font-semibold">
                  Totale ({lines.length}{" "}
                  {lines.length === 1 ? "riga" : "righe"})
                </TableCell>
                <TableCell className="text-right font-bold">
                  {formatCurrency(total)}
                </TableCell>
                <TableCell colSpan={2} />
              </TableRow>
            </TableFooter>
          </Table>
        </div>
      )}

      <PaymentLineForm
        open={lineFormOpen}
        onClose={() => setLineFormOpen(false)}
        tipo={tipo}
        onSubmit={(data) => onAddLine(data)}
      />

      <SchedulePickerDialog
        open={schedulePickerOpen}
        onClose={() => setSchedulePickerOpen(false)}
        onCreated={() => {
          // The SchedulePickerDialog creates an order directly;
          // in the wizard context we just close the dialog
          setSchedulePickerOpen(false);
        }}
        bankAccounts={bankAccounts}
      />
    </div>
  );
}
