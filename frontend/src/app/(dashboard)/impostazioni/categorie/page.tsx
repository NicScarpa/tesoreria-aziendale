"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Tag } from "lucide-react";
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
import { CategoryList } from "@/components/categories/category-list";
import { CategoryDialog } from "@/components/categories/category-dialog";
import type { Category } from "@/types/category";

export default function CategoriePage() {
  const { currentCompany } = useAuthStore();
  const userRole = currentCompany?.role;
  const canEdit = userRole === "owner" || userRole === "admin" || userRole === "editor";
  const canDelete = userRole === "owner" || userRole === "admin";

  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Category | null>(null);
  const [subParentCategory, setSubParentCategory] = useState<Category | null>(null);

  const loadCategories = useCallback(async () => {
    try {
      const resp = await api.get<Category[]>("/categories");
      setCategories(resp.data);
    } catch {
      toast.error("Errore nel caricamento delle categorie");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  const handleDeleteCategory = async () => {
    if (!deleteTarget) return;
    try {
      await api.delete(`/categories/${deleteTarget.id}`);
      toast.success("Categoria eliminata");
      loadCategories();
    } catch {
      toast.error("Errore nell'eliminazione della categoria");
    } finally {
      setDeleteTarget(null);
    }
  };

  const handleAddSubcategory = async () => {
    // Will be handled by a simple prompt
    if (!subParentCategory) return;
    const name = prompt("Nome sottocategoria:");
    if (!name?.trim()) return;
    try {
      await api.post(`/categories/${subParentCategory.id}/subcategories`, { name });
      toast.success("Sottocategoria creata");
      loadCategories();
    } catch (err: unknown) {
      const error = err as { response?: { status?: number } };
      if (error.response?.status === 409) {
        toast.error("Esiste già una sottocategoria con questo nome");
      } else {
        toast.error("Errore nella creazione");
      }
    }
    setSubParentCategory(null);
  };

  const handleDeleteSubcategory = async (sub: { id: string; name: string }) => {
    if (!confirm(`Eliminare la sottocategoria "${sub.name}"?`)) return;
    try {
      await api.delete(`/categories/subcategories/${sub.id}`);
      toast.success("Sottocategoria eliminata");
      loadCategories();
    } catch {
      toast.error("Errore nell'eliminazione");
    }
  };

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Categorie"
        description="Gestisci le categorie per classificare i movimenti bancari"
        actions={
          canEdit ? (
            <Button
              size="sm"
              onClick={() => {
                setEditingCategory(null);
                setDialogOpen(true);
              }}
            >
              <Plus className="h-4 w-4 mr-1" />
              Nuova categoria
            </Button>
          ) : undefined
        }
      />

      {categories.length === 0 ? (
        <EmptyState
          icon={Tag}
          title="Nessuna categoria"
          description="Crea la prima categoria per classificare i movimenti"
          actionLabel={canEdit ? "Crea categoria" : undefined}
          onAction={canEdit ? () => setDialogOpen(true) : undefined}
        />
      ) : (
        <CategoryList
          categories={categories}
          onEditCategory={(cat) => {
            setEditingCategory(cat);
            setDialogOpen(true);
          }}
          onDeleteCategory={setDeleteTarget}
          onAddSubcategory={(cat) => {
            setSubParentCategory(cat);
            handleAddSubcategory();
          }}
          onEditSubcategory={async (sub) => {
            const name = prompt("Nuovo nome:", sub.name);
            if (!name?.trim()) return;
            try {
              await api.patch(`/categories/subcategories/${sub.id}`, { name });
              toast.success("Sottocategoria aggiornata");
              loadCategories();
            } catch {
              toast.error("Errore nell'aggiornamento");
            }
          }}
          onDeleteSubcategory={handleDeleteSubcategory}
          canEdit={canEdit}
          canDelete={canDelete}
        />
      )}

      <CategoryDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        category={editingCategory}
        onSaved={loadCategories}
      />

      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminare la categoria?</AlertDialogTitle>
            <AlertDialogDescription>
              I movimenti associati a &quot;{deleteTarget?.name}&quot; verranno scollegati dalla categoria.
              Le regole di categorizzazione associate verranno eliminate.
              Questa azione non può essere annullata.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annulla</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteCategory} className="bg-red-600 hover:bg-red-700">
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
