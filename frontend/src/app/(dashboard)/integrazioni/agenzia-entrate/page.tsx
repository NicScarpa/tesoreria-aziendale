"use client";

import { useEffect, useMemo, useState } from "react";
import { Scale, RefreshCw, Save, Play, Bug, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { getConfig, updateConfig, toggleIntegration, adeTestConnection, adeSyncInvoices, adeSyncCorrispettivi } from "@/lib/api/integrations";
import type { IntegrationConfig } from "@/types/integration";
import { INTEGRATION_STATUS_LABELS, INTEGRATION_STATUS_COLORS } from "@/types/integration";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function yearStartISO(): string {
  const y = new Date().getFullYear();
  return `${y}-01-01`;
}

export default function AgenziaEntratePage() {
  const [cfg, setCfg] = useState<IntegrationConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingAuto, setSavingAuto] = useState(false);
  const [testing, setTesting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [toggling, setToggling] = useState(false);

  const [cf, setCf] = useState("");
  const [password, setPassword] = useState("");
  const [pin, setPin] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showPin, setShowPin] = useState(false);

  // Auto-sync settings (saved in cfg.config)
  const [lookbackDays, setLookbackDays] = useState(7);
  const [autoIssued, setAutoIssued] = useState(true);
  const [autoReceived, setAutoReceived] = useState(true);
  const [autoReceipts, setAutoReceipts] = useState(false);

  // Portal settings (saved in cfg.config)
  const [portalSaving, setPortalSaving] = useState(false);
  const [workingMode, setWorkingMode] = useState<"auto" | "me_stesso" | "incaricato">("auto");
  const [incaricante, setIncaricante] = useState("");
  const [corrTipo, setCorrTipo] = useState("RT");
  const [loginUrl, setLoginUrl] = useState("");

  // Sync dialog
  const [showSync, setShowSync] = useState(false);
  const [dateFrom, setDateFrom] = useState(yearStartISO());
  const [dateTo, setDateTo] = useState(todayISO());
  const [doIssued, setDoIssued] = useState(true);
  const [doReceived, setDoReceived] = useState(true);
  const [doReceipts, setDoReceipts] = useState(true);
  const [debug, setDebug] = useState(false);

  const statusBadge = useMemo(() => {
    if (!cfg) return null;
    return (
      <Badge className={INTEGRATION_STATUS_COLORS[cfg.status]}>
        {INTEGRATION_STATUS_LABELS[cfg.status]}
      </Badge>
    );
  }, [cfg]);

  const load = async () => {
    setLoading(true);
    try {
      const data = await getConfig("agenzia_entrate");
      setCfg(data);

      const c = (data?.config || {}) as Record<string, unknown>;
      const lb = Number(c.ade_auto_invoice_lookback_days ?? 7);
      setLookbackDays(Number.isFinite(lb) ? Math.max(1, Math.min(30, lb)) : 7);
      setAutoIssued(c.ade_auto_sync_issued === undefined ? true : Boolean(c.ade_auto_sync_issued));
      setAutoReceived(c.ade_auto_sync_received === undefined ? true : Boolean(c.ade_auto_sync_received));
      setAutoReceipts(c.ade_auto_sync_corrispettivi === undefined ? false : Boolean(c.ade_auto_sync_corrispettivi));

      const wm = String(c.ade_working_mode ?? "auto");
      setWorkingMode((wm === "me_stesso" || wm === "incaricato" || wm === "auto") ? (wm as any) : "auto");
      setIncaricante(String(c.ade_incaricante ?? ""));
      setCorrTipo(String(c.ade_corrispettivo_tipo ?? "RT").toUpperCase());
      setLoginUrl(String(c.ade_login_url ?? ""));
    } catch {
      toast.error("Errore nel caricamento configurazione AdE");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    if (!cf || !password || !pin) {
      toast.error("Inserisci CF, password e PIN");
      return;
    }
    setSaving(true);
    try {
      const updated = await updateConfig("agenzia_entrate", { credentials: { cf, password, pin } });
      setCfg(updated);
      toast.success("Credenziali salvate");
      setPassword("");
      setPin("");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore nel salvataggio credenziali");
    } finally {
      setSaving(false);
    }
  };

  const handleToggleAutoSync = async (enabled: boolean) => {
    if (!cfg) return;
    setToggling(true);
    try {
      const updated = await toggleIntegration("agenzia_entrate", enabled);
      setCfg(updated);
      toast.success(enabled ? "Import automatico attivato" : "Import automatico disattivato");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore nell'aggiornamento import automatico");
    } finally {
      setToggling(false);
    }
  };

  const handleSaveAutoSettings = async () => {
    setSavingAuto(true);
    try {
      const updated = await updateConfig("agenzia_entrate", {
        config: {
          ade_auto_invoice_lookback_days: Math.max(1, Math.min(30, Number(lookbackDays) || 7)),
          ade_auto_sync_issued: Boolean(autoIssued),
          ade_auto_sync_received: Boolean(autoReceived),
          ade_auto_sync_corrispettivi: Boolean(autoReceipts),
        },
      });
      setCfg(updated);
      toast.success("Impostazioni import automatico salvate");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore nel salvataggio impostazioni");
    } finally {
      setSavingAuto(false);
    }
  };

  const handleSavePortalSettings = async () => {
    setPortalSaving(true);
    try {
      const updated = await updateConfig("agenzia_entrate", {
        config: {
          ade_working_mode: workingMode,
          ade_incaricante: incaricante || null,
          ade_corrispettivo_tipo: (corrTipo || "RT").toUpperCase(),
          ade_login_url: loginUrl || null,
        },
      });
      setCfg(updated);
      toast.success("Impostazioni portale salvate");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore nel salvataggio impostazioni portale");
    } finally {
      setPortalSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const res = await adeTestConnection(debug);
      if (res.success) toast.success(res.message);
      else toast.error(res.message);
      load();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore nel test connessione");
    } finally {
      setTesting(false);
    }
  };

  const handleSync = async () => {
    if (!dateFrom || !dateTo) {
      toast.error("Seleziona il range date");
      return;
    }
    if (!(doIssued || doReceived || doReceipts)) {
      toast.error("Seleziona almeno un flusso da sincronizzare");
      return;
    }
    if (doReceipts) {
      const diffDays = Math.floor((new Date(dateTo).getTime() - new Date(dateFrom).getTime()) / (1000 * 60 * 60 * 24));
      if (diffDays > 93) {
        toast.error("Per i corrispettivi il periodo massimo consentito e' circa 3 mesi. Riduci l'intervallo e riprova.");
        return;
      }
    }
    setSyncing(true);
    try {
      if (doIssued) {
        const r = await adeSyncInvoices({ date_from: dateFrom, date_to: dateTo, direction: "issued", debug });
        toast.success(r.message || `Fatture emesse: +${r.imported_new}, dup ${r.updated}, err ${r.failed}`);
      }
      if (doReceived) {
        const r = await adeSyncInvoices({ date_from: dateFrom, date_to: dateTo, direction: "received", debug });
        toast.success(r.message || `Fatture ricevute: +${r.imported_new}, dup ${r.updated}, err ${r.failed}`);
      }
      if (doReceipts) {
        const r = await adeSyncCorrispettivi({ date_from: dateFrom, date_to: dateTo, debug });
        if (r.pending) {
          const id = r.external_request_id ? ` (ID ${r.external_request_id})` : "";
          toast.success((r.message || "Richiesta corrispettivi inviata ad AdE.") + id);
        } else {
          toast.success(r.message || `Corrispettivi: +${r.imported_new}, dup ${r.updated}, err ${r.failed}`);
        }
      }
      setShowSync(false);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore nella sincronizzazione");
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Agenzia Entrate" description="Connessione e import da Entratel/Fisconline" />
        <Card>
          <CardHeader><CardTitle className="text-base">Caricamento...</CardTitle></CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Agenzia Entrate"
        description="Import fatture e corrispettivi dal portale Fatture e Corrispettivi"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowSync(true)}>
              <Play className="h-4 w-4 mr-2" />
              Sincronizza
            </Button>
            <Button variant="outline" disabled={testing} onClick={handleTest}>
              <RefreshCw className={`h-4 w-4 mr-2 ${testing ? "animate-spin" : ""}`} />
              Test
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader className="flex flex-row items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Scale className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <CardTitle className="text-base">Connessione</CardTitle>
            <p className="text-xs text-muted-foreground">CF + Password + PIN (salvati cifrati lato server)</p>
          </div>
          {statusBadge}
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="space-y-0.5">
              <div className="text-sm font-medium">Import automatico</div>
              <div className="text-xs text-muted-foreground">
                Esegue una ricerca ogni giorno alle <strong>07:00</strong> e <strong>13:00</strong> (Europe/Rome).
              </div>
              <div className="text-xs text-muted-foreground">
                Nota: l&apos;auto-sync parte solo se l&apos;integrazione e&apos; abilitata e le credenziali sono salvate in questo pannello.
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={Boolean(cfg?.is_enabled)}
                disabled={toggling}
                onCheckedChange={(v) => handleToggleAutoSync(Boolean(v))}
              />
            </div>
          </div>

          <div className="rounded-md border p-3 space-y-3">
            <div className="text-sm font-medium">Impostazioni import automatico</div>
            <div className="grid gap-3 md:grid-cols-4">
              <div className="space-y-1 md:col-span-1">
                <Label>Lookback fatture (giorni)</Label>
                <Input
                  type="number"
                  min={1}
                  max={30}
                  value={String(lookbackDays)}
                  onChange={(e) => setLookbackDays(Number(e.target.value))}
                />
              </div>
              <div className="space-y-2 md:col-span-3">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Checkbox checked={autoIssued} onCheckedChange={(v) => setAutoIssued(Boolean(v))} />
                    <Label className="text-sm">Fatture emesse</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox checked={autoReceived} onCheckedChange={(v) => setAutoReceived(Boolean(v))} />
                    <Label className="text-sm">Fatture ricevute</Label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Checkbox checked={autoReceipts} onCheckedChange={(v) => setAutoReceipts(Boolean(v))} />
                    <Label className="text-sm">Corrispettivi (asincrono)</Label>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  Nota: i corrispettivi possono risultare <code>pending</code> fino a 5 giorni, poi vengono scaricati in automatico nei run successivi.
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" disabled={savingAuto} onClick={handleSaveAutoSettings}>
                <Save className="h-4 w-4 mr-2" />
                Salva impostazioni
              </Button>
            </div>
          </div>

          <div className="rounded-md border p-3 space-y-3">
            <div className="text-sm font-medium">Impostazioni portale (utenza di lavoro)</div>
            <div className="grid gap-3 md:grid-cols-4">
              <div className="space-y-1 md:col-span-1">
                <Label>Modalita'</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={workingMode}
                  onChange={(e) => setWorkingMode(e.target.value as any)}
                >
                  <option value="auto">Auto</option>
                  <option value="me_stesso">Me stesso</option>
                  <option value="incaricato">Incaricato</option>
                </select>
              </div>
              <div className="space-y-1 md:col-span-2">
                <Label>Incaricante (opzionale)</Label>
                <Input
                  value={incaricante}
                  onChange={(e) => setIncaricante(e.target.value)}
                  placeholder="Testo/CF come appare nel menu a tendina"
                />
              </div>
              <div className="space-y-1 md:col-span-1">
                <Label>Tipo corrispettivo</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={corrTipo}
                  onChange={(e) => setCorrTipo(e.target.value)}
                >
                  <option value="RT">RT (Registratori telematici)</option>
                  <option value="MC">MC</option>
                  <option value="DA">DA</option>
                  <option value="DC">DC</option>
                  <option value="RC">RC</option>
                </select>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-4">
              <div className="space-y-1 md:col-span-4">
                <Label>Login URL (opzionale)</Label>
                <Input
                  value={loginUrl}
                  onChange={(e) => setLoginUrl(e.target.value)}
                  placeholder="Lascia vuoto per usare il default"
                />
                <div className="text-xs text-muted-foreground">
                  Se AdE cambia URL o fa redirect strani, qui puoi forzare l&apos;URL di partenza.
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" disabled={portalSaving} onClick={handleSavePortalSettings}>
                <Save className="h-4 w-4 mr-2" />
                Salva impostazioni portale
              </Button>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <Label>Codice Fiscale</Label>
              <Input value={cf} onChange={(e) => setCf(e.target.value)} placeholder="RSSMRA80A01H501U" />
            </div>
            <div className="space-y-1">
              <Label>Password</Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="********"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <div className="space-y-1">
              <Label>PIN</Label>
              <div className="relative">
                <Input
                  type={showPin ? "text" : "password"}
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  placeholder="********"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPin(!showPin)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPin ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Button disabled={saving} onClick={handleSave}>
              <Save className="h-4 w-4 mr-2" />
              Salva
            </Button>
            <Button variant="outline" onClick={() => setShowSync(true)}>
              <Play className="h-4 w-4 mr-2" />
              Sincronizza
            </Button>
          </div>

          <Separator />

          <div className="text-sm text-muted-foreground">
            Se il portale cambia (CAPTCHA, bottoni export diversi), abilita <code>debug</code> nella sync per salvare screenshot e HTML in <code>uploads/ade_debug</code>.
          </div>
        </CardContent>
      </Card>

      <Dialog open={showSync} onOpenChange={setShowSync}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Sincronizzazione AdE</DialogTitle>
            <DialogDescription>Operazione lunga: il backend apre un browser headless e scarica i file dal portale.</DialogDescription>
          </DialogHeader>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label>Data da</Label>
              <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label>Data a</Label>
              <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Checkbox checked={doIssued} onCheckedChange={(v) => setDoIssued(Boolean(v))} />
              <span className="text-sm">Fatture emesse</span>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox checked={doReceived} onCheckedChange={(v) => setDoReceived(Boolean(v))} />
              <span className="text-sm">Fatture ricevute</span>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox checked={doReceipts} onCheckedChange={(v) => setDoReceipts(Boolean(v))} />
              <span className="text-sm">Corrispettivi</span>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <Checkbox checked={debug} onCheckedChange={(v) => setDebug(Boolean(v))} />
              <span className="text-sm flex items-center gap-1">
                <Bug className="h-4 w-4" /> Debug (salva screenshot/HTML)
              </span>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSync(false)} disabled={syncing}>Annulla</Button>
            <Button onClick={handleSync} disabled={syncing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? "animate-spin" : ""}`} />
              Avvia
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
