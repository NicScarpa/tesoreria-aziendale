"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CategorySelector } from "./category-selector";
import type { Category } from "@/types/category";
import type { Transaction } from "@/types/transaction";

interface AllocationRow {
  category_id: string;
  subcategory_id: string | null;
  amount: string;
}

interface Props {
  transaction: Transaction;
  categories: Category[];
  onUpdated: () => void;
}

export function AllocationEditor({ transaction, categories, onUpdated }: Props) {
  const absAmount = Math.abs(transaction.amount);
  const [rows, setRows] = useState<AllocationRow[]>(
    transaction.allocations.length > 0
      ? transaction.allocations.map((a) => ({
          category_id: a.category_id,
          subcategory_id: a.subcategory_id,
          amount: a.amount.toString(),
        }))
      : [{ category_id: "", subcategory_id: null, amount: absAmount.toString() }]
  );
  const [saving, setSaving] = useState(false);

  const addRow = () => {
    const used = rows.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0);
    const remaining = Math.max(0, absAmount - used);
    setRows([...rows, { category_id: "", subcategory_id: null, amount: remaining.toFixed(2) }]);
  };

  const removeRow = (index: number) => {
    setRows(rows.filter((_, i) => i !== index));
  };

  const updateRow = (index: number, field: keyof AllocationRow, value: string | null) => {
    const updated = [...rows];
    updated[index] = { ...updated[index], [field]: value };
    setRows(updated);
  };

  const totalAllocated = rows.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0);
  const isValid = Math.abs(totalAllocated - absAmount) < 0.01 && rows.every((r) => r.category_id);

  const handleSave = async () => {
    setSaving(true);
    try {
      const allocations = rows.map((r) => ({
        category_id: r.category_id,
        subcategory_id: r.subcategory_id,
        amount: parseFloat(r.amount),
      }));

      if (transaction.allocations.length > 0) {
        await api.put(`/transactions/${transaction.id}/allocations`, { allocations });
      } else {
        await api.post(`/transactions/${transaction.id}/allocations`, { allocations });
      }
      toast.success("Split salvato");
      onUpdated();
    } catch {
      toast.error("Errore nel salvataggio dello split");
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveSplit = async () => {
    try {
      await api.delete(`/transactions/${transaction.id}/allocations`);
      toast.success("Split rimosso");
      onUpdated();
    } catch {
      toast.error("Errore nella rimozione dello split");
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium">
          Split — Totale: {new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(absAmount)}
        </p>
        <span className={`text-xs ${isValid ? "text-emerald-600" : "text-red-600"}`}>
          Allocato: {new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(totalAllocated)}
        </span>
      </div>

      {rows.map((row, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="flex-1">
            <CategorySelector
              categories={categories}
              value={row.category_id || null}
              onChange={(v) => updateRow(i, "category_id", v || "")}
            />
          </div>
          <Input
            type="number"
            step="0.01"
            value={row.amount}
            onChange={(e) => updateRow(i, "amount", e.target.value)}
            className="w-28"
          />
          {rows.length > 1 && (
            <Button variant="ghost" size="sm" onClick={() => removeRow(i)}>
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      ))}

      <div className="flex gap-2">
        <Button variant="outline" size="sm" onClick={addRow}>
          <Plus className="h-4 w-4 mr-1" />
          Aggiungi riga
        </Button>
        <Button size="sm" onClick={handleSave} disabled={!isValid || saving}>
          Salva split
        </Button>
        {transaction.allocations.length > 0 && (
          <Button variant="ghost" size="sm" onClick={handleRemoveSplit}>
            Rimuovi split
          </Button>
        )}
      </div>
    </div>
  );
}
