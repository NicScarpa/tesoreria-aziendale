"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Search, X, Check, ReceiptText, RefreshCw, Download, Bug,
  ChevronLeft, ChevronRight, List, Info, Calendar, Eye, EyeOff,
  ArrowUpDown, FileText, Edit2, Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { listCorrispettivi, downloadCorrispettivoRaw, adeSyncCorrispettivi } from "@/lib/api/integrations";
import type { ReceiptImport } from "@/types/integration";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

/* ---------- helpers ---------- */

function formatCurrency(value: number | null): string {
  if (value === null) return "\u2014";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDateDDMMYYYY(d: string | null): string {
  if (!d) return "\u2014";
  const dt = new Date(d);
  const dd = String(dt.getDate()).padStart(2, "0");
  const mm = String(dt.getMonth() + 1).padStart(2, "0");
  const yyyy = dt.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function yearStartISO(): string {
  const y = new Date().getFullYear();
  return `${y}-01-01`;
}

/* ---------- main component ---------- */

export default function CorrispettiviPage() {
  const [items, setItems] = useState<ReceiptImport[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Filters
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  // Sync dialog
  const [showSync, setShowSync] = useState(false);
  const [syncFrom, setSyncFrom] = useState(yearStartISO());
  const [syncTo, setSyncTo] = useState(todayISO());
  const [debug, setDebug] = useState(false);

  // Device toggle
  const [showDevices, setShowDevices] = useState(false);

  // Sort
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  // Detail panel
  const [selectedReceipt, setSelectedReceipt] = useState<ReceiptImport | null>(null);

  // Date popover
  const [datePopoverOpen, setDatePopoverOpen] = useState(false);

  const hasActiveFilters = search !== "" || dateFrom !== "" || dateTo !== "" || statusFilter !== "all";

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const data = await listCorrispettivi(params);
      setItems(data.items);
      setTotal(data.total);
    } catch {
      toast.error("Errore nel caricamento dei corrispettivi");
    } finally {
      setLoading(false);
    }
  }, [page, dateFrom, dateTo]);

  useEffect(() => { loadData(); }, [loadData]);
  useEffect(() => { setPage(1); }, [dateFrom, dateTo]);

  const totalPages = Math.ceil(total / pageSize);

  const uniqueDevices = useMemo(() => {
    const ids = new Set<string>();
    items.forEach((r) => { if (r.device_id) ids.add(r.device_id); });
    return Array.from(ids);
  }, [items]);

  // Client-side filtering
  const filteredItems = useMemo(() => {
    let result = [...items];

    // Search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((r) =>
        (r.device_id && r.device_id.toLowerCase().includes(q)) ||
        (r.external_id && r.external_id.toLowerCase().includes(q))
      );
    }

    // Status
    if (statusFilter !== "all") {
      result = result.filter((r) => r.status === statusFilter);
    }

    // Sort by date
    result.sort((a, b) => {
      const da = new Date(a.business_date).getTime();
      const db = new Date(b.business_date).getTime();
      return sortDir === "desc" ? db - da : da - db;
    });

    return result;
  }, [items, search, statusFilter, sortDir]);

  const handleDownloadRaw = async (id: string, businessDate: string) => {
    try {
      const blob = await downloadCorrispettivoRaw(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `corrispettivo_${businessDate}.bin`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Errore nel download allegato");
    }
  };

  const handleSync = async () => {
    if (!syncFrom || !syncTo) {
      toast.error("Seleziona il range date");
      return;
    }
    const diffDays = Math.floor((new Date(syncTo).getTime() - new Date(syncFrom).getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays > 93) {
      toast.error("Periodo troppo lungo: per i corrispettivi AdE consente massimo ~3 mesi per richiesta.");
      return;
    }
    setSyncing(true);
    try {
      const res = await adeSyncCorrispettivi({ date_from: syncFrom, date_to: syncTo, debug });
      if ((res as any).pending) {
        const id = (res as any).external_request_id ? ` (ID ${(res as any).external_request_id})` : "";
        toast.success((res.message || "Richiesta corrispettivi inviata ad AdE.") + id);
      } else {
        toast.success(res.message || `Import completato: +${res.imported_new}, dup ${res.updated}, err ${res.failed}`);
      }
      setShowSync(false);
      loadData();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore nella sincronizzazione");
    } finally {
      setSyncing(false);
    }
  };

  const resetFilters = () => {
    setSearch("");
    setDateFrom("");
    setDateTo("");
    setStatusFilter("all");
  };

  if (loading && items.length === 0) {
    return (
      <div className="space-y-6">
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-0" style={{ fontFamily: "'Public Sans', sans-serif" }}>

      {/* Toggle dispositivi + Sync buttons */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Switch checked={showDevices} onCheckedChange={setShowDevices} />
          <span className="text-[13px] font-medium text-[#1a1a1a]">Mostra dispositivi</span>
          <Info className="h-3.5 w-3.5 text-[#817f7d]" />
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowSync(true)} className="rounded-lg text-[13px]">
            <RefreshCw className="h-4 w-4 mr-1.5" />
            Scarica
          </Button>
          <Button size="sm" onClick={() => setShowSync(true)} className="rounded-lg text-[13px] bg-[#6672ff] hover:bg-[#5560e6] text-white">
            <Download className="h-4 w-4 mr-1.5" />
            Aggiungi corrispettivo
          </Button>
        </div>
      </div>

      {/* Device badges row */}
      {showDevices && uniqueDevices.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4 p-3 bg-white border border-[#e5e4e3] rounded-lg">
          {uniqueDevices.map((d) => (
            <div key={d} className="flex items-center gap-1.5">
              <span
                className="inline-flex items-center px-3 py-1 text-[12px] font-medium rounded-full"
                style={{ backgroundColor: "#fddcdc", color: "#1a1a1a" }}
              >
                {d}
              </span>
              <span
                className="inline-flex items-center px-3 py-1 text-[12px] font-medium rounded-full"
                style={{ backgroundColor: "#e5e4e3", color: "#1a1a1a" }}
              >
                Non categorizzata
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Filter bar */}
      <div className="flex items-center gap-2 mb-3">
        <div className="relative flex-shrink-0">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#817f7d]" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Ricerca"
            className="pl-9 h-9 w-[200px] rounded-lg border-[#e5e4e3] text-[13px]"
          />
        </div>

        {/* Date filter popover */}
        <Popover open={datePopoverOpen} onOpenChange={setDatePopoverOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="h-9 rounded-lg border-[#e5e4e3] text-[13px] text-[#817f7d] gap-1.5">
              <Calendar className="h-4 w-4" />
              Data
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-3 space-y-2" align="start">
            <div className="space-y-1">
              <Label className="text-xs">Da</Label>
              <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="h-8 text-[13px]" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">A</Label>
              <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="h-8 text-[13px]" />
            </div>
            <Button size="sm" className="w-full h-7 text-xs" onClick={() => setDatePopoverOpen(false)}>Applica</Button>
          </PopoverContent>
        </Popover>

        {/* Status filter */}
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="h-9 w-[120px] rounded-lg border-[#e5e4e3] text-[13px] text-[#817f7d]">
            <SelectValue placeholder="Stato" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Stato</SelectItem>
            <SelectItem value="imported">Importato</SelectItem>
            <SelectItem value="error">Errore</SelectItem>
          </SelectContent>
        </Select>

        {/* Reset filters */}
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={resetFilters} className="h-9 px-2 text-[#817f7d]">
            <X className="h-4 w-4" />
          </Button>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Grid/list toggle (decorative) */}
        <Button variant="outline" size="sm" className="h-9 w-9 p-0 rounded-lg border-[#e5e4e3]">
          <List className="h-4 w-4 text-[#817f7d]" />
        </Button>
      </div>

      {/* Result count */}
      <div className="flex items-center gap-1.5 mb-2">
        <List className="h-3.5 w-3.5 text-[#817f7d]" />
        <span className="text-[13px] text-[#817f7d]">{total} risultati</span>
      </div>

      {filteredItems.length === 0 && items.length === 0 ? (
        <EmptyState
          icon={ReceiptText}
          title="Nessun corrispettivo"
          description="Avvia una sincronizzazione da Agenzia Entrate per popolare la lista"
          actionLabel="Sincronizza"
          onAction={() => setShowSync(true)}
        />
      ) : (
        <>
          <div className="rounded-lg border border-[#e5e4e3] overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[40px]" style={{ fontSize: "12px", fontWeight: 600, color: "#817f7d", textTransform: "uppercase", letterSpacing: "0.05em", padding: "10px 16px" }}>
                    <Checkbox />
                  </TableHead>
                  <TableHead
                    className="cursor-pointer select-none"
                    style={{ fontSize: "12px", fontWeight: 600, color: "#817f7d", textTransform: "uppercase", letterSpacing: "0.05em", padding: "10px 16px" }}
                    onClick={() => setSortDir((d) => d === "desc" ? "asc" : "desc")}
                  >
                    <span className="inline-flex items-center gap-1">
                      DATA
                      <ArrowUpDown className="h-3 w-3" />
                    </span>
                  </TableHead>
                  <TableHead style={{ fontSize: "12px", fontWeight: 600, color: "#817f7d", textTransform: "uppercase", letterSpacing: "0.05em", padding: "10px 16px" }}>
                    DESCRIZIONE
                  </TableHead>
                  <TableHead className="text-right" style={{ fontSize: "12px", fontWeight: 600, color: "#817f7d", textTransform: "uppercase", letterSpacing: "0.05em", padding: "10px 16px" }}>
                    IMPORTO
                  </TableHead>
                  <TableHead style={{ fontSize: "12px", fontWeight: 600, color: "#817f7d", textTransform: "uppercase", letterSpacing: "0.05em", padding: "10px 16px" }}>
                    CATEGORIA
                  </TableHead>
                  <TableHead style={{ fontSize: "12px", fontWeight: 600, color: "#817f7d", textTransform: "uppercase", letterSpacing: "0.05em", padding: "10px 16px" }}>
                    INCASSATO
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((r) => (
                  <TableRow
                    key={r.id}
                    className="cursor-pointer hover:bg-[#fafafa]"
                    onClick={() => setSelectedReceipt(r)}
                  >
                    <TableCell style={{ padding: "16px", fontSize: "13px", fontWeight: 500, color: "#1a1a1a" }} onClick={(e) => e.stopPropagation()}>
                      <Checkbox />
                    </TableCell>
                    <TableCell style={{ padding: "16px", fontSize: "13px", fontWeight: 500, color: "#1a1a1a" }}>
                      {formatDateDDMMYYYY(r.business_date)}
                    </TableCell>
                    <TableCell style={{ padding: "16px", fontSize: "13px", fontWeight: 500, color: "#1a1a1a" }}>
                      {r.device_id || ""}{r.device_id && r.external_id ? " - " : ""}{r.external_id || ""}
                    </TableCell>
                    <TableCell className="text-right" style={{ padding: "16px", fontSize: "13px", fontWeight: 500, color: "#1a1a1a" }}>
                      {formatCurrency(r.gross_total)}
                    </TableCell>
                    <TableCell style={{ padding: "16px" }}>
                      <span
                        className="inline-flex items-center px-2.5 py-0.5 text-[12px] font-medium rounded-full"
                        style={{ backgroundColor: "#e5e4e3", color: "#1a1a1a" }}
                      >
                        Non categorizzata
                      </span>
                    </TableCell>
                    <TableCell style={{ padding: "16px" }}>
                      <Check className="h-4 w-4" style={{ color: "#22c55e" }} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-[13px] text-[#817f7d]">
                {total} corrispettivi &middot; Pagina {page} di {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="rounded-lg"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="rounded-lg"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Detail Sheet (side panel) */}
      <Sheet open={!!selectedReceipt} onOpenChange={(open) => { if (!open) setSelectedReceipt(null); }}>
        <SheetContent className="w-[420px] sm:w-[460px] p-0 overflow-y-auto">
          {selectedReceipt && (
            <div className="flex flex-col h-full">
              {/* Sheet header */}
              <SheetHeader className="p-5 pb-3">
                <SheetTitle className="text-[15px] font-semibold text-[#1a1a1a]">
                  {selectedReceipt.device_id || "Corrispettivo"}
                </SheetTitle>
                <SheetDescription className="text-[22px] font-semibold text-[#1a1a1a] mt-1">
                  {formatCurrency(selectedReceipt.gross_total)}
                </SheetDescription>
                <div className="flex items-center gap-2 mt-3">
                  <Button variant="outline" size="sm" className="rounded-lg text-[13px] gap-1.5">
                    <Eye className="h-3.5 w-3.5" />
                    Anteprima
                  </Button>
                  <Button variant="outline" size="sm" className="rounded-lg text-[13px] gap-1.5">
                    <EyeOff className="h-3.5 w-3.5" />
                    Nascondi
                  </Button>
                </div>
              </SheetHeader>

              <Separator />

              {/* Tabs */}
              <Tabs defaultValue="documento" className="flex-1">
                <TabsList className="w-full justify-start rounded-none border-b bg-transparent px-5 h-auto py-0">
                  <TabsTrigger
                    value="documento"
                    className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#6672ff] data-[state=active]:text-[#1a1a1a] data-[state=active]:shadow-none text-[13px] font-medium px-3 py-2.5 text-[#817f7d]"
                  >
                    Documento
                  </TabsTrigger>
                  <TabsTrigger
                    value="incassi"
                    className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#6672ff] data-[state=active]:text-[#1a1a1a] data-[state=active]:shadow-none text-[13px] font-medium px-3 py-2.5 text-[#817f7d]"
                  >
                    Incassi
                  </TabsTrigger>
                </TabsList>

                {/* Documento tab */}
                <TabsContent value="documento" className="px-5 py-4 space-y-0 mt-0">
                  {/* Status badges */}
                  <div className="flex items-center gap-2 mb-5">
                    <span className="inline-flex items-center px-2.5 py-0.5 text-[12px] font-medium rounded-full bg-red-50 text-red-600 border border-red-200">
                      Passiva
                    </span>
                    <span className="inline-flex items-center px-2.5 py-0.5 text-[12px] font-medium rounded-full bg-green-50 text-green-600 border border-green-200">
                      Incassato
                    </span>
                  </div>

                  {/* Detail rows */}
                  <div className="space-y-4">
                    <DetailRow label="Tipo documento" value="Corrispettivo" />
                    <DetailRow label="Categoria">
                      <span
                        className="inline-flex items-center px-2.5 py-0.5 text-[12px] font-medium rounded-full"
                        style={{ backgroundColor: "#e5e4e3", color: "#1a1a1a" }}
                      >
                        Non categorizzata
                      </span>
                    </DetailRow>
                    <DetailRow label="Data documento" value={formatDateDDMMYYYY(selectedReceipt.business_date)} />
                    <DetailRow
                      label="Numero documento"
                      value={selectedReceipt.external_id || `W.${selectedReceipt.device_id || ""}`}
                    />
                    <DetailRow label="Nome cliente" value="" />
                    <DetailRow label="Identificativo cliente" value="" />
                    <DetailRow label="Importo IVA inclusa" value={formatCurrency(selectedReceipt.gross_total)} />
                    <DetailRow label="IVA" value={formatCurrency(selectedReceipt.vat_total)} />

                    <Separator />

                    <div className="flex items-center justify-between">
                      <span className="text-[13px] font-medium text-[#1a1a1a]">Allegati</span>
                      <button
                        className="text-[13px] text-[#6672ff] hover:underline cursor-pointer flex items-center gap-1"
                        onClick={() => {
                          if (selectedReceipt.raw_available) {
                            handleDownloadRaw(selectedReceipt.id, selectedReceipt.business_date);
                          }
                        }}
                      >
                        Carica allegati
                        <FileText className="h-3.5 w-3.5" />
                      </button>
                    </div>

                    <Separator />

                    <div>
                      <span className="text-[13px] font-medium text-[#1a1a1a]">Documenti collegati</span>
                    </div>

                    <Separator />

                    <div>
                      <span className="text-[13px] font-medium text-[#1a1a1a] block mb-2">Note</span>
                      <Textarea
                        placeholder=""
                        className="resize-none text-[13px] border-[#e5e4e3] rounded-lg min-h-[80px]"
                      />
                    </div>
                  </div>
                </TabsContent>

                {/* Incassi tab */}
                <TabsContent value="incassi" className="px-5 py-4 space-y-0 mt-0">
                  {/* Add deadline button */}
                  <div className="flex justify-end mb-4">
                    <Button variant="outline" size="sm" className="rounded-lg text-[13px] gap-1">
                      Aggiungi scadenza +
                    </Button>
                  </div>

                  {/* Scadenza card */}
                  <div className="border border-[#e5e4e3] rounded-lg p-4 space-y-4">
                    {/* Header with status */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] font-semibold text-[#1a1a1a]">Scadenza 1</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" className="h-7 rounded-lg text-[12px] gap-1 px-2">
                          <Edit2 className="h-3 w-3" />
                          Modifica
                        </Button>
                        <Button variant="outline" size="sm" className="h-7 rounded-lg text-[12px] gap-1 px-2 text-red-500 hover:text-red-600">
                          <Trash2 className="h-3 w-3" />
                          Rimuovi
                        </Button>
                      </div>
                    </div>

                    {/* Status */}
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] text-[#817f7d]">Stato</span>
                      <span className="inline-flex items-center px-2.5 py-0.5 text-[12px] font-medium rounded-full bg-green-50 text-green-600 border border-green-200">
                        Incassato
                      </span>
                    </div>

                    <Separator />

                    {/* Movimenti riconciliati */}
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] text-[#817f7d]">Movimenti riconciliati</span>
                      <span className="text-[13px] text-[#817f7d] italic">Nessun movimento riconciliato</span>
                    </div>

                    <Separator />

                    {/* Importo */}
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] text-[#817f7d]">Importo</span>
                      <span className="text-[13px] font-medium text-[#1a1a1a]">{formatCurrency(selectedReceipt.gross_total)}</span>
                    </div>

                    {/* Scadenza */}
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] text-[#817f7d]">Scadenza</span>
                      <span className="text-[13px] font-medium text-[#1a1a1a]">{formatDateDDMMYYYY(selectedReceipt.business_date)}</span>
                    </div>

                    {/* Data di pagamento originale */}
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] text-[#817f7d]">Data di pagamento originale</span>
                      <span className="text-[13px] font-medium text-[#1a1a1a]">{formatDateDDMMYYYY(selectedReceipt.business_date)}</span>
                    </div>

                    <Separator />

                    {/* Modalita di pagamento */}
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] text-[#817f7d]">Modalit&agrave; di pagamento</span>
                      <span className="text-[13px] font-medium text-[#1a1a1a]">Contanti</span>
                    </div>

                    {/* Conto in fattura */}
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] text-[#817f7d]">Conto in fattura</span>
                      <span className="text-[13px] text-[#817f7d]">&mdash;</span>
                    </div>

                    {/* Conto di pagamento */}
                    <div className="flex items-center justify-between">
                      <span className="text-[13px] text-[#817f7d]">Conto di pagamento</span>
                      <span className="text-[13px] font-medium text-[#1a1a1a]">Non assegnato</span>
                    </div>

                    <Separator />

                    {/* Note */}
                    <div className="flex items-center justify-between cursor-pointer">
                      <span className="text-[13px] text-[#817f7d]">Note</span>
                      <ChevronRight className="h-3.5 w-3.5 text-[#817f7d]" />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Sync Dialog */}
      <Dialog open={showSync} onOpenChange={setShowSync}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Sincronizza Corrispettivi</DialogTitle>
            <DialogDescription>Scarica e importa i corrispettivi dal portale AdE.</DialogDescription>
          </DialogHeader>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label>Data da</Label>
              <Input type="date" value={syncFrom} onChange={(e) => setSyncFrom(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label>Data a</Label>
              <Input type="date" value={syncTo} onChange={(e) => setSyncTo(e.target.value)} />
            </div>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <Checkbox checked={debug} onCheckedChange={(v) => setDebug(Boolean(v))} />
            <span className="text-sm flex items-center gap-1">
              <Bug className="h-4 w-4" /> Debug (salva screenshot/HTML)
            </span>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSync(false)} disabled={syncing}>Annulla</Button>
            <Button onClick={handleSync} disabled={syncing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? "animate-spin" : ""}`} />
              Avvia
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/* ---------- Detail Row helper ---------- */

function DetailRow({
  label,
  value,
  children,
}: {
  label: string;
  value?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[13px] text-[#817f7d]">{label}</span>
      {children || <span className="text-[13px] font-medium text-[#1a1a1a]">{value || "\u2014"}</span>}
    </div>
  );
}
