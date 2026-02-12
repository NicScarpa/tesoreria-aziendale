"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ScheduleAgingBand } from "@/types/schedule";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface AgingChartProps {
  attive: ScheduleAgingBand[];
  passive: ScheduleAgingBand[];
}

export function AgingChart({ attive, passive }: AgingChartProps) {
  // Merge bands by fascia
  const allFasce = new Set([...attive.map((b) => b.fascia), ...passive.map((b) => b.fascia)]);
  const chartData = Array.from(allFasce).map((fascia) => {
    const att = attive.find((b) => b.fascia === fascia);
    const pas = passive.find((b) => b.fascia === fascia);
    return {
      fascia,
      attive: att?.importo_residuo || 0,
      passive: pas?.importo_residuo || 0,
    };
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Aging scadenze</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="fascia" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
              <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip
                formatter={(value) => [
                  formatCurrency(value as number),
                  undefined,
                ]}
              />
              <Legend
                formatter={(value: string) =>
                  value === "attive" ? "Da incassare" : "Da pagare"
                }
              />
              <Bar dataKey="attive" fill="#22c55e" radius={[4, 4, 0, 0]} />
              <Bar dataKey="passive" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
