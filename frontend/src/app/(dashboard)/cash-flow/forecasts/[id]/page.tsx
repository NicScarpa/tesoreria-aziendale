"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import {
  getForecast,
  refreshForecast,
  updateForecast,
  getVariance,
} from "@/lib/api/cash-flow";
import type {
  CashFlowForecastDetail,
  VarianceResponse,
} from "@/types/cash-flow";
import { FORECAST_STATUS_LABELS, FORECAST_STATUS_COLORS, FORECAST_TYPE_LABELS } from "@/types/cash-flow";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CashFlowChart } from "@/components/cash-flow/CashFlowChart";
import { CashFlowDetailTable } from "@/components/cash-flow/CashFlowDetailTable";
import { ScenarioEditor } from "@/components/cash-flow/ScenarioEditor";
import { VarianceChart } from "@/components/cash-flow/VarianceChart";
import { cn } from "@/lib/utils";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT");
}

export default function ForecastDetailPage() {
  const params = useParams();
  const router = useRouter();
  const forecastId = params.id as string;

  const [forecast, setForecast] = useState<CashFlowForecastDetail | null>(null);
  const [variance, setVariance] = useState<VarianceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [f, v] = await Promise.all([
        getForecast(forecastId),
        getVariance(forecastId).catch(() => null),
      ]);
      setForecast(f);
      setVariance(v);
    } catch {
      toast.error("Previsione non trovata");
      router.push("/cash-flow/forecasts");
    } finally {
      setLoading(false);
    }
  }, [forecastId, router]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshForecast(forecastId);
      toast.success("Previsione aggiornata");
      fetchData();
    } catch {
      toast.error("Errore nell'aggiornamento");
    } finally {
      setRefreshing(false);
    }
  };

  const handleActivate = async () => {
    try {
      await updateForecast(forecastId, { stato: "attiva" });
      toast.success("Previsione attivata");
      fetchData();
    } catch {
      toast.error("Errore");
    }
  };

  const handleArchive = async () => {
    try {
      await updateForecast(forecastId, { stato: "archiviata" });
      toast.success("Previsione archiviata");
      fetchData();
    } catch {
      toast.error("Errore");
    }
  };

  if (loading) return <LoadingState />;
  if (!forecast) return null;

  const chartLines = forecast.lines.map((l) => ({
    ...l,
    importo: l.importo,
    saldo_progressivo: l.saldo_progressivo,
  }));

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/cash-flow/forecasts")}>
          <ArrowLeft className="mr-1 h-4 w-4" />
          Indietro
        </Button>
      </div>

      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{forecast.nome}</h1>
            <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", FORECAST_STATUS_COLORS[forecast.stato])}>
              {FORECAST_STATUS_LABELS[forecast.stato]}
            </span>
            <span className="rounded bg-muted px-2 py-0.5 text-xs">
              {FORECAST_TYPE_LABELS[forecast.tipo]}
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {formatDate(forecast.data_inizio)} - {formatDate(forecast.data_fine)}
            {forecast.descrizione && ` | ${forecast.descrizione}`}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={cn("mr-1 h-4 w-4", refreshing && "animate-spin")} />
            Aggiorna
          </Button>
          {forecast.stato === "bozza" && (
            <Button size="sm" onClick={handleActivate}>Attiva</Button>
          )}
          {forecast.stato === "attiva" && (
            <Button size="sm" variant="outline" onClick={handleArchive}>Archivia</Button>
          )}
        </div>
      </div>

      {/* KPI */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Saldo Iniziale", value: formatCurrency(forecast.saldo_iniziale) },
          { label: "Saldo Finale", value: formatCurrency(forecast.saldo_finale_previsto) },
          { label: "Entrate Previste", value: formatCurrency(forecast.totale_entrate_previste), color: "text-green-600" },
          { label: "Uscite Previste", value: formatCurrency(forecast.totale_uscite_previste), color: "text-red-600" },
        ].map((kpi) => (
          <div key={kpi.label} className="rounded-lg border bg-card p-3">
            <p className="text-xs text-muted-foreground">{kpi.label}</p>
            <p className={cn("text-xl font-bold", kpi.color)}>{kpi.value}</p>
          </div>
        ))}
      </div>

      <Tabs defaultValue="righe">
        <TabsList>
          <TabsTrigger value="righe">Righe ({forecast.lines.length})</TabsTrigger>
          <TabsTrigger value="scenari">Scenari ({forecast.scenarios.length})</TabsTrigger>
          <TabsTrigger value="varianza">Varianza</TabsTrigger>
        </TabsList>

        <TabsContent value="righe" className="space-y-4">
          <CashFlowChart lines={chartLines} />
          <CashFlowDetailTable lines={chartLines} />
        </TabsContent>

        <TabsContent value="scenari" className="space-y-4">
          <ScenarioEditor
            forecastId={forecastId}
            scenarios={forecast.scenarios}
            onUpdate={fetchData}
          />
        </TabsContent>

        <TabsContent value="varianza" className="space-y-4">
          {variance ? (
            <VarianceChart variance={variance} />
          ) : (
            <p className="text-sm text-muted-foreground">Nessun dato di varianza disponibile (servono dati storici)</p>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
