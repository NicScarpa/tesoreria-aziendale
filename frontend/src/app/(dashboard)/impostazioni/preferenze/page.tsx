"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { CompanySettings } from "@/types/settings";
import {
  displaySettingsSchema,
  type DisplaySettingsInput,
} from "@/lib/validations/settings";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

const TIMEZONES = [
  { value: "Europe/Rome", label: "Roma (CET/CEST)" },
  { value: "Europe/London", label: "Londra (GMT/BST)" },
  { value: "Europe/Berlin", label: "Berlino (CET/CEST)" },
  { value: "Europe/Paris", label: "Parigi (CET/CEST)" },
  { value: "Europe/Madrid", label: "Madrid (CET/CEST)" },
  { value: "Europe/Amsterdam", label: "Amsterdam (CET/CEST)" },
  { value: "Europe/Zurich", label: "Zurigo (CET/CEST)" },
  { value: "Europe/Vienna", label: "Vienna (CET/CEST)" },
  { value: "Europe/Brussels", label: "Bruxelles (CET/CEST)" },
  { value: "Europe/Lisbon", label: "Lisbona (WET/WEST)" },
  { value: "Europe/Athens", label: "Atene (EET/EEST)" },
  { value: "UTC", label: "UTC" },
];

export default function DisplaySettingsPage() {
  const { currentCompany } = useAuthStore();
  const companyId = currentCompany?.company_id;
  const isViewer = currentCompany?.role === "viewer";

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const form = useForm<DisplaySettingsInput>({
    resolver: zodResolver(displaySettingsSchema),
    defaultValues: {
      date_format: "DD/MM/YYYY",
      decimal_separator: ",",
      thousands_separator: ".",
      timezone: "Europe/Rome",
      first_day_of_week: 1,
    },
  });

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    api
      .get<CompanySettings>(`/companies/${companyId}/settings`)
      .then((res) => {
        const ds = res.data.display_settings;
        form.reset({
          date_format: ds.date_format,
          decimal_separator: ds.decimal_separator,
          thousands_separator: ds.thousands_separator,
          timezone: ds.timezone,
          first_day_of_week: ds.first_day_of_week,
        });
      })
      .catch(() => {
        toast.error("Errore nel caricamento delle preferenze di formato");
      })
      .finally(() => setLoading(false));
  }, [companyId, form]);

  const onSubmit = async (data: DisplaySettingsInput) => {
    if (!companyId) return;
    setSaving(true);
    try {
      await api.patch(`/companies/${companyId}/settings`, {
        display_settings: data,
      });
      toast.success("Preferenze di formato aggiornate");
    } catch {
      toast.error("Errore nel salvataggio");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Formato</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Preferenze di visualizzazione per date, numeri e fuso orario
          </p>
        </div>
        <Card>
          <CardContent>
            <div className="h-48 animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Formato</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Preferenze di visualizzazione per date, numeri e fuso orario
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Formato date e numeri</CardTitle>
              <CardDescription>
                Queste impostazioni influenzano come vengono visualizzati date e
                importi in tutta l&apos;applicazione
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="date_format"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Formato data</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isViewer}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleziona formato" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="DD/MM/YYYY">
                          DD/MM/YYYY (31/12/2026)
                        </SelectItem>
                        <SelectItem value="MM/DD/YYYY">
                          MM/DD/YYYY (12/31/2026)
                        </SelectItem>
                        <SelectItem value="YYYY-MM-DD">
                          YYYY-MM-DD (2026-12-31)
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="decimal_separator"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Separatore decimale</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isViewer}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleziona separatore" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value=",">Virgola (1.234,56)</SelectItem>
                        <SelectItem value=".">Punto (1,234.56)</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="thousands_separator"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Separatore migliaia</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isViewer}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleziona separatore" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value=".">Punto (1.234)</SelectItem>
                        <SelectItem value=",">Virgola (1,234)</SelectItem>
                        <SelectItem value=" ">Spazio (1 234)</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="timezone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Fuso orario</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isViewer}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleziona fuso orario" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {TIMEZONES.map((tz) => (
                          <SelectItem key={tz.value} value={tz.value}>
                            {tz.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="first_day_of_week"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Primo giorno della settimana</FormLabel>
                    <Select
                      onValueChange={(v) => field.onChange(Number(v))}
                      value={String(field.value)}
                      disabled={isViewer}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleziona giorno" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="1">Lunedi</SelectItem>
                        <SelectItem value="0">Domenica</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Usato nei calendari e nelle visualizzazioni settimanali
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Separator />

          {!isViewer && (
            <div className="flex justify-end">
              <Button type="submit" disabled={saving}>
                {saving ? "Salvataggio..." : "Salva modifiche"}
              </Button>
            </div>
          )}
        </form>
      </Form>
    </div>
  );
}
