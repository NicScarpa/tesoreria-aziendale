"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, FileText } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ExpectedTransactionDialog } from "@/components/reconciliation/expected-transaction-dialog";
import type { ExpectedTransaction, ExpectedTransactionListResponse } from "@/types/reconciliation";

const statusColors: Record<string, string> = {
  open: "bg-blue-100 text-blue-800",
  partially_matched: "bg-yellow-100 text-yellow-800",
  matched: "bg-green-100 text-green-800",
  expired: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
};

const statusLabels: Record<string, string> = {
  open: "Aperta",
  partially_matched: "Parz. matchata",
  matched: "Matchata",
  expired: "Scaduta",
  cancelled: "Annullata",
};

const docTypeLabels: Record<string, string> = {
  sales_invoice: "Fatt. vendita",
  purchase_invoice: "Fatt. acquisto",
  credit_note: "Nota credito",
  debit_note: "Nota debito",
  salary: "Stipendio",
  tax: "Tributo",
  other: "Altro",
};

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(amount);
}

export default function ExpectedTransactionsPage() {
  const { currentCompany } = useAuthStore();
  const canEdit = ["owner", "admin", "editor"].includes(currentCompany?.role ?? "");
  const isAdmin = ["owner", "admin"].includes(currentCompany?.role ?? "");

  const [items, setItems] = useState<ExpectedTransaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<ExpectedTransaction | null>(null);
  const [totals, setTotals] = useState({ expected: 0, matched: 0 });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", page.toString());
      params.set("page_size", "50");
      if (search) params.set("search", search);
      if (statusFilter) params.set("status", statusFilter);
      if (typeFilter) params.set("type", typeFilter);
      const resp = await api.get<ExpectedTransactionListResponse>(`/expected-transactions?${params}`);
      setItems(resp.data.items);
      setTotal(resp.data.total);
      setTotals({
        expected: resp.data.total_expected_amount,
        matched: resp.data.total_matched_amount,
      });
    } catch {
      toast.error("Errore nel caricamento");
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter, typeFilter]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleDelete = async (id: string) => {
    if (!confirm("Eliminare questa transazione attesa?")) return;
    try {
      await api.delete(`/expected-transactions/${id}`);
      toast.success("Eliminata");
      loadData();
    } catch {
      toast.error("Errore nell'eliminazione");
    }
  };

  const totalPages = Math.ceil(total / 50);

  return (
    <div className="space-y-4">
      <PageHeader
        title="Transazioni Attese"
        description="Fatture, scadenze e pagamenti attesi"
        actions={
          canEdit ? (
            <Button size="sm" onClick={() => { setEditingItem(null); setDialogOpen(true); }}>
              <Plus className="h-4 w-4 mr-1" />
              Nuova
            </Button>
          ) : undefined
        }
      />

      <div className="flex gap-3 items-center">
        <Input
          placeholder="Cerca..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="max-w-xs"
        />
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v === "all" ? "" : v); setPage(1); }}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Stato" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tutti</SelectItem>
            <SelectItem value="open">Aperte</SelectItem>
            <SelectItem value="partially_matched">Parz. matchate</SelectItem>
            <SelectItem value="matched">Matchate</SelectItem>
            <SelectItem value="expired">Scadute</SelectItem>
            <SelectItem value="cancelled">Annullate</SelectItem>
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={(v) => { setTypeFilter(v === "all" ? "" : v); setPage(1); }}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Tipo" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tutti</SelectItem>
            <SelectItem value="expected_inflow">Entrata</SelectItem>
            <SelectItem value="expected_outflow">Uscita</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex gap-4 text-sm text-muted-foreground">
        <span>Totale atteso: <strong className="text-foreground">{formatCurrency(totals.expected)}</strong></span>
        <span>Totale matchato: <strong className="text-foreground">{formatCurrency(totals.matched)}</strong></span>
      </div>

      {loading ? (
        <LoadingState />
      ) : items.length === 0 ? (
        <EmptyState icon={FileText} title="Nessuna transazione attesa" description="Crea una nuova transazione attesa per iniziare" />
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Scadenza</TableHead>
                <TableHead>Controparte</TableHead>
                <TableHead>Tipo doc.</TableHead>
                <TableHead>Riferimento</TableHead>
                <TableHead className="text-right">Importo</TableHead>
                <TableHead className="text-right">Matchato</TableHead>
                <TableHead>Stato</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((et) => (
                <TableRow key={et.id} className="cursor-pointer" onClick={() => { setEditingItem(et); setDialogOpen(true); }}>
                  <TableCell>{new Date(et.due_date).toLocaleDateString("it-IT")}</TableCell>
                  <TableCell>{et.counterpart_name ?? "—"}</TableCell>
                  <TableCell>{docTypeLabels[et.document_type] ?? et.document_type}</TableCell>
                  <TableCell className="font-mono text-xs">{et.reference_number ?? "—"}</TableCell>
                  <TableCell className={`text-right font-medium ${et.type === "expected_inflow" ? "text-green-600" : "text-red-600"}`}>
                    {et.type === "expected_inflow" ? "+" : "-"}{formatCurrency(et.expected_amount)}
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(et.matched_amount)}</TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[et.status] ?? ""}`}>
                      {statusLabels[et.status] ?? et.status}
                    </span>
                  </TableCell>
                  <TableCell>
                    {isAdmin && et.status === "open" && (
                      <Button size="sm" variant="ghost" onClick={(e) => { e.stopPropagation(); handleDelete(et.id); }}>
                        Elimina
                      </Button>
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

      <ExpectedTransactionDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        item={editingItem}
        onSaved={loadData}
      />
    </div>
  );
}
