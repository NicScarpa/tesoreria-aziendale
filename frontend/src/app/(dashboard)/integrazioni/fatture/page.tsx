"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { FileText, Upload, Search, ChevronLeft, ChevronRight, Download, CheckCircle, XCircle, Eye, Scale, RefreshCw, Bug } from "lucide-react";
import { toast } from "sonner";
import {
  listInvoices,
  uploadInvoice,
  elaborateInvoice,
  ignoreInvoice,
  downloadXml,
  elaborateBatch,
  uploadBatch,
  listBatches,
  adeSyncInvoices,
} from "@/lib/api/integrations";
import type { InvoiceImport, InvoiceImportBatch } from "@/types/integration";
import {
  INVOICE_DOC_TYPE_LABELS,
  INVOICE_DOC_TYPE_COLORS,
  INVOICE_STATUS_LABELS,
  INVOICE_STATUS_COLORS,
  INVOICE_BATCH_STATUS_LABELS,
} from "@/types/integration";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

function formatCurrency(value: number | null): string {
  if (value === null) return "\u2014";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(d: string | null): string {
  if (!d) return "\u2014";
  return new Date(d).toLocaleDateString("it-IT");
}

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function yearStartISO(): string {
  const y = new Date().getFullYear();
  return `${y}-01-01`;
}

export default function FatturePage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const batchInputRef = useRef<HTMLInputElement>(null);
  const [invoices, setInvoices] = useState<InvoiceImport[]>([]);
  const [batches, setBatches] = useState<InvoiceImportBatch[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [tab, setTab] = useState("fatture");

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Filters
  const [search, setSearch] = useState("");
  const [tipoFilter, setTipoFilter] = useState("all");
  const [statoFilter, setStatoFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // AdE import dialog
  const [showAdeImport, setShowAdeImport] = useState(false);
  const [adeFrom, setAdeFrom] = useState(yearStartISO());
  const [adeTo, setAdeTo] = useState(todayISO());
  const [adeIssued, setAdeIssued] = useState(true);
  const [adeReceived, setAdeReceived] = useState(true);
  const [adeDebug, setAdeDebug] = useState(false);
  const [adeImporting, setAdeImporting] = useState(false);

  // Detail sheet
  const [selectedInvoice, setSelectedInvoice] = useState<InvoiceImport | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (search) params.search = search;
      if (tipoFilter !== "all") params.tipo_documento = tipoFilter;
      if (statoFilter !== "all") params.stato = statoFilter;
      if (dateFrom) params.data_da = dateFrom;
      if (dateTo) params.data_a = dateTo;

      const [invoiceData, batchData] = await Promise.all([
        listInvoices(params),
        listBatches(),
      ]);
      setInvoices(invoiceData.items);
      setTotal(invoiceData.total);
      setBatches(batchData.items);
    } catch {
      toast.error("Errore nel caricamento delle fatture");
    } finally {
      setLoading(false);
    }
  }, [page, search, tipoFilter, statoFilter, dateFrom, dateTo]);

  useEffect(() => { loadData(); }, [loadData]);
  useEffect(() => { setPage(1); }, [search, tipoFilter, statoFilter, dateFrom, dateTo]);

  const totalPages = Math.ceil(total / pageSize);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadInvoice(file);
      toast.success("Fattura importata con successo");
      loadData();
    } catch {
      toast.error("Errore nell'importazione");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleBatchUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      await uploadBatch(Array.from(files));
      toast.success("Batch importato");
      loadData();
    } catch {
      toast.error("Errore nel batch import");
    } finally {
      setUploading(false);
      if (batchInputRef.current) batchInputRef.current.value = "";
    }
  };

  const handleElaborate = async (id: string) => {
    try {
      const result = await elaborateInvoice(id);
      toast.success(result.message || "Fattura elaborata");
      loadData();
      setSelectedInvoice(null);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore nell'elaborazione");
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

  const handleElaborateAll = async () => {
    try {
      const result = await elaborateBatch({ filter_stato: "importata" });
      toast.success(`Elaborate ${result.total} fatture`);
      loadData();
    } catch {
      toast.error("Errore nell'elaborazione batch");
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

  const handleAdeImport = async () => {
    if (!adeFrom || !adeTo) {
      toast.error("Seleziona il range date");
      return;
    }
    if (!(adeIssued || adeReceived)) {
      toast.error("Seleziona almeno Emesse o Ricevute");
      return;
    }
    setAdeImporting(true);
    try {
      if (adeIssued) {
        const r = await adeSyncInvoices({ date_from: adeFrom, date_to: adeTo, direction: "issued", debug: adeDebug });
        toast.success(r.message || `Emesse: +${r.imported_new}, dup ${r.updated}, err ${r.failed}`);
      }
      if (adeReceived) {
        const r = await adeSyncInvoices({ date_from: adeFrom, date_to: adeTo, direction: "received", debug: adeDebug });
        toast.success(r.message || `Ricevute: +${r.imported_new}, dup ${r.updated}, err ${r.failed}`);
      }
      setShowAdeImport(false);
      loadData();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore import da AdE");
    } finally {
      setAdeImporting(false);
    }
  };

  if (loading && invoices.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title="Fatture Elettroniche" description="Importa e gestisci fatture FatturaPA" />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Fatture Elettroniche"
        description="Importa e gestisci fatture FatturaPA"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" disabled={adeImporting} onClick={() => setShowAdeImport(true)}>
              <Scale className="h-4 w-4 mr-2" />
              Importa da AdE
            </Button>
            <Button variant="outline" disabled={uploading} onClick={() => batchInputRef.current?.click()}>
              <Upload className="h-4 w-4 mr-2" />
              Carica Multiple
            </Button>
            <Button disabled={uploading} onClick={() => fileInputRef.current?.click()}>
              <Upload className="h-4 w-4 mr-2" />
              Carica XML
            </Button>
            <Button variant="outline" onClick={handleElaborateAll}>
              <CheckCircle className="h-4 w-4 mr-2" />
              Elabora Tutte
            </Button>
            <input ref={fileInputRef} type="file" accept=".xml,.p7m" className="hidden" onChange={handleUpload} />
            <input ref={batchInputRef} type="file" accept=".xml,.p7m,.zip" multiple className="hidden" onChange={handleBatchUpload} />
          </div>
        }
      />

      <Dialog open={showAdeImport} onOpenChange={setShowAdeImport}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Importa Fatture da Agenzia Entrate</DialogTitle>
            <DialogDescription>Il backend apre un browser headless e scarica i file dal portale.</DialogDescription>
          </DialogHeader>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label>Data da</Label>
              <Input type="date" value={adeFrom} onChange={(e) => setAdeFrom(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label>Data a</Label>
              <Input type="date" value={adeTo} onChange={(e) => setAdeTo(e.target.value)} />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Checkbox checked={adeIssued} onCheckedChange={(v) => setAdeIssued(Boolean(v))} />
              <span className="text-sm">Fatture emesse</span>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox checked={adeReceived} onCheckedChange={(v) => setAdeReceived(Boolean(v))} />
              <span className="text-sm">Fatture ricevute</span>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <Checkbox checked={adeDebug} onCheckedChange={(v) => setAdeDebug(Boolean(v))} />
              <span className="text-sm flex items-center gap-1">
                <Bug className="h-4 w-4" /> Debug (salva screenshot/HTML)
              </span>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAdeImport(false)} disabled={adeImporting}>Annulla</Button>
            <Button onClick={handleAdeImport} disabled={adeImporting}>
              <RefreshCw className={`h-4 w-4 mr-2 ${adeImporting ? "animate-spin" : ""}`} />
              Avvia
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="fatture">Fatture ({total})</TabsTrigger>
          <TabsTrigger value="batch">Batch ({batches.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="fatture" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Cerca per numero, cedente..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
            </div>
            <Select value={tipoFilter} onValueChange={setTipoFilter}>
              <SelectTrigger className="w-[160px]"><SelectValue placeholder="Tipo" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti i tipi</SelectItem>
                {Object.entries(INVOICE_DOC_TYPE_LABELS).map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={statoFilter} onValueChange={setStatoFilter}>
              <SelectTrigger className="w-[160px]"><SelectValue placeholder="Stato" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tutti gli stati</SelectItem>
                {Object.entries(INVOICE_STATUS_LABELS).map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}
              </SelectContent>
            </Select>
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="w-[150px]" />
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="w-[150px]" />
          </div>

          {/* Table */}
          {invoices.length === 0 ? (
            <EmptyState icon={FileText} title="Nessuna fattura" description="Importa la tua prima fattura elettronica" actionLabel="Carica XML" onAction={() => fileInputRef.current?.click()} />
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tipo</TableHead>
                      <TableHead>Numero</TableHead>
                      <TableHead>Data</TableHead>
                      <TableHead>Controparte</TableHead>
                      <TableHead className="text-right">Importo</TableHead>
                      <TableHead>Stato</TableHead>
                      <TableHead />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices.map((inv) => (
                      <TableRow key={inv.id} className="cursor-pointer" onClick={() => setSelectedInvoice(inv)}>
                        <TableCell>
                          <Badge className={INVOICE_DOC_TYPE_COLORS[inv.tipo_documento]}>
                            {INVOICE_DOC_TYPE_LABELS[inv.tipo_documento]}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-medium text-sm">{inv.numero_fattura || "\u2014"}</TableCell>
                        <TableCell className="text-sm">{formatDate(inv.data_fattura)}</TableCell>
                        <TableCell>
                          <p className="text-sm">{inv.cedente_denominazione || "\u2014"}</p>
                          {inv.cedente_piva && <p className="text-xs text-muted-foreground">P.IVA {inv.cedente_piva}</p>}
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm">{formatCurrency(inv.importo_totale)}</TableCell>
                        <TableCell>
                          <Badge className={INVOICE_STATUS_COLORS[inv.stato]}>
                            {INVOICE_STATUS_LABELS[inv.stato]}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); setSelectedInvoice(inv); }}>
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
                  <p className="text-sm text-muted-foreground">{total} fatture &middot; Pagina {page} di {totalPages}</p>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft className="h-4 w-4" /></Button>
                    <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}><ChevronRight className="h-4 w-4" /></Button>
                  </div>
                </div>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="batch" className="space-y-4">
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data Import</TableHead>
                  <TableHead>Fonte</TableHead>
                  <TableHead>Totale</TableHead>
                  <TableHead>Importate</TableHead>
                  <TableHead>Errori</TableHead>
                  <TableHead>Duplicate</TableHead>
                  <TableHead>Stato</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {batches.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell className="text-sm">{formatDate(b.data_import)}</TableCell>
                    <TableCell className="text-sm">{b.fonte}</TableCell>
                    <TableCell className="text-sm">{b.totale_fatture}</TableCell>
                    <TableCell className="text-sm">{b.fatture_importate}</TableCell>
                    <TableCell className="text-sm text-destructive">{b.fatture_errore}</TableCell>
                    <TableCell className="text-sm">{b.fatture_duplicate}</TableCell>
                    <TableCell className="text-sm">{INVOICE_BATCH_STATUS_LABELS[b.stato] || b.stato}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </TabsContent>
      </Tabs>

      {/* Invoice Detail Sheet */}
      <Sheet open={!!selectedInvoice} onOpenChange={() => setSelectedInvoice(null)}>
        <SheetContent className="w-[500px] overflow-y-auto">
          {selectedInvoice && (
            <>
              <SheetHeader>
                <SheetTitle>Fattura {selectedInvoice.numero_fattura}</SheetTitle>
                <SheetDescription>
                  <Badge className={INVOICE_DOC_TYPE_COLORS[selectedInvoice.tipo_documento]}>
                    {INVOICE_DOC_TYPE_LABELS[selectedInvoice.tipo_documento]}
                  </Badge>
                  {" "}
                  <Badge className={INVOICE_STATUS_COLORS[selectedInvoice.stato]}>
                    {INVOICE_STATUS_LABELS[selectedInvoice.stato]}
                  </Badge>
                </SheetDescription>
              </SheetHeader>

              <div className="mt-4 space-y-4">
                <div>
                  <h4 className="text-sm font-semibold mb-1">Cedente</h4>
                  <p className="text-sm">{selectedInvoice.cedente_denominazione}</p>
                  {selectedInvoice.cedente_piva && <p className="text-xs text-muted-foreground">P.IVA: {selectedInvoice.cedente_piva}</p>}
                </div>

                <Separator />

                <div>
                  <h4 className="text-sm font-semibold mb-1">Cessionario</h4>
                  <p className="text-sm">{selectedInvoice.cessionario_denominazione}</p>
                  {selectedInvoice.cessionario_piva && <p className="text-xs text-muted-foreground">P.IVA: {selectedInvoice.cessionario_piva}</p>}
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div><span className="text-muted-foreground">Data:</span> {formatDate(selectedInvoice.data_fattura)}</div>
                  <div><span className="text-muted-foreground">Valuta:</span> {selectedInvoice.valuta}</div>
                  <div><span className="text-muted-foreground">Imponibile:</span> {formatCurrency(selectedInvoice.imponibile_totale)}</div>
                  <div><span className="text-muted-foreground">IVA:</span> {formatCurrency(selectedInvoice.iva_totale)}</div>
                  <div className="col-span-2"><span className="text-muted-foreground">Totale:</span> <strong>{formatCurrency(selectedInvoice.importo_totale)}</strong></div>
                </div>

                <Separator />

                <div className="text-sm">
                  <h4 className="font-semibold mb-1">Pagamento</h4>
                  <p>Scadenza: {formatDate(selectedInvoice.data_scadenza_pagamento)}</p>
                  {selectedInvoice.iban_pagamento && <p>IBAN: {selectedInvoice.iban_pagamento}</p>}
                </div>

                <Separator />

                {/* Actions */}
                <div className="flex gap-2">
                  {selectedInvoice.xml_file_nome && (
                    <Button size="sm" variant="outline" onClick={() => handleDownloadXml(selectedInvoice.id, selectedInvoice.xml_file_nome!)}>
                      <Download className="h-3 w-3 mr-1" /> XML
                    </Button>
                  )}
                  {selectedInvoice.stato === "importata" && (
                    <>
                      <Button size="sm" onClick={() => handleElaborate(selectedInvoice.id)}>
                        <CheckCircle className="h-3 w-3 mr-1" /> Elabora
                      </Button>
                      <Button size="sm" variant="ghost" className="text-muted-foreground" onClick={() => handleIgnore(selectedInvoice.id)}>
                        <XCircle className="h-3 w-3 mr-1" /> Ignora
                      </Button>
                    </>
                  )}
                </div>

                {selectedInvoice.errore_dettaglio && (
                  <p className="text-xs text-destructive mt-2">{selectedInvoice.errore_dettaglio}</p>
                )}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
