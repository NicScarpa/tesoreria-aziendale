"use client";

import { useState } from "react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import api from "@/lib/api";
import { createReminderSchema, type CreateReminderInput } from "@/lib/validations/schedule";
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

interface ReminderDialogProps {
  scheduleId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}

export function ReminderDialog({ scheduleId, open, onOpenChange, onCreated }: ReminderDialogProps) {
  const [saving, setSaving] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<CreateReminderInput>({
    resolver: zodResolver(createReminderSchema),
    defaultValues: { giorni_prima: 3, tipo: "in_app" },
  });

  const onSubmit = async (data: CreateReminderInput) => {
    if (!scheduleId) return;
    setSaving(true);
    try {
      await api.post(`/schedules/${scheduleId}/reminders`, data);
      toast.success("Promemoria aggiunto");
      reset();
      onOpenChange(false);
      onCreated();
    } catch {
      toast.error("Errore nell'aggiunta");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Aggiungi promemoria</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label>Giorni prima della scadenza</Label>
            <Input
              type="number"
              min={0}
              {...register("giorni_prima", { valueAsNumber: true })}
            />
          </div>

          <div className="space-y-2">
            <Label>Tipo notifica</Label>
            <Select defaultValue="in_app" onValueChange={(v) => setValue("tipo", v as CreateReminderInput["tipo"])}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="in_app">In-app</SelectItem>
                <SelectItem value="email">Email</SelectItem>
                <SelectItem value="entrambi">Entrambi</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Messaggio</Label>
            <Textarea {...register("messaggio")} placeholder="Messaggio personalizzato..." rows={2} />
          </div>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Salvataggio..." : "Aggiungi"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
