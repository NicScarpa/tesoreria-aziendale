"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Plus,
  CalendarClock,
  List,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  RefreshCcw,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type {
  Schedule,
  ScheduleListResponse,
  ScheduleCalendarDay,
  ScheduleSummary,
} from "@/types/schedule";
import {
  SCHEDULE_STATUS_LABELS,
  SCHEDULE_TYPE_LABELS,
  DOCUMENT_TYPE_LABELS,
  PAYMENT_METHOD_LABELS,
} from "@/types/schedule";
import type { BankAccount } from "@/types/bank-account";
import { ExportButton } from "@/components/shared/export-button";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScheduleSummaryCards } from "@/components/schedules/schedule-summary-cards";
import { ScheduleFilters } from "@/components/schedules/schedule-filters";
import { ScheduleStatusBadge } from "@/components/schedules/schedule-status-badge";
import { PriorityBadge } from "@/components/schedules/priority-badge";
import { RecurrencePreview } from "@/components/schedules/recurrence-preview";
import { ScheduleCalendar } from "@/components/schedules/schedule-calendar";
import { CreateScheduleSheet } from "@/components/schedules/create-schedule-sheet";
import { PaymentDialog } from "@/components/schedules/payment-dialog";
import { cn } from "@/lib/utils";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT");
}

export default function ScadenzarioPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { currentCompany } = useAuthStore();
  const userRole = currentCompany?.role;
  const canEdit = userRole === "owner" || userRole === "admin" || userRole === "editor";

  // State
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<ScheduleSummary | null>(null);
  const [calendarDays, setCalendarDays] = useState<ScheduleCalendarDay[]>([]);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState(searchParams?.get("search") || "");
  const [statusFilter, setStatusFilter] = useState(searchParams?.get("stato") || "all");
  const [typeFilter, setTypeFilter] = useState(searchParams?.get("tipo") || "all");
  const [priorityFilter, setPriorityFilter] = useState(searchParams?.get("priorita") || "all");
  const [viewMode, setViewMode] = useState<"list" | "calendar">("list");

  // Calendar state
  const now = new Date();
  const [calMonth, setCalMonth] = useState(now.getMonth() + 1);
  const [calYear, setCalYear] = useState(now.getFullYear());

  // Dialogs
  const [createOpen, setCreateOpen] = useState(false);
  const [paymentSchedule, setPaymentSchedule] = useState<Schedule | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.set("stato", statusFilter);
      if (typeFilter !== "all") params.set("tipo", typeFilter);
      if (priorityFilter !== "all") params.set("priorita", priorityFilter);
      if (search) params.set("search", search);
      params.set("page_size", "100");

      const [listResp, summaryResp, accountsResp] = await Promise.all([
        api.get<ScheduleListResponse>(`/schedules?${params}`),
        api.get<ScheduleSummary>("/schedules/summary"),
        api.get<BankAccount[]>("/bank-accounts"),
      ]);

      setSchedules(listResp.data.items);
      setTotal(listResp.data.total);
      setSummary(summaryResp.data);
      setBankAccounts(accountsResp.data);
    } catch {
      toast.error("Errore nel caricamento dello scadenzario");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter, priorityFilter, search]);

  const loadCalendar = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      params.set("month", String(calMonth));
      params.set("year", String(calYear));
      if (typeFilter !== "all") params.set("tipo", typeFilter);
      const resp = await api.get<ScheduleCalendarDay[]>(`/schedules/calendar?${params}`);
      setCalendarDays(resp.data);
    } catch {
      // Non-critical
    }
  }, [calMonth, calYear, typeFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (viewMode === "calendar") {
      loadCalendar();
    }
  }, [viewMode, loadCalendar]);

  const monthNames = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
  ];

  const prevMonth = () => {
    if (calMonth === 1) {
      setCalMonth(12);
      setCalYear((y) => y - 1);
    } else {
      setCalMonth((m) => m - 1);
    }
  };

  const nextMonth = () => {
    if (calMonth === 12) {
      setCalMonth(1);
      setCalYear((y) => y + 1);
    } else {
      setCalMonth((m) => m + 1);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Scadenzario" description="Gestisci scadenze e pagamenti" />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Scadenzario"
        description="Gestisci scadenze e pagamenti"
        actions={
          <div className="flex gap-2">
            <ExportButton reportType="scadenzario" label="Esporta" />
            {canEdit && (
              <Button onClick={() => setCreateOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Nuova scadenza
              </Button>
            )}
          </div>
        }
      />

      <ScheduleSummaryCards summary={summary} />

      <ScheduleFilters
        search={search}
        onSearchChange={setSearch}
        statusFilter={statusFilter}
        onStatusChange={setStatusFilter}
        typeFilter={typeFilter}
        onTypeChange={setTypeFilter}
        priorityFilter={priorityFilter}
        onPriorityChange={setPriorityFilter}
      />

      <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as "list" | "calendar")}>
        <TabsList>
          <TabsTrigger value="list">
            <List className="h-4 w-4 mr-1" />
            Lista
          </TabsTrigger>
          <TabsTrigger value="calendar">
            <CalendarDays className="h-4 w-4 mr-1" />
            Calendario
          </TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="mt-4">
          {schedules.length === 0 ? (
            <EmptyState
              icon={CalendarClock}
              title="Nessuna scadenza"
              description="Crea la tua prima scadenza per iniziare a tracciare pagamenti e incassi"
              actionLabel={canEdit ? "Nuova scadenza" : undefined}
              onAction={canEdit ? () => setCreateOpen(true) : undefined}
            />
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Scadenza</TableHead>
                    <TableHead>Controparte</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead className="text-right">Importo</TableHead>
                    <TableHead className="text-right">Residuo</TableHead>
                    <TableHead>Stato</TableHead>
                    <TableHead>Priorita</TableHead>
                    <TableHead>Data</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schedules.map((s) => {
                    const isOverdue =
                      s.stato !== "pagata" &&
                      s.stato !== "annullata" &&
                      new Date(s.data_scadenza) < new Date();
                    return (
                      <TableRow
                        key={s.id}
                        className={cn(
                          "cursor-pointer",
                          isOverdue && "bg-red-50/50",
                          s.stato === "pagata" && "opacity-60"
                        )}
                        onClick={() => router.push(`/scadenzario/${s.id}`)}
                      >
                        <TableCell>
                          <div>
                            <p className="font-medium text-sm truncate max-w-[200px]">
                              {s.descrizione}
                            </p>
                            {s.riferimento_documento && (
                              <p className="text-xs text-muted-foreground">{s.riferimento_documento}</p>
                            )}
                            {s.source === "import_fatture_sdi" && (
                              <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700">
                                Da fattura
                              </span>
                            )}
                            {s.is_ricorrente && (
                              <RecurrencePreview
                                isRicorrente={s.is_ricorrente}
                                ricorrenzaTipo={s.ricorrenza_tipo}
                                ricorrenzaAttiva={s.ricorrenza_attiva}
                                ricorrenzaProssimaGenerazione={s.ricorrenza_prossima_generazione}
                              />
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">{s.controparte_nome || "—"}</TableCell>
                        <TableCell>
                          <span
                            className={cn(
                              "text-xs font-medium",
                              s.tipo === "attiva" ? "text-green-700" : "text-red-700"
                            )}
                          >
                            {SCHEDULE_TYPE_LABELS[s.tipo]}
                          </span>
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm">
                          {formatCurrency(s.importo_totale)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-sm">
                          {s.importo_residuo > 0 ? formatCurrency(s.importo_residuo) : "—"}
                        </TableCell>
                        <TableCell>
                          <ScheduleStatusBadge status={s.stato} />
                        </TableCell>
                        <TableCell>
                          <PriorityBadge priority={s.priorita} />
                        </TableCell>
                        <TableCell className="text-sm whitespace-nowrap">
                          {formatDate(s.data_scadenza)}
                        </TableCell>
                        <TableCell>
                          {canEdit && s.stato !== "pagata" && s.stato !== "annullata" && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                setPaymentSchedule(s);
                              }}
                            >
                              Paga
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
          {total > 0 && (
            <p className="text-sm text-muted-foreground text-center mt-2">
              {total} scadenze totali
            </p>
          )}
        </TabsContent>

        <TabsContent value="calendar" className="mt-4">
          <div className="flex items-center justify-between mb-4">
            <Button variant="outline" size="sm" onClick={prevMonth}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <h3 className="text-lg font-semibold">
              {monthNames[calMonth - 1]} {calYear}
            </h3>
            <Button variant="outline" size="sm" onClick={nextMonth}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
          <ScheduleCalendar
            days={calendarDays}
            month={calMonth}
            year={calYear}
            onDayClick={(day) => {
              if (day.scadenze.length === 1) {
                router.push(`/scadenzario/${day.scadenze[0].id}`);
              }
            }}
          />
        </TabsContent>
      </Tabs>

      <CreateScheduleSheet
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={loadData}
        bankAccounts={bankAccounts}
      />

      <PaymentDialog
        schedule={paymentSchedule}
        open={!!paymentSchedule}
        onOpenChange={(open) => !open && setPaymentSchedule(null)}
        onCreated={loadData}
      />
    </div>
  );
}
