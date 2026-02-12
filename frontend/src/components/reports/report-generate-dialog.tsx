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
import { Label } from "@/components/ui/label";
import { FormatSelector } from "./format-selector";
import { ReportParamsForm } from "./report-params-form";
import { generateReport, generateQuickReport } from "@/lib/api/reports";
import type { ReportDefinition, ReportExecution, ReportFormat } from "@/types/report";

interface ReportGenerateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  definition?: ReportDefinition | null;
  // For quick generation without definition
  reportType?: string;
  defaultParams?: Record<string, unknown>;
  onGenerated?: (execution: ReportExecution) => void;
}

export function ReportGenerateDialog({
  open,
  onOpenChange,
  definition,
  reportType,
  defaultParams,
  onGenerated,
}: ReportGenerateDialogProps) {
  const [formato, setFormato] = useState<ReportFormat>(
    definition?.formato_default || "pdf"
  );
  const [parametri, setParametri] = useState<Record<string, unknown>>(
    defaultParams || definition?.parametri_default || {}
  );
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      let execution: ReportExecution;
      if (definition) {
        execution = await generateReport(definition.id, { formato, parametri });
      } else {
        execution = await generateQuickReport({
          tipo: reportType || "personalizzato",
          formato,
          parametri,
        });
      }

      if (execution.stato === "completato") {
        toast.success("Report generato con successo");
      } else if (execution.stato === "errore") {
        toast.error(`Errore: ${execution.errore || "errore sconosciuto"}`);
      } else {
        toast.info("Report in generazione...");
      }

      onGenerated?.(execution);
      onOpenChange(false);
    } catch {
      toast.error("Errore nella generazione del report");
    } finally {
      setLoading(false);
    }
  };

  const tipo = definition?.tipo || reportType || "personalizzato";
  const title = definition?.nome || `Genera Report`;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            {definition?.descrizione || "Configura i parametri e il formato di esportazione"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Formato</Label>
            <FormatSelector value={formato} onChange={setFormato} disabled={loading} />
          </div>

          <ReportParamsForm tipo={tipo} parametri={parametri} onChange={setParametri} />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Annulla
          </Button>
          <Button onClick={handleGenerate} disabled={loading}>
            {loading ? "Generazione..." : "Genera Report"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
