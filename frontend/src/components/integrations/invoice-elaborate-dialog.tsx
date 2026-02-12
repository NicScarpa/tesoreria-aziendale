"use client";

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { InvoiceImport } from "@/types/integration";

function formatCurrency(value: number | null): string {
  if (value === null) return "\u2014";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface Props {
  invoice: InvoiceImport | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (id: string) => void;
  loading?: boolean;
}

export function InvoiceElaborateDialog({ invoice, open, onOpenChange, onConfirm, loading }: Props) {
  if (!invoice) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Conferma Elaborazione</DialogTitle>
          <DialogDescription>Verra creata una scadenza a partire da questa fattura.</DialogDescription>
        </DialogHeader>

        <div className="space-y-2 text-sm">
          <p><strong>Fattura:</strong> {invoice.numero_fattura}</p>
          <p><strong>Cedente:</strong> {invoice.cedente_denominazione}</p>
          <p><strong>Importo:</strong> {formatCurrency(invoice.importo_totale)}</p>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
          <Button disabled={loading} onClick={() => onConfirm(invoice.id)}>
            {loading ? "Elaborazione..." : "Elabora"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
