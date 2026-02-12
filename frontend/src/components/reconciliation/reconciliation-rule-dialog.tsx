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
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { createReconciliationRuleSchema, type CreateReconciliationRuleInput } from "@/lib/validations/reconciliation";
import type { ReconciliationRule } from "@/types/reconciliation";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rule: ReconciliationRule | null;
  onSaved: () => void;
}

export function ReconciliationRuleDialog({ open, onOpenChange, rule, onSaved }: Props) {
  const isEdit = !!rule;

  const form = useForm<CreateReconciliationRuleInput>({
    resolver: zodResolver(createReconciliationRuleSchema),
    defaultValues: {
      name: "",
      match_amount: true,
      amount_tolerance: 0.01,
      match_date: true,
      date_tolerance_days: 3,
      match_description: false,
      match_counterpart: true,
      auto_confirm: false,
      min_confidence: 0.8,
      priority: 0,
      is_active: true,
      match_type: "exact_amount",
      action: "suggest",
      require_same_counterpart: false,
    },
  });

  useEffect(() => {
    if (rule) {
      form.reset({
        name: rule.name,
        description: rule.description ?? undefined,
        match_amount: rule.match_amount,
        amount_tolerance: rule.amount_tolerance,
        match_date: rule.match_date,
        date_tolerance_days: rule.date_tolerance_days,
        match_description: rule.match_description,
        match_counterpart: rule.match_counterpart,
        auto_confirm: rule.auto_confirm,
        min_confidence: rule.min_confidence,
        priority: rule.priority,
        is_active: rule.is_active,
        match_type: rule.match_type,
        action: rule.action,
        require_same_counterpart: rule.require_same_counterpart,
      });
    } else {
      form.reset();
    }
  }, [rule, form, open]);

  const onSubmit = async (data: CreateReconciliationRuleInput) => {
    try {
      if (isEdit) {
        await api.patch(`/reconciliation-rules/${rule.id}`, data);
        toast.success("Regola aggiornata");
      } else {
        await api.post("/reconciliation-rules", data);
        toast.success("Regola creata");
      }
      onOpenChange(false);
      onSaved();
    } catch {
      toast.error("Errore nel salvataggio");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Modifica regola" : "Nuova regola"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label>Nome</Label>
            <Input {...form.register("name")} placeholder="Nome regola" />
            {form.formState.errors.name && (
              <p className="text-xs text-destructive mt-1">{form.formState.errors.name.message}</p>
            )}
          </div>
          <div>
            <Label>Descrizione</Label>
            <Textarea {...form.register("description")} placeholder="Descrizione opzionale" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Tipo match</Label>
              <Select value={form.watch("match_type")} onValueChange={(v) => form.setValue("match_type", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="exact_amount">Importo esatto</SelectItem>
                  <SelectItem value="amount_tolerance">Con tolleranza</SelectItem>
                  <SelectItem value="reference">Riferimento</SelectItem>
                  <SelectItem value="counterpart">Controparte</SelectItem>
                  <SelectItem value="combined">Combinato</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Azione</Label>
              <Select value={form.watch("action")} onValueChange={(v) => form.setValue("action", v)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="suggest">Suggerisci</SelectItem>
                  <SelectItem value="auto_reconcile">Auto-riconcilia</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Tolleranza importo</Label>
              <Input type="number" step="0.01" {...form.register("amount_tolerance")} />
            </div>
            <div>
              <Label>Tolleranza giorni</Label>
              <Input type="number" {...form.register("date_tolerance_days")} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Confidenza minima (0-1)</Label>
              <Input type="number" step="0.01" {...form.register("min_confidence")} />
            </div>
            <div>
              <Label>Priorita</Label>
              <Input type="number" {...form.register("priority")} />
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Match importo</Label>
              <Switch checked={form.watch("match_amount")} onCheckedChange={(v) => form.setValue("match_amount", v)} />
            </div>
            <div className="flex items-center justify-between">
              <Label>Match data</Label>
              <Switch checked={form.watch("match_date")} onCheckedChange={(v) => form.setValue("match_date", v)} />
            </div>
            <div className="flex items-center justify-between">
              <Label>Match descrizione</Label>
              <Switch checked={form.watch("match_description")} onCheckedChange={(v) => form.setValue("match_description", v)} />
            </div>
            <div className="flex items-center justify-between">
              <Label>Match controparte</Label>
              <Switch checked={form.watch("match_counterpart")} onCheckedChange={(v) => form.setValue("match_counterpart", v)} />
            </div>
            <div className="flex items-center justify-between">
              <Label>Richiedi stessa controparte</Label>
              <Switch checked={form.watch("require_same_counterpart")} onCheckedChange={(v) => form.setValue("require_same_counterpart", v)} />
            </div>
            <div className="flex items-center justify-between">
              <Label>Conferma automatica</Label>
              <Switch checked={form.watch("auto_confirm")} onCheckedChange={(v) => form.setValue("auto_confirm", v)} />
            </div>
            <div className="flex items-center justify-between">
              <Label>Attiva</Label>
              <Switch checked={form.watch("is_active")} onCheckedChange={(v) => form.setValue("is_active", v)} />
            </div>
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
