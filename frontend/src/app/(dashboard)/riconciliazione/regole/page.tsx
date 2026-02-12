"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, GripVertical, TestTube, Settings2 } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import { ReconciliationRuleDialog } from "@/components/reconciliation/reconciliation-rule-dialog";
import type { ReconciliationRule } from "@/types/reconciliation";

export default function RegolePage() {
  const { currentCompany } = useAuthStore();
  const isAdmin = ["owner", "admin"].includes(currentCompany?.role ?? "");
  const canEdit = ["owner", "admin", "editor"].includes(currentCompany?.role ?? "");

  const [rules, setRules] = useState<ReconciliationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<ReconciliationRule | null>(null);

  const loadRules = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await api.get<ReconciliationRule[]>("/reconciliation-rules");
      setRules(resp.data);
    } catch {
      toast.error("Errore nel caricamento regole");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadRules(); }, [loadRules]);

  const handleToggle = async (rule: ReconciliationRule) => {
    try {
      await api.patch(`/reconciliation-rules/${rule.id}`, { is_active: !rule.is_active });
      toast.success(rule.is_active ? "Regola disattivata" : "Regola attivata");
      loadRules();
    } catch {
      toast.error("Errore nell'aggiornamento");
    }
  };

  const handleTest = async (rule: ReconciliationRule) => {
    try {
      const resp = await api.post(`/reconciliation-rules/${rule.id}/test`);
      const { matching_count } = resp.data;
      toast.info(`La regola "${rule.name}" trova ${matching_count} match potenziali`);
    } catch {
      toast.error("Errore nel test");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Eliminare questa regola?")) return;
    try {
      await api.delete(`/reconciliation-rules/${id}`);
      toast.success("Regola eliminata");
      loadRules();
    } catch {
      toast.error("Errore nell'eliminazione");
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Regole di Riconciliazione"
        description="Configura le regole per il matching automatico"
        actions={
          isAdmin ? (
            <Button size="sm" onClick={() => { setEditingRule(null); setDialogOpen(true); }}>
              <Plus className="h-4 w-4 mr-1" />
              Nuova regola
            </Button>
          ) : undefined
        }
      />

      {loading ? <LoadingState /> : rules.length === 0 ? (
        <EmptyState icon={Settings2} title="Nessuna regola" description="Crea una regola per configurare il matching automatico" />
      ) : (
        <div className="space-y-3">
          {rules.map((rule) => (
            <Card key={rule.id} className="p-4">
              <div className="flex items-center gap-4">
                <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab" />
                <Switch checked={rule.is_active} onCheckedChange={() => handleToggle(rule)} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium">{rule.name}</p>
                    <Badge variant="outline">{rule.match_type}</Badge>
                    <Badge variant={rule.action === "auto_reconcile" ? "default" : "secondary"}>
                      {rule.action === "auto_reconcile" ? "Auto" : "Suggerimento"}
                    </Badge>
                  </div>
                  {rule.description && <p className="text-xs text-muted-foreground mt-1">{rule.description}</p>}
                  <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
                    <span>Priorita: {rule.priority}</span>
                    <span>Confidenza min: {(rule.min_confidence * 100).toFixed(0)}%</span>
                    <span>Applicata: {rule.times_applied}x</span>
                    {rule.confirmation_rate != null && <span>Tasso conferma: {rule.confirmation_rate}%</span>}
                  </div>
                </div>
                <div className="flex gap-1">
                  {canEdit && (
                    <Button size="sm" variant="ghost" onClick={() => handleTest(rule)}>
                      <TestTube className="h-4 w-4" />
                    </Button>
                  )}
                  {isAdmin && (
                    <>
                      <Button size="sm" variant="ghost" onClick={() => { setEditingRule(rule); setDialogOpen(true); }}>
                        Modifica
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => handleDelete(rule.id)}>
                        Elimina
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <ReconciliationRuleDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        rule={editingRule}
        onSaved={loadRules}
      />
    </div>
  );
}
