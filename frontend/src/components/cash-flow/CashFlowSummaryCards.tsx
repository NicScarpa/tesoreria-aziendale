"use client";

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Clock } from "lucide-react";
import { getCashFlowSummary } from "@/lib/api/cash-flow";
import type { CashFlowSummary } from "@/types/cash-flow";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function TrendIcon({ value }: { value: number }) {
  if (value > 0) return <TrendingUp className="h-4 w-4 text-green-600" />;
  if (value < 0) return <TrendingDown className="h-4 w-4 text-red-600" />;
  return <Minus className="h-4 w-4 text-gray-400" />;
}

export function CashFlowSummaryCards() {
  const [data, setData] = useState<CashFlowSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCashFlowSummary()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 animate-pulse rounded-lg border bg-muted" />
        ))}
      </div>
    );
  }

  if (!data) return null;

  const cards = [
    {
      label: "Saldo Attuale",
      value: formatCurrency(data.saldo_attuale),
      trend: data.trend_7gg,
      trendLabel: "vs 7gg",
    },
    {
      label: "Previsione 30gg",
      value: formatCurrency(data.previsione_30gg),
      trend: data.trend_30gg,
      trendLabel: "delta",
    },
    {
      label: "Runway",
      value: data.runway_mesi ? `${data.runway_mesi} mesi` : "N/D",
      icon: <Clock className="h-4 w-4 text-muted-foreground" />,
      sub: data.burn_rate_mensile ? `Burn rate: ${formatCurrency(data.burn_rate_mensile)}/mese` : undefined,
    },
    {
      label: "Prossimo Alert",
      value: data.prossimo_alert
        ? new Date(data.prossimo_alert.data_prevista).toLocaleDateString("it-IT")
        : "Nessuno",
      icon: data.prossimo_alert ? <AlertTriangle className="h-4 w-4 text-amber-500" /> : undefined,
      sub: data.prossimo_alert?.messaggio,
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <div key={card.label} className="rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{card.label}</p>
            {card.icon}
          </div>
          <p className="mt-1 text-2xl font-bold">{card.value}</p>
          {card.trend !== undefined && (
            <div className="mt-1 flex items-center gap-1 text-sm">
              <TrendIcon value={card.trend} />
              <span className={card.trend >= 0 ? "text-green-600" : "text-red-600"}>
                {formatCurrency(Math.abs(card.trend))}
              </span>
              <span className="text-muted-foreground">{card.trendLabel}</span>
            </div>
          )}
          {card.sub && (
            <p className="mt-1 truncate text-xs text-muted-foreground">{card.sub}</p>
          )}
        </div>
      ))}
    </div>
  );
}
