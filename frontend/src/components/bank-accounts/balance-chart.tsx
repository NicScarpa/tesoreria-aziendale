"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BalanceChartPoint } from "@/types/bank-account";

interface Props {
  data: BalanceChartPoint[];
  loading?: boolean;
}

export function BalanceChart({ data, loading }: Props) {
  const chartData = useMemo(
    () =>
      data.map((d) => ({
        ...d,
        date: new Date(d.date).toLocaleDateString("it-IT", {
          day: "2-digit",
          month: "2-digit",
        }),
      })),
    [data]
  );

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Andamento saldo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 animate-pulse rounded bg-muted" />
        </CardContent>
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Andamento saldo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-64 items-center justify-center text-muted-foreground">
            Nessun dato disponibile
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Andamento saldo</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(v: number) =>
                new Intl.NumberFormat("it-IT", {
                  notation: "compact",
                  compactDisplay: "short",
                }).format(v)
              }
              className="text-muted-foreground"
            />
            <Tooltip
              formatter={(value) =>
                new Intl.NumberFormat("it-IT", {
                  style: "currency",
                  currency: "EUR",
                }).format(value as number)
              }
            />
            <Area
              type="monotone"
              dataKey="current_balance"
              name="Saldo contabile"
              stroke="#2563eb"
              fill="#2563eb"
              fillOpacity={0.1}
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="available_balance"
              name="Saldo disponibile"
              stroke="#059669"
              fill="#059669"
              fillOpacity={0.05}
              strokeWidth={2}
              strokeDasharray="4 4"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
