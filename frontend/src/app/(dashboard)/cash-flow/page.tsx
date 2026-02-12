"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { TrendingUp } from "lucide-react";
import { ExportButton } from "@/components/shared/export-button";
import { toast } from "sonner";
import { getCashFlowProjection } from "@/lib/api/cash-flow";
import type { CashFlowProjection } from "@/types/cash-flow";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { CashFlowSummaryCards } from "@/components/cash-flow/CashFlowSummaryCards";
import { CashFlowChart } from "@/components/cash-flow/CashFlowChart";
import { CashFlowControls, type CashFlowFilters } from "@/components/cash-flow/CashFlowControls";
import { CashFlowDetailTable } from "@/components/cash-flow/CashFlowDetailTable";
import { AlertPanel } from "@/components/cash-flow/AlertPanel";

function defaultFilters(): CashFlowFilters {
  const today = new Date();
  const start = new Date(today);
  start.setDate(start.getDate() - 30);
  const end = new Date(today);
  end.setDate(end.getDate() + 90);
  return {
    data_inizio: start.toISOString().split("T")[0],
    data_fine: end.toISOString().split("T")[0],
    raggruppamento: "giornaliero",
    includi_scadenze: true,
    includi_pagamenti: true,
    includi_ricorrenze: true,
  };
}

export default function CashFlowPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<CashFlowFilters>(defaultFilters);
  const [projection, setProjection] = useState<CashFlowProjection | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProjection = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getCashFlowProjection({
        data_inizio: filters.data_inizio,
        data_fine: filters.data_fine,
        includi_scadenze: filters.includi_scadenze,
        includi_pagamenti: filters.includi_pagamenti,
        includi_ricorrenze: filters.includi_ricorrenze,
      });
      setProjection(data);
    } catch {
      toast.error("Errore nel caricamento del cash flow");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchProjection();
  }, [fetchProjection]);

  const handleSave = () => {
    router.push(
      `/cash-flow/forecasts?action=new&data_inizio=${filters.data_inizio}&data_fine=${filters.data_fine}`
    );
  };

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Cash Flow"
        description="Analisi e previsioni di liquidita"
        actions={
          <ExportButton reportType="cash_flow" label="Esporta previsione" />
        }
      />

      <CashFlowControls
        filters={filters}
        onChange={setFilters}
        onSave={handleSave}
      />

      <CashFlowSummaryCards />

      {loading ? (
        <LoadingState />
      ) : projection ? (
        <>
          <CashFlowChart
            lines={projection.lines}
            sogliaMinima={10000}
          />

          <CashFlowDetailTable lines={projection.lines} />
        </>
      ) : (
        <div className="rounded-lg border p-12 text-center">
          <TrendingUp className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium">Nessun dato disponibile</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Importa movimenti bancari o crea scadenze per visualizzare il cash flow.
          </p>
        </div>
      )}

      <AlertPanel />
    </div>
  );
}
