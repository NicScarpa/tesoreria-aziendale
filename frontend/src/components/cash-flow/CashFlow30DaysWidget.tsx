"use client";

import { useEffect, useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip } from "recharts";
import { getCashFlowProjection } from "@/lib/api/cash-flow";
import type { CashFlowProjectionLine } from "@/types/cash-flow";

interface CashFlow30DaysWidgetProps {
  accountId: string;
  className?: string;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

export function CashFlow30DaysWidget({ accountId, className }: CashFlow30DaysWidgetProps) {
  const [lines, setLines] = useState<CashFlowProjectionLine[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const today = new Date();
    const end = new Date(today);
    end.setDate(end.getDate() + 30);

    getCashFlowProjection({
      data_inizio: today.toISOString().split("T")[0],
      data_fine: end.toISOString().split("T")[0],
      bank_account_ids: accountId,
    })
      .then((data) => setLines(data.lines))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [accountId]);

  if (loading) {
    return <div className={`h-24 animate-pulse rounded-lg bg-muted ${className}`} />;
  }

  if (lines.length === 0) {
    return (
      <div className={`flex h-24 items-center justify-center rounded-lg border text-xs text-muted-foreground ${className}`}>
        Nessuna previsione 30gg
      </div>
    );
  }

  const chartData = lines.map((l) => ({
    data: l.data,
    saldo: l.saldo_progressivo,
  }));

  return (
    <div className={`rounded-lg border bg-card p-3 ${className}`}>
      <p className="text-xs font-medium text-muted-foreground">Cash Flow 30gg</p>
      <ResponsiveContainer width="100%" height={60}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id={`miniGrad-${accountId}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Tooltip formatter={(v) => formatCurrency(Number(v))} labelFormatter={() => ""} />
          <Area type="monotone" dataKey="saldo" stroke="#3b82f6" fill={`url(#miniGrad-${accountId})`} strokeWidth={1.5} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
