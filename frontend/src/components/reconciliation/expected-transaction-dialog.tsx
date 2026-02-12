"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { createExpectedTransactionSchema, type CreateExpectedTransactionInput } from "@/lib/validations/reconciliation";
import type { ExpectedTransaction } from "@/types/reconciliation";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  item: ExpectedTransaction | null;
  onSaved: () => void;
}

export function ExpectedTransactionDialog({ open, onOpenChange, item, onSaved }: Props) {
  const isEdit = !!item;

  const form = useForm<CreateExpectedTransactionInput>({
    resolver: zodResolver(createExpectedTransactionSchema),
    defaultValues: {
      type: "expected_outflow",
      expected_amount: 0,
      due_date: "",
      document_type: "other",
      source: "manual",
    },
  });

  useEffect(() => {
    if (item) {
      form.reset({
        type: item.type,
        expected_amount: item.expected_amount,
        due_date: item.due_date,
        currency: item.currency,
        counterpart_name: item.counterpart_name ?? undefined,
        counterpart_iban: item.counterpart_iban ?? undefined,
        description: item.description ?? undefined,
        reference_number: item.reference_number ?? undefined,
        document_type: item.document_type,
        source: item.source,
      });
    } else {
      form.reset({
        type: "expected_outflow",
        expected_amount: 0,
        due_date: new Date().toISOString().split("T")[0],
        document_type: "other",
        source: "manual",
      });
    }
  }, [item, form, open]);

  const onSubmit = async (data: CreateExpectedTransactionInput) => {
    try {
      if (isEdit) {
        await api.patch(`/expected-transactions/${item.id}`, data);
        toast.success("Transazione attesa aggiornata");
      } else {
        await api.post("/expected-transactions", data);
        toast.success("Transazione attesa creata");
      }
      onOpenChange(false);
      onSaved();
    } catch {
      toast.error("Errore nel salvataggio");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Modifica transazione attesa" : "Nuova transazione attesa"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Tipo</Label>
              <Select value={form.watch("type")} onValueChange={(v) => form.setValue("type", v as "expected_inflow" | "expected_outflow")}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="expected_inflow">Entrata attesa</SelectItem>
                  <SelectItem value="expected_outflow">Uscita attesa</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Importo</Label>
              <Input type="number" step="0.01" {...form.register("expected_amount")} />
              {form.formState.errors.expected_amount && (
                <p className="text-xs text-destructive mt-1">{form.formState.errors.expected_amount.message}</p>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Data scadenza</Label>
              <Input type="date" {...form.register("due_date")} />
            </div>
            <div>
              <Label>Tipo documento</Label>
              <Select value={form.watch("document_type")} onValueChange={(v) => form.setValue("document_type", v as CreateExpectedTransactionInput["document_type"])}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="sales_invoice">Fattura vendita</SelectItem>
                  <SelectItem value="purchase_invoice">Fattura acquisto</SelectItem>
                  <SelectItem value="credit_note">Nota credito</SelectItem>
                  <SelectItem value="debit_note">Nota debito</SelectItem>
                  <SelectItem value="salary">Stipendio</SelectItem>
                  <SelectItem value="tax">Tributo</SelectItem>
                  <SelectItem value="other">Altro</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label>Controparte</Label>
            <Input {...form.register("counterpart_name")} placeholder="Nome controparte" />
          </div>
          <div>
            <Label>IBAN controparte</Label>
            <Input {...form.register("counterpart_iban")} placeholder="IT..." />
          </div>
          <div>
            <Label>Riferimento</Label>
            <Input {...form.register("reference_number")} placeholder="FT-2026/001" />
          </div>
          <div>
            <Label>Descrizione</Label>
            <Textarea {...form.register("description")} placeholder="Descrizione..." />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
            <Button type="submit">{isEdit ? "Salva" : "Crea"}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
