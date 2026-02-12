"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import api from "@/lib/api";
import {
  createBankAccountSchema,
  type CreateBankAccountInput,
} from "@/lib/validations/bank-account";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}

export function CreateBankAccountDialog({ open, onOpenChange, onCreated }: Props) {
  const [submitting, setSubmitting] = useState(false);

  const form = useForm<CreateBankAccountInput>({
    resolver: zodResolver(createBankAccountSchema),
    defaultValues: {
      nickname: "",
      iban: "",
      currency: "EUR",
      color: "#6b7280",
      is_default: false,
    },
  });

  const onSubmit = async (data: CreateBankAccountInput) => {
    setSubmitting(true);
    try {
      await api.post("/bank-accounts", data);
      toast.success("Conto creato con successo");
      onOpenChange(false);
      form.reset();
      onCreated();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Errore nella creazione del conto";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Nuovo conto bancario</DialogTitle>
          <DialogDescription>
            Inserisci i dati del conto da aggiungere manualmente.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="nickname"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nome conto</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="es. Conto Principale BPM" />
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
                    <Input
                      {...field}
                      value={field.value ?? ""}
                      placeholder="IT60 X054 2811 1010 0000 0123 456"
                      className="font-mono"
                    />
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
                      <Input {...field} placeholder="EUR" maxLength={3} />
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
                    <Select
                      onValueChange={field.onChange}
                      value={field.value ?? undefined}
                    >
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
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="current_balance"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Saldo iniziale</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
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
                name="bank_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Banca</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        placeholder="es. Banco BPM"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
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
                        <Input {...field} value={field.value || ""} className="flex-1" />
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="is_default"
                render={({ field }) => (
                  <FormItem className="flex items-end gap-2 pb-2">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <FormLabel className="!mt-0">Conto predefinito</FormLabel>
                  </FormItem>
                )}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Annulla
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Creazione..." : "Crea conto"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
