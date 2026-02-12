"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Plus, CreditCard, Search, ChevronLeft, ChevronRight } from "lucide-react";
import { ExportButton } from "@/components/shared/export-button";
import { toast } from "sonner";
import {
  listPaymentOrders,
  getPaymentSummary,
} from "@/lib/api/payments";
import type {
  PaymentOrder,
  PaymentOrderSummary,
  PaymentOrderStatus,
  PaymentOrderType,
} from "@/types/payment";
import {
  PAYMENT_ORDER_TYPE_LABELS,
  PAYMENT_ORDER_STATUS_LABELS,
} from "@/types/payment";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PaymentSummaryCards } from "@/components/payments/PaymentSummaryCards";
import { PaymentStatusBadge } from "@/components/payments/PaymentStatusBadge";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "\u2014";
  return new Date(dateStr).toLocaleDateString("it-IT");
}

type QuickFilter = "tutti" | "bozze" | "da_approvare" | "in_corso" | "eseguiti";

const QUICK_FILTER_MAP: Record<QuickFilter, PaymentOrderStatus | null> = {
  tutti: null,
  bozze: "bozza",
  da_approvare: "da_approvare",
  in_corso: null, // handled separately
  eseguiti: "eseguita",
};

const IN_CORSO_STATUSES: PaymentOrderStatus[] = [
  "approvata",
  "file_generato",
  "inviata_banca",
];

export default function PagamentiPage() {
  const router = useRouter();

  // Data
  const [orders, setOrders] = useState<PaymentOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<PaymentOrderSummary | null>(null);
  const [loading, setLoading] = useState(true);

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [quickFilter, setQuickFilter] = useState<QuickFilter>("tutti");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };

      // Quick filter overrides status filter
      if (quickFilter !== "tutti") {
        if (quickFilter === "in_corso") {
          params.stato = IN_CORSO_STATUSES.join(",");
        } else {
          const mapped = QUICK_FILTER_MAP[quickFilter];
          if (mapped) params.stato = mapped;
        }
      } else if (statusFilter !== "all") {
        params.stato = statusFilter;
      }

      if (typeFilter !== "all") params.tipo = typeFilter;
      if (search) params.search = search;
      if (dateFrom) params.data_da = dateFrom;
      if (dateTo) params.data_a = dateTo;

      const [listData, summaryData] = await Promise.all([
        listPaymentOrders(params),
        getPaymentSummary(),
      ]);

      setOrders(listData.items);
      setTotal(listData.total);
      setSummary(summaryData);
    } catch {
      toast.error("Errore nel caricamento dei pagamenti");
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, typeFilter, search, dateFrom, dateTo, quickFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [statusFilter, typeFilter, search, dateFrom, dateTo, quickFilter]);

  const totalPages = Math.ceil(total / pageSize);

  const handleQuickFilterChange = (value: string) => {
    setQuickFilter(value as QuickFilter);
    setStatusFilter("all"); // reset manual status filter
  };

  if (loading && orders.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Pagamenti"
          description="Gestisci ordini di pagamento e disposizioni"
        />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Pagamenti"
        description="Gestisci ordini di pagamento e disposizioni"
        actions={
          <div className="flex gap-2">
            <ExportButton reportType="pagamenti" label="Esporta" />
            <Button onClick={() => router.push("/pagamenti/nuovo")}>
              <Plus className="h-4 w-4 mr-2" />
              Nuovo Pagamento
            </Button>
          </div>
        }
      />

      {/* Summary cards */}
      <PaymentSummaryCards summary={summary} />

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Cerca riferimento, beneficiario..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setQuickFilter("tutti"); }}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Stato" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tutti gli stati</SelectItem>
            {Object.entries(PAYMENT_ORDER_STATUS_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Tipo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tutti i tipi</SelectItem>
            {Object.entries(PAYMENT_ORDER_TYPE_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="w-[150px]"
          placeholder="Da"
        />
        <Input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="w-[150px]"
          placeholder="A"
        />
      </div>

      {/* Quick filter tabs */}
      <Tabs value={quickFilter} onValueChange={handleQuickFilterChange}>
        <TabsList>
          <TabsTrigger value="tutti">Tutti</TabsTrigger>
          <TabsTrigger value="bozze">Bozze</TabsTrigger>
          <TabsTrigger value="da_approvare">Da approvare</TabsTrigger>
          <TabsTrigger value="in_corso">In corso</TabsTrigger>
          <TabsTrigger value="eseguiti">Eseguiti</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Table */}
      {orders.length === 0 ? (
        <EmptyState
          icon={CreditCard}
          title="Nessun pagamento"
          description="Crea il tuo primo ordine di pagamento per iniziare"
          actionLabel="Nuovo Pagamento"
          onAction={() => router.push("/pagamenti/nuovo")}
        />
      ) : (
        <>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Riferimento</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead className="text-right">Importo</TableHead>
                  <TableHead>Data Esecuzione</TableHead>
                  <TableHead>Disposizioni</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow
                    key={order.id}
                    className="cursor-pointer"
                    onClick={() => router.push(`/pagamenti/${order.id}`)}
                  >
                    <TableCell>
                      <p className="font-medium text-sm">{order.riferimento_interno}</p>
                      {order.note && (
                        <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {order.note}
                        </p>
                      )}
                    </TableCell>
                    <TableCell className="text-sm">
                      {PAYMENT_ORDER_TYPE_LABELS[order.tipo]}
                    </TableCell>
                    <TableCell>
                      <PaymentStatusBadge stato={order.stato} />
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">
                      {formatCurrency(order.importo_totale)}
                    </TableCell>
                    <TableCell className="text-sm whitespace-nowrap">
                      {formatDate(order.data_esecuzione_richiesta)}
                    </TableCell>
                    <TableCell className="text-sm text-center">
                      {order.numero_disposizioni}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/pagamenti/${order.id}`);
                        }}
                      >
                        Dettagli
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
                {total} pagamenti totali &middot; Pagina {page} di {totalPages}
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

          {totalPages <= 1 && total > 0 && (
            <p className="text-sm text-muted-foreground text-center">
              {total} pagamenti totali
            </p>
          )}
        </>
      )}
    </div>
  );
}
