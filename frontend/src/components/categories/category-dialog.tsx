"use client";

import { useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import type { Category } from "@/types/category";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  category?: Category | null;
  onSaved: () => void;
}

export function CategoryDialog({ open, onOpenChange, category, onSaved }: Props) {
  const isEdit = !!category;
  const [name, setName] = useState(category?.name || "");
  const [color, setColor] = useState(category?.color || "#6b7280");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) {
      toast.error("Nome categoria obbligatorio");
      return;
    }
    setSaving(true);
    try {
      if (isEdit) {
        await api.patch(`/categories/${category.id}`, { name, color });
        toast.success("Categoria aggiornata");
      } else {
        await api.post("/categories", { name, color });
        toast.success("Categoria creata");
      }
      onSaved();
      onOpenChange(false);
    } catch (err: unknown) {
      const error = err as { response?: { status?: number } };
      if (error.response?.status === 409) {
        toast.error("Esiste già una categoria con questo nome");
      } else {
        toast.error("Errore nel salvataggio");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Modifica categoria" : "Nuova categoria"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label htmlFor="cat-name">Nome</Label>
            <Input
              id="cat-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Nome categoria"
            />
          </div>
          <div>
            <Label htmlFor="cat-color">Colore</Label>
            <div className="flex items-center gap-3 mt-1">
              <input
                type="color"
                id="cat-color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="h-10 w-10 rounded cursor-pointer"
              />
              <Input
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="w-28 font-mono"
                placeholder="#RRGGBB"
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annulla
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Salvataggio..." : isEdit ? "Salva" : "Crea"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
