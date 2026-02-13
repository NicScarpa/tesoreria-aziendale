"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Upload,
  Search,
  ChevronLeft,
  ChevronRight,
  Download,
  CheckCircle,
  XCircle,
  Eye,
} from "lucide-react";
import { toast } from "sonner";
import {
  listInvoicesWithDirection,
  elaborateInvoice,
  ignoreInvoice,
  downloadXml,
  downloadPdf,
} from "@/lib/api/integrations";
import type { InvoiceImport } from "@/types/integration";
import {
  INVOICE_DOC_TYPE_LABELS,
  INVOICE_DOC_TYPE_COLORS,
  INVOICE_STATUS_LABELS,
  INVOICE_STATUS_COLORS,
} from "@/types/integration";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";

function formatCurrency(value: number | null): string {
  if (value === null) return "\u2014";
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

function formatDate(d: string | null): string {
  if (!d) return "\u2014";
  return new Date(d).toLocaleDateString("it-IT");
}

interface InvoiceListPageProps {
  direction: "ricevute" | "emesse";
  title: string;
  description: string;
}

export function InvoiceListPage({
  direction,
  title,
  description,
}: InvoiceListPageProps) {
  const [items, setItems] = useState<InvoiceImport[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Filters
  const [search, setSearch] = useState("");
  const [statoFilter, setStatoFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Detail sheet
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceImport | null>(
    null
  );

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (search) params.search = search;
      if (statoFilter !== "all") params.stato = statoFilter;
      if (dateFrom) params.data_da = dateFrom;
      if (dateTo) params.data_a = dateTo;

      const data = await listInvoicesWithDirection(
        direction === "ricevute" ? "ricevute" : "emesse",
        params
      );
      setItems(data.items);
      setTotal(data.total);
    } catch {
      toast.error("Errore nel caricamento delle fatture");
    } finally {
      setLoading(false);
    }
  }, [page, search, statoFilter, dateFrom, dateTo, direction]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    setPage(1);
  }, [search, statoFilter, dateFrom, dateTo]);

  const totalPages = Math.ceil(total / pageSize);

  const handleElaborate = async (id: string) => {
    try {
      const result = await elaborateInvoice(id);
      toast.success(result.message || "Fattura elaborata");
      loadData();
      setSelectedInvoice(null);
    } catch (err: unknown) {
      const axiosErr = err as {
        response?: { data?: { detail?: string } };
      };
      toast.error(
        axiosErr?.response?.data?.detail || "Errore nell'elaborazione"
      );
    }
  };

  const handleIgnore = async (id: string) => {
    try {
      await ignoreInvoice(id);
      toast.success("Fattura ignorata");
      loadData();
      setSelectedInvoice(null);
    } catch {
      toast.error("Errore");
    }
  };

  const handleDownloadXml = async (id: string, nome: string) => {
    try {
      const blob = await downloadXml(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = nome || "fattura.xml";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Errore nel download");
    }
  };

  const handleDownloadPdf = async (id: string, nome: string) => {
    try {
      const blob = await downloadPdf(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = nome ? nome.replace(/\.xml$/i, ".pdf") : "fattura.pdf";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Errore nel download PDF");
    }
  };

  const counterpartLabel =
    direction === "ricevute" ? "Fornitore" : "Cliente";

  const getCounterpartName = (inv: InvoiceImport) =>
    direction === "ricevute"
      ? inv.cedente_denominazione
      : inv.cessionario_denominazione;

  const getCounterpartPiva = (inv: InvoiceImport) =>
    direction === "ricevute" ? inv.cedente_piva : inv.cessionario_piva;

  if (loading && items.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title={title} description={description} />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        description={description}
        actions={
          <Button asChild>
            <Link href="/fatture/import">
              <Upload className="h-4 w-4 mr-2" />
              Carica
            </Link>
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={`Cerca per numero, ${direction === "ricevute" ? "cedente" : "cessionario"}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={statoFilter} onValueChange={setStatoFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Stato" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tutti gli stati</SelectItem>
            {Object.entries(INVOICE_STATUS_LABELS).map(([v, l]) => (
              <SelectItem key={v} value={v}>
                {l}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="w-[150px]"
        />
        <Input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="w-[150px]"
        />
      </div>

      {/* Table */}
      {items.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Nessuna fattura"
          description={`Non ci sono fatture ${direction} corrispondenti ai filtri`}
        />
      ) : (
        <>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Numero</TableHead>
                  <TableHead>{counterpartLabel}</TableHead>
                  <TableHead>Data</TableHead>
                  <TableHead className="text-right">Importo</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((inv) => (
                  <TableRow
                    key={inv.id}
                    className="cursor-pointer"
                    onClick={() => setSelectedInvoice(inv)}
                  >
                    <TableCell>
                      <Badge className={INVOICE_DOC_TYPE_COLORS[inv.tipo_documento]}>
                        {INVOICE_DOC_TYPE_LABELS[inv.tipo_documento]}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-medium text-sm">
                      {inv.numero_fattura || "\u2014"}
                    </TableCell>
                    <TableCell>
                      <p className="text-sm">
                        {getCounterpartName(inv) || "\u2014"}
                      </p>
                      {getCounterpartPiva(inv) && (
                        <p className="text-xs text-muted-foreground">
                          P.IVA {getCounterpartPiva(inv)}
                        </p>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatDate(inv.data_fattura)}
                    </TableCell>
                    <TableCell className="text-right">
                      <p className="font-mono text-sm">
                        {formatCurrency(inv.importo_totale)}
                      </p>
                      {inv.iva_totale !== null && (
                        <p className="text-xs text-muted-foreground">
                          IVA {formatCurrency(inv.iva_totale)}
                        </p>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className={INVOICE_STATUS_COLORS[inv.stato]}>
                        {INVOICE_STATUS_LABELS[inv.stato]}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedInvoice(inv);
                        }}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {total} fatture &middot; Pagina {page} di {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Invoice Detail Sheet */}
      <Sheet
        open={!!selectedInvoice}
        onOpenChange={() => setSelectedInvoice(null)}
      >
        <SheetContent className="w-[500px] overflow-y-auto">
          {selectedInvoice && (
            <>
              <SheetHeader>
                <SheetTitle>
                  Fattura {selectedInvoice.numero_fattura}
                </SheetTitle>
                <SheetDescription>
                  <Badge
                    className={
                      INVOICE_DOC_TYPE_COLORS[selectedInvoice.tipo_documento]
                    }
                  >
                    {INVOICE_DOC_TYPE_LABELS[selectedInvoice.tipo_documento]}
                  </Badge>{" "}
                  <Badge
                    className={INVOICE_STATUS_COLORS[selectedInvoice.stato]}
                  >
                    {INVOICE_STATUS_LABELS[selectedInvoice.stato]}
                  </Badge>
                </SheetDescription>
              </SheetHeader>

              <div className="mt-4 space-y-4">
                {/* Documento */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-muted-foreground">
                      Tipo documento:
                    </span>{" "}
                    {INVOICE_DOC_TYPE_LABELS[selectedInvoice.tipo_documento]}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Data:</span>{" "}
                    {formatDate(selectedInvoice.data_fattura)}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Numero:</span>{" "}
                    {selectedInvoice.numero_fattura || "\u2014"}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Valuta:</span>{" "}
                    {selectedInvoice.valuta}
                  </div>
                </div>

                <Separator />

                {/* Controparte */}
                <div>
                  <h4 className="text-sm font-semibold mb-1">
                    {direction === "ricevute" ? "Cedente" : "Cessionario"}
                  </h4>
                  <p className="text-sm">{getCounterpartName(selectedInvoice)}</p>
                  {getCounterpartPiva(selectedInvoice) && (
                    <p className="text-xs text-muted-foreground">
                      P.IVA: {getCounterpartPiva(selectedInvoice)}
                    </p>
                  )}
                </div>

                <Separator />

                {/* Importi */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-muted-foreground">Imponibile:</span>{" "}
                    {formatCurrency(selectedInvoice.imponibile_totale)}
                  </div>
                  <div>
                    <span className="text-muted-foreground">IVA:</span>{" "}
                    {formatCurrency(selectedInvoice.iva_totale)}
                  </div>
                  <div className="col-span-2">
                    <span className="text-muted-foreground">Totale:</span>{" "}
                    <strong>
                      {formatCurrency(selectedInvoice.importo_totale)}
                    </strong>
                  </div>
                </div>

                <Separator />

                {/* Pagamento */}
                <div className="text-sm">
                  <h4 className="font-semibold mb-1">Pagamento</h4>
                  {selectedInvoice.modalita_pagamento && (
                    <p>Modalita: {selectedInvoice.modalita_pagamento}</p>
                  )}
                  <p>
                    Scadenza:{" "}
                    {formatDate(selectedInvoice.data_scadenza_pagamento)}
                  </p>
                  {selectedInvoice.iban_pagamento && (
                    <p>IBAN: {selectedInvoice.iban_pagamento}</p>
                  )}
                </div>

                <Separator />

                {/* Allegati & Azioni */}
                <div className="flex flex-wrap gap-2">
                  {selectedInvoice.xml_file_nome && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        handleDownloadXml(
                          selectedInvoice.id,
                          selectedInvoice.xml_file_nome!
                        )
                      }
                    >
                      <Download className="h-3 w-3 mr-1" /> XML
                    </Button>
                  )}
                  {selectedInvoice.xml_file_nome && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        handleDownloadPdf(
                          selectedInvoice.id,
                          selectedInvoice.xml_file_nome!
                        )
                      }
                    >
                      <Download className="h-3 w-3 mr-1" /> PDF
                    </Button>
                  )}
                  {selectedInvoice.stato === "importata" && (
                    <>
                      <Button
                        size="sm"
                        onClick={() => handleElaborate(selectedInvoice.id)}
                      >
                        <CheckCircle className="h-3 w-3 mr-1" /> Elabora
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-muted-foreground"
                        onClick={() => handleIgnore(selectedInvoice.id)}
                      >
                        <XCircle className="h-3 w-3 mr-1" /> Ignora
                      </Button>
                    </>
                  )}
                </div>

                {selectedInvoice.errore_dettaglio && (
                  <p className="text-xs text-destructive mt-2">
                    {selectedInvoice.errore_dettaglio}
                  </p>
                )}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
