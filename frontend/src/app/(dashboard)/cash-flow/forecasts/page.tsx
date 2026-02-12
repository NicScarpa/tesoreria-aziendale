"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus, FileBarChart, Trash2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { listForecasts, createForecast, deleteForecast } from "@/lib/api/cash-flow";
import type { CashFlowForecast } from "@/types/cash-flow";
import { FORECAST_STATUS_LABELS, FORECAST_STATUS_COLORS, FORECAST_TYPE_LABELS } from "@/types/cash-flow";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT");
}

export default function ForecastsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [forecasts, setForecasts] = useState<CashFlowForecast[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(searchParams.get("action") === "new");

  // Form state
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState("base");
  const [dataInizio, setDataInizio] = useState(
    searchParams.get("data_inizio") || new Date().toISOString().split("T")[0]
  );
  const [dataFine, setDataFine] = useState(() => {
    const d = searchParams.get("data_fine");
    if (d) return d;
    const end = new Date();
    end.setDate(end.getDate() + 90);
    return end.toISOString().split("T")[0];
  });
  const [creating, setCreating] = useState(false);

  const fetchForecasts = async () => {
    setLoading(true);
    try {
      const data = await listForecasts();
      setForecasts(data.items);
      setTotal(data.total);
    } catch {
      toast.error("Errore nel caricamento delle previsioni");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecasts();
  }, []);

  const handleCreate = async () => {
    if (!nome.trim()) return;
    setCreating(true);
    try {
      const forecast = await createForecast({
        nome,
        tipo,
        data_inizio: dataInizio,
        data_fine: dataFine,
      });
      toast.success("Previsione creata");
      setDialogOpen(false);
      router.push(`/cash-flow/forecasts/${forecast.id}`);
    } catch {
      toast.error("Errore nella creazione");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteForecast(id);
      toast.success("Previsione eliminata");
      fetchForecasts();
    } catch {
      toast.error("Errore nell'eliminazione");
    }
  };

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="Previsioni"
        description="Gestisci le previsioni di cash flow salvate"
        actions={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Nuova Previsione
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Nuova Previsione Cash Flow</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-2">
                <div>
                  <label className="text-sm font-medium">Nome</label>
                  <Input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="es. Previsione Q1 2026" />
                </div>
                <div>
                  <label className="text-sm font-medium">Tipo</label>
                  <Select value={tipo} onValueChange={setTipo}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="base">Base</SelectItem>
                      <SelectItem value="ottimistico">Ottimistico</SelectItem>
                      <SelectItem value="pessimistico">Pessimistico</SelectItem>
                      <SelectItem value="personalizzato">Personalizzato</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-sm font-medium">Data inizio</label>
                    <Input type="date" value={dataInizio} onChange={(e) => setDataInizio(e.target.value)} />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Data fine</label>
                    <Input type="date" value={dataFine} onChange={(e) => setDataFine(e.target.value)} />
                  </div>
                </div>
                <Button onClick={handleCreate} disabled={creating || !nome.trim()} className="w-full">
                  {creating ? "Generazione..." : "Genera Previsione"}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        }
      />

      {loading ? (
        <LoadingState />
      ) : forecasts.length === 0 ? (
        <EmptyState
          title="Nessuna previsione"
          description="Crea la tua prima previsione di cash flow per iniziare"
          icon={FileBarChart}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {forecasts.map((f) => (
            <Link
              key={f.id}
              href={`/cash-flow/forecasts/${f.id}`}
              className="group rounded-lg border bg-card p-4 transition-colors hover:border-primary/50"
            >
              <div className="flex items-start justify-between">
                <h3 className="font-medium group-hover:text-primary">{f.nome}</h3>
                <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", FORECAST_STATUS_COLORS[f.stato])}>
                  {FORECAST_STATUS_LABELS[f.stato]}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {FORECAST_TYPE_LABELS[f.tipo]} | {formatDate(f.data_inizio)} - {formatDate(f.data_fine)}
              </p>
              <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Saldo iniziale</p>
                  <p className="font-medium">{formatCurrency(f.saldo_iniziale)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Saldo finale</p>
                  <p className="font-medium">{formatCurrency(f.saldo_finale_previsto)}</p>
                </div>
              </div>
              <div className="mt-2 flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2"
                  onClick={(e) => {
                    e.preventDefault();
                    handleDelete(f.id);
                  }}
                >
                  <Trash2 className="h-3 w-3 text-destructive" />
                </Button>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
