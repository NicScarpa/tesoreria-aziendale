"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FormatSelector } from "./format-selector";
import { createReportDefinition } from "@/lib/api/reports";
import type { ReportDefinition, ReportFormat, ReportType } from "@/types/report";
import { REPORT_TYPE_LABELS } from "@/types/report";

interface ReportCreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated?: (definition: ReportDefinition) => void;
}

export function ReportCreateDialog({ open, onOpenChange, onCreated }: ReportCreateDialogProps) {
  const [nome, setNome] = useState("");
  const [descrizione, setDescrizione] = useState("");
  const [tipo, setTipo] = useState<ReportType>("personalizzato");
  const [formato, setFormato] = useState<ReportFormat>("pdf");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!nome.trim()) {
      toast.error("Nome obbligatorio");
      return;
    }
    setLoading(true);
    try {
      const definition = await createReportDefinition({
        nome: nome.trim(),
        descrizione: descrizione.trim() || null,
        tipo,
        formato_default: formato,
      });
      toast.success("Report personalizzato creato");
      onCreated?.(definition);
      onOpenChange(false);
      setNome("");
      setDescrizione("");
    } catch {
      toast.error("Errore nella creazione del report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Nuovo Report Personalizzato</DialogTitle>
          <DialogDescription>
            Crea una definizione di report personalizzata riutilizzabile
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Nome *</Label>
            <Input
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="Es. Report settimanale vendite"
            />
          </div>

          <div className="space-y-2">
            <Label>Descrizione</Label>
            <Textarea
              value={descrizione}
              onChange={(e) => setDescrizione(e.target.value)}
              placeholder="Descrizione del report..."
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label>Tipo di report</Label>
            <Select value={tipo} onValueChange={(v) => setTipo(v as ReportType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(REPORT_TYPE_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Formato predefinito</Label>
            <FormatSelector value={formato} onChange={setFormato} />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Annulla
          </Button>
          <Button onClick={handleCreate} disabled={loading || !nome.trim()}>
            {loading ? "Creazione..." : "Crea Report"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
