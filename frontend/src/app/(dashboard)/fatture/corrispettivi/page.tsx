"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ReceiptText, RefreshCw, Download, Bug, ChevronLeft, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import { listCorrispettivi, downloadCorrispettivoRaw, adeSyncCorrispettivi } from "@/lib/api/integrations";
import type { ReceiptImport } from "@/types/integration";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

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

export default function CorrispettiviPage() {
  const [items, setItems] = useState<ReceiptImport[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Filters
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Sync dialog
  const [showSync, setShowSync] = useState(false);
  const [syncFrom, setSyncFrom] = useState(yearStartISO());
  const [syncTo, setSyncTo] = useState(todayISO());
  const [debug, setDebug] = useState(false);

  // Device toggle
  const [showDevices, setShowDevices] = useState(false);

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

  if (loading && items.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title="Corrispettivi" description="Importa e consulta i corrispettivi da AdE" />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Corrispettivi"
        description="Importa e consulta i corrispettivi da AdE"
        actions={
          <Button variant="outline" onClick={() => setShowSync(true)}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Sincronizza
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="space-y-1">
          <Label>Data da</Label>
          <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="w-[170px]" />
        </div>
        <div className="space-y-1">
          <Label>Data a</Label>
          <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="w-[170px]" />
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <Switch checked={showDevices} onCheckedChange={setShowDevices} />
          <Label className="text-sm">Mostra dispositivi</Label>
        </div>
      </div>

      {/* Device badges */}
      {showDevices && uniqueDevices.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {uniqueDevices.map((d) => (
            <Badge key={d} variant="outline">{d}</Badge>
          ))}
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState
          icon={ReceiptText}
          title="Nessun corrispettivo"
          description="Avvia una sincronizzazione da Agenzia Entrate per popolare la lista"
          actionLabel="Sincronizza"
          onAction={() => setShowSync(true)}
        />
      ) : (
        <>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data</TableHead>
                  <TableHead>Dispositivo</TableHead>
                  <TableHead>External ID</TableHead>
                  <TableHead className="text-right">Totale</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="text-sm">{formatDate(r.business_date)}</TableCell>
                    <TableCell className="text-sm">{r.device_id || "\u2014"}</TableCell>
                    <TableCell className="text-sm">{r.external_id || "\u2014"}</TableCell>
                    <TableCell className="text-sm text-right">{formatCurrency(r.gross_total)}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{r.status}</Badge>
                      {r.errore_dettaglio && (
                        <div className="text-xs text-destructive mt-1 line-clamp-1">{r.errore_dettaglio}</div>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={!r.raw_available}
                        onClick={() => handleDownloadRaw(r.id, r.business_date)}
                      >
                        <Download className="h-4 w-4 mr-1" /> Raw
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
                {total} corrispettivi &middot; Pagina {page} di {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

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
