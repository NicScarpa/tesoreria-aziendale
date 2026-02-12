"use client";

import { AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  PAYMENT_ORDER_TYPE_LABELS,
  PAYMENT_PRIORITY_LABELS,
  type PaymentOrderLine,
  type PaymentOrderType,
  type PaymentPriority,
} from "@/types/payment";
import type { BankAccount } from "@/types/bank-account";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("it-IT");
}

interface StepReviewConfig {
  tipo: PaymentOrderType;
  bank_account_id: string | null;
  data_esecuzione_richiesta: string;
  priorita: PaymentPriority;
  note: string;
}

interface StepReviewProps {
  config: StepReviewConfig;
  lines: PaymentOrderLine[];
  bankAccounts: BankAccount[];
}

export function StepReview({ config, lines, bankAccounts }: StepReviewProps) {
  const total = lines.reduce((sum, line) => sum + line.importo, 0);
  const bankAccount = bankAccounts.find((a) => a.id === config.bank_account_id);

  const PRIORITY_COLORS: Record<PaymentPriority, string> = {
    normale: "bg-gray-100 text-gray-700",
    alta: "bg-amber-100 text-amber-700",
    urgente: "bg-red-100 text-red-700",
  };

  return (
    <div className="space-y-6">
      {/* Warning if no lines */}
      {lines.length === 0 && (
        <div className="flex items-center gap-3 rounded-md border border-amber-200 bg-amber-50 p-4">
          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
          <p className="text-sm text-amber-800">
            Attenzione: non sono state aggiunte righe di pagamento. L'ordine
            verra creato senza disposizioni.
          </p>
        </div>
      )}

      {/* Configuration summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Configurazione</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Tipo pagamento</dt>
              <dd className="font-medium">
                {PAYMENT_ORDER_TYPE_LABELS[config.tipo]}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Conto bancario</dt>
              <dd className="font-medium">
                {bankAccount
                  ? bankAccount.nickname || bankAccount.iban
                  : "Non selezionato"}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Data esecuzione</dt>
              <dd className="font-medium">
                {formatDate(config.data_esecuzione_richiesta)}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Priorita</dt>
              <dd>
                <Badge
                  variant="secondary"
                  className={cn(PRIORITY_COLORS[config.priorita])}
                >
                  {PAYMENT_PRIORITY_LABELS[config.priorita]}
                </Badge>
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Lines summary */}
      {lines.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Righe di pagamento ({lines.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Beneficiario</TableHead>
                  <TableHead>IBAN</TableHead>
                  <TableHead className="text-right">Importo</TableHead>
                  <TableHead>Causale</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lines.map((line, index) => (
                  <TableRow key={line.id || index}>
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
                  </TableRow>
                ))}
              </TableBody>
              <TableFooter>
                <TableRow>
                  <TableCell colSpan={2} className="font-semibold">
                    Totale
                  </TableCell>
                  <TableCell className="text-right font-bold">
                    {formatCurrency(total)}
                  </TableCell>
                  <TableCell />
                </TableRow>
              </TableFooter>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Note preview */}
      {config.note && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Note</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
              {config.note}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
