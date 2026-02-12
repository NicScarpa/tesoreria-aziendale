"use client";

import { useRouter } from "next/navigation";
import { ArrowUpRight, ArrowDownRight, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { EntrateUsciteSection } from "@/types/dashboard";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface Props {
  data: EntrateUsciteSection;
}

export function IncomeExpenseWidget({ data }: Props) {
  const router = useRouter();

  const confrontoColor = data.confronto_mese_precedente >= 0 ? "text-green-600" : "text-red-600";

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-muted-foreground">Entrate / Uscite</CardTitle>
        <Button variant="ghost" size="sm" onClick={() => router.push("/movimenti")} className="text-xs">
          Vedi tutto <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 grid-cols-2">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100 dark:bg-green-950">
              <ArrowUpRight className="h-4 w-4 text-green-600" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Entrate</p>
              <p className="text-lg font-bold text-green-600">{formatCurrency(data.entrate)}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 dark:bg-red-950">
              <ArrowDownRight className="h-4 w-4 text-red-600" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Uscite</p>
              <p className="text-lg font-bold text-red-600">{formatCurrency(data.uscite)}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between rounded-lg bg-muted/50 p-3">
          <span className="text-sm text-muted-foreground">Saldo netto</span>
          <span className={`text-sm font-bold ${data.saldo_netto >= 0 ? "text-green-600" : "text-red-600"}`}>
            {formatCurrency(data.saldo_netto)}
          </span>
        </div>

        {data.confronto_mese_precedente !== 0 && (
          <p className={`text-xs ${confrontoColor}`}>
            {data.confronto_mese_precedente > 0 ? "+" : ""}{data.confronto_mese_precedente}% rispetto al periodo precedente
          </p>
        )}

        {data.top_categorie.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-medium text-muted-foreground">Top Categorie</p>
            {data.top_categorie.map((cat) => (
              <div key={cat.nome} className="flex items-center justify-between text-sm">
                <span className="truncate">{cat.nome}</span>
                <span className="font-medium">{formatCurrency(cat.importo)}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
