"use client";

import { FileText, Clock, Send, CheckCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { PaymentOrderSummary } from "@/types/payment";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

interface PaymentSummaryCardsProps {
  summary: PaymentOrderSummary | null;
  loading?: boolean;
}

export function PaymentSummaryCards({ summary, loading }: PaymentSummaryCardsProps) {
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
      label: "Bozze",
      count: summary.totale_bozze,
      importo: summary.importo_bozze,
      icon: FileText,
      iconColor: "text-gray-500",
      bgColor: "bg-gray-50",
      borderColor: "border-l-gray-400",
    },
    {
      label: "Da Approvare",
      count: summary.totale_da_approvare,
      importo: summary.importo_da_approvare,
      icon: Clock,
      iconColor: "text-amber-600",
      bgColor: "bg-amber-50",
      borderColor: "border-l-amber-400",
    },
    {
      label: "In Corso",
      count: summary.totale_approvate,
      importo: summary.importo_approvate,
      icon: Send,
      iconColor: "text-blue-600",
      bgColor: "bg-blue-50",
      borderColor: "border-l-blue-400",
    },
    {
      label: "Eseguite",
      count: summary.totale_eseguite,
      importo: summary.importo_eseguite,
      icon: CheckCircle,
      iconColor: "text-green-600",
      bgColor: "bg-green-50",
      borderColor: "border-l-green-400",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.label} className={cn("border-l-4", card.borderColor)}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{card.label}</p>
                  <p className="text-2xl font-bold">{card.count}</p>
                  <p className="text-sm font-medium text-muted-foreground">
                    {formatCurrency(card.importo)}
                  </p>
                </div>
                <div className={cn("rounded-full p-3", card.bgColor)}>
                  <Icon className={cn("h-6 w-6", card.iconColor)} />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
