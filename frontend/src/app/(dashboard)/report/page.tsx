"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Plus, Search, Clock, BarChart3, Calendar, ChevronLeft, ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import {
  listReportDefinitions,
  listExecutions,
  listSchedules,
  togglePreferito,
  downloadExecution,
  deleteExecution,
  deleteSchedule,
  updateSchedule,
  runScheduleNow,
  triggerDownload,
} from "@/lib/api/reports";
import type {
  ReportDefinition,
  ReportExecution,
  ReportSchedule,
} from "@/types/report";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ReportCard } from "@/components/reports/report-card";
import { ReportExecutionRow } from "@/components/reports/report-execution-row";
import { ReportScheduleRow } from "@/components/reports/report-schedule-row";
import { ReportGenerateDialog } from "@/components/reports/report-generate-dialog";
import { ReportCreateDialog } from "@/components/reports/report-create-dialog";
import { ReportScheduleDialog } from "@/components/reports/report-schedule-dialog";

export default function ReportPage() {
  const [activeTab, setActiveTab] = useState("report");
  const [loading, setLoading] = useState(true);

  // Data
  const [definitions, setDefinitions] = useState<ReportDefinition[]>([]);
  const [executions, setExecutions] = useState<ReportExecution[]>([]);
  const [executionsTotal, setExecutionsTotal] = useState(0);
  const [schedules, setSchedules] = useState<ReportSchedule[]>([]);

  // Pagination for executions
  const [execPage, setExecPage] = useState(1);
  const execPageSize = 10;

  // Filters
  const [search, setSearch] = useState("");

  // Dialogs
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [selectedDefinition, setSelectedDefinition] = useState<ReportDefinition | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<ReportSchedule | null>(null);

  // Polling for in-progress executions
  const [pollingActive, setPollingActive] = useState(false);

  const loadDefinitions = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      const data = await listReportDefinitions(params);
      setDefinitions(data.items);
    } catch {
      toast.error("Errore nel caricamento dei report");
    }
  }, [search]);

  const loadExecutions = useCallback(async () => {
    try {
      const data = await listExecutions({ page: execPage, per_page: execPageSize });
      setExecutions(data.items);
      setExecutionsTotal(data.total);

      // Check if any executions are in progress
      const hasInProgress = data.items.some(
        (e) => e.stato === "in_coda" || e.stato === "in_generazione"
      );
      setPollingActive(hasInProgress);
    } catch {
      toast.error("Errore nel caricamento dello storico");
    }
  }, [execPage]);

  const loadSchedules = useCallback(async () => {
    try {
      const data = await listSchedules();
      setSchedules(data.items);
    } catch {
      toast.error("Errore nel caricamento delle programmazioni");
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([loadDefinitions(), loadExecutions(), loadSchedules()]);
    setLoading(false);
  }, [loadDefinitions, loadExecutions, loadSchedules]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // Polling
  useEffect(() => {
    if (!pollingActive) return;
    const interval = setInterval(loadExecutions, 2000);
    return () => clearInterval(interval);
  }, [pollingActive, loadExecutions]);

  // Handlers
  const handleGenerate = (definition: ReportDefinition) => {
    setSelectedDefinition(definition);
    setGenerateDialogOpen(true);
  };

  const handleTogglePreferito = async (definition: ReportDefinition) => {
    try {
      await togglePreferito(definition.id);
      await loadDefinitions();
    } catch {
      toast.error("Errore nell'aggiornamento");
    }
  };

  const handleDownload = async (execution: ReportExecution) => {
    try {
      const blob = await downloadExecution(execution.id);
      triggerDownload(blob, `${execution.nome}.${execution.formato}`);
    } catch {
      toast.error("Errore nel download del file");
    }
  };

  const handleDeleteExecution = async (execution: ReportExecution) => {
    try {
      await deleteExecution(execution.id);
      toast.success("Esecuzione eliminata");
      loadExecutions();
    } catch {
      toast.error("Errore nell'eliminazione");
    }
  };

  const handleToggleScheduleActive = async (schedule: ReportSchedule) => {
    try {
      await updateSchedule(schedule.id, { attivo: !schedule.attivo });
      toast.success(schedule.attivo ? "Programmazione disattivata" : "Programmazione attivata");
      loadSchedules();
    } catch {
      toast.error("Errore nell'aggiornamento");
    }
  };

  const handleRunScheduleNow = async (schedule: ReportSchedule) => {
    try {
      await runScheduleNow(schedule.id);
      toast.success("Report in generazione");
      loadExecutions();
    } catch {
      toast.error("Errore nell'esecuzione");
    }
  };

  const handleDeleteSchedule = async (schedule: ReportSchedule) => {
    try {
      await deleteSchedule(schedule.id);
      toast.success("Programmazione eliminata");
      loadSchedules();
    } catch {
      toast.error("Errore nell'eliminazione");
    }
  };

  const execTotalPages = Math.ceil(executionsTotal / execPageSize);

  // Filter definitions
  const filteredDefinitions = definitions;
  const preferiti = filteredDefinitions.filter((d) => d.is_preferito);
  const systemDefs = filteredDefinitions.filter((d) => d.is_system && !d.is_preferito);
  const customDefs = filteredDefinitions.filter((d) => !d.is_system);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Centro Report"
          description="Genera, scarica e programma report aziendali"
        />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Centro Report"
        description="Genera, scarica e programma report aziendali"
        actions={
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Nuovo Report
          </Button>
        }
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="report">
            <BarChart3 className="h-4 w-4 mr-2" />
            Report
          </TabsTrigger>
          <TabsTrigger value="storico">
            <Clock className="h-4 w-4 mr-2" />
            Storico ({executionsTotal})
          </TabsTrigger>
          <TabsTrigger value="programmazioni">
            <Calendar className="h-4 w-4 mr-2" />
            Programmazioni ({schedules.length})
          </TabsTrigger>
        </TabsList>

        {/* Tab: Report */}
        <TabsContent value="report" className="space-y-6 mt-4">
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Cerca report..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>

          {preferiti.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-3">Preferiti</h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {preferiti.map((d) => (
                  <ReportCard
                    key={d.id}
                    definition={d}
                    onGenerate={handleGenerate}
                    onTogglePreferito={handleTogglePreferito}
                  />
                ))}
              </div>
            </div>
          )}

          {systemDefs.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-3">Report di Sistema</h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {systemDefs.map((d) => (
                  <ReportCard
                    key={d.id}
                    definition={d}
                    onGenerate={handleGenerate}
                    onTogglePreferito={handleTogglePreferito}
                  />
                ))}
              </div>
            </div>
          )}

          {customDefs.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground mb-3">Report Personalizzati</h3>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {customDefs.map((d) => (
                  <ReportCard
                    key={d.id}
                    definition={d}
                    onGenerate={handleGenerate}
                    onTogglePreferito={handleTogglePreferito}
                  />
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Tab: Storico */}
        <TabsContent value="storico" className="space-y-4 mt-4">
          {executions.length === 0 ? (
            <EmptyState
              icon={Clock}
              title="Nessun report generato"
              description="Genera il tuo primo report dalla sezione Report"
            />
          ) : (
            <>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome</TableHead>
                      <TableHead>Formato</TableHead>
                      <TableHead>Stato</TableHead>
                      <TableHead>Data</TableHead>
                      <TableHead>Dimensione</TableHead>
                      <TableHead />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {executions.map((e) => (
                      <ReportExecutionRow
                        key={e.id}
                        execution={e}
                        onDownload={handleDownload}
                        onDelete={handleDeleteExecution}
                      />
                    ))}
                  </TableBody>
                </Table>
              </div>

              {execTotalPages > 1 && (
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    {executionsTotal} report totali &middot; Pagina {execPage} di {execTotalPages}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={execPage <= 1}
                      onClick={() => setExecPage((p) => p - 1)}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={execPage >= execTotalPages}
                      onClick={() => setExecPage((p) => p + 1)}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </TabsContent>

        {/* Tab: Programmazioni */}
        <TabsContent value="programmazioni" className="space-y-4 mt-4">
          <div className="flex justify-end">
            <Button
              size="sm"
              onClick={() => {
                setEditingSchedule(null);
                setScheduleDialogOpen(true);
              }}
            >
              <Plus className="h-4 w-4 mr-2" />
              Nuova Programmazione
            </Button>
          </div>

          {schedules.length === 0 ? (
            <EmptyState
              icon={Calendar}
              title="Nessuna programmazione"
              description="Programma la generazione automatica dei report"
              actionLabel="Nuova Programmazione"
              onAction={() => setScheduleDialogOpen(true)}
            />
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Frequenza</TableHead>
                    <TableHead>Formato</TableHead>
                    <TableHead>Prossima esecuzione</TableHead>
                    <TableHead>Ultima esecuzione</TableHead>
                    <TableHead>Attivo</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schedules.map((s) => (
                    <ReportScheduleRow
                      key={s.id}
                      schedule={s}
                      onToggleActive={handleToggleScheduleActive}
                      onRunNow={handleRunScheduleNow}
                      onEdit={(s) => {
                        setEditingSchedule(s);
                        setScheduleDialogOpen(true);
                      }}
                      onDelete={handleDeleteSchedule}
                    />
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <ReportGenerateDialog
        open={generateDialogOpen}
        onOpenChange={setGenerateDialogOpen}
        definition={selectedDefinition}
        onGenerated={() => {
          loadExecutions();
          setActiveTab("storico");
        }}
      />

      <ReportCreateDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreated={() => loadDefinitions()}
      />

      <ReportScheduleDialog
        open={scheduleDialogOpen}
        onOpenChange={setScheduleDialogOpen}
        definitions={definitions}
        schedule={editingSchedule}
        onSaved={() => loadSchedules()}
      />
    </div>
  );
}
