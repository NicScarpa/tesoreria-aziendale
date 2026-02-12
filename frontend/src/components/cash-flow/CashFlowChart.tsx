"use client";

import { useMemo } from "react";
import {
  Area,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CashFlowProjectionLine } from "@/types/cash-flow";

interface CashFlowChartProps {
  lines: CashFlowProjectionLine[];
  sogliaMinima?: number;
  className?: string;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

export function CashFlowChart({ lines, sogliaMinima, className }: CashFlowChartProps) {
  const chartData = useMemo(() => {
    const today = new Date().toISOString().split("T")[0];
    return lines.map((l) => ({
      data: l.data,
      saldo: l.saldo_progressivo,
      importo: l.tipo === "entrata" ? l.importo : -l.importo,
      isPassato: l.data <= today,
      confidenza: l.confidenza,
    }));
  }, [lines]);

  const today = new Date().toISOString().split("T")[0];

  if (chartData.length === 0) {
    return (
      <div className={`flex h-64 items-center justify-center rounded-lg border bg-muted/20 ${className}`}>
        <p className="text-muted-foreground">Nessun dato disponibile</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="saldoGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="data"
            tickFormatter={(d) => new Date(d).toLocaleDateString("it-IT", { day: "2-digit", month: "short" })}
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis
            tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            tick={{ fontSize: 11 }}
            width={50}
          />
          <Tooltip
            formatter={(value) => formatCurrency(Number(value))}
            labelFormatter={(label) => new Date(label).toLocaleDateString("it-IT", { weekday: "short", day: "numeric", month: "long" })}
          />
          <Area
            type="monotone"
            dataKey="saldo"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#saldoGradient)"
            name="Saldo"
          />
          <ReferenceLine
            x={today}
            stroke="#6b7280"
            strokeDasharray="3 3"
            label={{ value: "Oggi", position: "top", fontSize: 11 }}
          />
          {sogliaMinima !== undefined && (
            <ReferenceLine
              y={sogliaMinima}
              stroke="#ef4444"
              strokeDasharray="5 5"
              label={{ value: `Soglia: ${formatCurrency(sogliaMinima)}`, position: "right", fontSize: 10, fill: "#ef4444" }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
