"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plug, Landmark, FileText, Building2, Scale, Webhook, Plus, Trash2, Copy } from "lucide-react";
import { toast } from "sonner";
import { getOverview, listWebhooks, createWebhook, deleteWebhook, toggleIntegration } from "@/lib/api/integrations";
import type { IntegrationStatusItem, WebhookEndpoint } from "@/types/integration";
import { INTEGRATION_STATUS_LABELS, INTEGRATION_STATUS_COLORS, WEBHOOK_TYPE_LABELS } from "@/types/integration";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

const INTEGRATION_ICONS: Record<string, typeof Plug> = {
  open_banking: Landmark,
  fatture_elettroniche: FileText,
  cbi_corporate_banking: Building2,
  agenzia_entrate: Scale,
};

const INTEGRATION_ROUTES: Record<string, string> = {
  open_banking: "/integrazioni/open-banking",
  fatture_elettroniche: "/integrazioni/fatture",
  cbi_corporate_banking: "/integrazioni/cbi-sepa",
  agenzia_entrate: "/integrazioni/agenzia-entrate",
};

export default function IntegrazioniPage() {
  const router = useRouter();
  const [integrations, setIntegrations] = useState<IntegrationStatusItem[]>([]);
  const [webhooks, setWebhooks] = useState<WebhookEndpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState<Record<string, boolean>>({});
  const [webhookType, setWebhookType] = useState("open_banking_sync");
  const [showWebhooks, setShowWebhooks] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [overviewData, webhookData] = await Promise.all([
        getOverview(),
        listWebhooks(),
      ]);
      setIntegrations(overviewData.integrations);
      setWebhooks(webhookData.items);
    } catch {
      toast.error("Errore nel caricamento delle integrazioni");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWebhook = async () => {
    try {
      await createWebhook(webhookType);
      toast.success("Webhook creato");
      loadData();
    } catch {
      toast.error("Errore nella creazione del webhook");
    }
  };

  const handleDeleteWebhook = async (id: string) => {
    try {
      await deleteWebhook(id);
      toast.success("Webhook eliminato");
      loadData();
    } catch {
      toast.error("Errore nell'eliminazione del webhook");
    }
  };

  const handleToggleIntegration = async (integrationType: string, enabled: boolean) => {
    setToggling((m) => ({ ...m, [integrationType]: true }));
    try {
      await toggleIntegration(integrationType, enabled);
      setIntegrations((prev) =>
        prev.map((it) => (it.integration_type === integrationType ? { ...it, is_enabled: enabled } : it))
      );
      toast.success(enabled ? "Integrazione attivata" : "Integrazione disattivata");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore nell'aggiornamento integrazione");
    } finally {
      setToggling((m) => ({ ...m, [integrationType]: false }));
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Integrazioni" description="Connetti il gestionale con servizi esterni" />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Integrazioni" description="Connetti il gestionale con servizi esterni" />

      {/* Integration cards grid */}
      <div className="grid gap-4 md:grid-cols-3">
        {integrations.map((item) => {
          const Icon = INTEGRATION_ICONS[item.integration_type] || Plug;
          const route = INTEGRATION_ROUTES[item.integration_type];
          const busy = Boolean(toggling[item.integration_type]);
          return (
            <Card key={item.integration_type} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => route && router.push(route)}>
              <CardHeader className="flex flex-row items-center gap-3 pb-2">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <CardTitle className="text-base">{item.label}</CardTitle>
                </div>
                <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                  <Switch
                    checked={Boolean(item.is_enabled)}
                    disabled={busy}
                    onCheckedChange={(v) => handleToggleIntegration(item.integration_type, Boolean(v))}
                  />
                </div>
                <Badge className={INTEGRATION_STATUS_COLORS[item.status]}>
                  {INTEGRATION_STATUS_LABELS[item.status]}
                </Badge>
              </CardHeader>
              <CardContent>
                <CardDescription>{item.description}</CardDescription>
                <div className="mt-2 text-xs text-muted-foreground">
                  Stato: <strong>{item.is_enabled ? "Attiva" : "Disattiva"}</strong>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Webhook section */}
      <div className="space-y-4">
        <Button variant="outline" onClick={() => setShowWebhooks(!showWebhooks)}>
          <Webhook className="h-4 w-4 mr-2" />
          Webhook ({webhooks.length})
        </Button>

        {showWebhooks && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Webhook Endpoints</CardTitle>
              <CardDescription>Ricevi notifiche in tempo reale sugli eventi</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2">
                <Select value={webhookType} onValueChange={setWebhookType}>
                  <SelectTrigger className="w-[200px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(WEBHOOK_TYPE_LABELS).map(([val, label]) => (
                      <SelectItem key={val} value={val}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button size="sm" onClick={handleCreateWebhook}>
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
                          <Button size="sm" variant="ghost" onClick={() => handleDeleteWebhook(wh.id)}>
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
        )}
      </div>
    </div>
  );
}
