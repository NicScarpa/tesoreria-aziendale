"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Pencil, Star } from "lucide-react";
import { toast } from "sonner";
import { format, subDays } from "date-fns";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { formatIBAN } from "@/lib/iban";
import type {
  BankAccount,
  BankAccountBalance,
  BalanceChartPoint,
  BankAccountAccess,
} from "@/types/bank-account";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BalanceChart } from "@/components/bank-accounts/balance-chart";
import { BalanceHistoryTable } from "@/components/bank-accounts/balance-history-table";
import { AccessTable } from "@/components/bank-accounts/access-table";
import { UpdateBalanceDialog } from "@/components/bank-accounts/update-balance-dialog";
import { EditBankAccountSheet } from "@/components/bank-accounts/edit-bank-account-sheet";
import { TransactionTable } from "@/components/transactions/transaction-table";
import { TransactionDetailSheet } from "@/components/transactions/transaction-detail-sheet";
import type { Transaction, TransactionListResponse } from "@/types/transaction";
import type { Category } from "@/types/category";
import type { Schedule, ScheduleListResponse } from "@/types/schedule";
import { ScheduleStatusBadge } from "@/components/schedules/schedule-status-badge";
import { CashFlow30DaysWidget } from "@/components/cash-flow/CashFlow30DaysWidget";

function formatCurrency(value: number | null, currency = "EUR"): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency }).format(value);
}

const STATUS_LABELS: Record<string, string> = {
  active: "Attivo",
  inactive: "Inattivo",
  hidden: "Nascosto",
  closed: "Chiuso",
  blocked: "Bloccato",
};

const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  checking: "Conto corrente",
  savings: "Risparmio",
  cash: "Cassa",
  credit_card: "Carta di credito",
  loan: "Prestito",
  other: "Altro",
};

export default function ContoDetailPage() {
  const params = useParams();
  const router = useRouter();
  const accountId = params.id as string;

  const { currentCompany } = useAuthStore();
  const userRole = currentCompany?.role;
  const canEdit = userRole === "owner" || userRole === "admin" || userRole === "editor";
  const isAdmin = userRole === "owner" || userRole === "admin";

  const [account, setAccount] = useState<BankAccount | null>(null);
  const [chartData, setChartData] = useState<BalanceChartPoint[]>([]);
  const [balances, setBalances] = useState<BankAccountBalance[]>([]);
  const [accesses, setAccesses] = useState<BankAccountAccess[]>([]);
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);

  const [editOpen, setEditOpen] = useState(false);
  const [balanceDialogOpen, setBalanceDialogOpen] = useState(false);

  const [accountTransactions, setAccountTransactions] = useState<Transaction[]>([]);
  const [txCategories, setTxCategories] = useState<Category[]>([]);
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [txDetailOpen, setTxDetailOpen] = useState(false);
  const [accountSchedules, setAccountSchedules] = useState<Schedule[]>([]);

  const loadAccount = useCallback(async () => {
    try {
      const res = await api.get<BankAccount>(`/bank-accounts/${accountId}`);
      setAccount(res.data);
    } catch {
      toast.error("Conto non trovato");
      router.push("/conti");
    } finally {
      setLoading(false);
    }
  }, [accountId, router]);

  const loadChart = useCallback(async () => {
    setChartLoading(true);
    try {
      const dateTo = format(new Date(), "yyyy-MM-dd");
      const dateFrom = format(subDays(new Date(), 30), "yyyy-MM-dd");
      const res = await api.get<BalanceChartPoint[]>(
        `/bank-accounts/${accountId}/balance-chart?date_from=${dateFrom}&date_to=${dateTo}`
      );
      setChartData(res.data);
    } catch {
      // Chart data is optional
    } finally {
      setChartLoading(false);
    }
  }, [accountId]);

  const loadBalances = useCallback(async () => {
    try {
      const res = await api.get<BankAccountBalance[]>(`/bank-accounts/${accountId}/balances`);
      setBalances(res.data);
    } catch {
      // Non-critical
    }
  }, [accountId]);

  const loadAccountTransactions = useCallback(async () => {
    try {
      const resp = await api.get<TransactionListResponse>(
        `/transactions?bank_account_id=${accountId}&page_size=20`
      );
      setAccountTransactions(resp.data.items);
    } catch {
      // Non-critical
    }
  }, [accountId]);

  const loadTxCategories = useCallback(async () => {
    try {
      const resp = await api.get<Category[]>("/categories");
      setTxCategories(resp.data);
    } catch {}
  }, []);

  const loadAccountSchedules = useCallback(async () => {
    try {
      const resp = await api.get<ScheduleListResponse>(
        `/schedules?bank_account_id=${accountId}&stato=aperta&page_size=10`
      );
      setAccountSchedules(resp.data.items);
    } catch {
      // Non-critical
    }
  }, [accountId]);

  const loadAccesses = useCallback(async () => {
    if (!isAdmin) return;
    try {
      const res = await api.get<BankAccountAccess[]>(`/bank-accounts/${accountId}/accesses`);
      setAccesses(res.data);
    } catch {
      // Non-critical
    }
  }, [accountId, isAdmin]);

  useEffect(() => {
    loadAccount();
    loadChart();
    loadBalances();
    loadAccesses();
    loadAccountTransactions();
    loadTxCategories();
    loadAccountSchedules();
  }, [loadAccount, loadChart, loadBalances, loadAccesses, loadAccountTransactions, loadTxCategories, loadAccountSchedules]);

  const reload = () => {
    loadAccount();
    loadChart();
    loadBalances();
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <LoadingState />
      </div>
    );
  }

  if (!account) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/conti")}>
          <ArrowLeft className="h-4 w-4 mr-1" />
          Conti
        </Button>
      </div>

      <PageHeader
        title={
          <span className="flex items-center gap-2">
            <span
              className="h-4 w-4 rounded-full shrink-0"
              style={{ backgroundColor: account.color || "#6b7280" }}
            />
            {account.nickname || "Conto"}
            {account.is_default && (
              <Star className="h-5 w-5 text-amber-500 fill-amber-500" />
            )}
          </span>
        }
        description={account.iban ? formatIBAN(account.iban) : undefined}
        actions={
          canEdit ? (
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setBalanceDialogOpen(true)}>
                Aggiorna saldo
              </Button>
              <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
                <Pencil className="h-4 w-4 mr-1" />
                Modifica
              </Button>
            </div>
          ) : undefined
        }
      />

      {/* Saldi quick info */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Saldo contabile</p>
            <p className="text-2xl font-bold">
              {formatCurrency(account.current_balance, account.currency)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Saldo disponibile</p>
            <p className="text-2xl font-bold">
              {formatCurrency(account.available_balance, account.currency)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Fido bancario</p>
            <p className="text-2xl font-bold">
              {formatCurrency(account.credit_limit, account.currency)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Panoramica</TabsTrigger>
          <TabsTrigger value="movements">Movimenti</TabsTrigger>
          <TabsTrigger value="schedules">Scadenze</TabsTrigger>
          <TabsTrigger value="balances">Storico saldi</TabsTrigger>
          {isAdmin && <TabsTrigger value="accesses">Accessi</TabsTrigger>}
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <BalanceChart data={chartData} loading={chartLoading} />

          <CashFlow30DaysWidget accountId={accountId} />

          <Card>
            <CardHeader>
              <CardTitle>Dettagli conto</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-muted-foreground">Stato</dt>
                  <dd>
                    <Badge variant={account.status === "active" ? "default" : "secondary"}>
                      {STATUS_LABELS[account.status] || account.status}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Tipo</dt>
                  <dd>{account.account_type ? ACCOUNT_TYPE_LABELS[account.account_type] : "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Banca</dt>
                  <dd>{account.bank_name || "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Valuta</dt>
                  <dd>{account.currency}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">BIC</dt>
                  <dd className="font-mono">{account.bic || "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">ABI / CAB</dt>
                  <dd className="font-mono">
                    {account.bank_abi && account.bank_cab
                      ? `${account.bank_abi} / ${account.bank_cab}`
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Connessione</dt>
                  <dd>{account.bank_connection_id ? "Open Banking" : "Manuale"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Ultima sincronizzazione</dt>
                  <dd>
                    {account.last_synced_at
                      ? new Date(account.last_synced_at).toLocaleString("it-IT")
                      : "—"}
                  </dd>
                </div>
                {account.notes && (
                  <div className="col-span-2">
                    <dt className="text-muted-foreground">Note</dt>
                    <dd className="whitespace-pre-wrap">{account.notes}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="movements" className="space-y-4">
          <TransactionTable
            transactions={accountTransactions}
            onSelect={(tx) => {
              setSelectedTx(tx);
              setTxDetailOpen(true);
            }}
            onToggleVerified={canEdit ? async (tx) => {
              try {
                await api.patch(`/transactions/${tx.id}/verify`);
                loadAccountTransactions();
              } catch {}
            } : undefined}
          />
          {accountTransactions.length > 0 && (
            <div className="text-center">
              <Button
                variant="link"
                onClick={() => router.push(`/movimenti?bank_account_id=${accountId}`)}
              >
                Vedi tutti i movimenti
              </Button>
            </div>
          )}
        </TabsContent>

        <TabsContent value="schedules" className="space-y-4">
          {accountSchedules.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-sm text-muted-foreground">
                Nessuna scadenza aperta per questo conto.
              </CardContent>
            </Card>
          ) : (
            <>
              <Card>
                <CardContent className="p-0">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="px-4 py-3 font-medium">Scadenza</th>
                        <th className="px-4 py-3 font-medium">Tipo</th>
                        <th className="px-4 py-3 font-medium">Controparte</th>
                        <th className="px-4 py-3 font-medium text-right">Importo</th>
                        <th className="px-4 py-3 font-medium text-right">Residuo</th>
                        <th className="px-4 py-3 font-medium">Stato</th>
                      </tr>
                    </thead>
                    <tbody>
                      {accountSchedules.map((s) => (
                        <tr
                          key={s.id}
                          className="border-b cursor-pointer hover:bg-muted/50"
                          onClick={() => router.push(`/scadenzario/${s.id}`)}
                        >
                          <td className="px-4 py-3">
                            {new Date(s.data_scadenza).toLocaleDateString("it-IT")}
                          </td>
                          <td className="px-4 py-3 capitalize">{s.tipo}</td>
                          <td className="px-4 py-3">{s.controparte_nome || "—"}</td>
                          <td className="px-4 py-3 text-right font-mono">
                            {formatCurrency(s.importo_totale, account.currency)}
                          </td>
                          <td className="px-4 py-3 text-right font-mono font-semibold">
                            {formatCurrency(s.importo_residuo, account.currency)}
                          </td>
                          <td className="px-4 py-3">
                            <ScheduleStatusBadge status={s.stato} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
              <div className="text-center">
                <Button
                  variant="link"
                  onClick={() => router.push(`/scadenzario?bank_account_id=${accountId}`)}
                >
                  Vedi tutte le scadenze
                </Button>
              </div>
            </>
          )}
        </TabsContent>

        <TabsContent value="balances" className="space-y-4">
          <BalanceHistoryTable balances={balances} />
        </TabsContent>

        {isAdmin && (
          <TabsContent value="accesses">
            <AccessTable
              accountId={accountId}
              accesses={accesses}
              onRefresh={loadAccesses}
            />
          </TabsContent>
        )}
      </Tabs>

      <UpdateBalanceDialog
        account={account}
        open={balanceDialogOpen}
        onOpenChange={setBalanceDialogOpen}
        onUpdated={reload}
      />

      <EditBankAccountSheet
        account={account}
        open={editOpen}
        onOpenChange={setEditOpen}
        onUpdated={reload}
      />

      <TransactionDetailSheet
        transaction={selectedTx}
        open={txDetailOpen}
        onOpenChange={setTxDetailOpen}
        categories={txCategories}
        onUpdated={loadAccountTransactions}
      />
    </div>
  );
}
