"use client";

import { useState } from "react";
import { FileDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ReportGenerateDialog } from "@/components/reports/report-generate-dialog";
import type { ReportExecution } from "@/types/report";
import { downloadExecution, triggerDownload } from "@/lib/api/reports";
import { toast } from "sonner";

interface ExportButtonProps {
  reportType: string;
  defaultParams?: Record<string, unknown>;
  label?: string;
  variant?: "default" | "outline" | "ghost" | "secondary";
  size?: "default" | "sm" | "lg" | "icon";
}

export function ExportButton({
  reportType,
  defaultParams = {},
  label = "Esporta",
  variant = "outline",
  size = "sm",
}: ExportButtonProps) {
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleGenerated = async (execution: ReportExecution) => {
    if (execution.stato === "completato") {
      try {
        const blob = await downloadExecution(execution.id);
        const ext = execution.formato || "pdf";
        triggerDownload(blob, `${execution.nome}.${ext}`);
      } catch {
        toast.error("Errore nel download del file");
      }
    }
  };

  return (
    <>
      <Button variant={variant} size={size} onClick={() => setDialogOpen(true)}>
        <FileDown className="h-4 w-4 mr-2" />
        {label}
      </Button>
      <ReportGenerateDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        reportType={reportType}
        defaultParams={defaultParams}
        onGenerated={handleGenerated}
      />
    </>
  );
}
