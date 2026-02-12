"use client";

import { useState } from "react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import api from "@/lib/api";
import { createScheduleSchema, type CreateScheduleInput } from "@/lib/validations/schedule";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
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
import { Switch } from "@/components/ui/switch";
import type { BankAccount } from "@/types/bank-account";

interface CreateScheduleSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
  bankAccounts: BankAccount[];
}

export function CreateScheduleSheet({ open, onOpenChange, onCreated, bankAccounts }: CreateScheduleSheetProps) {
  const [saving, setSaving] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CreateScheduleInput>({
    resolver: zodResolver(createScheduleSchema),
    defaultValues: {
      tipo: "passiva",
      priorita: "normale",
      tipo_documento: "altro",
      valuta: "EUR",
      is_ricorrente: false,
    },
  });

  const isRicorrente = watch("is_ricorrente");
  const tipo = watch("tipo");

  const onSubmit = async (data: CreateScheduleInput) => {
    setSaving(true);
    try {
      await api.post("/schedules", data);
      toast.success("Scadenza creata");
      reset();
      onOpenChange(false);
      onCreated();
    } catch {
      toast.error("Errore nella creazione");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Nuova scadenza</SheetTitle>
        </SheetHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 mt-4">
          {/* Tipo */}
          <div className="space-y-2">
            <Label>Tipo</Label>
            <Select value={tipo} onValueChange={(v) => setValue("tipo", v as "attiva" | "passiva")}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="passiva">Da pagare</SelectItem>
                <SelectItem value="attiva">Da incassare</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Descrizione */}
          <div className="space-y-2">
            <Label>Descrizione *</Label>
            <Input {...register("descrizione")} placeholder="Es: Fattura fornitore ABC" />
            {errors.descrizione && <p className="text-xs text-destructive">{errors.descrizione.message}</p>}
          </div>

          {/* Importo + Valuta */}
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2 space-y-2">
              <Label>Importo *</Label>
              <Input
                type="number"
                step="0.01"
                {...register("importo_totale", { valueAsNumber: true })}
                placeholder="0,00"
              />
              {errors.importo_totale && <p className="text-xs text-destructive">{errors.importo_totale.message}</p>}
            </div>
            <div className="space-y-2">
              <Label>Valuta</Label>
              <Input {...register("valuta")} defaultValue="EUR" />
            </div>
          </div>

          {/* Date */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Data scadenza *</Label>
              <Input type="date" {...register("data_scadenza")} />
              {errors.data_scadenza && <p className="text-xs text-destructive">{errors.data_scadenza.message}</p>}
            </div>
            <div className="space-y-2">
              <Label>Data emissione</Label>
              <Input type="date" {...register("data_emissione")} />
            </div>
          </div>

          {/* Documento */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Tipo documento</Label>
              <Select
                defaultValue="altro"
                onValueChange={(v) => setValue("tipo_documento", v as CreateScheduleInput["tipo_documento"])}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fattura_acquisto">Fattura acquisto</SelectItem>
                  <SelectItem value="fattura_vendita">Fattura vendita</SelectItem>
                  <SelectItem value="nota_credito">Nota credito</SelectItem>
                  <SelectItem value="nota_debito">Nota debito</SelectItem>
                  <SelectItem value="stipendio">Stipendio</SelectItem>
                  <SelectItem value="tassa_f24">Tassa F24</SelectItem>
                  <SelectItem value="contributo">Contributo</SelectItem>
                  <SelectItem value="affitto">Affitto</SelectItem>
                  <SelectItem value="utenza">Utenza</SelectItem>
                  <SelectItem value="rata_prestito">Rata prestito</SelectItem>
                  <SelectItem value="altro">Altro</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Numero documento</Label>
              <Input {...register("numero_documento")} placeholder="FT-2026/001" />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Riferimento documento</Label>
            <Input {...register("riferimento_documento")} placeholder="Riferimento per riconciliazione" />
          </div>

          {/* Controparte */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Controparte</Label>
              <Input {...register("controparte_nome")} placeholder="Nome controparte" />
            </div>
            <div className="space-y-2">
              <Label>IBAN controparte</Label>
              <Input {...register("controparte_iban")} placeholder="IT..." />
            </div>
          </div>

          {/* Conto bancario */}
          <div className="space-y-2">
            <Label>Conto bancario</Label>
            <Select onValueChange={(v) => setValue("bank_account_id", v === "none" ? null : v)}>
              <SelectTrigger>
                <SelectValue placeholder="Seleziona conto" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Nessuno</SelectItem>
                {bankAccounts.map((a) => (
                  <SelectItem key={a.id} value={a.id}>
                    {a.nickname || a.iban}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Priorita + Metodo pagamento */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Priorita</Label>
              <Select defaultValue="normale" onValueChange={(v) => setValue("priorita", v as CreateScheduleInput["priorita"])}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bassa">Bassa</SelectItem>
                  <SelectItem value="normale">Normale</SelectItem>
                  <SelectItem value="alta">Alta</SelectItem>
                  <SelectItem value="urgente">Urgente</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Metodo pagamento</Label>
              <Select onValueChange={(v) => setValue("metodo_pagamento", v === "none" ? null : v as CreateScheduleInput["metodo_pagamento"])}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Nessuno</SelectItem>
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
          </div>

          {/* Ricorrenza */}
          <div className="flex items-center gap-3">
            <Switch
              checked={isRicorrente}
              onCheckedChange={(v) => setValue("is_ricorrente", v)}
            />
            <Label>Scadenza ricorrente</Label>
          </div>

          {isRicorrente && (
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Frequenza</Label>
                <Select onValueChange={(v) => setValue("ricorrenza_tipo", v as CreateScheduleInput["ricorrenza_tipo"])}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="settimanale">Settimanale</SelectItem>
                    <SelectItem value="mensile">Mensile</SelectItem>
                    <SelectItem value="bimestrale">Bimestrale</SelectItem>
                    <SelectItem value="trimestrale">Trimestrale</SelectItem>
                    <SelectItem value="semestrale">Semestrale</SelectItem>
                    <SelectItem value="annuale">Annuale</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Fine ricorrenza</Label>
                <Input type="date" {...register("ricorrenza_fine")} />
              </div>
            </div>
          )}

          {/* Note */}
          <div className="space-y-2">
            <Label>Note</Label>
            <Textarea {...register("note")} placeholder="Note aggiuntive..." rows={3} />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Salvataggio..." : "Crea scadenza"}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
