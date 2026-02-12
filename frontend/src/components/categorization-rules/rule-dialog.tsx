"use client";

import { useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { CategorySelector } from "@/components/transactions/category-selector";
import { RuleConditionBuilder } from "./rule-condition-builder";
import type { CategorizationRule, RuleCondition } from "@/types/categorization-rule";
import type { Category } from "@/types/category";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rule?: CategorizationRule | null;
  categories: Category[];
  onSaved: () => void;
}

export function RuleDialog({ open, onOpenChange, rule, categories, onSaved }: Props) {
  const isEdit = !!rule;
  const [name, setName] = useState(rule?.name || "");
  const [direction, setDirection] = useState<string>(rule?.direction || "outflow");
  const [categoryId, setCategoryId] = useState<string | null>(rule?.category_id || null);
  const [conditions, setConditions] = useState<RuleCondition[]>(rule?.conditions || []);
  const [priority, setPriority] = useState(rule?.priority || 0);
  const [isActive, setIsActive] = useState(rule?.is_active ?? true);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!categoryId) {
      toast.error("Seleziona una categoria");
      return;
    }
    if (conditions.length === 0) {
      toast.error("Aggiungi almeno una condizione");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name: name || null,
        direction,
        category_id: categoryId,
        conditions,
        priority,
        is_active: isActive,
      };

      if (isEdit) {
        await api.patch(`/categorization-rules/${rule.id}`, payload);
        toast.success("Regola aggiornata");
      } else {
        await api.post("/categorization-rules", payload);
        toast.success("Regola creata");
      }
      onSaved();
      onOpenChange(false);
    } catch {
      toast.error("Errore nel salvataggio");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Modifica regola" : "Nuova regola"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <Label>Nome (opzionale)</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Es: Stipendi dipendenti" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Direzione</Label>
              <Select value={direction} onValueChange={setDirection}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="outflow">Uscita</SelectItem>
                  <SelectItem value="inflow">Entrata</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Priorità</Label>
              <Input
                type="number"
                value={priority}
                onChange={(e) => setPriority(parseInt(e.target.value) || 0)}
                className="mt-1"
              />
            </div>
          </div>

          <div>
            <Label>Categoria</Label>
            <CategorySelector
              categories={categories}
              value={categoryId}
              onChange={setCategoryId}
              className="mt-1"
            />
          </div>

          <div>
            <Label>Condizioni (tutte devono essere vere)</Label>
            <RuleConditionBuilder
              conditions={conditions}
              onChange={setConditions}
            />
          </div>

          <div className="flex items-center gap-2">
            <Switch checked={isActive} onCheckedChange={setIsActive} />
            <Label>Attiva</Label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Salvataggio..." : isEdit ? "Salva" : "Crea"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
