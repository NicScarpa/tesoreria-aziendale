"use client";

import { useState } from "react";
import { toast } from "sonner";
import { CheckCircle2, Circle } from "lucide-react";
import api from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { CategorySelector } from "./category-selector";
import type { Transaction } from "@/types/transaction";
import type { Category } from "@/types/category";

function formatCurrency(value: number, currency = "EUR"): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency }).format(value);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

const TX_TYPE_LABELS: Record<string, string> = {
  credit_transfer: "Bonifico",
  direct_debit: "Addebito diretto",
  card_payment: "Carta",
  cash: "Contante",
  fee: "Commissione",
  interest: "Interesse",
  tax: "Tasse",
  other: "Altro",
};

const STATUS_LABELS: Record<string, string> = {
  booked: "Contabilizzato",
  pending: "In sospeso",
  rejected: "Rifiutato",
};

interface Props {
  transaction: Transaction | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  categories: Category[];
  onUpdated: () => void;
}

export function TransactionDetailSheet({
  transaction,
  open,
  onOpenChange,
  categories,
  onUpdated,
}: Props) {
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const tx = transaction;
  if (!tx) return null;

  const handleCategoryChange = async (categoryId: string | null) => {
    try {
      await api.patch(`/transactions/${tx.id}`, { category_id: categoryId });
      toast.success("Categoria aggiornata");
      onUpdated();
    } catch {
      toast.error("Errore nell'aggiornamento della categoria");
    }
  };

  const handleSaveNotes = async () => {
    setSaving(true);
    try {
      await api.patch(`/transactions/${tx.id}`, { notes });
      toast.success("Note salvate");
      onUpdated();
    } catch {
      toast.error("Errore nel salvataggio delle note");
    } finally {
      setSaving(false);
    }
  };

  const handleToggleVerified = async () => {
    try {
      await api.patch(`/transactions/${tx.id}/verify`);
      onUpdated();
    } catch {
      toast.error("Errore nella verifica");
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <span className={tx.amount >= 0 ? "text-emerald-600" : "text-red-600"}>
              {formatCurrency(tx.amount, tx.currency)}
            </span>
            <button onClick={handleToggleVerified}>
              {tx.verified ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              ) : (
                <Circle className="h-5 w-5 text-muted-foreground/30" />
              )}
            </button>
          </SheetTitle>
        </SheetHeader>

        <div className="space-y-6 mt-6">
          {/* Info base */}
          <div className="space-y-3">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-muted-foreground">Data</dt>
                <dd>{formatDate(tx.transaction_date)}</dd>
              </div>
              {tx.value_date && (
                <div>
                  <dt className="text-muted-foreground">Data valuta</dt>
                  <dd>{formatDate(tx.value_date)}</dd>
                </div>
              )}
              <div>
                <dt className="text-muted-foreground">Tipo</dt>
                <dd>{TX_TYPE_LABELS[tx.transaction_type] || tx.transaction_type}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Stato</dt>
                <dd>
                  <Badge variant={tx.status === "booked" ? "default" : "secondary"}>
                    {STATUS_LABELS[tx.status] || tx.status}
                  </Badge>
                </dd>
              </div>
              {tx.counterpart_name && (
                <div className="col-span-2">
                  <dt className="text-muted-foreground">Controparte</dt>
                  <dd>{tx.counterpart_name}</dd>
                </div>
              )}
              {tx.counterpart_iban && (
                <div className="col-span-2">
                  <dt className="text-muted-foreground">IBAN controparte</dt>
                  <dd className="font-mono text-xs">{tx.counterpart_iban}</dd>
                </div>
              )}
              {tx.bank_account_nickname && (
                <div>
                  <dt className="text-muted-foreground">Conto</dt>
                  <dd>{tx.bank_account_nickname}</dd>
                </div>
              )}
            </dl>

            {tx.description && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Descrizione</p>
                <p className="text-sm bg-muted/50 p-2 rounded">{tx.description}</p>
              </div>
            )}

            {tx.remittance_info && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Causale</p>
                <p className="text-sm bg-muted/50 p-2 rounded">{tx.remittance_info}</p>
              </div>
            )}
          </div>

          {/* Categoria */}
          <div>
            <p className="text-sm font-medium mb-2">Categoria</p>
            <CategorySelector
              categories={categories}
              value={tx.category_id}
              onChange={handleCategoryChange}
            />
          </div>

          {/* Allocazioni */}
          {tx.allocations.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-2">Split ({tx.allocations.length})</p>
              <div className="space-y-1">
                {tx.allocations.map((alloc) => (
                  <div key={alloc.id} className="flex items-center justify-between text-sm p-2 border rounded">
                    <span className="flex items-center gap-2">
                      {alloc.category && (
                        <span
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: alloc.category.color }}
                        />
                      )}
                      {alloc.category?.name || "—"}
                    </span>
                    <span className="font-mono">{formatCurrency(alloc.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Note */}
          <div>
            <p className="text-sm font-medium mb-2">Note</p>
            <Textarea
              placeholder="Aggiungi una nota..."
              defaultValue={tx.notes || ""}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
            <Button
              size="sm"
              className="mt-2"
              onClick={handleSaveNotes}
              disabled={saving}
            >
              Salva note
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
