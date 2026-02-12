"use client";

import { useMemo } from "react";
import {
  Bar,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import type { VarianceResponse } from "@/types/cash-flow";

interface VarianceChartProps {
  variance: VarianceResponse;
  className?: string;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

export function VarianceChart({ variance, className }: VarianceChartProps) {
  const chartData = useMemo(() => {
    return variance.lines.map((l) => ({
      data: new Date(l.data).toLocaleDateString("it-IT", { day: "2-digit", month: "short" }),
      previsto: l.importo_previsto,
      reale: l.importo_reale,
      varianza: l.varianza,
    }));
  }, [variance]);

  return (
    <div className={className}>
      <div className="mb-4 flex items-center gap-6">
        <div className="rounded-lg border bg-card px-4 py-2">
          <p className="text-xs text-muted-foreground">Accuracy</p>
          <p className="text-xl font-bold">{variance.accuracy.toFixed(1)}%</p>
        </div>
        <div className="rounded-lg border bg-card px-4 py-2">
          <p className="text-xs text-muted-foreground">Varianza Totale</p>
          <p className="text-xl font-bold">{formatCurrency(variance.varianza_totale)}</p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData}>
          <XAxis dataKey="data" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value) => formatCurrency(Number(value))} />
          <Legend />
          <Line type="monotone" dataKey="previsto" stroke="#3b82f6" strokeWidth={2} name="Previsto" dot={false} />
          <Line type="monotone" dataKey="reale" stroke="#22c55e" strokeWidth={2} name="Reale" dot={false} />
          <Bar dataKey="varianza" fill="#f59e0b" opacity={0.5} name="Varianza" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
