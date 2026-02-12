"use client";

import { useState } from "react";
import { Plus, Trash2, Copy, Webhook } from "lucide-react";
import { toast } from "sonner";
import { listWebhooks, createWebhook, deleteWebhook } from "@/lib/api/integrations";
import type { WebhookEndpoint } from "@/types/integration";
import { WEBHOOK_TYPE_LABELS } from "@/types/integration";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface Props {
  webhooks: WebhookEndpoint[];
  onRefresh: () => void;
}

export function WebhookSection({ webhooks, onRefresh }: Props) {
  const [tipo, setTipo] = useState("open_banking_sync");

  const handleCreate = async () => {
    try {
      await createWebhook(tipo);
      toast.success("Webhook creato");
      onRefresh();
    } catch {
      toast.error("Errore nella creazione");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteWebhook(id);
      toast.success("Webhook eliminato");
      onRefresh();
    } catch {
      toast.error("Errore nell'eliminazione");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Webhook className="h-4 w-4" /> Webhook Endpoints
        </CardTitle>
        <CardDescription>Ricevi notifiche in tempo reale sugli eventi</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <Select value={tipo} onValueChange={setTipo}>
            <SelectTrigger className="w-[200px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(WEBHOOK_TYPE_LABELS).map(([val, label]) => (
                <SelectItem key={val} value={val}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button size="sm" onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-1" /> Crea
          </Button>
        </div>

        {webhooks.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tipo</TableHead>
                <TableHead>URL Path</TableHead>
                <TableHead>Chiamate</TableHead>
                <TableHead>Errori</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {webhooks.map((wh) => (
                <TableRow key={wh.id}>
                  <TableCell className="text-sm">{WEBHOOK_TYPE_LABELS[wh.tipo] || wh.tipo}</TableCell>
                  <TableCell>
                    <code className="text-xs bg-muted px-2 py-1 rounded">/webhooks/{wh.url_path}</code>
                    <Button size="sm" variant="ghost" className="ml-1 h-6 w-6 p-0" onClick={() => { navigator.clipboard.writeText(`/webhooks/${wh.url_path}`); toast.success("Copiato"); }}>
                      <Copy className="h-3 w-3" />
                    </Button>
                  </TableCell>
                  <TableCell className="text-sm">{wh.trigger_count}</TableCell>
                  <TableCell className="text-sm">{wh.failure_count}</TableCell>
                  <TableCell>
                    <Button size="sm" variant="ghost" onClick={() => handleDelete(wh.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
