"use client";

import { Landmark, TrendingUp, TrendingDown, CreditCard } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { BankAccountSummary } from "@/types/bank-account";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

interface Props {
  summary: BankAccountSummary | null;
  loading?: boolean;
}

export function BankAccountSummaryCards({ summary, loading }: Props) {
  if (loading || !summary) {
    return (
      <div className="grid gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="h-16 animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: "Conti attivi",
      value: summary.count.toString(),
      icon: Landmark,
      color: "text-blue-600",
    },
    {
      label: "Saldo contabile",
      value: formatCurrency(summary.total_current_balance),
      icon: TrendingUp,
      color: "text-emerald-600",
    },
    {
      label: "Saldo disponibile",
      value: formatCurrency(summary.total_available_balance),
      icon: TrendingDown,
      color: "text-amber-600",
    },
    {
      label: "Fido totale",
      value: formatCurrency(summary.total_credit_limit),
      icon: CreditCard,
      color: "text-purple-600",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.label}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{card.label}</p>
                  <p className="text-2xl font-bold">{card.value}</p>
                </div>
                <Icon className={`h-8 w-8 ${card.color} opacity-80`} />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
