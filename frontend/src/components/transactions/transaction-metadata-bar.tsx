"use client";

import { ArrowDownLeft, ArrowUpRight, HelpCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { TransactionMetadata } from "@/types/transaction";

function formatCurrency(value: number, currency = "EUR"): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency }).format(value);
}

interface Props {
  metadata: TransactionMetadata | null;
  loading?: boolean;
}

export function TransactionMetadataBar({ metadata, loading }: Props) {
  if (loading || !metadata) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              <div className="h-8 w-32 bg-muted animate-pulse rounded mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <ArrowDownLeft className="h-4 w-4 text-emerald-500" />
            <p className="text-sm text-muted-foreground">Entrate</p>
          </div>
          <p className="text-2xl font-bold text-emerald-600">
            {formatCurrency(metadata.totals.positive)}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <ArrowUpRight className="h-4 w-4 text-red-500" />
            <p className="text-sm text-muted-foreground">Uscite</p>
          </div>
          <p className="text-2xl font-bold text-red-600">
            {formatCurrency(metadata.totals.negative)}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-amber-500" />
            <p className="text-sm text-muted-foreground">Non categorizzati</p>
          </div>
          <p className="text-2xl font-bold text-amber-600">
            {metadata.total_uncategorized}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
