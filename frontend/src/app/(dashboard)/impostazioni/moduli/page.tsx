"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { Switch } from "@/components/ui/switch";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

const AVAILABLE_MODULES = [
  {
    key: "cashflow",
    label: "Cash Flow",
    description: "Monitoraggio e previsioni di cassa",
  },
  {
    key: "budget",
    label: "Budget",
    description: "Pianificazione e controllo budget",
  },
  {
    key: "sdi",
    label: "Fatturazione SDI",
    description: "Integrazione Sistema di Interscambio",
  },
  {
    key: "reconciliation",
    label: "Riconciliazione",
    description: "Riconciliazione bancaria automatica",
  },
  {
    key: "pisp",
    label: "Pagamenti PSD2",
    description: "Disposizioni di pagamento via PSD2",
  },
  {
    key: "f24",
    label: "F24",
    description: "Gestione pagamenti F24",
  },
  {
    key: "cbi_import",
    label: "Import CBI",
    description: "Importazione flussi CBI",
  },
  {
    key: "sepa_export",
    label: "Export SEPA",
    description: "Esportazione file SEPA XML",
  },
];

export default function ModulesSettingsPage() {
  const { currentCompany } = useAuthStore();
  const companyId = currentCompany?.company_id;
  const isOwner = currentCompany?.role === "owner";

  const [enabledFeatures, setEnabledFeatures] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!companyId) return;
    setLoading(true);
    api
      .get<{ features: string[] }>(`/companies/${companyId}/modules`)
      .then((res) => {
        setEnabledFeatures(res.data.features);
      })
      .catch(() => {
        toast.error("Errore nel caricamento dei moduli");
      })
      .finally(() => setLoading(false));
  }, [companyId]);

  const toggleModule = async (moduleKey: string, enabled: boolean) => {
    if (!companyId) return;

    const newFeatures = enabled
      ? [...enabledFeatures, moduleKey]
      : enabledFeatures.filter((f) => f !== moduleKey);

    setEnabledFeatures(newFeatures);
    setSaving(true);

    try {
      await api.patch(`/companies/${companyId}/modules`, {
        features: newFeatures,
      });
      toast.success(
        enabled
          ? `Modulo "${AVAILABLE_MODULES.find((m) => m.key === moduleKey)?.label}" attivato`
          : `Modulo "${AVAILABLE_MODULES.find((m) => m.key === moduleKey)?.label}" disattivato`
      );
    } catch {
      // Rollback
      setEnabledFeatures(
        enabled
          ? enabledFeatures.filter((f) => f !== moduleKey)
          : [...enabledFeatures, moduleKey]
      );
      toast.error("Errore nell'aggiornamento del modulo");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Moduli</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Attiva o disattiva i moduli disponibili per la tua azienda
          </p>
        </div>
        <Card>
          <CardContent>
            <div className="h-64 animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Moduli</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Attiva o disattiva i moduli disponibili per la tua azienda
        </p>
        {!isOwner && (
          <p className="text-muted-foreground text-xs mt-2">
            Solo il proprietario puo modificare i moduli attivi.
          </p>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Moduli disponibili</CardTitle>
          <CardDescription>
            {enabledFeatures.length} di {AVAILABLE_MODULES.length} moduli
            attivi
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-1">
          {AVAILABLE_MODULES.map((mod) => {
            const isEnabled = enabledFeatures.includes(mod.key);
            return (
              <div
                key={mod.key}
                className="flex items-center justify-between rounded-lg border p-4"
              >
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">{mod.label}</p>
                  <p className="text-muted-foreground text-sm">
                    {mod.description}
                  </p>
                </div>
                <Switch
                  checked={isEnabled}
                  onCheckedChange={(checked) => toggleModule(mod.key, checked)}
                  disabled={!isOwner || saving}
                />
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
