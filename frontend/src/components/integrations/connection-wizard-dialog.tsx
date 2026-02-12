"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { searchInstitutions, connectBank } from "@/lib/api/integrations";
import type { InstitutionInfo } from "@/types/integration";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { BankInstitutionPicker } from "./bank-institution-picker";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function ConnectionWizardDialog({ open, onOpenChange, onSuccess }: Props) {
  const [step, setStep] = useState(0);
  const [institutions, setInstitutions] = useState<InstitutionInfo[]>([]);
  const [selected, setSelected] = useState<InstitutionInfo | null>(null);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    if (open) {
      setStep(0);
      setSelected(null);
      searchInstitutions().then(setInstitutions).catch(() => toast.error("Errore caricamento banche"));
    }
  }, [open]);

  const handleConnect = async () => {
    if (!selected) return;
    setConnecting(true);
    try {
      const result = await connectBank(selected.id, window.location.origin + "/integrazioni/open-banking");
      if (result.authorization_url) {
        window.open(result.authorization_url, "_blank");
      }
      onOpenChange(false);
      toast.success("Connessione avviata. Completa l'autorizzazione nella finestra aperta.");
      setTimeout(onSuccess, 2000);
    } catch {
      toast.error("Errore nell'avvio della connessione");
    } finally {
      setConnecting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Connetti una Banca</DialogTitle>
          <DialogDescription>
            {step === 0 ? "Seleziona la tua banca" : "Conferma la connessione"}
          </DialogDescription>
        </DialogHeader>

        {step === 0 && (
          <BankInstitutionPicker institutions={institutions} selected={selected} onSelect={setSelected} />
        )}

        {step === 1 && selected && (
          <div className="space-y-3">
            <p className="text-sm">Stai per connetterti a <strong>{selected.name}</strong>.</p>
            <p className="text-sm text-muted-foreground">
              Verrai reindirizzato alla banca per autorizzare l'accesso ai movimenti. Il consenso ha validità di 90 giorni.
            </p>
          </div>
        )}

        <DialogFooter>
          {step === 0 ? (
            <Button disabled={!selected} onClick={() => setStep(1)}>Avanti</Button>
          ) : (
            <>
              <Button variant="outline" onClick={() => setStep(0)}>Indietro</Button>
              <Button disabled={connecting} onClick={handleConnect}>
                {connecting ? "Connessione..." : "Autorizza"}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
