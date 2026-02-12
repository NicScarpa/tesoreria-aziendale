"use client";

import { cn } from "@/lib/utils";

interface PaymentProgressBarProps {
  importoTotale: number;
  importoPagato: number;
  className?: string;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

export function PaymentProgressBar({ importoTotale, importoPagato, className }: PaymentProgressBarProps) {
  const percentage = importoTotale > 0 ? Math.min((importoPagato / importoTotale) * 100, 100) : 0;
  const residuo = importoTotale - importoPagato;

  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Pagato: {formatCurrency(importoPagato)}</span>
        <span>Residuo: {formatCurrency(residuo)}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-100">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            percentage >= 100
              ? "bg-green-500"
              : percentage > 0
                ? "bg-amber-500"
                : "bg-gray-300"
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-right text-muted-foreground">{percentage.toFixed(0)}%</p>
    </div>
  );
}
