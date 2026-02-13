"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, RefreshCw, Bug } from "lucide-react";
import { toast } from "sonner";
import { uploadBatch, adeSyncInvoices } from "@/lib/api/integrations";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function yearStartISO(): string {
  const y = new Date().getFullYear();
  return `${y}-01-01`;
}

export default function ImportFatturePage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // AdE dialog
  const [showAdeImport, setShowAdeImport] = useState(false);
  const [adeFrom, setAdeFrom] = useState(yearStartISO());
  const [adeTo, setAdeTo] = useState(todayISO());
  const [adeIssued, setAdeIssued] = useState(true);
  const [adeReceived, setAdeReceived] = useState(true);
  const [adeDebug, setAdeDebug] = useState(false);
  const [adeImporting, setAdeImporting] = useState(false);

  const handleFiles = useCallback(async (files: File[]) => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      const result = await uploadBatch(files);
      toast.success(`${result.fatture_importate} fatture importate con successo`);
    } catch {
      toast.error("Errore nel caricamento dei file");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) handleFiles(Array.from(files));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    if (files) handleFiles(Array.from(files));
  };

  const handleAdeImport = async () => {
    if (!adeFrom || !adeTo) {
      toast.error("Seleziona il range date");
      return;
    }
    if (!(adeIssued || adeReceived)) {
      toast.error("Seleziona almeno Emesse o Ricevute");
      return;
    }
    setAdeImporting(true);
    try {
      if (adeIssued) {
        const r = await adeSyncInvoices({ date_from: adeFrom, date_to: adeTo, direction: "issued", debug: adeDebug });
        toast.success(r.message || `Emesse: +${r.imported_new}, dup ${r.updated}, err ${r.failed}`);
      }
      if (adeReceived) {
        const r = await adeSyncInvoices({ date_from: adeFrom, date_to: adeTo, direction: "received", debug: adeDebug });
        toast.success(r.message || `Ricevute: +${r.imported_new}, dup ${r.updated}, err ${r.failed}`);
      }
      setShowAdeImport(false);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      toast.error(axiosErr?.response?.data?.detail || "Errore import da AdE");
    } finally {
      setAdeImporting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto py-6">
      <h1 className="text-xl font-semibold">Carica fatture</h1>

      <div className="rounded-lg bg-blue-50 p-3 text-sm text-blue-700">
        Puoi caricare fatture ricevute o emesse.
      </div>

      {/* Drop zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer ${
          dragOver ? "border-primary bg-primary/5" : "border-gray-200 hover:border-primary/50"
        }`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="h-10 w-10 text-primary mx-auto mb-3" />
        <p className="font-medium">{uploading ? "Caricamento in corso..." : "Trascina qui i file XML/P7M"}</p>
        <p className="text-sm text-muted-foreground mt-1">Fino a 100 file, massimo 5 MB per ciascuno</p>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          multiple
          accept=".xml,.p7m,.zip"
          onChange={handleInputChange}
        />
      </div>

      {/* Divider */}
      <div className="relative my-8">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="bg-white px-4 text-muted-foreground">oppure</span>
        </div>
      </div>

      {/* AdE import button */}
      <div className="flex justify-center">
        <Button
          variant="outline"
          className="w-full max-w-md"
          onClick={() => setShowAdeImport(true)}
          disabled={adeImporting}
        >
          Importa da Agenzia delle Entrate
        </Button>
      </div>

      {/* AdE import dialog */}
      <Dialog open={showAdeImport} onOpenChange={setShowAdeImport}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Importa da Agenzia delle Entrate</DialogTitle>
            <DialogDescription>
              Il backend apre un browser headless e scarica i file dal portale.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label>Data da</Label>
              <Input type="date" value={adeFrom} onChange={(e) => setAdeFrom(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label>Data a</Label>
              <Input type="date" value={adeTo} onChange={(e) => setAdeTo(e.target.value)} />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Checkbox checked={adeIssued} onCheckedChange={(v) => setAdeIssued(Boolean(v))} />
              <span className="text-sm">Fatture emesse</span>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox checked={adeReceived} onCheckedChange={(v) => setAdeReceived(Boolean(v))} />
              <span className="text-sm">Fatture ricevute</span>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <Checkbox checked={adeDebug} onCheckedChange={(v) => setAdeDebug(Boolean(v))} />
              <span className="text-sm flex items-center gap-1 text-muted-foreground">
                <Bug className="h-4 w-4" /> Debug (salva screenshot/HTML)
              </span>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAdeImport(false)} disabled={adeImporting}>
              Annulla
            </Button>
            <Button onClick={handleAdeImport} disabled={adeImporting}>
              <RefreshCw className={`h-4 w-4 mr-2 ${adeImporting ? "animate-spin" : ""}`} />
              Avvia importazione
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
