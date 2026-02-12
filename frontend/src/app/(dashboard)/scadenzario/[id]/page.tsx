"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Pencil,
  Trash2,
  Plus,
  Bell,
  RefreshCcw,
  FileText,
  Upload,
  Download,
  XCircle,
  StopCircle,
} from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type {
  Schedule,
  SchedulePayment,
  ScheduleReminder,
  ScheduleAttachment,
} from "@/types/schedule";
import {
  SCHEDULE_STATUS_LABELS,
  SCHEDULE_TYPE_LABELS,
  DOCUMENT_TYPE_LABELS,
  PRIORITY_LABELS,
  PAYMENT_METHOD_LABELS,
  RECURRENCE_LABELS,
} from "@/types/schedule";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScheduleStatusBadge } from "@/components/schedules/schedule-status-badge";
import { PriorityBadge } from "@/components/schedules/priority-badge";
import { PaymentProgressBar } from "@/components/schedules/payment-progress-bar";
import { RecurrencePreview } from "@/components/schedules/recurrence-preview";
import { PaymentDialog } from "@/components/schedules/payment-dialog";
import { ReminderDialog } from "@/components/schedules/reminder-dialog";
import { CashFlowImpactCard } from "@/components/cash-flow/CashFlowImpactCard";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleDateString("it-IT");
}

export default function ScadenzaDetailPage() {
  const params = useParams();
  const router = useRouter();
  const scheduleId = params.id as string;
  const { currentCompany } = useAuthStore();
  const canEdit = ["owner", "admin", "editor"].includes(currentCompany?.role ?? "");
  const canDelete = ["owner", "admin"].includes(currentCompany?.role ?? "");

  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [payments, setPayments] = useState<SchedulePayment[]>([]);
  const [reminders, setReminders] = useState<ScheduleReminder[]>([]);
  const [attachments, setAttachments] = useState<ScheduleAttachment[]>([]);
  const [occurrences, setOccurrences] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);

  const [paymentOpen, setPaymentOpen] = useState(false);
  const [reminderOpen, setReminderOpen] = useState(false);

  const loadSchedule = useCallback(async () => {
    try {
      const resp = await api.get<Schedule>(`/schedules/${scheduleId}`);
      setSchedule(resp.data);
    } catch {
      toast.error("Scadenza non trovata");
      router.push("/scadenzario");
    } finally {
      setLoading(false);
    }
  }, [scheduleId, router]);

  const loadRelated = useCallback(async () => {
    try {
      const [payResp, remResp, attResp] = await Promise.all([
        api.get<SchedulePayment[]>(`/schedules/${scheduleId}/payments`),
        api.get<ScheduleReminder[]>(`/schedules/${scheduleId}/reminders`),
        api.get<ScheduleAttachment[]>(`/schedules/${scheduleId}/attachments`),
      ]);
      setPayments(payResp.data);
      setReminders(remResp.data);
      setAttachments(attResp.data);
    } catch {
      // Non-critical
    }
  }, [scheduleId]);

  const loadOccurrences = useCallback(async () => {
    try {
      const resp = await api.get<Schedule[]>(`/schedules/${scheduleId}/occurrences`);
      setOccurrences(resp.data);
    } catch {
      // Non-critical
    }
  }, [scheduleId]);

  useEffect(() => {
    loadSchedule();
    loadRelated();
  }, [loadSchedule, loadRelated]);

  const reload = () => {
    loadSchedule();
    loadRelated();
  };

  const handleDelete = async () => {
    if (!confirm("Sei sicuro di voler eliminare questa scadenza?")) return;
    try {
      await api.delete(`/schedules/${scheduleId}`);
      toast.success("Scadenza eliminata");
      router.push("/scadenzario");
    } catch {
      toast.error("Errore nell'eliminazione");
    }
  };

  const handleCancel = async () => {
    try {
      await api.put(`/schedules/${scheduleId}/stato`, { stato: "annullata" });
      toast.success("Scadenza annullata");
      reload();
    } catch {
      toast.error("Errore nell'annullamento");
    }
  };

  const handleGenerateNext = async () => {
    try {
      await api.post(`/schedules/${scheduleId}/generate-next`);
      toast.success("Occorrenza generata");
      loadOccurrences();
    } catch {
      toast.error("Errore nella generazione");
    }
  };

  const handleStopRecurrence = async () => {
    try {
      await api.put(`/schedules/${scheduleId}/stop-recurrence`);
      toast.success("Ricorrenza disattivata");
      reload();
    } catch {
      toast.error("Errore");
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      await api.post(`/schedules/${scheduleId}/attachments`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      toast.success("Allegato caricato");
      loadRelated();
    } catch {
      toast.error("Errore nel caricamento");
    }
    e.target.value = "";
  };

  const handleDeleteAttachment = async (attId: string) => {
    try {
      await api.delete(`/schedules/attachments/${attId}`);
      toast.success("Allegato eliminato");
      loadRelated();
    } catch {
      toast.error("Errore");
    }
  };

  const handleDeletePayment = async (payId: string) => {
    if (!confirm("Eliminare questo pagamento?")) return;
    try {
      await api.delete(`/schedules/${scheduleId}/payments/${payId}`);
      toast.success("Pagamento eliminato");
      reload();
    } catch {
      toast.error("Errore");
    }
  };

  const handleDeleteReminder = async (remId: string) => {
    try {
      await api.delete(`/schedules/${scheduleId}/reminders/${remId}`);
      toast.success("Promemoria eliminato");
      loadRelated();
    } catch {
      toast.error("Errore");
    }
  };

  if (loading) return <LoadingState />;
  if (!schedule) return null;

  const isActive = schedule.stato !== "pagata" && schedule.stato !== "annullata";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/scadenzario")}>
          <ArrowLeft className="h-4 w-4 mr-1" />
          Scadenzario
        </Button>
      </div>

      <PageHeader
        title={
          <span className="flex items-center gap-3">
            <span className={schedule.tipo === "attiva" ? "text-green-700" : "text-red-700"}>
              {SCHEDULE_TYPE_LABELS[schedule.tipo]}
            </span>
            <ScheduleStatusBadge status={schedule.stato} />
            <PriorityBadge priority={schedule.priorita} />
          </span>
        }
        description={schedule.descrizione}
        actions={
          canEdit && isActive ? (
            <div className="flex gap-2">
              <Button size="sm" onClick={() => setPaymentOpen(true)}>
                <Plus className="h-4 w-4 mr-1" />
                Registra pagamento
              </Button>
              {canDelete && (
                <Button size="sm" variant="destructive" onClick={handleDelete}>
                  <Trash2 className="h-4 w-4 mr-1" />
                  Elimina
                </Button>
              )}
            </div>
          ) : undefined
        }
      />

      {/* Progress bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <p className="text-sm text-muted-foreground">Importo totale</p>
              <p className="text-2xl font-bold">{formatCurrency(schedule.importo_totale)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Pagato</p>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(schedule.importo_pagato)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Residuo</p>
              <p className="text-2xl font-bold text-amber-600">
                {formatCurrency(schedule.importo_residuo)}
              </p>
            </div>
          </div>
          <PaymentProgressBar
            importoTotale={schedule.importo_totale}
            importoPagato={schedule.importo_pagato}
          />
        </CardContent>
      </Card>

      <CashFlowImpactCard schedule={schedule} />

      {/* Tabs */}
      <Tabs defaultValue="info" onValueChange={(v) => v === "occorrenze" && loadOccurrences()}>
        <TabsList>
          <TabsTrigger value="info">Informazioni</TabsTrigger>
          <TabsTrigger value="pagamenti">Pagamenti ({payments.length})</TabsTrigger>
          <TabsTrigger value="allegati">Allegati ({attachments.length})</TabsTrigger>
          <TabsTrigger value="promemoria">Promemoria ({reminders.length})</TabsTrigger>
          {schedule.is_ricorrente && <TabsTrigger value="occorrenze">Occorrenze</TabsTrigger>}
        </TabsList>

        {/* Info tab */}
        <TabsContent value="info" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Dettagli scadenza</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-muted-foreground">Tipo documento</dt>
                  <dd>{DOCUMENT_TYPE_LABELS[schedule.tipo_documento]}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Numero documento</dt>
                  <dd>{schedule.numero_documento || "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Riferimento</dt>
                  <dd>{schedule.riferimento_documento || "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Controparte</dt>
                  <dd>{schedule.controparte_nome || "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">IBAN controparte</dt>
                  <dd className="font-mono text-xs">{schedule.controparte_iban || "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Conto bancario</dt>
                  <dd>{schedule.bank_account_nickname || "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Data emissione</dt>
                  <dd>{formatDate(schedule.data_emissione)}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Data scadenza</dt>
                  <dd className="font-semibold">{formatDate(schedule.data_scadenza)}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Data pagamento</dt>
                  <dd>{formatDate(schedule.data_pagamento)}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Metodo pagamento</dt>
                  <dd>
                    {schedule.metodo_pagamento
                      ? PAYMENT_METHOD_LABELS[schedule.metodo_pagamento]
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Origine</dt>
                  <dd>{schedule.source}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Expected Transaction</dt>
                  <dd>
                    {schedule.expected_transaction_id ? (
                      <Badge variant="outline" className="text-xs">
                        Collegata
                      </Badge>
                    ) : (
                      "—"
                    )}
                  </dd>
                </div>
                {schedule.note && (
                  <div className="col-span-2">
                    <dt className="text-muted-foreground">Note</dt>
                    <dd className="whitespace-pre-wrap">{schedule.note}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>

          {/* Recurrence info */}
          {schedule.is_ricorrente && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <RefreshCcw className="h-4 w-4" />
                  Ricorrenza
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <RecurrencePreview
                  isRicorrente={schedule.is_ricorrente}
                  ricorrenzaTipo={schedule.ricorrenza_tipo}
                  ricorrenzaAttiva={schedule.ricorrenza_attiva}
                  ricorrenzaProssimaGenerazione={schedule.ricorrenza_prossima_generazione}
                />
                {canEdit && schedule.ricorrenza_attiva && (
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={handleGenerateNext}>
                      <RefreshCcw className="h-4 w-4 mr-1" />
                      Genera prossima
                    </Button>
                    <Button size="sm" variant="outline" onClick={handleStopRecurrence}>
                      <StopCircle className="h-4 w-4 mr-1" />
                      Disattiva
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Cancel action */}
          {canEdit && isActive && (
            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={handleCancel}>
                <XCircle className="h-4 w-4 mr-1" />
                Annulla scadenza
              </Button>
            </div>
          )}
        </TabsContent>

        {/* Payments tab */}
        <TabsContent value="pagamenti">
          {canEdit && isActive && (
            <div className="flex justify-end mb-4">
              <Button size="sm" onClick={() => setPaymentOpen(true)}>
                <Plus className="h-4 w-4 mr-1" />
                Registra pagamento
              </Button>
            </div>
          )}
          {payments.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              Nessun pagamento registrato
            </p>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Data</TableHead>
                    <TableHead className="text-right">Importo</TableHead>
                    <TableHead>Metodo</TableHead>
                    <TableHead>Riferimento</TableHead>
                    <TableHead>Note</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payments.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>{formatDate(p.data_pagamento)}</TableCell>
                      <TableCell className="text-right font-mono">
                        {formatCurrency(p.importo)}
                      </TableCell>
                      <TableCell>
                        {p.metodo ? PAYMENT_METHOD_LABELS[p.metodo] : "—"}
                      </TableCell>
                      <TableCell className="text-sm">{p.riferimento || "—"}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {p.note || "—"}
                      </TableCell>
                      <TableCell>
                        {canEdit && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeletePayment(p.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>

        {/* Attachments tab */}
        <TabsContent value="allegati">
          {canEdit && (
            <div className="flex justify-end mb-4">
              <label>
                <input type="file" className="hidden" onChange={handleUpload} accept=".pdf,.jpg,.jpeg,.png,.xml" />
                <Button size="sm" asChild>
                  <span>
                    <Upload className="h-4 w-4 mr-1" />
                    Carica allegato
                  </span>
                </Button>
              </label>
            </div>
          )}
          {attachments.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              Nessun allegato
            </p>
          ) : (
            <div className="space-y-2">
              {attachments.map((a) => (
                <div key={a.id} className="flex items-center justify-between rounded-md border p-3">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">{a.original_filename}</p>
                      <p className="text-xs text-muted-foreground">
                        {(a.file_size / 1024).toFixed(0)} KB &middot; {a.content_type}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => window.open(`/api/v1/schedules/attachments/${a.id}/download`)}
                    >
                      <Download className="h-3.5 w-3.5" />
                    </Button>
                    {canEdit && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteAttachment(a.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Reminders tab */}
        <TabsContent value="promemoria">
          {canEdit && isActive && (
            <div className="flex justify-end mb-4">
              <Button size="sm" onClick={() => setReminderOpen(true)}>
                <Bell className="h-4 w-4 mr-1" />
                Aggiungi promemoria
              </Button>
            </div>
          )}
          {reminders.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              Nessun promemoria configurato
            </p>
          ) : (
            <div className="space-y-2">
              {reminders.map((r) => (
                <div key={r.id} className="flex items-center justify-between rounded-md border p-3">
                  <div className="flex items-center gap-3">
                    <Bell className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm">
                        {r.giorni_prima} giorni prima &middot;{" "}
                        <span className="text-muted-foreground">{r.tipo}</span>
                      </p>
                      {r.messaggio && (
                        <p className="text-xs text-muted-foreground">{r.messaggio}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {r.inviato ? (
                      <Badge variant="outline" className="text-xs bg-green-50">
                        Inviato
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-xs">
                        In attesa
                      </Badge>
                    )}
                    {canEdit && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteReminder(r.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Occurrences tab */}
        {schedule.is_ricorrente && (
          <TabsContent value="occorrenze">
            {occurrences.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                Nessuna occorrenza generata
              </p>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Descrizione</TableHead>
                      <TableHead>Data scadenza</TableHead>
                      <TableHead className="text-right">Importo</TableHead>
                      <TableHead>Stato</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {occurrences.map((occ) => (
                      <TableRow
                        key={occ.id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/scadenzario/${occ.id}`)}
                      >
                        <TableCell className="text-sm">{occ.descrizione}</TableCell>
                        <TableCell>{formatDate(occ.data_scadenza)}</TableCell>
                        <TableCell className="text-right font-mono">
                          {formatCurrency(occ.importo_totale)}
                        </TableCell>
                        <TableCell>
                          <ScheduleStatusBadge status={occ.stato} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </TabsContent>
        )}
      </Tabs>

      <PaymentDialog
        schedule={schedule}
        open={paymentOpen}
        onOpenChange={setPaymentOpen}
        onCreated={reload}
      />

      <ReminderDialog
        scheduleId={scheduleId}
        open={reminderOpen}
        onOpenChange={setReminderOpen}
        onCreated={() => loadRelated()}
      />
    </div>
  );
}
