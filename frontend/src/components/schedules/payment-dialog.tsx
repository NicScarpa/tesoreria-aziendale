"use client";

import { useState } from "react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import api from "@/lib/api";
import { createPaymentSchema, type CreatePaymentInput } from "@/lib/validations/schedule";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Schedule } from "@/types/schedule";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface PaymentDialogProps {
  schedule: Schedule | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}

export function PaymentDialog({ schedule, open, onOpenChange, onCreated }: PaymentDialogProps) {
  const [saving, setSaving] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<CreatePaymentInput>({
    resolver: zodResolver(createPaymentSchema),
    defaultValues: {
      importo: schedule?.importo_residuo ?? 0,
      data_pagamento: new Date().toISOString().split("T")[0],
    },
  });

  const onSubmit = async (data: CreatePaymentInput) => {
    if (!schedule) return;
    setSaving(true);
    try {
      await api.post(`/schedules/${schedule.id}/payments`, data);
      toast.success("Pagamento registrato");
      reset();
      onOpenChange(false);
      onCreated();
    } catch {
      toast.error("Errore nella registrazione");
    } finally {
      setSaving(false);
    }
  };

  if (!schedule) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Registra pagamento</DialogTitle>
        </DialogHeader>
        <div className="text-sm text-muted-foreground mb-4">
          <p>{schedule.descrizione}</p>
          <p>
            Totale: {formatCurrency(schedule.importo_totale)} | Residuo:{" "}
            <span className="font-semibold">{formatCurrency(schedule.importo_residuo)}</span>
          </p>
        </div>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label>Importo *</Label>
            <Input
              type="number"
              step="0.01"
              {...register("importo", { valueAsNumber: true })}
            />
            {errors.importo && <p className="text-xs text-destructive">{errors.importo.message}</p>}
          </div>

          <div className="space-y-2">
            <Label>Data pagamento *</Label>
            <Input type="date" {...register("data_pagamento")} />
            {errors.data_pagamento && <p className="text-xs text-destructive">{errors.data_pagamento.message}</p>}
          </div>

          <div className="space-y-2">
            <Label>Metodo</Label>
            <Select onValueChange={(v) => setValue("metodo", v as CreatePaymentInput["metodo"])}>
              <SelectTrigger>
                <SelectValue placeholder="Seleziona" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="bonifico">Bonifico</SelectItem>
                <SelectItem value="ri_ba">Ri.Ba.</SelectItem>
                <SelectItem value="sdd">SDD</SelectItem>
                <SelectItem value="carta">Carta</SelectItem>
                <SelectItem value="contanti">Contanti</SelectItem>
                <SelectItem value="f24">F24</SelectItem>
                <SelectItem value="altro">Altro</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Riferimento</Label>
            <Input {...register("riferimento")} placeholder="N. bonifico, CRO, etc." />
          </div>

          <div className="space-y-2">
            <Label>Note</Label>
            <Textarea {...register("note")} rows={2} />
          </div>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Salvataggio..." : "Registra"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
