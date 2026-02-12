"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Landmark, Search } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { BankAccount, BankAccountSummary } from "@/types/bank-account";
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
import { BankAccountSummaryCards } from "@/components/bank-accounts/bank-account-summary-cards";
import { BankAccountCard } from "@/components/bank-accounts/bank-account-card";
import { CreateBankAccountDialog } from "@/components/bank-accounts/create-bank-account-dialog";
import { UpdateBalanceDialog } from "@/components/bank-accounts/update-balance-dialog";
import { EditBankAccountSheet } from "@/components/bank-accounts/edit-bank-account-sheet";

export default function ContiPage() {
  const { currentCompany } = useAuthStore();
  const userRole = currentCompany?.role;
  const canEdit = userRole === "owner" || userRole === "admin" || userRole === "editor";
  const canDelete = userRole === "owner" || userRole === "admin";

  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [summary, setSummary] = useState<BankAccountSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const [createOpen, setCreateOpen] = useState(false);
  const [balanceAccount, setBalanceAccount] = useState<BankAccount | null>(null);
  const [editAccount, setEditAccount] = useState<BankAccount | null>(null);

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (statusFilter === "hidden") params.set("include_hidden", "true");

      const [accountsRes, summaryRes] = await Promise.all([
        api.get<BankAccount[]>(`/bank-accounts?${params}`),
        api.get<BankAccountSummary>("/bank-accounts/summary"),
      ]);
      setAccounts(accountsRes.data);
      setSummary(summaryRes.data);
    } catch {
      toast.error("Errore nel caricamento dei conti");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleHide = async (account: BankAccount) => {
    try {
      const endpoint = account.hidden_at ? "unhide" : "hide";
      await api.post(`/bank-accounts/${account.id}/${endpoint}`);
      toast.success(account.hidden_at ? "Conto mostrato" : "Conto nascosto");
      load();
    } catch {
      toast.error("Errore nell'operazione");
    }
  };

  const handleDelete = async (account: BankAccount) => {
    if (!confirm(`Sei sicuro di voler chiudere il conto "${account.nickname}"?`)) return;
    try {
      await api.delete(`/bank-accounts/${account.id}`);
      toast.success("Conto chiuso");
      load();
    } catch {
      toast.error("Errore nella chiusura del conto");
    }
  };

  const filtered = accounts.filter((a) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      a.nickname?.toLowerCase().includes(q) ||
      a.iban?.toLowerCase().includes(q) ||
      a.bank_name?.toLowerCase().includes(q)
    );
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Conti bancari" description="Gestisci i tuoi conti bancari" />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Conti bancari"
        description="Gestisci i tuoi conti bancari"
        actions={
          canEdit ? (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Nuovo conto
            </Button>
          ) : undefined
        }
      />

      <BankAccountSummaryCards summary={summary} />

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Cerca per nome, IBAN o banca..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Stato" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tutti</SelectItem>
            <SelectItem value="active">Attivi</SelectItem>
            <SelectItem value="closed">Chiusi</SelectItem>
            <SelectItem value="hidden">Nascosti</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon={Landmark}
          title="Nessun conto bancario"
          description="Aggiungi il tuo primo conto per iniziare"
          actionLabel={canEdit ? "Nuovo conto" : undefined}
          onAction={canEdit ? () => setCreateOpen(true) : undefined}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((account) => (
            <BankAccountCard
              key={account.id}
              account={account}
              canEdit={canEdit}
              canDelete={canDelete}
              onEdit={(a) => setEditAccount(a)}
              onHide={handleHide}
              onDelete={handleDelete}
              onUpdateBalance={(a) => setBalanceAccount(a)}
            />
          ))}
        </div>
      )}

      <CreateBankAccountDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={load}
      />

      <UpdateBalanceDialog
        account={balanceAccount}
        open={!!balanceAccount}
        onOpenChange={(open) => !open && setBalanceAccount(null)}
        onUpdated={load}
      />

      <EditBankAccountSheet
        account={editAccount}
        open={!!editAccount}
        onOpenChange={(open) => !open && setEditAccount(null)}
        onUpdated={load}
      />
    </div>
  );
}
