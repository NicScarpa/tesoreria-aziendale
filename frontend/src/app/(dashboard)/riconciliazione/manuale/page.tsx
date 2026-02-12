"use client";

import { useEffect, useState, useCallback } from "react";
import { Link2 } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import type { Transaction, TransactionListResponse } from "@/types/transaction";
import type { ExpectedTransaction, ExpectedTransactionListResponse } from "@/types/reconciliation";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(amount);
}

export default function ManualReconciliationPage() {
  const { currentCompany } = useAuthStore();
  const canEdit = ["owner", "admin", "editor"].includes(currentCompany?.role ?? "");

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [expected, setExpected] = useState<ExpectedTransaction[]>([]);
  const [loadingTx, setLoadingTx] = useState(true);
  const [loadingEt, setLoadingEt] = useState(true);
  const [selectedTxIds, setSelectedTxIds] = useState<Set<string>>(new Set());
  const [selectedEtIds, setSelectedEtIds] = useState<Set<string>>(new Set());
  const [notes, setNotes] = useState("");
  const [searchTx, setSearchTx] = useState("");
  const [searchEt, setSearchEt] = useState("");

  const loadTransactions = useCallback(async () => {
    setLoadingTx(true);
    try {
      const params = new URLSearchParams({ page_size: "100" });
      if (searchTx) params.set("search", searchTx);
      const resp = await api.get<TransactionListResponse>(`/transactions?${params}`);
      // Filter only unreconciled on client side
      setTransactions(resp.data.items.filter(t => t.reconciliation_status === "unreconciled" || !t.reconciliation_status));
    } catch {
      toast.error("Errore caricamento movimenti");
    } finally {
      setLoadingTx(false);
    }
  }, [searchTx]);

  const loadExpected = useCallback(async () => {
    setLoadingEt(true);
    try {
      const params = new URLSearchParams({ page_size: "100", status: "open" });
      if (searchEt) params.set("search", searchEt);
      const resp = await api.get<ExpectedTransactionListResponse>(`/expected-transactions?${params}`);
      setExpected(resp.data.items);
    } catch {
      toast.error("Errore caricamento attese");
    } finally {
      setLoadingEt(false);
    }
  }, [searchEt]);

  useEffect(() => { loadTransactions(); }, [loadTransactions]);
  useEffect(() => { loadExpected(); }, [loadExpected]);

  const toggleTx = (id: string) => {
    const next = new Set(selectedTxIds);
    if (next.has(id)) { next.delete(id); } else { next.add(id); }
    setSelectedTxIds(next);
  };

  const toggleEt = (id: string) => {
    const next = new Set(selectedEtIds);
    if (next.has(id)) { next.delete(id); } else { next.add(id); }
    setSelectedEtIds(next);
  };

  const selectedTxTotal = transactions
    .filter(t => selectedTxIds.has(t.id))
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  const selectedEtTotal = expected
    .filter(e => selectedEtIds.has(e.id))
    .reduce((sum, e) => sum + (e.expected_amount - e.matched_amount), 0);

  const diff = Math.abs(selectedTxTotal - selectedEtTotal);
  const canReconcile = canEdit && selectedTxIds.size > 0 && selectedEtIds.size > 0;

  const handleReconcile = async () => {
    try {
      await api.post("/reconciliation", {
        transaction_ids: Array.from(selectedTxIds),
        expected_transaction_ids: Array.from(selectedEtIds),
        notes: notes || undefined,
      });
      toast.success("Riconciliazione creata");
      setSelectedTxIds(new Set());
      setSelectedEtIds(new Set());
      setNotes("");
      loadTransactions();
      loadExpected();
    } catch {
      toast.error("Errore nella riconciliazione");
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Riconciliazione Manuale" description="Seleziona movimenti e transazioni attese da riconciliare" />

      {/* Match bar */}
      <Card className="p-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 text-sm">
            <span>Movimenti: <strong>{formatCurrency(selectedTxTotal)}</strong></span>
            <span>Attese: <strong>{formatCurrency(selectedEtTotal)}</strong></span>
            <Badge variant={diff < 0.01 ? "default" : "secondary"}>
              Diff: {formatCurrency(diff)}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Textarea
              placeholder="Note..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="h-9 min-h-0 w-48 resize-none"
            />
            <Button onClick={handleReconcile} disabled={!canReconcile}>
              <Link2 className="h-4 w-4 mr-1" />
              Riconcilia
            </Button>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left: Transactions */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold">Movimenti non riconciliati</h3>
            <Input placeholder="Cerca..." value={searchTx} onChange={(e) => setSearchTx(e.target.value)} className="max-w-48 h-8" />
          </div>
          {loadingTx ? <LoadingState /> : (
            <div className="space-y-1 max-h-[60vh] overflow-y-auto">
              {transactions.map(tx => (
                <div
                  key={tx.id}
                  onClick={() => toggleTx(tx.id)}
                  className={`flex items-center gap-3 p-3 rounded-md border cursor-pointer transition-colors ${
                    selectedTxIds.has(tx.id) ? "border-primary bg-primary/5" : "hover:bg-accent"
                  }`}
                >
                  <Checkbox checked={selectedTxIds.has(tx.id)} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{tx.description ?? "—"}</p>
                    <p className="text-xs text-muted-foreground">{tx.counterpart_name ?? ""} &middot; {new Date(tx.transaction_date).toLocaleDateString("it-IT")}</p>
                  </div>
                  <span className={`text-sm font-medium ${tx.direction === "inflow" ? "text-green-600" : "text-red-600"}`}>
                    {tx.direction === "inflow" ? "+" : "-"}{formatCurrency(Math.abs(tx.amount))}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Expected */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold">Transazioni attese</h3>
            <Input placeholder="Cerca..." value={searchEt} onChange={(e) => setSearchEt(e.target.value)} className="max-w-48 h-8" />
          </div>
          {loadingEt ? <LoadingState /> : (
            <div className="space-y-1 max-h-[60vh] overflow-y-auto">
              {expected.map(et => (
                <div
                  key={et.id}
                  onClick={() => toggleEt(et.id)}
                  className={`flex items-center gap-3 p-3 rounded-md border cursor-pointer transition-colors ${
                    selectedEtIds.has(et.id) ? "border-primary bg-primary/5" : "hover:bg-accent"
                  }`}
                >
                  <Checkbox checked={selectedEtIds.has(et.id)} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{et.description ?? et.counterpart_name ?? "—"}</p>
                    <p className="text-xs text-muted-foreground">{et.reference_number ?? ""} &middot; Scad. {new Date(et.due_date).toLocaleDateString("it-IT")}</p>
                  </div>
                  <span className={`text-sm font-medium ${et.type === "expected_inflow" ? "text-green-600" : "text-red-600"}`}>
                    {et.type === "expected_inflow" ? "+" : "-"}{formatCurrency(et.expected_amount)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
