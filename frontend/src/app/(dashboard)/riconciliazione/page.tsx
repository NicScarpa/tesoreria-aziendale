"use client";

import { useEffect, useState, useCallback } from "react";
import { Play, CheckCircle2, XCircle, Inbox } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { DashboardData, Reconciliation } from "@/types/reconciliation";

function ScoreBadge({ score }: { score: number | null }) {
  if (score == null) return null;
  const variant = score >= 80 ? "default" : score >= 50 ? "secondary" : "destructive";
  return <Badge variant={variant}>{score}%</Badge>;
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(amount);
}

export default function ReconciliationDashboardPage() {
  const { currentCompany } = useAuthStore();
  const canEdit = ["owner", "admin", "editor"].includes(currentCompany?.role ?? "");

  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [suggestions, setSuggestions] = useState<Reconciliation[]>([]);
  const [loading, setLoading] = useState(true);
  const [matching, setMatching] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [dashResp, sugResp] = await Promise.all([
        api.get<DashboardData>("/reconciliation/dashboard"),
        api.get<Reconciliation[]>("/reconciliation/suggestions"),
      ]);
      setDashboard(dashResp.data);
      setSuggestions(sugResp.data);
    } catch {
      toast.error("Errore nel caricamento della dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleAutoMatch = async () => {
    setMatching(true);
    try {
      const resp = await api.post("/reconciliation/auto-match", { dry_run: false });
      const { total_matches, confirmed, suggested } = resp.data;
      toast.success(`${total_matches} match trovati: ${confirmed} confermati, ${suggested} da confermare`);
      loadData();
    } catch {
      toast.error("Errore nell'auto-riconciliazione");
    } finally {
      setMatching(false);
    }
  };

  const handleConfirm = async (id: string) => {
    try {
      await api.put(`/reconciliation/${id}/confirm`);
      toast.success("Riconciliazione confermata");
      loadData();
    } catch {
      toast.error("Errore nella conferma");
    }
  };

  const handleReject = async (id: string) => {
    try {
      await api.put(`/reconciliation/${id}/reject`);
      toast.success("Suggerimento rifiutato");
      loadData();
    } catch {
      toast.error("Errore nel rifiuto");
    }
  };

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Riconciliazione"
        description="Panoramica stato riconciliazione bancaria"
        actions={
          canEdit ? (
            <Button onClick={handleAutoMatch} disabled={matching}>
              <Play className="h-4 w-4 mr-1" />
              {matching ? "Elaborazione..." : "Auto-Riconcilia"}
            </Button>
          ) : undefined
        }
      />

      {dashboard && (
        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-5">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Non riconciliati</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">{dashboard.unreconciled_transactions}</div><p className="text-xs text-muted-foreground">{formatCurrency(dashboard.total_unreconciled_amount)}</p></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Attese aperte</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">{dashboard.open_expected}</div><p className="text-xs text-muted-foreground">{formatCurrency(dashboard.total_open_expected_amount)}</p></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Suggerimenti</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">{dashboard.pending_suggestions}</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">% Riconciliazione</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">{dashboard.reconciliation_rate}%</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Scadute</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-destructive">{dashboard.expired_expected}</div></CardContent>
          </Card>
        </div>
      )}

      <div>
        <h3 className="text-lg font-semibold mb-4">Suggerimenti pendenti</h3>
        {suggestions.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="Nessun suggerimento"
            description="Esegui l'auto-riconciliazione per generare suggerimenti di match"
          />
        ) : (
          <div className="space-y-3">
            {suggestions.map((rec) => (
              <Card key={rec.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ScoreBadge score={rec.matching_score} />
                    <div>
                      <p className="text-sm font-medium">
                        {rec.applied_rule ?? "Match automatico"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {rec.lines.length} righe &middot;{" "}
                        {new Date(rec.reconciliation_date).toLocaleDateString("it-IT")}
                      </p>
                    </div>
                  </div>
                  {canEdit && (
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => handleReject(rec.id)}>
                        <XCircle className="h-4 w-4 mr-1" />
                        Rifiuta
                      </Button>
                      <Button size="sm" onClick={() => handleConfirm(rec.id)}>
                        <CheckCircle2 className="h-4 w-4 mr-1" />
                        Conferma
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
