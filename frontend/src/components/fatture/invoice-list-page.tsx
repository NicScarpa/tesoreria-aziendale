"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  FileText,
  Search,
  ChevronLeft,
  ChevronRight,
  Download,
  Eye,
  EyeOff,
  Calendar,
  List,
  ArrowUpDown,
  X,
  Check,
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
} from "@/types/integration";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
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
} from "@/components/ui/sheet";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

/* ---------- helpers ---------- */

function formatCurrency(value: number | null): string {
  if (value === null) return "\u2014";
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

function formatCurrencyShort(value: number | null): string {
  if (value === null) return "\u2014";
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(d: string | null): string {
  if (!d) return "\u2014";
  const dt = new Date(d);
  return dt.toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** Friendly doc-type label for table subtitle */
function docTypeShortLabel(tipo: string): string {
  const map: Record<string, string> = {
    fattura_vendita: "Fattura",
    fattura_acquisto: "Fattura",
    nota_credito_vendita: "Nota di credito",
    nota_credito_acquisto: "Nota di credito",
    autofattura: "Autofattura",
  };
  return map[tipo] ?? "Fattura";
}

/** Color for the small FileText icon based on doc type */
function docTypeIconColor(tipo: string): string {
  const map: Record<string, string> = {
    fattura_vendita: "#8cddba",
    fattura_acquisto: "#c0c8ff",
    nota_credito_vendita: "#ffd98c",
    nota_credito_acquisto: "#ffe6b2",
    autofattura: "#c8b9df",
  };
  return map[tipo] ?? "#c0c8ff";
}

/* ---------- constants ---------- */

const TABLE_HEAD_STYLE =
  "text-[12px] font-semibold text-[#817f7d] uppercase tracking-[0.05em] px-4 py-2.5";

/* ---------- component ---------- */

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
  // suppress unused-var lint for props used by callers
  void title;
  void description;

  const [items, setItems] = useState<InvoiceImport[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Sub-tab
  const [activeSubTab, setActiveSubTab] = useState<"tutte" | "da_pagare">(
    "tutte"
  );

  // Filters
  const [search, setSearch] = useState("");
  const [statoFilter, setStatoFilter] = useState("all");
  const [tipoDocFilter, setTipoDocFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Sort
  const [sortByConsegna, setSortByConsegna] = useState<"asc" | "desc">("desc");

  // Detail sheet
  const [selectedInvoice, setSelectedInvoice] =
    useState<InvoiceImport | null>(null);

  const hasActiveFilters =
    search !== "" ||
    statoFilter !== "all" ||
    tipoDocFilter !== "all" ||
    dateFrom !== "" ||
    dateTo !== "";

  const resetFilters = () => {
    setSearch("");
    setStatoFilter("all");
    setTipoDocFilter("all");
    setDateFrom("");
    setDateTo("");
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (search) params.search = search;
      if (activeSubTab === "da_pagare") {
        params.stato = "importata";
      } else if (statoFilter !== "all") {
        params.stato = statoFilter;
      }
      if (tipoDocFilter !== "all") params.tipo_documento = tipoDocFilter;
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
  }, [
    page,
    search,
    statoFilter,
    tipoDocFilter,
    dateFrom,
    dateTo,
    direction,
    activeSubTab,
  ]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    setPage(1);
  }, [search, statoFilter, tipoDocFilter, dateFrom, dateTo, activeSubTab]);

  const totalPages = Math.ceil(total / pageSize);

  // Summary for "Da pagare" sub-tab
  const daPagareSummary = useMemo(() => {
    if (activeSubTab !== "da_pagare") return null;
    const totaleImporto = items.reduce(
      (acc, inv) => acc + (inv.importo_totale ?? 0),
      0
    );
    return { totaleImporto, count: total };
  }, [activeSubTab, items, total]);

  /* --- actions --- */

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

  const getCounterpartName = (inv: InvoiceImport) =>
    direction === "ricevute"
      ? inv.cedente_denominazione
      : inv.cessionario_denominazione;

  const getCounterpartPiva = (inv: InvoiceImport) =>
    direction === "ricevute" ? inv.cedente_piva : inv.cessionario_piva;

  const sortedItems = useMemo(() => {
    if (direction === "emesse") return items;
    return [...items].sort((a, b) => {
      const da = new Date(a.data_importazione).getTime();
      const db = new Date(b.data_importazione).getTime();
      return sortByConsegna === "desc" ? db - da : da - db;
    });
  }, [items, sortByConsegna, direction]);

  /* --- loading state --- */

  if (loading && items.length === 0) {
    return <LoadingState />;
  }

  /* --- render --- */

  return (
    <div className="space-y-4">
      {/* Sub-tab pills */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1">
          <button
            className={cn(
              "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
              activeSubTab === "tutte"
                ? "bg-[#f2f2f2] text-[#1a1a1a]"
                : "text-[#817f7d] hover:text-[#1a1a1a]"
            )}
            onClick={() => setActiveSubTab("tutte")}
          >
            Tutte
          </button>
          <button
            className={cn(
              "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
              activeSubTab === "da_pagare"
                ? "bg-[#f2f2f2] text-[#1a1a1a]"
                : "text-[#817f7d] hover:text-[#1a1a1a]"
            )}
            onClick={() => setActiveSubTab("da_pagare")}
          >
            {direction === "ricevute" ? "Da pagare" : "Da incassare"}
          </button>
        </div>
      </div>

      {/* Filters row 1 */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <div className="relative min-w-[180px] max-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#817f7d]" />
          <Input
            placeholder="Ricerca"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-9 rounded-lg border-[#e5e4e3] text-[13px]"
          />
        </div>

        {/* Date Popover */}
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className={cn(
                "h-9 gap-1.5 rounded-lg border-[#e5e4e3] text-[13px] font-medium",
                (dateFrom || dateTo)
                  ? "text-[#1a1a1a]"
                  : "text-[#817f7d]"
              )}
            >
              <Calendar className="h-3.5 w-3.5" />
              Data documento
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-3 space-y-2" align="start">
            <div className="space-y-1">
              <label className="text-xs font-medium text-[#817f7d]">Da</label>
              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="h-8 text-[13px]"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-[#817f7d]">A</label>
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="h-8 text-[13px]"
              />
            </div>
          </PopoverContent>
        </Popover>

        {/* Stato */}
        <Select value={statoFilter} onValueChange={setStatoFilter}>
          <SelectTrigger className="w-[150px] h-9 rounded-lg border-[#e5e4e3] text-[13px]">
            <SelectValue placeholder="Stato" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Stato</SelectItem>
            <SelectItem value="importata">Da pagare</SelectItem>
            <SelectItem value="scadenza_creata">Pagato</SelectItem>
            <SelectItem value="elaborata">Parzialmente pagato</SelectItem>
          </SelectContent>
        </Select>

        {/* Reset */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            className="h-9 px-2 text-[#817f7d] hover:text-[#1a1a1a]"
            onClick={resetFilters}
          >
            <X className="h-4 w-4" />
          </Button>
        )}

        {/* view toggle placeholder */}
        <div className="ml-auto flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-9 w-9 p-0 text-[#817f7d]"
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Filters row 2 */}
      <div className="flex flex-wrap items-center gap-2">
        <Select value="all" onValueChange={() => {}}>
          <SelectTrigger className="w-[150px] h-9 rounded-lg border-[#e5e4e3] text-[13px]">
            <SelectValue placeholder="Categoria" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Categoria</SelectItem>
          </SelectContent>
        </Select>

        <Select value={tipoDocFilter} onValueChange={setTipoDocFilter}>
          <SelectTrigger className="w-[180px] h-9 rounded-lg border-[#e5e4e3] text-[13px]">
            <SelectValue placeholder="Tipo documento" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tipo documento</SelectItem>
            <SelectItem value="fattura_acquisto">Fattura</SelectItem>
            <SelectItem value="nota_credito_acquisto">
              Nota di credito
            </SelectItem>
            <SelectItem value="nota_credito_vendita">
              Nota di debito
            </SelectItem>
            <SelectItem value="autofattura">Autofattura</SelectItem>
            <SelectItem value="fattura_vendita">Parcella</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Results count + summary */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-[13px] text-[#817f7d]">
          <List className="h-3.5 w-3.5" />
          <span>{total} risultati</span>
        </div>
        {daPagareSummary && (
          <div className="flex items-center gap-4 ml-auto text-[13px]">
            <span className="text-[#817f7d]">
              Fatture totali: <span className="font-medium text-[#1a1a1a]">{daPagareSummary.count}</span>
            </span>
            <span className="text-[#817f7d]">
              Importo totale:{" "}
              <span className="font-medium text-[#1a1a1a]">
                {formatCurrencyShort(daPagareSummary.totaleImporto)}
              </span>
            </span>
          </div>
        )}
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
          <div className="rounded-lg border border-[#e5e4e3] bg-white">
            <Table>
              <TableHeader>
                <TableRow className="border-b border-[#e5e4e3] hover:bg-transparent">
                  <TableHead className={cn(TABLE_HEAD_STYLE, "w-[40px]")}>
                    <Checkbox />
                  </TableHead>
                  <TableHead className={cn(TABLE_HEAD_STYLE, "w-[28px]")} />
                  <TableHead className={TABLE_HEAD_STYLE}>
                    Numero documento
                  </TableHead>
                  <TableHead className={TABLE_HEAD_STYLE}>
                    Descrizione
                  </TableHead>
                  <TableHead className={TABLE_HEAD_STYLE}>
                    Data documento
                  </TableHead>
                  {direction === "ricevute" && (
                    <TableHead className={TABLE_HEAD_STYLE}>
                      <button
                        className="flex items-center gap-1 hover:text-[#1a1a1a] transition-colors"
                        onClick={() =>
                          setSortByConsegna((s) =>
                            s === "desc" ? "asc" : "desc"
                          )
                        }
                      >
                        Data di consegna
                        <ArrowUpDown className="h-3 w-3" />
                      </button>
                    </TableHead>
                  )}
                  <TableHead className={cn(TABLE_HEAD_STYLE, "text-right")}>
                    Importo
                  </TableHead>
                  <TableHead className={TABLE_HEAD_STYLE}>Categoria</TableHead>
                  <TableHead className={cn(TABLE_HEAD_STYLE, "w-[70px]")}>
                    {direction === "ricevute" ? "Pagata" : "Incassata"}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedItems.map((inv) => (
                  <TableRow
                    key={inv.id}
                    className="cursor-pointer border-b border-[#e5e4e3] hover:bg-[#fafafa]"
                    onClick={() => setSelectedInvoice(inv)}
                  >
                    {/* Checkbox */}
                    <TableCell className="px-4 py-3 w-[40px]">
                      <Checkbox
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>

                    {/* File icon */}
                    <TableCell className="px-1 py-3 w-[28px]">
                      <FileText
                        className="h-4 w-4"
                        style={{ color: docTypeIconColor(inv.tipo_documento) }}
                      />
                    </TableCell>

                    {/* Numero documento */}
                    <TableCell className="px-4 py-3">
                      <p className="text-[13px] font-medium text-[#1a1a1a] leading-tight">
                        {inv.numero_fattura || "\u2014"}
                      </p>
                      <p className="text-[11px] text-[#817f7d] leading-tight mt-0.5">
                        {docTypeShortLabel(inv.tipo_documento)}
                      </p>
                    </TableCell>

                    {/* Descrizione (controparte) */}
                    <TableCell className="px-4 py-3 text-[13px] text-[#1a1a1a]">
                      {getCounterpartName(inv) || "\u2014"}
                    </TableCell>

                    {/* Data documento */}
                    <TableCell className="px-4 py-3 text-[13px] text-[#1a1a1a]">
                      {formatDate(inv.data_fattura)}
                    </TableCell>

                    {/* Data di consegna (solo ricevute) */}
                    {direction === "ricevute" && (
                      <TableCell className="px-4 py-3 text-[13px] text-[#1a1a1a]">
                        {formatDate(inv.data_importazione)}
                      </TableCell>
                    )}

                    {/* Importo */}
                    <TableCell className="px-4 py-3 text-right">
                      <p className="text-[13px] font-medium text-[#1a1a1a] leading-tight">
                        {formatCurrency(inv.importo_totale)}
                      </p>
                      {inv.imponibile_totale !== null && (
                        <p className="text-[11px] text-[#817f7d] leading-tight mt-0.5">
                          netto {formatCurrency(inv.imponibile_totale)}
                        </p>
                      )}
                    </TableCell>

                    {/* Categoria */}
                    <TableCell className="px-4 py-3">
                      <Badge className="bg-[#e5e4e3] text-[#1a1a1a] text-[11px] font-medium rounded-full px-2.5 py-0.5 hover:bg-[#e5e4e3]">
                        Non categorizzata
                      </Badge>
                    </TableCell>

                    {/* Pagata/Incassata checkmark */}
                    <TableCell className="px-4 py-3 w-[70px]">
                      {inv.stato === "scadenza_creata" && (
                        <Check className="h-5 w-5 text-[#22c55e]" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-[13px] text-[#817f7d]">
                Pagina {page} di {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 w-8 p-0 rounded-lg border-[#e5e4e3]"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 w-8 p-0 rounded-lg border-[#e5e4e3]"
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
        <SheetContent className="w-[480px] sm:max-w-[480px] overflow-y-auto p-0">
          {selectedInvoice && (
            <DetailPanel
              invoice={selectedInvoice}
              direction={direction}
              getCounterpartName={getCounterpartName}
              getCounterpartPiva={getCounterpartPiva}
              onElaborate={handleElaborate}
              onIgnore={handleIgnore}
              onDownloadXml={handleDownloadXml}
              onDownloadPdf={handleDownloadPdf}
            />
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

/* ================================================================
   Detail Panel (Sheet content)
   ================================================================ */

interface DetailPanelProps {
  invoice: InvoiceImport;
  direction: "ricevute" | "emesse";
  getCounterpartName: (inv: InvoiceImport) => string | null;
  getCounterpartPiva: (inv: InvoiceImport) => string | null;
  onElaborate: (id: string) => void;
  onIgnore: (id: string) => void;
  onDownloadXml: (id: string, nome: string) => void;
  onDownloadPdf: (id: string, nome: string) => void;
}

function DetailPanel({
  invoice,
  direction,
  getCounterpartName,
  getCounterpartPiva,
  onElaborate,
  onIgnore,
  onDownloadXml,
  onDownloadPdf,
}: DetailPanelProps) {
  const counterpartName = getCounterpartName(invoice) || "\u2014";
  const counterpartPiva = getCounterpartPiva(invoice);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <SheetHeader className="p-6 pb-4 space-y-3">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#f2f2f2]">
            <span className="text-sm font-semibold text-[#1a1a1a]">
              {counterpartName.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <SheetTitle className="text-base font-semibold text-[#1a1a1a] leading-tight">
              {counterpartName}
            </SheetTitle>
            <p className="text-[13px] text-[#817f7d] mt-0.5">
              {docTypeShortLabel(invoice.tipo_documento)} &middot;{" "}
              {invoice.numero_fattura || "\u2014"}
            </p>
            <p className="text-lg font-semibold text-[#1a1a1a] mt-1">
              {formatCurrency(invoice.importo_totale)}
            </p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          {invoice.xml_file_nome && (
            <>
              <Button
                variant="outline"
                size="sm"
                className="h-8 rounded-lg border-[#e5e4e3] text-[13px] gap-1.5"
                onClick={() =>
                  onDownloadPdf(invoice.id, invoice.xml_file_nome!)
                }
              >
                <Eye className="h-3.5 w-3.5" />
                Anteprima
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="h-8 rounded-lg border-[#e5e4e3] text-[13px] gap-1.5"
                onClick={() =>
                  onDownloadXml(invoice.id, invoice.xml_file_nome!)
                }
              >
                <Download className="h-3.5 w-3.5" />
                XML
              </Button>
            </>
          )}
          <Button
            variant="outline"
            size="sm"
            className="h-8 rounded-lg border-[#e5e4e3] text-[13px] gap-1.5"
            onClick={() => onIgnore(invoice.id)}
          >
            <EyeOff className="h-3.5 w-3.5" />
            Nascondi
          </Button>
          {invoice.stato === "importata" && (
            <Button
              size="sm"
              className="h-8 rounded-lg text-[13px] gap-1.5 bg-[#6672ff] hover:bg-[#5560e6]"
              onClick={() => onElaborate(invoice.id)}
            >
              <Check className="h-3.5 w-3.5" />
              Elabora
            </Button>
          )}
        </div>
      </SheetHeader>

      {/* Tabs */}
      <Tabs defaultValue="documento" className="flex-1">
        <div className="border-b border-[#e5e4e3] px-6">
          <TabsList className="h-auto p-0 bg-transparent rounded-none gap-4">
            <TabsTrigger
              value="documento"
              className="rounded-none border-b-2 border-transparent px-0 py-2.5 text-[13px] font-medium text-[#817f7d] data-[state=active]:border-[#1a1a1a] data-[state=active]:text-[#1a1a1a] data-[state=active]:shadow-none data-[state=active]:bg-transparent"
            >
              Documento
            </TabsTrigger>
            <TabsTrigger
              value="scadenze"
              className="rounded-none border-b-2 border-transparent px-0 py-2.5 text-[13px] font-medium text-[#817f7d] data-[state=active]:border-[#1a1a1a] data-[state=active]:text-[#1a1a1a] data-[state=active]:shadow-none data-[state=active]:bg-transparent"
            >
              Scadenze
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab: Documento */}
        <TabsContent value="documento" className="mt-0 p-6 space-y-5">
          <DetailRow
            label="Tipo documento"
            value={INVOICE_DOC_TYPE_LABELS[invoice.tipo_documento]}
          />
          <DetailRow label="Categoria">
            <Badge className="bg-[#e5e4e3] text-[#1a1a1a] text-[11px] font-medium rounded-full px-2.5 py-0.5 hover:bg-[#e5e4e3]">
              Non categorizzata
            </Badge>
          </DetailRow>
          <DetailRow
            label="Data documento"
            value={formatDate(invoice.data_fattura)}
          />
          <DetailRow
            label="Numero documento"
            value={invoice.numero_fattura || "\u2014"}
          />
          <DetailRow
            label={
              direction === "ricevute" ? "Nome fornitore" : "Nome cliente"
            }
            value={counterpartName}
          />
          <DetailRow
            label={
              direction === "ricevute"
                ? "Identificativo fornitore"
                : "Identificativo cliente"
            }
            value={counterpartPiva ? `P.IVA ${counterpartPiva}` : "\u2014"}
          />
          <DetailRow
            label="Importo IVA inclusa"
            value={formatCurrency(invoice.importo_totale)}
          />
          <DetailRow
            label="IVA"
            value={formatCurrency(invoice.iva_totale)}
          />
          <DetailRow label="Ritenuta d'acconto" value="\u2014" />

          <div className="border-t border-[#e5e4e3] pt-5 space-y-5">
            <DetailRow label="Allegati">
              <span className="text-[13px] text-[#6672ff] font-medium cursor-pointer hover:underline">
                Carica allegati
              </span>
            </DetailRow>
            <DetailRow label="Documenti collegati" value="" />
          </div>

          <div className="border-t border-[#e5e4e3] pt-5">
            <p className="text-[12px] font-medium text-[#817f7d] mb-2">Note</p>
            <Textarea
              placeholder=""
              className="min-h-[80px] text-[13px] rounded-lg border-[#e5e4e3] resize-none"
            />
          </div>

          {invoice.errore_dettaglio && (
            <p className="text-[12px] text-red-600 mt-2">
              {invoice.errore_dettaglio}
            </p>
          )}
        </TabsContent>

        {/* Tab: Scadenze */}
        <TabsContent value="scadenze" className="mt-0 p-6 space-y-4">
          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              className="h-8 rounded-lg border-[#e5e4e3] text-[13px] gap-1"
            >
              Aggiungi scadenza +
            </Button>
          </div>

          {invoice.schedule_id ? (
            <ScadenzaCard invoice={invoice} direction={direction} />
          ) : (
            <div className="text-center py-8">
              <p className="text-[13px] text-[#817f7d] mb-3">
                Nessuna scadenza
              </p>
              <Button
                variant="outline"
                size="sm"
                className="h-8 rounded-lg border-[#e5e4e3] text-[13px]"
              >
                Aggiungi scadenza
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

/* ================================================================
   Detail Row (label : value)
   ================================================================ */

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
    <div className="flex items-start justify-between gap-4">
      <span className="text-[12px] font-medium text-[#817f7d] shrink-0 pt-0.5">
        {label}
      </span>
      <div className="text-right">
        {children || (
          <span className="text-[13px] text-[#1a1a1a]">
            {value || "\u2014"}
          </span>
        )}
      </div>
    </div>
  );
}

/* ================================================================
   Scadenza Card
   ================================================================ */

function ScadenzaCard({
  invoice,
  direction,
}: {
  invoice: InvoiceImport;
  direction: "ricevute" | "emesse";
}) {
  void direction;

  const isPaid = invoice.stato === "scadenza_creata";

  return (
    <div className="rounded-lg border border-[#e5e4e3] p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-[13px] font-semibold text-[#1a1a1a]">
          Scadenza 1
        </h4>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-7 px-2.5 rounded-lg border-[#e5e4e3] text-[12px]"
          >
            Modifica
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="h-7 px-2.5 rounded-lg border-[#e5e4e3] text-[12px] text-red-500 hover:text-red-600"
          >
            Rimuovi
          </Button>
        </div>
      </div>

      <div className="flex items-center">
        <Badge
          className={cn(
            "text-[11px] font-medium rounded-full px-2.5 py-0.5",
            isPaid
              ? "bg-[#8cddba] text-[#1a1a1a]"
              : "bg-[#ffd98c] text-[#1a1a1a]"
          )}
        >
          {isPaid ? "Pagato" : "Da pagare"}
        </Badge>
      </div>

      <div className="text-[13px] text-[#817f7d] italic">
        Movimenti riconciliati
      </div>
      {isPaid && invoice.cedente_denominazione && (
        <p className="text-[12px] text-[#817f7d]">
          {invoice.cedente_denominazione} &middot;{" "}
          {formatCurrency(invoice.importo_totale)}
        </p>
      )}

      <div className="space-y-3 pt-2">
        <ScadenzaRow
          label="Importo"
          value={formatCurrency(invoice.importo_totale)}
        />
        <ScadenzaRow
          label="Scadenza"
          value={formatDate(invoice.data_scadenza_pagamento)}
        />
        <ScadenzaRow
          label="Data di pagamento originale"
          value={formatDate(invoice.data_scadenza_pagamento)}
        />
        <ScadenzaRow
          label="Modalita di pagamento"
          value={invoice.modalita_pagamento || "\u2014"}
        />
        <ScadenzaRow
          label="Conto in fattura"
          value={invoice.iban_pagamento || "\u2014"}
        />
        <ScadenzaRow label="Conto di pagamento" value="\u2014" />
        <ScadenzaRow label="Note" value="\u2014" />
      </div>
    </div>
  );
}

function ScadenzaRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-[12px] font-medium text-[#817f7d] shrink-0">
        {label}
      </span>
      <span className="text-[13px] text-[#1a1a1a] text-right">{value}</span>
    </div>
  );
}
