"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import api from "@/lib/api";
import {
  updateBankAccountSchema,
  type UpdateBankAccountInput,
} from "@/lib/validations/bank-account";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Checkbox } from "@/components/ui/checkbox";
import type { BankAccount } from "@/types/bank-account";

interface Props {
  account: BankAccount | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpdated: () => void;
}

export function EditBankAccountSheet({ account, open, onOpenChange, onUpdated }: Props) {
  const [submitting, setSubmitting] = useState(false);

  const form = useForm<UpdateBankAccountInput>({
    resolver: zodResolver(updateBankAccountSchema),
  });

  useEffect(() => {
    if (account) {
      form.reset({
        nickname: account.nickname ?? undefined,
        iban: account.iban ?? undefined,
        bic: account.bic ?? undefined,
        currency: account.currency ?? undefined,
        credit_limit: account.credit_limit ?? undefined,
        account_type: account.account_type ?? undefined,
        color: account.color ?? undefined,
        notes: account.notes ?? undefined,
        is_default: account.is_default,
        bank_name: account.bank_name ?? undefined,
        ignore_balance: account.ignore_balance,
      });
    }
  }, [account, form]);

  const onSubmit = async (data: UpdateBankAccountInput) => {
    if (!account) return;
    setSubmitting(true);
    try {
      await api.patch(`/bank-accounts/${account.id}`, data);
      toast.success("Conto aggiornato");
      onOpenChange(false);
      onUpdated();
    } catch {
      toast.error("Errore nell'aggiornamento");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Modifica conto</SheetTitle>
          <SheetDescription>{account?.nickname}</SheetDescription>
        </SheetHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 py-4">
            <FormField
              control={form.control}
              name="nickname"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome conto</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="iban"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>IBAN</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ""} className="font-mono" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="currency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Valuta</FormLabel>
                    <FormControl>
                      <Input {...field} value={field.value ?? ""} maxLength={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="account_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tipo conto</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value ?? undefined}>
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleziona" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="checking">Conto corrente</SelectItem>
                        <SelectItem value="savings">Risparmio</SelectItem>
                        <SelectItem value="cash">Cassa</SelectItem>
                        <SelectItem value="credit_card">Carta di credito</SelectItem>
                        <SelectItem value="loan">Prestito</SelectItem>
                        <SelectItem value="other">Altro</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="bank_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Banca</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value ?? ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="credit_limit"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Fido bancario</FormLabel>
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
              name="color"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Colore</FormLabel>
                  <FormControl>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={field.value || "#6b7280"}
                        onChange={field.onChange}
                        className="h-9 w-9 rounded border cursor-pointer"
                      />
                      <Input {...field} value={field.value ?? ""} className="flex-1" />
                    </div>
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
                    <Textarea {...field} value={field.value ?? ""} rows={3} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="space-y-3">
              <FormField
                control={form.control}
                name="is_default"
                render={({ field }) => (
                  <FormItem className="flex items-center gap-2">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <FormLabel className="!mt-0">Conto predefinito</FormLabel>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="ignore_balance"
                render={({ field }) => (
                  <FormItem className="flex items-center gap-2">
                    <FormControl>
                      <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                    <FormLabel className="!mt-0">Escludi dal totale saldi</FormLabel>
                  </FormItem>
                )}
              />
            </div>
            <SheetFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Annulla
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Salvataggio..." : "Salva modifiche"}
              </Button>
            </SheetFooter>
          </form>
        </Form>
      </SheetContent>
    </Sheet>
  );
}
