"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Zap } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { RuleList } from "@/components/categorization-rules/rule-list";
import { RuleDialog } from "@/components/categorization-rules/rule-dialog";
import type { CategorizationRule } from "@/types/categorization-rule";
import type { Category } from "@/types/category";

export default function RegolePage() {
  const { currentCompany } = useAuthStore();
  const userRole = currentCompany?.role;
  const canEdit = userRole === "owner" || userRole === "admin" || userRole === "editor";
  const canDelete = userRole === "owner" || userRole === "admin";

  const [rules, setRules] = useState<CategorizationRule[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<CategorizationRule | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<CategorizationRule | null>(null);

  const loadRules = useCallback(async () => {
    try {
      const resp = await api.get<CategorizationRule[]>("/categorization-rules");
      setRules(resp.data);
    } catch {
      toast.error("Errore nel caricamento delle regole");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadCategories = useCallback(async () => {
    try {
      const resp = await api.get<Category[]>("/categories");
      setCategories(resp.data);
    } catch {}
  }, []);

  useEffect(() => {
    loadRules();
    loadCategories();
  }, [loadRules, loadCategories]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(`/categorization-rules/${deleteTarget.id}`);
      toast.success("Regola eliminata");
      loadRules();
    } catch {
      toast.error("Errore nell'eliminazione");
    } finally {
      setDeleteTarget(null);
    }
  };

  const handleTest = async (rule: CategorizationRule) => {
    try {
      const resp = await api.post<{ matching_count: number }>(`/categorization-rules/${rule.id}/test`);
      toast.info(`${resp.data.matching_count} movimenti corrispondono a questa regola`);
    } catch {
      toast.error("Errore nel test della regola");
    }
  };

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regole di categorizzazione"
        description="Configura regole per categorizzare automaticamente i movimenti"
        actions={
          canEdit ? (
            <Button
              size="sm"
              onClick={() => {
                setEditingRule(null);
                setDialogOpen(true);
              }}
            >
              <Plus className="h-4 w-4 mr-1" />
              Nuova regola
            </Button>
          ) : undefined
        }
      />

      {rules.length === 0 ? (
        <EmptyState
          icon={Zap}
          title="Nessuna regola"
          description="Crea regole per categorizzare automaticamente i movimenti bancari"
          actionLabel={canEdit ? "Crea regola" : undefined}
          onAction={canEdit ? () => setDialogOpen(true) : undefined}
        />
      ) : (
        <RuleList
          rules={rules}
          onEdit={(rule) => {
            setEditingRule(rule);
            setDialogOpen(true);
          }}
          onDelete={setDeleteTarget}
          onTest={handleTest}
          canEdit={canEdit}
          canDelete={canDelete}
        />
      )}

      <RuleDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        rule={editingRule}
        categories={categories}
        onSaved={loadRules}
      />

      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminare la regola?</AlertDialogTitle>
            <AlertDialogDescription>
              La regola &quot;{deleteTarget?.name || "senza nome"}&quot; verrà eliminata definitivamente.
              I movimenti già categorizzati non verranno modificati.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annulla</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-600 hover:bg-red-700">
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
