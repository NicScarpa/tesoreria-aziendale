"use client";

import { ArrowDownLeft, ArrowUpRight, AlertTriangle, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ScheduleSummary } from "@/types/schedule";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface ScheduleSummaryCardsProps {
  summary: ScheduleSummary | null;
}

export function ScheduleSummaryCards({ summary }: ScheduleSummaryCardsProps) {
  if (!summary) return null;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Da incassare</CardTitle>
          <ArrowDownLeft className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {formatCurrency(summary.somma_attive_aperte)}
          </div>
          <p className="text-xs text-muted-foreground">{summary.totale_attive} scadenze attive</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Da pagare</CardTitle>
          <ArrowUpRight className="h-4 w-4 text-red-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">
            {formatCurrency(summary.somma_passive_aperte)}
          </div>
          <p className="text-xs text-muted-foreground">{summary.totale_passive} scadenze passive</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Scadute</CardTitle>
          <AlertTriangle className="h-4 w-4 text-destructive" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-destructive">
            {formatCurrency(summary.somma_scadute)}
          </div>
          <p className="text-xs text-muted-foreground">{summary.totale_scadute} scadenze scadute</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">Prossimi 7gg</CardTitle>
          <Clock className="h-4 w-4 text-amber-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{summary.prossime_7_giorni}</div>
          <p className="text-xs text-muted-foreground">
            {summary.ricorrenti_attive} ricorrenti attive
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
