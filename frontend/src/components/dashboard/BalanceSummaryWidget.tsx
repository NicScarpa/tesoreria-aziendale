"use client";

import { useRouter } from "next/navigation";
import { Wallet, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SaldiSection } from "@/types/dashboard";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface Props {
  data: SaldiSection;
}

export function BalanceSummaryWidget({ data }: Props) {
  const router = useRouter();

  const TrendIcon = data.variazione_giorno > 0 ? TrendingUp : data.variazione_giorno < 0 ? TrendingDown : Minus;
  const trendColor = data.variazione_giorno > 0 ? "text-green-600" : data.variazione_giorno < 0 ? "text-red-600" : "text-gray-500";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <Wallet className="h-4 w-4" />
          Panoramica Saldi
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-sm text-muted-foreground">Saldo Totale</p>
            <p className="text-2xl font-bold">{formatCurrency(data.totale)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Disponibile</p>
            <p className="text-2xl font-bold">{formatCurrency(data.disponibile)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Variazione Giorno</p>
            <div className="flex items-center gap-1">
              <TrendIcon className={`h-5 w-5 ${trendColor}`} />
              <p className={`text-2xl font-bold ${trendColor}`}>
                {formatCurrency(data.variazione_giorno)}
              </p>
            </div>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Variazione %</p>
            <p className={`text-2xl font-bold ${trendColor}`}>
              {data.variazione_percentuale > 0 ? "+" : ""}{data.variazione_percentuale}%
            </p>
          </div>
        </div>

        {data.conti.length > 0 && (
          <div className="space-y-2 pt-2 border-t">
            {data.conti.map((conto) => (
              <button
                key={conto.id}
                onClick={() => router.push(`/conti/${conto.id}`)}
                className="flex w-full items-center justify-between rounded-lg p-2 hover:bg-muted/50 transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: conto.colore }}
                  />
                  <div>
                    <p className="text-sm font-medium">{conto.nome}</p>
                    {conto.banca && (
                      <p className="text-xs text-muted-foreground">{conto.banca}</p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold">{formatCurrency(conto.saldo)}</p>
                  {conto.variazione_giorno !== 0 && (
                    <p className={`text-xs ${conto.variazione_giorno > 0 ? "text-green-600" : "text-red-600"}`}>
                      {conto.variazione_giorno > 0 ? "+" : ""}{formatCurrency(conto.variazione_giorno)}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
