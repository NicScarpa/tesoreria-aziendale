"use client";

import { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import { getRunway } from "@/lib/api/cash-flow";
import type { RunwayResponse } from "@/types/cash-flow";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "N/D";
  return new Date(dateStr).toLocaleDateString("it-IT", { day: "numeric", month: "long", year: "numeric" });
}

interface RunwayGaugeProps {
  data?: RunwayResponse;
  className?: string;
}

export function RunwayGauge({ data: propData, className }: RunwayGaugeProps) {
  const [data, setData] = useState<RunwayResponse | null>(propData || null);
  const [loading, setLoading] = useState(!propData);

  useEffect(() => {
    if (propData) {
      setData(propData);
      return;
    }
    getRunway()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [propData]);

  if (loading) {
    return <div className={`h-32 animate-pulse rounded-lg border bg-muted ${className}`} />;
  }

  if (!data) return null;

  const maxMonths = 24;
  const percentage = Math.min((data.runway_mesi / maxMonths) * 100, 100);
  const gaugeColor =
    data.runway_mesi <= 3 ? "bg-red-500" :
    data.runway_mesi <= 6 ? "bg-amber-500" :
    data.runway_mesi <= 12 ? "bg-yellow-500" : "bg-green-500";

  return (
    <div className={`rounded-lg border bg-card p-4 ${className}`}>
      <div className="flex items-center gap-2">
        <Clock className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-medium">Runway Liquidita</h3>
      </div>

      <div className="mt-4">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold">{data.runway_mesi.toFixed(1)}</span>
          <span className="text-sm text-muted-foreground">mesi</span>
        </div>

        <div className="mt-2 h-3 w-full overflow-hidden rounded-full bg-muted">
          <div className={`h-full rounded-full transition-all ${gaugeColor}`} style={{ width: `${percentage}%` }} />
        </div>

        <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Saldo attuale</p>
            <p className="font-medium">{formatCurrency(data.saldo_attuale)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Burn rate</p>
            <p className="font-medium">{formatCurrency(data.burn_rate_mensile)}/mese</p>
          </div>
          <div className="col-span-2">
            <p className="text-muted-foreground">Data esaurimento stimata</p>
            <p className="font-medium">{formatDate(data.data_esaurimento)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
