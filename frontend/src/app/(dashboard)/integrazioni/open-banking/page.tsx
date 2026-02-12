"use client";

import { useEffect, useState, useCallback } from "react";
import { Landmark, RefreshCw, Unlink, Plus, Clock, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import {
  listConnections,
  syncConnection,
  deleteConnection,
  renewConsent,
  getConnectionLogs,
  searchInstitutions,
  connectBank,
} from "@/lib/api/integrations";
import type { OpenBankingConnection, OpenBankingSyncLog, InstitutionInfo } from "@/types/integration";
import { OB_CONNECTION_STATUS_LABELS, OB_CONNECTION_STATUS_COLORS, SYNC_FREQUENCY_LABELS, SYNC_LOG_STATUS_LABELS, SYNC_LOG_STATUS_COLORS } from "@/types/integration";
import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";

function formatDate(d: string | null): string {
  if (!d) return "\u2014";
  return new Date(d).toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function isConsentExpiring(conn: OpenBankingConnection): boolean {
  if (!conn.consenso_scadenza) return false;
  const diff = new Date(conn.consenso_scadenza).getTime() - Date.now();
  return diff > 0 && diff < 14 * 24 * 60 * 60 * 1000;
}

export default function OpenBankingPage() {
  const [connections, setConnections] = useState<OpenBankingConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<string | null>(null);

  // Wizard
  const [showWizard, setShowWizard] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);
  const [institutions, setInstitutions] = useState<InstitutionInfo[]>([]);
  const [instSearch, setInstSearch] = useState("");
  const [selectedInst, setSelectedInst] = useState<InstitutionInfo | null>(null);

  // Logs sheet
  const [logsConnection, setLogsConnection] = useState<string | null>(null);
  const [logs, setLogs] = useState<OpenBankingSyncLog[]>([]);

  const loadConnections = useCallback(async () => {
    try {
      const data = await listConnections();
      setConnections(data.items);
    } catch {
      toast.error("Errore nel caricamento delle connessioni");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadConnections(); }, [loadConnections]);

  const handleSync = async (id: string) => {
    setSyncing(id);
    try {
      await syncConnection(id);
      toast.success("Sincronizzazione completata");
      loadConnections();
    } catch {
      toast.error("Errore nella sincronizzazione");
    } finally {
      setSyncing(null);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteConnection(id);
      toast.success("Connessione revocata");
      loadConnections();
    } catch {
      toast.error("Errore nella revoca");
    }
  };

  const handleRenew = async (id: string) => {
    try {
      const result = await renewConsent(id);
      if (result.authorization_url) {
        window.open(result.authorization_url, "_blank");
      }
      toast.success("Rinnovo consenso avviato");
    } catch {
      toast.error("Errore nel rinnovo");
    }
  };

  const openLogs = async (connectionId: string) => {
    setLogsConnection(connectionId);
    try {
      const data = await getConnectionLogs(connectionId);
      setLogs(data.items);
    } catch {
      toast.error("Errore nel caricamento dei log");
    }
  };

  const openWizard = async () => {
    setShowWizard(true);
    setWizardStep(0);
    setSelectedInst(null);
    try {
      const data = await searchInstitutions();
      setInstitutions(data);
    } catch {
      toast.error("Errore nel caricamento delle banche");
    }
  };

  const handleConnect = async () => {
    if (!selectedInst) return;
    try {
      const result = await connectBank(selectedInst.id, window.location.origin + "/integrazioni/open-banking");
      if (result.authorization_url) {
        window.open(result.authorization_url, "_blank");
      }
      setShowWizard(false);
      toast.success("Connessione avviata. Completa l'autorizzazione nella finestra aperta.");
      setTimeout(loadConnections, 2000);
    } catch {
      toast.error("Errore nell'avvio della connessione");
    }
  };

  const filteredInstitutions = institutions.filter((i) =>
    i.name.toLowerCase().includes(instSearch.toLowerCase())
  );

  const expiringConnections = connections.filter(isConsentExpiring);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Open Banking" description="Gestisci connessioni bancarie PSD2" />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Open Banking"
        description="Gestisci connessioni bancarie PSD2"
        actions={
          <Button onClick={openWizard}>
            <Plus className="h-4 w-4 mr-2" />
            Connetti Banca
          </Button>
        }
      />

      {/* Consent expiry banner */}
      {expiringConnections.length > 0 && (
        <Alert variant="destructive" className="border-amber-500 bg-amber-50 text-amber-800">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {expiringConnections.length} connessione/i con consenso in scadenza nei prossimi 14 giorni.
            Rinnova il consenso per evitare interruzioni.
          </AlertDescription>
        </Alert>
      )}

      {/* Connection cards */}
      {connections.length === 0 ? (
        <EmptyState
          icon={Landmark}
          title="Nessuna connessione"
          description="Connetti la tua prima banca tramite Open Banking"
          actionLabel="Connetti Banca"
          onAction={openWizard}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {connections.map((conn) => (
            <Card key={conn.id}>
              <CardHeader className="flex flex-row items-center gap-3 pb-2">
                {conn.institution_logo_url ? (
                  <img src={conn.institution_logo_url} alt="" className="h-8 w-8 rounded" />
                ) : (
                  <Landmark className="h-8 w-8 text-muted-foreground" />
                )}
                <div className="flex-1">
                  <CardTitle className="text-base">{conn.institution_nome || "Banca"}</CardTitle>
                  <p className="text-xs text-muted-foreground">
                    {SYNC_FREQUENCY_LABELS[conn.frequenza_sync]}
                  </p>
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
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={syncing === conn.id}
                    onClick={() => handleSync(conn.id)}
                  >
                    <RefreshCw className={`h-3 w-3 mr-1 ${syncing === conn.id ? "animate-spin" : ""}`} />
                    Sync
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => openLogs(conn.id)}>
                    <Clock className="h-3 w-3 mr-1" /> Log
                  </Button>
                  {isConsentExpiring(conn) && (
                    <Button size="sm" variant="outline" className="text-amber-700" onClick={() => handleRenew(conn.id)}>
                      Rinnova Consenso
                    </Button>
                  )}
                  <Button size="sm" variant="ghost" className="text-destructive" onClick={() => handleDelete(conn.id)}>
                    <Unlink className="h-3 w-3 mr-1" /> Revoca
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Wizard Dialog */}
      <Dialog open={showWizard} onOpenChange={setShowWizard}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Connetti una Banca</DialogTitle>
            <DialogDescription>
              {wizardStep === 0 ? "Seleziona la tua banca" : "Conferma la connessione"}
            </DialogDescription>
          </DialogHeader>

          {wizardStep === 0 && (
            <div className="space-y-3">
              <Input
                placeholder="Cerca banca..."
                value={instSearch}
                onChange={(e) => setInstSearch(e.target.value)}
              />
              <ScrollArea className="h-[300px]">
                <div className="grid grid-cols-2 gap-2">
                  {filteredInstitutions.map((inst) => (
                    <Button
                      key={inst.id}
                      variant={selectedInst?.id === inst.id ? "default" : "outline"}
                      className="justify-start h-auto py-2 px-3"
                      onClick={() => setSelectedInst(inst)}
                    >
                      <span className="text-sm truncate">{inst.name}</span>
                    </Button>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}

          {wizardStep === 1 && selectedInst && (
            <div className="space-y-3">
              <p className="text-sm">Stai per connetterti a <strong>{selectedInst.name}</strong>.</p>
              <p className="text-sm text-muted-foreground">
                Verrai reindirizzato alla banca per autorizzare l&apos;accesso ai movimenti del conto.
                Il consenso ha validit&agrave; di 90 giorni.
              </p>
            </div>
          )}

          <DialogFooter>
            {wizardStep === 0 ? (
              <Button disabled={!selectedInst} onClick={() => setWizardStep(1)}>
                Avanti
              </Button>
            ) : (
              <>
                <Button variant="outline" onClick={() => setWizardStep(0)}>Indietro</Button>
                <Button onClick={handleConnect}>Autorizza</Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sync Logs Sheet */}
      <Sheet open={!!logsConnection} onOpenChange={() => setLogsConnection(null)}>
        <SheetContent className="w-[500px]">
          <SheetHeader>
            <SheetTitle>Log Sincronizzazione</SheetTitle>
            <SheetDescription>Storico delle sincronizzazioni</SheetDescription>
          </SheetHeader>
          <div className="mt-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead>Nuovi</TableHead>
                  <TableHead>Dup</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="text-xs">{formatDate(log.data_sync)}</TableCell>
                    <TableCell>
                      <Badge className={SYNC_LOG_STATUS_COLORS[log.stato]}>
                        {SYNC_LOG_STATUS_LABELS[log.stato]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{log.movimenti_nuovi}</TableCell>
                    <TableCell className="text-sm">{log.movimenti_duplicati}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
