"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { ScheduleAgingResponse } from "@/types/schedule";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AgingChart } from "@/components/schedules/aging-chart";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

export default function AgingPage() {
  const router = useRouter();
  const { currentCompany } = useAuthStore();

  const [aging, setAging] = useState<ScheduleAgingResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const resp = await api.get<ScheduleAgingResponse>("/schedules/aging");
      setAging(resp.data);
    } catch {
      toast.error("Errore nel caricamento dell'aging");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) return <LoadingState />;
  if (!aging) return null;

  const totaleAttive = aging.attive.reduce((sum, b) => sum + b.importo_residuo, 0);
  const totalePassive = aging.passive.reduce((sum, b) => sum + b.importo_residuo, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/scadenzario")}>
          <ArrowLeft className="h-4 w-4 mr-1" />
          Scadenzario
        </Button>
      </div>

      <PageHeader
        title="Aging scadenze"
        description="Analisi per fascia temporale delle scadenze aperte"
      />

      <AgingChart attive={aging.attive} passive={aging.passive} />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Attive */}
        <Card>
          <CardHeader>
            <CardTitle className="text-green-700">
              Da incassare &mdash; {formatCurrency(totaleAttive)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {aging.attive.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                Nessuna scadenza attiva
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fascia</TableHead>
                    <TableHead className="text-right">N.</TableHead>
                    <TableHead className="text-right">Totale</TableHead>
                    <TableHead className="text-right">Residuo</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {aging.attive.map((band) => (
                    <TableRow
                      key={band.fascia}
                      className="cursor-pointer hover:bg-green-50/50"
                      onClick={() =>
                        router.push(`/scadenzario?tipo=attiva&stato=aperta`)
                      }
                    >
                      <TableCell className="font-medium">{band.fascia}</TableCell>
                      <TableCell className="text-right">{band.conteggio}</TableCell>
                      <TableCell className="text-right font-mono">
                        {formatCurrency(band.importo_totale)}
                      </TableCell>
                      <TableCell className="text-right font-mono font-semibold">
                        {formatCurrency(band.importo_residuo)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Passive */}
        <Card>
          <CardHeader>
            <CardTitle className="text-red-700">
              Da pagare &mdash; {formatCurrency(totalePassive)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {aging.passive.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                Nessuna scadenza passiva
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fascia</TableHead>
                    <TableHead className="text-right">N.</TableHead>
                    <TableHead className="text-right">Totale</TableHead>
                    <TableHead className="text-right">Residuo</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {aging.passive.map((band) => (
                    <TableRow
                      key={band.fascia}
                      className="cursor-pointer hover:bg-red-50/50"
                      onClick={() =>
                        router.push(`/scadenzario?tipo=passiva&stato=aperta`)
                      }
                    >
                      <TableCell className="font-medium">{band.fascia}</TableCell>
                      <TableCell className="text-right">{band.conteggio}</TableCell>
                      <TableCell className="text-right font-mono">
                        {formatCurrency(band.importo_totale)}
                      </TableCell>
                      <TableCell className="text-right font-mono font-semibold">
                        {formatCurrency(band.importo_residuo)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
