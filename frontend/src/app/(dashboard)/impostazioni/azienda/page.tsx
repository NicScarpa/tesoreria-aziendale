"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { Company } from "@/types/auth";
import { companySchema, type CompanyInput } from "@/lib/validations/settings";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

export default function CompanySettingsPage() {
  const { currentCompany } = useAuthStore();
  const companyId = currentCompany?.company_id;
  const isViewer = currentCompany?.role === "viewer";

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const form = useForm<CompanyInput>({
    resolver: zodResolver(companySchema),
    defaultValues: {
      name: "",
      vat_number: null,
      tax_number: null,
      country: "IT",
      address: null,
      fiscal_regime: null,
      group_vat_number: null,
      city: null,
      postal_code: null,
      province_code: null,
      certified_email: null,
      destination_code: null,
      default_currency: "EUR",
    },
  });

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    api
      .get<Company>(`/companies/${companyId}`)
      .then((res) => {
        const c = res.data;
        form.reset({
          name: c.name,
          vat_number: c.vat_number,
          tax_number: c.tax_number,
          country: c.country,
          address: c.address,
          fiscal_regime: c.fiscal_regime,
          group_vat_number: c.group_vat_number,
          city: c.city,
          postal_code: c.postal_code,
          province_code: c.province_code,
          certified_email: c.certified_email,
          destination_code: c.destination_code,
          default_currency: c.default_currency,
        });
      })
      .catch(() => {
        toast.error("Errore nel caricamento dei dati aziendali");
      })
      .finally(() => setLoading(false));
  }, [companyId, form]);

  const onSubmit = async (data: CompanyInput) => {
    if (!companyId) return;
    setSaving(true);
    try {
      await api.patch(`/companies/${companyId}`, data);
      toast.success("Dati aziendali aggiornati");
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
          <h1 className="text-2xl font-bold">Dati aziendali</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Informazioni identificative e fiscali dell&apos;azienda
          </p>
        </div>
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
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
        <h1 className="text-2xl font-bold">Dati aziendali</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Informazioni identificative e fiscali dell&apos;azienda
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Dati identificativi */}
          <Card>
            <CardHeader>
              <CardTitle>Dati identificativi</CardTitle>
              <CardDescription>
                Ragione sociale, partita IVA e codice fiscale
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem className="sm:col-span-2">
                    <FormLabel>Ragione sociale</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        disabled={isViewer}
                        placeholder="Nome azienda"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="vat_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Partita IVA</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="12345678901"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="tax_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Codice fiscale</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="RSSMRA80A01H501U"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="fiscal_regime"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Regime fiscale</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="RF01"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="group_vat_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>P.IVA gruppo</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="P.IVA gruppo (opzionale)"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Sede legale */}
          <Card>
            <CardHeader>
              <CardTitle>Sede legale</CardTitle>
              <CardDescription>
                Indirizzo e localizzazione della sede legale
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="address"
                render={({ field }) => (
                  <FormItem className="sm:col-span-2">
                    <FormLabel>Indirizzo</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="Via Roma 1"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="city"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Citta</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="Milano"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="postal_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>CAP</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="20100"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="province_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Provincia</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="MI"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="country"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Paese</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        disabled={isViewer}
                        placeholder="IT"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Fatturazione elettronica */}
          <Card>
            <CardHeader>
              <CardTitle>Fatturazione elettronica</CardTitle>
              <CardDescription>
                PEC e codice destinatario SDI
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="certified_email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>PEC</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="azienda@pec.it"
                        type="email"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="destination_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Codice destinatario SDI</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        value={field.value ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        disabled={isViewer}
                        placeholder="A1B2C3D"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Altro */}
          <Card>
            <CardHeader>
              <CardTitle>Altro</CardTitle>
              <CardDescription>
                Valuta predefinita e logo aziendale
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="default_currency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Valuta predefinita</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={isViewer}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Seleziona valuta" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="EUR">EUR - Euro</SelectItem>
                        <SelectItem value="USD">USD - Dollaro USA</SelectItem>
                        <SelectItem value="GBP">GBP - Sterlina</SelectItem>
                        <SelectItem value="CHF">CHF - Franco svizzero</SelectItem>
                      </SelectContent>
                    </Select>
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
