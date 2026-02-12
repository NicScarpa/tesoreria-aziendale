"use client";

import { useRouter } from "next/navigation";
import { TrendingUp, TrendingDown, Minus, ArrowRight } from "lucide-react";
import {
  ComposedChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { CashFlowPreviewSection } from "@/types/dashboard";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatCompact(value: number): string {
  if (Math.abs(value) >= 1000) {
    return `${(value / 1000).toFixed(0)}k`;
  }
  return value.toFixed(0);
}

interface Props {
  data: CashFlowPreviewSection;
}

export function CashFlowMiniWidget({ data }: Props) {
  const router = useRouter();

  const TrendIcon = data.trend === "crescente" ? TrendingUp : data.trend === "decrescente" ? TrendingDown : Minus;
  const trendColor = data.trend === "crescente" ? "text-green-600" : data.trend === "decrescente" ? "text-red-600" : "text-gray-500";

  const chartData = data.mini_chart_data.map((point) => ({
    data: point.data,
    entrate: Number(point.entrate),
    uscite: Number(point.uscite),
    saldo: Number(point.saldo),
  }));

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-muted-foreground">Cash Flow Preview</CardTitle>
        <Button variant="ghost" size="sm" onClick={() => router.push("/cash-flow")} className="text-xs">
          Dettagli <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs text-muted-foreground">Previsione 7gg</p>
            <p className="text-lg font-bold">{formatCurrency(data.previsione_7gg)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Previsione 30gg</p>
            <p className="text-lg font-bold">{formatCurrency(data.previsione_30gg)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Trend</p>
            <div className="flex items-center gap-1">
              <TrendIcon className={`h-4 w-4 ${trendColor}`} />
              <p className={`text-lg font-bold capitalize ${trendColor}`}>{data.trend}</p>
            </div>
          </div>
        </div>

        {chartData.length > 0 && (
          <div className="h-[200px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="data"
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v) => new Date(v).toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit" })}
                />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={formatCompact} />
                <Tooltip
                  formatter={(value) => formatCurrency(Number(value))}
                  labelFormatter={(label) => new Date(label).toLocaleDateString("it-IT")}
                />
                <Bar dataKey="entrate" fill="#22c55e" barSize={16} radius={[2, 2, 0, 0]} name="Entrate" />
                <Bar dataKey="uscite" fill="#ef4444" barSize={16} radius={[2, 2, 0, 0]} name="Uscite" />
                <Line
                  type="monotone"
                  dataKey="saldo"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  name="Saldo"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}

        {data.prossimo_alert && (
          <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">
            {data.prossimo_alert}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
