"use client";

import { useRouter } from "next/navigation";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AlertSection } from "@/types/dashboard";
import { GRAVITA_COLORS } from "@/types/dashboard";

const GRAVITA_ICONS = {
  info: Info,
  warning: AlertTriangle,
  critical: AlertCircle,
};

interface Props {
  data: AlertSection;
}

export function AlertWidget({ data }: Props) {
  const router = useRouter();

  if (data.totale === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <AlertTriangle className="h-4 w-4" />
          Alert Attivi ({data.totale})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {data.items.map((alert) => {
            const Icon = GRAVITA_ICONS[alert.gravita] || AlertTriangle;
            const colorClass = GRAVITA_COLORS[alert.gravita] || GRAVITA_COLORS.warning;

            return (
              <button
                key={alert.id}
                onClick={() => router.push("/cash-flow")}
                className="flex w-full items-start gap-3 rounded-lg p-2 hover:bg-muted/50 transition-colors text-left"
              >
                <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${colorClass}`}>
                  <Icon className="h-3 w-3" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm">{alert.messaggio}</p>
                  {alert.data_prevista && (
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {new Date(alert.data_prevista).toLocaleDateString("it-IT")}
                    </p>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
