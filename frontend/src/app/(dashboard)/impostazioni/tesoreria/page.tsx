"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { CompanySettings } from "@/types/settings";
import {
  treasurySettingsSchema,
  type TreasurySettingsInput,
} from "@/lib/validations/settings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
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
import { Badge } from "@/components/ui/badge";

export default function TreasurySettingsPage() {
  const { currentCompany } = useAuthStore();
  const companyId = currentCompany?.company_id;
  const isViewer = currentCompany?.role === "viewer";

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [reconciliationRulesCount, setReconciliationRulesCount] = useState(0);

  const form = useForm<TreasurySettingsInput>({
    resolver: zodResolver(treasurySettingsSchema),
    defaultValues: {
      min_cash_threshold: null,
      critical_cash_threshold: null,
      advance_notice_days: 7,
      auto_categorize: false,
      auto_reconcile: false,
      cashflow_update_mode: "daily",
    },
  });

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);

    Promise.all([
      api.get<CompanySettings>(`/companies/${companyId}/settings`),
      api.get(`/reconciliation-rules`).catch(() => ({ data: [] })),
    ])
      .then(([settingsRes, rulesRes]) => {
        const ts = settingsRes.data.treasury_settings;
        form.reset({
          min_cash_threshold: ts.min_cash_threshold,
          critical_cash_threshold: ts.critical_cash_threshold,
          advance_notice_days: ts.advance_notice_days,
          auto_categorize: ts.auto_categorize,
          auto_reconcile: ts.auto_reconcile,
          cashflow_update_mode: ts.cashflow_update_mode,
        });
        const rules = Array.isArray(rulesRes.data) ? rulesRes.data : [];
        setReconciliationRulesCount(
          rules.filter((r: { is_active: boolean }) => r.is_active).length
        );
      })
      .catch(() => {
        toast.error("Errore nel caricamento delle impostazioni di tesoreria");
      })
      .finally(() => setLoading(false));
  }, [companyId, form]);

  const onSubmit = async (data: TreasurySettingsInput) => {
    if (!companyId) return;
    setSaving(true);
    try {
      await api.patch(`/companies/${companyId}/settings`, {
        treasury_settings: data,
      });
      toast.success("Impostazioni di tesoreria aggiornate");
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
          <h1 className="text-2xl font-bold">Tesoreria</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Soglie, automazioni e regole di tesoreria
          </p>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent>
                <div className="h-24 animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Tesoreria</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Soglie, automazioni e regole di tesoreria
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Soglie alert cassa */}
          <Card>
            <CardHeader>
              <CardTitle>Soglie alert cassa</CardTitle>
              <CardDescription>
                Definisci le soglie per le notifiche di saldo basso e critico
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="min_cash_threshold"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Soglia minima</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        disabled={isViewer}
                        placeholder="10000"
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value === ""
                              ? null
                              : Number(e.target.value)
                          )
                        }
                      />
                    </FormControl>
                    <FormDescription>
                      Alert quando il saldo scende sotto questa soglia
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="critical_cash_threshold"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Soglia critica</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        disabled={isViewer}
                        placeholder="5000"
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value === ""
                              ? null
                              : Number(e.target.value)
                          )
                        }
                      />
                    </FormControl>
                    <FormDescription>
                      Alert critico quando il saldo scende sotto questa soglia
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Automazioni */}
          <Card>
            <CardHeader>
              <CardTitle>Automazioni</CardTitle>
              <CardDescription>
                Configura categorizzazione automatica, riconciliazione e
                aggiornamento cash flow
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <FormField
                control={form.control}
                name="auto_categorize"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">
                        Categorizzazione automatica
                      </FormLabel>
                      <FormDescription>
                        Categorizza automaticamente i movimenti bancari in base
                        ai pattern
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={isViewer}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="auto_reconcile"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">
                        Riconciliazione automatica
                      </FormLabel>
                      <FormDescription>
                        Riconcilia automaticamente i movimenti che corrispondono
                        con alta confidenza
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={isViewer}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="cashflow_update_mode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Aggiornamento cash flow</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isViewer}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleziona modalita" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="manual">Manuale</SelectItem>
                        <SelectItem value="daily">Giornaliero</SelectItem>
                        <SelectItem value="realtime">Tempo reale</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Frequenza di aggiornamento delle previsioni di cassa
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Preavviso */}
          <Card>
            <CardHeader>
              <CardTitle>Preavviso scadenze</CardTitle>
              <CardDescription>
                Giorni di anticipo per le notifiche sulle scadenze in arrivo
              </CardDescription>
            </CardHeader>
            <CardContent>
              <FormField
                control={form.control}
                name="advance_notice_days"
                render={({ field }) => (
                  <FormItem className="max-w-xs">
                    <FormLabel>Giorni di preavviso</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        disabled={isViewer}
                        min={1}
                        max={90}
                        {...field}
                        onChange={(e) => field.onChange(Number(e.target.value))}
                      />
                    </FormControl>
                    <FormDescription>Da 1 a 90 giorni</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Regole di riconciliazione */}
          <Card>
            <CardHeader>
              <CardTitle>Regole di riconciliazione</CardTitle>
              <CardDescription>
                Gestisci le regole per il matching automatico tra movimenti
                bancari e registrazioni contabili
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">Regole attive</p>
                  <p className="text-muted-foreground text-sm">
                    {reconciliationRulesCount === 0
                      ? "Nessuna regola configurata"
                      : `${reconciliationRulesCount} ${reconciliationRulesCount === 1 ? "regola attiva" : "regole attive"}`}
                  </p>
                </div>
                <Badge variant="secondary">
                  {reconciliationRulesCount}
                </Badge>
              </div>
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
