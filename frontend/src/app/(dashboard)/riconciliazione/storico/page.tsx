"use client";

import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { History } from "lucide-react";
import type { Reconciliation, ReconciliationListResponse } from "@/types/reconciliation";

const statusLabels: Record<string, string> = {
  confirmed: "Confermata",
  pending: "In attesa",
  cancelled: "Annullata",
};

const typeLabels: Record<string, string> = {
  automatic: "Automatica",
  manual: "Manuale",
  suggested: "Suggerita",
};

export default function StoricoPage() {
  const { currentCompany } = useAuthStore();
  const isAdmin = ["owner", "admin"].includes(currentCompany?.role ?? "");

  const [items, setItems] = useState<Reconciliation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: page.toString(), page_size: "50" });
      if (statusFilter) params.set("status", statusFilter);
      if (typeFilter) params.set("type", typeFilter);
      const resp = await api.get<ReconciliationListResponse>(`/reconciliation?${params}`);
      setItems(resp.data.items);
      setTotal(resp.data.total);
    } catch {
      toast.error("Errore nel caricamento");
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, typeFilter]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleUndo = async (id: string) => {
    try {
      await api.post(`/reconciliation/${id}/undo`);
      toast.success("Riconciliazione annullata");
      loadData();
    } catch {
      toast.error("Errore nell'annullamento");
    }
  };

  const totalPages = Math.ceil(total / 50);

  return (
    <div className="space-y-4">
      <PageHeader title="Storico Riconciliazioni" description="Tutte le riconciliazioni effettuate" />

      <div className="flex gap-3">
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v === "all" ? "" : v); setPage(1); }}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Stato" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tutti</SelectItem>
            <SelectItem value="confirmed">Confermate</SelectItem>
            <SelectItem value="pending">In attesa</SelectItem>
            <SelectItem value="cancelled">Annullate</SelectItem>
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={(v) => { setTypeFilter(v === "all" ? "" : v); setPage(1); }}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Tipo" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tutti</SelectItem>
            <SelectItem value="automatic">Automatica</SelectItem>
            <SelectItem value="manual">Manuale</SelectItem>
            <SelectItem value="suggested">Suggerita</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {loading ? <LoadingState /> : items.length === 0 ? (
        <EmptyState icon={History} title="Nessuna riconciliazione" description="Non ci sono riconciliazioni nel periodo selezionato" />
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Stato</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Regola</TableHead>
                <TableHead>Righe</TableHead>
                <TableHead>Note</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((rec) => (
                <TableRow key={rec.id}>
                  <TableCell>{new Date(rec.reconciliation_date).toLocaleDateString("it-IT")}</TableCell>
                  <TableCell><Badge variant="outline">{typeLabels[rec.type] ?? rec.type}</Badge></TableCell>
                  <TableCell>
                    <Badge variant={rec.status === "confirmed" ? "default" : rec.status === "pending" ? "secondary" : "destructive"}>
                      {statusLabels[rec.status] ?? rec.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{rec.matching_score != null ? `${rec.matching_score}%` : "—"}</TableCell>
                  <TableCell className="text-xs">{rec.applied_rule ?? "—"}</TableCell>
                  <TableCell>{rec.lines.length}</TableCell>
                  <TableCell className="max-w-32 truncate text-xs">{rec.notes ?? ""}</TableCell>
                  <TableCell>
                    {isAdmin && rec.status === "confirmed" && (
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button size="sm" variant="ghost">Annulla</Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Annullare la riconciliazione?</AlertDialogTitle>
                            <AlertDialogDescription>I movimenti e le transazioni attese torneranno allo stato precedente.</AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>No</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleUndo(rec.id)}>Annulla riconciliazione</AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">{total} totali</p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Precedente</Button>
                <span className="flex items-center text-sm px-2">Pagina {page} di {totalPages}</span>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Successiva</Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
