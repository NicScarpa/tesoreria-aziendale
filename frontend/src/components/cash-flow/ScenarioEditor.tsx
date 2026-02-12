"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { createScenario, deleteScenario, updateScenario } from "@/lib/api/cash-flow";
import type { CashFlowScenario } from "@/types/cash-flow";
import { SCENARIO_TYPE_LABELS } from "@/types/cash-flow";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";

interface ScenarioEditorProps {
  forecastId: string;
  scenarios: CashFlowScenario[];
  onUpdate: () => void;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

export function ScenarioEditor({ forecastId, scenarios, onUpdate }: ScenarioEditorProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [nome, setNome] = useState("");
  const [tipoAggiustamento, setTipoAggiustamento] = useState("aggiunta");
  const [importoModificato, setImportoModificato] = useState("");
  const [tipoMovimento, setTipoMovimento] = useState("entrata");
  const [dataModificata, setDataModificata] = useState("");
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    if (!nome.trim()) return;
    setCreating(true);
    try {
      await createScenario(forecastId, {
        nome,
        tipo_aggiustamento: tipoAggiustamento,
        importo_modificato: importoModificato ? Number(importoModificato) : undefined,
        tipo_movimento: tipoMovimento,
        data_modificata: dataModificata || undefined,
      });
      toast.success("Scenario creato");
      setDialogOpen(false);
      setNome("");
      setImportoModificato("");
      setDataModificata("");
      onUpdate();
    } catch {
      toast.error("Errore nella creazione dello scenario");
    } finally {
      setCreating(false);
    }
  };

  const handleToggle = async (scenario: CashFlowScenario) => {
    try {
      await updateScenario(forecastId, scenario.id, { attivo: !scenario.attivo });
      onUpdate();
    } catch {
      toast.error("Errore nell'aggiornamento");
    }
  };

  const handleDelete = async (scenarioId: string) => {
    try {
      await deleteScenario(forecastId, scenarioId);
      toast.success("Scenario eliminato");
      onUpdate();
    } catch {
      toast.error("Errore nell'eliminazione");
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Scenari What-If</h3>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="outline" className="h-8">
              <Plus className="mr-1 h-3 w-3" />
              Nuovo
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nuovo Scenario</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div>
                <label className="text-sm font-medium">Nome</label>
                <Input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="es. Nuovo cliente" />
              </div>
              <div>
                <label className="text-sm font-medium">Tipo aggiustamento</label>
                <Select value={tipoAggiustamento} onValueChange={setTipoAggiustamento}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="aggiunta">Aggiunta</SelectItem>
                    <SelectItem value="rimozione">Rimozione</SelectItem>
                    <SelectItem value="modifica_importo">Modifica Importo</SelectItem>
                    <SelectItem value="spostamento_data">Spostamento Data</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Tipo movimento</label>
                <Select value={tipoMovimento} onValueChange={setTipoMovimento}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="entrata">Entrata</SelectItem>
                    <SelectItem value="uscita">Uscita</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Importo</label>
                <Input type="number" value={importoModificato} onChange={(e) => setImportoModificato(e.target.value)} placeholder="0.00" />
              </div>
              <div>
                <label className="text-sm font-medium">Data</label>
                <Input type="date" value={dataModificata} onChange={(e) => setDataModificata(e.target.value)} />
              </div>
              <Button onClick={handleCreate} disabled={creating || !nome.trim()} className="w-full">
                {creating ? "Creazione..." : "Crea Scenario"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {scenarios.length === 0 && (
        <p className="text-sm text-muted-foreground">Nessuno scenario configurato</p>
      )}

      {scenarios.map((sc) => (
        <div key={sc.id} className={cn("flex items-center gap-3 rounded-lg border p-3", !sc.attivo && "opacity-50")}>
          <Switch checked={sc.attivo} onCheckedChange={() => handleToggle(sc)} />
          <div className="flex-1">
            <p className="text-sm font-medium">{sc.nome}</p>
            <div className="flex gap-2 text-xs text-muted-foreground">
              <span className="rounded bg-muted px-1">{SCENARIO_TYPE_LABELS[sc.tipo_aggiustamento]}</span>
              {sc.importo_modificato && <span>{formatCurrency(sc.importo_modificato)}</span>}
              {sc.data_modificata && <span>{new Date(sc.data_modificata).toLocaleDateString("it-IT")}</span>}
            </div>
          </div>
          <Button variant="ghost" size="sm" className="h-7 px-2 text-destructive" onClick={() => handleDelete(sc.id)}>
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      ))}
    </div>
  );
}
