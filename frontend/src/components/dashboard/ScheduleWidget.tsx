"use client";

import { useRouter } from "next/navigation";
import { Calendar, ArrowRight, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ScadenzeSection } from "@/types/dashboard";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface Props {
  data: ScadenzeSection;
}

export function ScheduleWidget({ data }: Props) {
  const router = useRouter();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <Calendar className="h-4 w-4" />
          Scadenze
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-2 grid-cols-3">
          <div className="text-center">
            <p className="text-2xl font-bold">{data.in_scadenza_oggi}</p>
            <p className="text-xs text-muted-foreground">Oggi</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{data.in_scadenza_7gg}</p>
            <p className="text-xs text-muted-foreground">7 giorni</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-600">{data.scadute_conteggio}</p>
            <p className="text-xs text-muted-foreground">Scadute</p>
          </div>
        </div>

        {data.scadute_importo > 0 && (
          <div className="flex items-center gap-2 rounded-md bg-red-50 p-2 text-sm dark:bg-red-950">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <span className="text-red-700 dark:text-red-300">
              {formatCurrency(data.scadute_importo)} scaduti
            </span>
          </div>
        )}

        {data.prossime.length > 0 && (
          <div className="space-y-2">
            {data.prossime.map((s) => (
              <div key={s.id} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 min-w-0">
                  <Badge
                    variant={s.stato === "scaduta" ? "destructive" : "secondary"}
                    className="text-[10px] shrink-0"
                  >
                    {new Date(s.data_scadenza).toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit" })}
                  </Badge>
                  <span className="truncate">{s.descrizione || "—"}</span>
                </div>
                <span className="font-medium shrink-0 ml-2">{formatCurrency(s.importo)}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button variant="ghost" size="sm" className="w-full text-xs" onClick={() => router.push("/scadenzario")}>
          Vedi tutte <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      </CardFooter>
    </Card>
  );
}
