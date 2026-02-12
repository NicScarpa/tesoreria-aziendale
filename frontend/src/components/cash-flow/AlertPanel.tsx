"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Check, X, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { listAlerts, resolveAlert, ignoreAlert } from "@/lib/api/cash-flow";
import type { CashFlowAlert } from "@/types/cash-flow";
import { ALERT_TYPE_LABELS, ALERT_TYPE_COLORS } from "@/types/cash-flow";
import { Button } from "@/components/ui/button";

interface AlertPanelProps {
  className?: string;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT");
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

export function AlertPanel({ className }: AlertPanelProps) {
  const [alerts, setAlerts] = useState<CashFlowAlert[]>([]);
  const [collapsed, setCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const data = await listAlerts({ stato: "attivo" });
      setAlerts(data.items);
    } catch {
      // Non-critical
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleResolve = async (id: string) => {
    try {
      await resolveAlert(id);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
      toast.success("Alert risolto");
    } catch {
      toast.error("Errore nella risoluzione dell'alert");
    }
  };

  const handleIgnore = async (id: string) => {
    try {
      await ignoreAlert(id);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
      toast.info("Alert ignorato");
    } catch {
      toast.error("Errore");
    }
  };

  if (loading || alerts.length === 0) return null;

  return (
    <div className={cn("rounded-lg border", className)}>
      <button
        className="flex w-full items-center justify-between p-3 text-left"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          <span className="text-sm font-medium">
            {alerts.length} alert attiv{alerts.length === 1 ? "o" : "i"}
          </span>
        </div>
        {collapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
      </button>

      {!collapsed && (
        <div className="border-t">
          {alerts.map((alert) => (
            <div key={alert.id} className="flex items-start gap-3 border-b p-3 last:border-b-0">
              <span className={cn("mt-0.5 inline-flex rounded-full px-2 py-0.5 text-xs font-medium", ALERT_TYPE_COLORS[alert.tipo])}>
                {ALERT_TYPE_LABELS[alert.tipo]}
              </span>
              <div className="flex-1">
                <p className="text-sm">{alert.messaggio}</p>
                <div className="mt-1 flex gap-3 text-xs text-muted-foreground">
                  <span>Data: {formatDate(alert.data_prevista)}</span>
                  <span>Saldo: {formatCurrency(alert.saldo_previsto)}</span>
                  <span>Soglia: {formatCurrency(alert.soglia)}</span>
                </div>
              </div>
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => handleResolve(alert.id)}>
                  <Check className="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => handleIgnore(alert.id)}>
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
