"use client";

import { useEffect, useState } from "react";
import {
  getSeasonality,
  getTrends,
  getRunway,
} from "@/lib/api/cash-flow";
import type {
  SeasonalityResponse,
  TrendResponse,
  RunwayResponse,
} from "@/types/cash-flow";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { RunwayGauge } from "@/components/cash-flow/RunwayGauge";

const MESI_IT = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"];

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

export default function AnalysisPage() {
  const [seasonality, setSeasonality] = useState<SeasonalityResponse | null>(null);
  const [trends, setTrends] = useState<TrendResponse | null>(null);
  const [runway, setRunway] = useState<RunwayResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getSeasonality().catch(() => null),
      getTrends({ mesi: 6 }).catch(() => null),
      getRunway().catch(() => null),
    ]).then(([s, t, r]) => {
      setSeasonality(s);
      setTrends(t);
      setRunway(r);
      setLoading(false);
    });
  }, []);

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Analisi Cash Flow"
        description="Stagionalita, trend e runway"
      />

      <Tabs defaultValue="stagionalita">
        <TabsList>
          <TabsTrigger value="stagionalita">Stagionalita</TabsTrigger>
          <TabsTrigger value="trend">Trend</TabsTrigger>
          <TabsTrigger value="runway">Runway</TabsTrigger>
        </TabsList>

        <TabsContent value="stagionalita" className="space-y-4">
          {seasonality ? (
            <>
              <p className="text-sm text-muted-foreground">
                Media entrate/uscite per mese (ultimi {seasonality.periodo_analisi_mesi} mesi)
              </p>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={seasonality.mesi.map((m) => ({
                  mese: MESI_IT[m.mese - 1],
                  entrate: m.entrate_medie,
                  uscite: m.uscite_medie,
                  netto: m.saldo_netto_medio,
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mese" />
                  <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                  <Legend />
                  <Bar dataKey="entrate" fill="#22c55e" name="Entrate" />
                  <Bar dataKey="uscite" fill="#ef4444" name="Uscite" />
                </BarChart>
              </ResponsiveContainer>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Dati insufficienti per l'analisi stagionale</p>
          )}
        </TabsContent>

        <TabsContent value="trend" className="space-y-4">
          {trends ? (
            <>
              <div className="flex gap-4 text-sm">
                <span>Entrate: <strong className={trends.trend_entrate === "crescente" ? "text-green-600" : trends.trend_entrate === "decrescente" ? "text-red-600" : ""}>{trends.trend_entrate}</strong></span>
                <span>Uscite: <strong className={trends.trend_uscite === "crescente" ? "text-red-600" : trends.trend_uscite === "decrescente" ? "text-green-600" : ""}>{trends.trend_uscite}</strong></span>
              </div>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={trends.punti}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="periodo" />
                  <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                  <Legend />
                  <Line type="monotone" dataKey="entrate" stroke="#22c55e" strokeWidth={2} name="Entrate" />
                  <Line type="monotone" dataKey="uscite" stroke="#ef4444" strokeWidth={2} name="Uscite" />
                  <Line type="monotone" dataKey="saldo_netto" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" name="Saldo Netto" />
                </LineChart>
              </ResponsiveContainer>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Dati insufficienti per l'analisi trend</p>
          )}
        </TabsContent>

        <TabsContent value="runway" className="space-y-4">
          {runway ? (
            <div className="max-w-md">
              <RunwayGauge data={runway} />
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Dati insufficienti per il calcolo del runway</p>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
