"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { RefreshCw, Settings2 } from "lucide-react";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import { it } from "date-fns/locale";
import { useAuthStore } from "@/stores/auth-store";
import { getDashboard, getWidgets, updateWidgets, resetWidgets } from "@/lib/api/dashboard";
import type { DashboardData, DashboardWidget } from "@/types/dashboard";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState } from "@/components/shared/empty-state";
import { DashboardGrid } from "@/components/dashboard/DashboardGrid";
import { DashboardSkeleton } from "@/components/dashboard/DashboardSkeleton";
import { WidgetCustomizer } from "@/components/dashboard/WidgetCustomizer";
import { Landmark } from "lucide-react";

const AUTO_REFRESH_MS = 5 * 60 * 1000; // 5 minutes

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 12) return "Buongiorno";
  if (hour >= 12 && hour < 18) return "Buon pomeriggio";
  return "Buonasera";
}

const PERIOD_OPTIONS = [
  { value: "30", label: "Ultimo mese" },
  { value: "90", label: "Ultimi 3 mesi" },
  { value: "180", label: "Ultimi 6 mesi" },
  { value: "365", label: "Ultimo anno" },
];

export default function DashboardPage() {
  const { user, currentCompany } = useAuthStore();

  const [data, setData] = useState<DashboardData | null>(null);
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [period, setPeriod] = useState("30");
  const [customizerOpen, setCustomizerOpen] = useState(false);

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadData = useCallback(async (showRefresh = false) => {
    try {
      if (showRefresh) setRefreshing(true);

      const today = new Date();
      const periodDays = parseInt(period);
      const periodStart = new Date(today.getTime() - periodDays * 24 * 60 * 60 * 1000);

      const params: Record<string, string> = {
        period_start: periodStart.toISOString().split("T")[0],
        period_end: today.toISOString().split("T")[0],
      };

      const [dashboardData, widgetData] = await Promise.all([
        getDashboard(params),
        getWidgets(),
      ]);

      setData(dashboardData);
      setWidgets(widgetData);
      setLastUpdate(new Date());
    } catch {
      toast.error("Errore nel caricamento della dashboard");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [period]);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh with Page Visibility API
  useEffect(() => {
    const startInterval = () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => loadData(true), AUTO_REFRESH_MS);
    };

    const handleVisibility = () => {
      if (document.hidden) {
        if (intervalRef.current) clearInterval(intervalRef.current);
      } else {
        loadData(true);
        startInterval();
      }
    };

    startInterval();
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [loadData]);

  const handleSaveWidgets = async (updatedWidgets: DashboardWidget[]) => {
    try {
      const saved = await updateWidgets(updatedWidgets.map((w) => ({
        widget_type: w.widget_type,
        posizione: w.posizione,
        colonna: w.colonna,
        dimensione: w.dimensione,
        visibile: w.visibile,
        configurazione: w.configurazione,
      })));
      setWidgets(saved);
      toast.success("Layout salvato");
    } catch {
      toast.error("Errore nel salvataggio");
    }
  };

  const handleResetWidgets = async () => {
    try {
      const reset = await resetWidgets();
      setWidgets(reset);
      setCustomizerOpen(false);
      toast.success("Layout ripristinato");
    } catch {
      toast.error("Errore nel ripristino");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <DashboardSkeleton />
      </div>
    );
  }

  // Empty state: no accounts
  if (data && data.saldi.conti.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">
            {getGreeting()}, {user?.first_name}
          </h1>
          <p className="text-sm text-muted-foreground">
            {new Date().toLocaleDateString("it-IT", {
              weekday: "long", day: "numeric", month: "long", year: "numeric",
            })}
          </p>
        </div>
        <EmptyState
          icon={Landmark}
          title="Nessun conto bancario configurato"
          description="Per iniziare, aggiungi almeno un conto bancario. La dashboard mostrera i dati aggregati di tutti i moduli."
          actionLabel="Aggiungi Conto"
          onAction={() => window.location.href = "/conti"}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            {getGreeting()}, {user?.first_name}
          </h1>
          <p className="text-sm text-muted-foreground">
            {new Date().toLocaleDateString("it-IT", {
              weekday: "long", day: "numeric", month: "long", year: "numeric",
            })}
            {currentCompany && ` — ${currentCompany.company_name}`}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {lastUpdate && (
            <span className="text-xs text-muted-foreground hidden sm:inline">
              Aggiornato {formatDistanceToNow(lastUpdate, { addSuffix: true, locale: it })}
            </span>
          )}
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[140px] h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PERIOD_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="icon"
            className="h-9 w-9"
            onClick={() => setCustomizerOpen(true)}
          >
            <Settings2 className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-9 w-9"
            onClick={() => loadData(true)}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Widget Grid */}
      {data && <DashboardGrid data={data} widgets={widgets} />}

      {/* Widget Customizer Dialog */}
      <WidgetCustomizer
        open={customizerOpen}
        onOpenChange={setCustomizerOpen}
        widgets={widgets}
        onSave={handleSaveWidgets}
        onReset={handleResetWidgets}
      />
    </div>
  );
}
