"use client";

import { Landmark, RefreshCw, Unlink, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { OpenBankingConnection } from "@/types/integration";
import { OB_CONNECTION_STATUS_LABELS, OB_CONNECTION_STATUS_COLORS, SYNC_FREQUENCY_LABELS } from "@/types/integration";

function formatDate(d: string | null): string {
  if (!d) return "\u2014";
  return new Date(d).toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

interface Props {
  connection: OpenBankingConnection;
  syncing?: boolean;
  onSync: (id: string) => void;
  onLogs: (id: string) => void;
  onRenew: (id: string) => void;
  onDelete: (id: string) => void;
}

export function OpenBankingConnectionCard({ connection: conn, syncing, onSync, onLogs, onRenew, onDelete }: Props) {
  const isExpiring = conn.consenso_scadenza && new Date(conn.consenso_scadenza).getTime() - Date.now() < 14 * 24 * 60 * 60 * 1000 && new Date(conn.consenso_scadenza).getTime() > Date.now();

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-3 pb-2">
        {conn.institution_logo_url ? (
          <img src={conn.institution_logo_url} alt="" className="h-8 w-8 rounded" />
        ) : (
          <Landmark className="h-8 w-8 text-muted-foreground" />
        )}
        <div className="flex-1">
          <CardTitle className="text-base">{conn.institution_nome || "Banca"}</CardTitle>
          <p className="text-xs text-muted-foreground">{SYNC_FREQUENCY_LABELS[conn.frequenza_sync]}</p>
        </div>
        <Badge className={OB_CONNECTION_STATUS_COLORS[conn.stato]}>
          {OB_CONNECTION_STATUS_LABELS[conn.stato]}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-muted-foreground">Ultimo sync:</span>
            <p className="font-medium">{formatDate(conn.ultimo_sync)}</p>
          </div>
          <div>
            <span className="text-muted-foreground">Consenso scade:</span>
            <p className="font-medium">{formatDate(conn.consenso_scadenza)}</p>
          </div>
        </div>
        {conn.errore_ultimo && (
          <p className="text-xs text-destructive">{conn.errore_ultimo}</p>
        )}
        <div className="flex gap-2 flex-wrap">
          <Button size="sm" variant="outline" disabled={syncing} onClick={() => onSync(conn.id)}>
            <RefreshCw className={`h-3 w-3 mr-1 ${syncing ? "animate-spin" : ""}`} />
            Sync
          </Button>
          <Button size="sm" variant="outline" onClick={() => onLogs(conn.id)}>
            <Clock className="h-3 w-3 mr-1" /> Log
          </Button>
          {isExpiring && (
            <Button size="sm" variant="outline" className="text-amber-700" onClick={() => onRenew(conn.id)}>
              Rinnova Consenso
            </Button>
          )}
          <Button size="sm" variant="ghost" className="text-destructive" onClick={() => onDelete(conn.id)}>
            <Unlink className="h-3 w-3 mr-1" /> Revoca
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
