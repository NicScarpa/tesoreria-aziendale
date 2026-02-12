"use client";

import { useEffect, useState } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";
import { getCashFlowSummary } from "@/lib/api/cash-flow";

interface CashFlowImpactCardProps {
  schedule: {
    tipo: string;
    importo_totale: number;
    importo_pagato: number;
    data_scadenza: string;
  };
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

export function CashFlowImpactCard({ schedule }: CashFlowImpactCardProps) {
  const [saldoAttuale, setSaldoAttuale] = useState<number | null>(null);

  useEffect(() => {
    getCashFlowSummary()
      .then((data) => setSaldoAttuale(data.saldo_attuale))
      .catch(() => {});
  }, []);

  const importoResiduo = schedule.importo_totale - schedule.importo_pagato;
  const isEntrata = schedule.tipo === "attiva";
  const impatto = isEntrata ? importoResiduo : -importoResiduo;
  const saldoDopo = saldoAttuale !== null ? saldoAttuale + impatto : null;

  return (
    <div className="rounded-lg border bg-card p-3">
      <p className="text-xs font-medium text-muted-foreground">Impatto Cash Flow</p>
      <div className="mt-2 flex items-center gap-2">
        {isEntrata ? (
          <TrendingUp className="h-4 w-4 text-green-600" />
        ) : (
          <TrendingDown className="h-4 w-4 text-red-600" />
        )}
        <span className={`text-lg font-bold ${isEntrata ? "text-green-600" : "text-red-600"}`}>
          {isEntrata ? "+" : "-"}{formatCurrency(importoResiduo)}
        </span>
      </div>
      {saldoDopo !== null && (
        <p className="mt-1 text-xs text-muted-foreground">
          Saldo dopo: {formatCurrency(saldoDopo)}
        </p>
      )}
    </div>
  );
}
