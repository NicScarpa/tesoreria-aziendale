"use client";

import { useRouter } from "next/navigation";
import { CreditCard, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { PagamentiSection } from "@/types/dashboard";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface Props {
  data: PagamentiSection;
}

export function PaymentPendingWidget({ data }: Props) {
  const router = useRouter();

  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push("/pagamenti?stato=da_approvare")}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <CreditCard className="h-4 w-4" />
          Pagamenti
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Da approvare</span>
          <div className="flex items-center gap-2">
            {data.da_approvare_conteggio > 0 && (
              <Badge variant="secondary" className="bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                {data.da_approvare_conteggio}
              </Badge>
            )}
            <span className="text-sm font-bold">{formatCurrency(data.da_approvare_importo)}</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" /> In attesa
          </span>
          <span className="text-sm font-medium">{data.in_attesa_esecuzione}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Eseguiti questo mese</span>
          <span className="text-sm font-medium">{data.eseguiti_mese}</span>
        </div>
      </CardContent>
    </Card>
  );
}
