"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import api from "@/lib/api";
import {
  updateBalanceSchema,
  type UpdateBalanceInput,
} from "@/lib/validations/bank-account";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import type { BankAccount } from "@/types/bank-account";

interface Props {
  account: BankAccount | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdated: () => void;
}

export function UpdateBalanceDialog({ account, open, onOpenChange, onUpdated }: Props) {
  const [submitting, setSubmitting] = useState(false);

  const form = useForm<UpdateBalanceInput>({
    resolver: zodResolver(updateBalanceSchema),
    values: {
      current_balance: account?.current_balance ?? null,
      available_balance: account?.available_balance ?? null,
      notes: null,
    },
  });

  const onSubmit = async (data: UpdateBalanceInput) => {
    if (!account) return;
    setSubmitting(true);
    try {
      await api.patch(`/bank-accounts/${account.id}/balance`, data);
      toast.success("Saldo aggiornato");
      onOpenChange(false);
      onUpdated();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Errore nell'aggiornamento del saldo";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Aggiorna saldo</DialogTitle>
          <DialogDescription>
            {account?.nickname || "Conto"}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="current_balance"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Saldo contabile</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      value={field.value ?? ""}
                      onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="available_balance"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Saldo disponibile</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      value={field.value ?? ""}
                      onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="notes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Note</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      value={field.value ?? ""}
                      placeholder="Motivo aggiornamento..."
                      rows={2}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Annulla
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Salvataggio..." : "Salva"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
