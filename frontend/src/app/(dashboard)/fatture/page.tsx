"use client";

import { useCallback, useEffect, useState } from "react";
import { TrendingUp, TrendingDown, ArrowLeftRight, Info } from "lucide-react";
import { toast } from "sonner";
import { getInvoiceStats } from "@/lib/api/integrations";
import type { InvoiceStats, InvoiceMonthlyData } from "@/types/integration";
import { LoadingState } from "@/components/shared/loading-state";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) return "\u2014";
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

function formatCompact(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `${(value / 1_000).toFixed(0)}K`;
  }
  return value.toFixed(0);
}

const MESI_LABELS = [
  "Gen",
  "Feb",
  "Mar",
  "Apr",
  "Mag",
  "Giu",
  "Lug",
  "Ago",
  "Set",
  "Ott",
  "Nov",
  "Dic",
];

const TRIMESTRI_LABELS = ["Gen/Mar", "Apr/Giu", "Lug/Set", "Ott/Dic"];

const TEAL = "#33b9c0";
const PINK = "#f9567c";

const currentYear = new Date().getFullYear();
const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

type Divisione = "mensile" | "trimestrale";

interface ChartDataPoint {
  label: string;
  ricavi: number;
  costi: number;
}

function prepareChartData(
  perMese: InvoiceMonthlyData[],
  anno: string,
  divisione: Divisione,
  field: "imponibile" | "iva"
): ChartDataPoint[] {
  const emesseKey =
    field === "imponibile" ? "emesse_imponibile" : "emesse_iva";
  const ricevuteKey =
    field === "imponibile" ? "ricevute_imponibile" : "ricevute_iva";

  if (divisione === "mensile") {
    return MESI_LABELS.map((label, i) => {
      const meseKey = `${anno}-${String(i + 1).padStart(2, "0")}`;
      const found = perMese.find((m) => m.mese === meseKey);
      return {
        label,
        ricavi: found ? found[emesseKey] : 0,
        costi: found ? found[ricevuteKey] : 0,
      };
    });
  }

  // Trimestrale
  return TRIMESTRI_LABELS.map((label, qi) => {
    let ricavi = 0;
    let costi = 0;
    for (let m = qi * 3; m < qi * 3 + 3; m++) {
      const meseKey = `${anno}-${String(m + 1).padStart(2, "0")}`;
      const found = perMese.find((d) => d.mese === meseKey);
      if (found) {
        ricavi += found[emesseKey];
        costi += found[ricevuteKey];
      }
    }
    return { label, ricavi, costi };
  });
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string }>;
  label?: string;
  ricaviLabel: string;
  costiLabel: string;
  diffLabel: string;
}

function CustomTooltip({
  active,
  payload,
  label,
  ricaviLabel,
  costiLabel,
  diffLabel,
}: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const ricavi = payload.find((p) => p.dataKey === "ricavi")?.value ?? 0;
  const costi = payload.find((p) => p.dataKey === "costi")?.value ?? 0;
  const diff = ricavi - costi;
  return (
    <div className="rounded-lg border bg-white p-3 shadow-md text-sm">
      <p className="font-medium mb-1">{label}</p>
      <p style={{ color: TEAL }}>
        {ricaviLabel}: {formatCurrency(ricavi)}
      </p>
      <p style={{ color: PINK }}>
        {costiLabel}: {formatCurrency(costi)}
      </p>
      <p className="border-t mt-1 pt-1 font-medium">
        {diffLabel}: {formatCurrency(diff)}
      </p>
    </div>
  );
}

export default function FattureSituazionePage() {
  const [stats, setStats] = useState<InvoiceStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(String(currentYear));
  const [divisione, setDivisione] = useState<Divisione>("mensile");

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

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  if (loading) {
    return <LoadingState />;
  }

  const imponibileData = prepareChartData(
    stats?.per_mese ?? [],
    selectedYear,
    divisione,
    "imponibile"
  );
  const ivaData = prepareChartData(
    stats?.per_mese ?? [],
    selectedYear,
    divisione,
    "iva"
  );

  const ricaviImponibile = stats?.emesse_imponibile ?? 0;
  const costiImponibile = stats?.ricevute_imponibile ?? 0;
  const diffImponibile = ricaviImponibile - costiImponibile;

  const ivaCredito = stats?.emesse_iva ?? 0;
  const ivaDebito = stats?.ricevute_iva ?? 0;
  const ivaNetta = ivaCredito - ivaDebito;

  return (
    <div className="space-y-6">
      {/* Filtri */}
      <div className="flex items-end gap-4">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1 block">
            Anno
          </label>
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Anno" />
            </SelectTrigger>
            <SelectContent>
              {years.map((y) => (
                <SelectItem key={y} value={String(y)}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-1 block">
            Divisione
          </label>
          <Select
            value={divisione}
            onValueChange={(v) => setDivisione(v as Divisione)}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="mensile">Mensile</SelectItem>
              <SelectItem value="trimestrale">Trimestrale</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Grafici affiancati */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Grafico Imponibile */}
        <div className="rounded-lg border bg-white">
          <div className="p-4 pb-0">
            <h3 className="text-base font-semibold">
              Imponibile {selectedYear}
            </h3>
          </div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={imponibileData} barGap={2}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#e5e7eb"
                />
                <XAxis
                  dataKey="label"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#9ca3af" }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#9ca3af" }}
                  tickFormatter={formatCompact}
                />
                <Tooltip
                  content={
                    <CustomTooltip
                      ricaviLabel="Ricavi"
                      costiLabel="Costi"
                      diffLabel="Differenza"
                    />
                  }
                />
                <Bar
                  dataKey="ricavi"
                  fill={TEAL}
                  radius={[2, 2, 0, 0]}
                  maxBarSize={24}
                />
                <Bar
                  dataKey="costi"
                  fill={PINK}
                  radius={[2, 2, 0, 0]}
                  maxBarSize={24}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {/* KPI sotto grafico Imponibile */}
          <div className="grid grid-cols-3 border-t">
            <div className="p-4 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 shrink-0" style={{ color: TEAL }} />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Ricavi</p>
                <p className="text-sm font-semibold truncate">
                  {formatCurrency(ricaviImponibile)}
                </p>
              </div>
            </div>
            <div className="p-4 flex items-center gap-2 border-l">
              <TrendingDown
                className="h-4 w-4 shrink-0"
                style={{ color: PINK }}
              />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Costi</p>
                <p className="text-sm font-semibold truncate">
                  {formatCurrency(costiImponibile)}
                </p>
              </div>
            </div>
            <div className="p-4 flex items-center gap-2 border-l">
              <ArrowLeftRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">Differenza</p>
                <p
                  className="text-sm font-semibold truncate"
                  style={{ color: diffImponibile >= 0 ? TEAL : PINK }}
                >
                  {formatCurrency(diffImponibile)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Grafico IVA */}
        <div className="rounded-lg border bg-white">
          <div className="p-4 pb-0 flex items-center gap-2">
            <h3 className="text-base font-semibold">
              Calcolo IVA {selectedYear}
            </h3>
            <Info className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="p-4">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={ivaData} barGap={2}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#e5e7eb"
                />
                <XAxis
                  dataKey="label"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#9ca3af" }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#9ca3af" }}
                  tickFormatter={formatCompact}
                />
                <Tooltip
                  content={
                    <CustomTooltip
                      ricaviLabel="A credito"
                      costiLabel="A debito"
                      diffLabel="IVA netta"
                    />
                  }
                />
                <Bar
                  dataKey="ricavi"
                  fill={TEAL}
                  radius={[2, 2, 0, 0]}
                  maxBarSize={24}
                />
                <Bar
                  dataKey="costi"
                  fill={PINK}
                  radius={[2, 2, 0, 0]}
                  maxBarSize={24}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {/* KPI sotto grafico IVA */}
          <div className="grid grid-cols-3 border-t">
            <div className="p-4 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 shrink-0" style={{ color: TEAL }} />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">A credito</p>
                <p className="text-sm font-semibold truncate">
                  {formatCurrency(ivaCredito)}
                </p>
              </div>
            </div>
            <div className="p-4 flex items-center gap-2 border-l">
              <TrendingDown
                className="h-4 w-4 shrink-0"
                style={{ color: PINK }}
              />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">A debito</p>
                <p className="text-sm font-semibold truncate">
                  {formatCurrency(ivaDebito)}
                </p>
              </div>
            </div>
            <div className="p-4 flex items-center gap-2 border-l">
              <ArrowLeftRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">IVA netta</p>
                <p
                  className="text-sm font-semibold truncate"
                  style={{ color: ivaNetta >= 0 ? TEAL : PINK }}
                >
                  {formatCurrency(ivaNetta)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sezione Andamento Entrate/Uscite */}
      <div className="rounded-lg border bg-white p-4">
        <div className="flex items-center gap-2">
          <Info className="h-4 w-4 text-muted-foreground shrink-0" />
          <p className="text-sm text-muted-foreground">
            Per visualizzare l&apos;andamento Entrate/Uscite,{" "}
            <span className="text-[#6672ff] font-medium cursor-pointer hover:underline">
              associa le controparti
            </span>{" "}
            alle tue fatture.
          </p>
        </div>
      </div>

      {/* Tabelle Clienti / Fornitori */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Clienti */}
        <div className="rounded-lg border bg-white">
          <div className="p-4 flex items-center gap-2 border-b">
            <TrendingUp className="h-4 w-4" style={{ color: TEAL }} />
            <h3 className="font-semibold text-sm">Clienti</h3>
          </div>
          {stats && stats.top_clienti.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Cliente</TableHead>
                  <TableHead className="text-right">
                    Ricavi (imponibili)
                  </TableHead>
                  <TableHead className="text-right">Documenti</TableHead>
                  <TableHead className="text-right">
                    % {selectedYear}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.top_clienti.map((c) => (
                  <TableRow key={c.nome}>
                    <TableCell className="text-sm">{c.nome}</TableCell>
                    <TableCell className="text-sm text-right">
                      {formatCurrency(c.imponibile)}
                    </TableCell>
                    <TableCell className="text-sm text-right">
                      {c.documenti}
                    </TableCell>
                    <TableCell className="text-sm text-right">
                      {c.percentuale.toFixed(1)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Nessun dato disponibile
            </p>
          )}
        </div>

        {/* Top Fornitori */}
        <div className="rounded-lg border bg-white">
          <div className="p-4 flex items-center gap-2 border-b">
            <TrendingDown className="h-4 w-4" style={{ color: PINK }} />
            <h3 className="font-semibold text-sm">Fornitori</h3>
          </div>
          {stats && stats.top_fornitori.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fornitore</TableHead>
                  <TableHead className="text-right">
                    Costi (imponibili)
                  </TableHead>
                  <TableHead className="text-right">Documenti</TableHead>
                  <TableHead className="text-right">
                    % {selectedYear}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.top_fornitori.map((f) => (
                  <TableRow key={f.nome}>
                    <TableCell className="text-sm">{f.nome}</TableCell>
                    <TableCell className="text-sm text-right">
                      {formatCurrency(f.imponibile)}
                    </TableCell>
                    <TableCell className="text-sm text-right">
                      {f.documenti}
                    </TableCell>
                    <TableCell className="text-sm text-right">
                      {f.percentuale.toFixed(1)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Nessun dato disponibile
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
