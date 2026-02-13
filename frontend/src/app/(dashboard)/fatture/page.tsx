"use client";

import { useCallback, useEffect, useState } from "react";
import { TrendingUp, TrendingDown, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";
import { getInvoiceStats } from "@/lib/api/integrations";
import type { InvoiceStats } from "@/types/integration";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) return "\u2014";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

const currentYear = new Date().getFullYear();
const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

export default function FattureSituazionePage() {
  const [stats, setStats] = useState<InvoiceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(String(currentYear));

  const loadStats = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getInvoiceStats({ anno: selectedYear });
      setStats(data);
    } catch {
      toast.error("Errore nel caricamento delle statistiche");
    } finally {
      setLoading(false);
    }
  }, [selectedYear]);

  useEffect(() => { loadStats(); }, [loadStats]);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Situazione Fatture"
          description="Panoramica fatture elettroniche ricevute ed emesse"
        />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Situazione Fatture"
        description="Panoramica fatture elettroniche ricevute ed emesse"
        actions={
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Anno" />
            </SelectTrigger>
            <SelectContent>
              {years.map((y) => (
                <SelectItem key={y} value={String(y)}>{y}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-lg border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Fatture Emesse</p>
              <p className="text-2xl font-bold">{stats?.emesse_count ?? 0}</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500/50" />
          </div>
        </div>
        <div className="rounded-lg border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Fatture Ricevute</p>
              <p className="text-2xl font-bold">{stats?.ricevute_count ?? 0}</p>
            </div>
            <TrendingDown className="h-8 w-8 text-red-500/50" />
          </div>
        </div>
        <div className="rounded-lg border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Totale Emesso</p>
              <p className="text-2xl font-bold text-green-600">{formatCurrency(stats?.emesse_totale ?? 0)}</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500/50" />
          </div>
        </div>
        <div className="rounded-lg border p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Totale Ricevuto</p>
              <p className="text-2xl font-bold text-red-600">{formatCurrency(stats?.ricevute_totale ?? 0)}</p>
            </div>
            <TrendingDown className="h-8 w-8 text-red-500/50" />
          </div>
        </div>
      </div>

      {/* Da elaborare banner */}
      {stats && stats.da_elaborare > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <AlertCircle className="h-5 w-5 text-blue-600 shrink-0" />
          <p className="text-sm text-blue-700">
            Hai <strong>{stats.da_elaborare}</strong> fatture da elaborare.{" "}
            <Link href="/fatture/ricevute" className="underline font-medium">
              Vai alle ricevute
            </Link>
          </p>
        </div>
      )}

      {/* Top Clienti / Fornitori */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-lg border p-4">
          <h3 className="font-semibold mb-3">Top Clienti</h3>
          {stats && stats.top_clienti.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead className="text-right">Fatturato</TableHead>
                  <TableHead className="text-right">Doc.</TableHead>
                  <TableHead className="text-right">%</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.top_clienti.map((c) => (
                  <TableRow key={c.nome}>
                    <TableCell className="text-sm">{c.nome}</TableCell>
                    <TableCell className="text-sm text-right">{formatCurrency(c.totale)}</TableCell>
                    <TableCell className="text-sm text-right">{c.documenti}</TableCell>
                    <TableCell className="text-sm text-right">{c.percentuale.toFixed(1)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground py-4 text-center">Nessun dato disponibile</p>
          )}
        </div>

        <div className="rounded-lg border p-4">
          <h3 className="font-semibold mb-3">Top Fornitori</h3>
          {stats && stats.top_fornitori.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead className="text-right">Fatturato</TableHead>
                  <TableHead className="text-right">Doc.</TableHead>
                  <TableHead className="text-right">%</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.top_fornitori.map((f) => (
                  <TableRow key={f.nome}>
                    <TableCell className="text-sm">{f.nome}</TableCell>
                    <TableCell className="text-sm text-right">{formatCurrency(f.totale)}</TableCell>
                    <TableCell className="text-sm text-right">{f.documenti}</TableCell>
                    <TableCell className="text-sm text-right">{f.percentuale.toFixed(1)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground py-4 text-center">Nessun dato disponibile</p>
          )}
        </div>
      </div>
    </div>
  );
}
