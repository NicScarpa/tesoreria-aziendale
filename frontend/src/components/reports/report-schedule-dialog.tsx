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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FormatSelector } from "./format-selector";
import { createSchedule, updateSchedule } from "@/lib/api/reports";
import type {
  ReportDefinition,
  ReportFormat,
  ReportFrequency,
  ReportSchedule,
} from "@/types/report";
import { REPORT_FREQUENCY_LABELS } from "@/types/report";

interface ReportScheduleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  definitions: ReportDefinition[];
  schedule?: ReportSchedule | null;
  onSaved?: () => void;
}

export function ReportScheduleDialog({
  open,
  onOpenChange,
  definitions,
  schedule,
  onSaved,
}: ReportScheduleDialogProps) {
  const isEdit = !!schedule;
  const [nome, setNome] = useState(schedule?.nome || "");
  const [reportDefinitionId, setReportDefinitionId] = useState(
    schedule?.report_definition_id || ""
  );
  const [frequenza, setFrequenza] = useState<ReportFrequency>(schedule?.frequenza || "mensile");
  const [formato, setFormato] = useState<ReportFormat>(schedule?.formato || "pdf");
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!nome.trim()) {
      toast.error("Nome obbligatorio");
      return;
    }
    if (!isEdit && !reportDefinitionId) {
      toast.error("Seleziona un report");
      return;
    }
    setLoading(true);
    try {
      if (isEdit && schedule) {
        await updateSchedule(schedule.id, {
          nome: nome.trim(),
          frequenza,
          formato,
        });
        toast.success("Programmazione aggiornata");
      } else {
        await createSchedule({
          report_definition_id: reportDefinitionId,
          nome: nome.trim(),
          frequenza,
          formato,
        });
        toast.success("Programmazione creata");
      }
      onSaved?.();
      onOpenChange(false);
    } catch {
      toast.error("Errore nel salvataggio della programmazione");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifica Programmazione" : "Nuova Programmazione"}
          </DialogTitle>
          <DialogDescription>
            Pianifica la generazione automatica di un report
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {!isEdit && (
            <div className="space-y-2">
              <Label>Report *</Label>
              <Select value={reportDefinitionId} onValueChange={setReportDefinitionId}>
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona un report..." />
                </SelectTrigger>
                <SelectContent>
                  {definitions.map((d) => (
                    <SelectItem key={d.id} value={d.id}>
                      {d.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <Label>Nome *</Label>
            <Input
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="Es. Saldi settimanali"
            />
          </div>

          <div className="space-y-2">
            <Label>Frequenza</Label>
            <Select value={frequenza} onValueChange={(v) => setFrequenza(v as ReportFrequency)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(REPORT_FREQUENCY_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Formato</Label>
            <FormatSelector value={formato} onChange={setFormato} />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Annulla
          </Button>
          <Button onClick={handleSave} disabled={loading || !nome.trim()}>
            {loading ? "Salvataggio..." : isEdit ? "Salva" : "Crea"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
