"use client";

import { Download, CheckCircle, XCircle } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import type { InvoiceImport } from "@/types/integration";
import { INVOICE_DOC_TYPE_LABELS, INVOICE_DOC_TYPE_COLORS, INVOICE_STATUS_LABELS, INVOICE_STATUS_COLORS } from "@/types/integration";

function formatCurrency(value: number | null): string {
  if (value === null) return "\u2014";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(d: string | null): string {
  if (!d) return "\u2014";
  return new Date(d).toLocaleDateString("it-IT");
}

interface Props {
  invoice: InvoiceImport | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onElaborate: (id: string) => void;
  onIgnore: (id: string) => void;
  onDownloadXml: (id: string, nome: string) => void;
}

export function InvoiceDetailSheet({ invoice, open, onOpenChange, onElaborate, onIgnore, onDownloadXml }: Props) {
  if (!invoice) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[500px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Fattura {invoice.numero_fattura}</SheetTitle>
          <SheetDescription>
            <Badge className={INVOICE_DOC_TYPE_COLORS[invoice.tipo_documento]}>
              {INVOICE_DOC_TYPE_LABELS[invoice.tipo_documento]}
            </Badge>{" "}
            <Badge className={INVOICE_STATUS_COLORS[invoice.stato]}>
              {INVOICE_STATUS_LABELS[invoice.stato]}
            </Badge>
          </SheetDescription>
        </SheetHeader>

        <div className="mt-4 space-y-4">
          <div>
            <h4 className="text-sm font-semibold mb-1">Cedente</h4>
            <p className="text-sm">{invoice.cedente_denominazione}</p>
            {invoice.cedente_piva && <p className="text-xs text-muted-foreground">P.IVA: {invoice.cedente_piva}</p>}
          </div>
          <Separator />
          <div>
            <h4 className="text-sm font-semibold mb-1">Cessionario</h4>
            <p className="text-sm">{invoice.cessionario_denominazione}</p>
            {invoice.cessionario_piva && <p className="text-xs text-muted-foreground">P.IVA: {invoice.cessionario_piva}</p>}
          </div>
          <Separator />
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-muted-foreground">Data:</span> {formatDate(invoice.data_fattura)}</div>
            <div><span className="text-muted-foreground">Valuta:</span> {invoice.valuta}</div>
            <div><span className="text-muted-foreground">Imponibile:</span> {formatCurrency(invoice.imponibile_totale)}</div>
            <div><span className="text-muted-foreground">IVA:</span> {formatCurrency(invoice.iva_totale)}</div>
            <div className="col-span-2"><span className="text-muted-foreground">Totale:</span> <strong>{formatCurrency(invoice.importo_totale)}</strong></div>
          </div>
          <Separator />
          <div className="text-sm">
            <h4 className="font-semibold mb-1">Pagamento</h4>
            <p>Scadenza: {formatDate(invoice.data_scadenza_pagamento)}</p>
            {invoice.iban_pagamento && <p>IBAN: {invoice.iban_pagamento}</p>}
            {invoice.modalita_pagamento && <p>Modalita: {invoice.modalita_pagamento}</p>}
          </div>
          <Separator />
          <div className="flex gap-2">
            {invoice.xml_file_nome && (
              <Button size="sm" variant="outline" onClick={() => onDownloadXml(invoice.id, invoice.xml_file_nome!)}>
                <Download className="h-3 w-3 mr-1" /> XML
              </Button>
            )}
            {invoice.stato === "importata" && (
              <>
                <Button size="sm" onClick={() => onElaborate(invoice.id)}>
                  <CheckCircle className="h-3 w-3 mr-1" /> Elabora
                </Button>
                <Button size="sm" variant="ghost" className="text-muted-foreground" onClick={() => onIgnore(invoice.id)}>
                  <XCircle className="h-3 w-3 mr-1" /> Ignora
                </Button>
              </>
            )}
          </div>
          {invoice.errore_dettaglio && (
            <p className="text-xs text-destructive">{invoice.errore_dettaglio}</p>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
