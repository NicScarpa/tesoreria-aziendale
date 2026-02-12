"use client";

import { useState, useCallback } from "react";
import { Upload, FileText } from "lucide-react";
import { toast } from "sonner";
import { uploadInvoice } from "@/lib/api/integrations";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function InvoiceUploadDialog({ open, onOpenChange, onSuccess }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f && (f.name.endsWith(".xml") || f.name.endsWith(".p7m"))) {
      setFile(f);
    } else {
      toast.error("Seleziona un file .xml o .xml.p7m");
    }
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await uploadInvoice(file);
      toast.success("Fattura importata");
      onOpenChange(false);
      onSuccess();
    } catch {
      toast.error("Errore nell'importazione");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) setFile(null); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Carica Fattura XML</DialogTitle>
        </DialogHeader>

        <div
          className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
            dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25"
          }`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          {file ? (
            <>
              <FileText className="h-8 w-8 text-primary mb-2" />
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
              <Button size="sm" variant="ghost" className="mt-2" onClick={() => setFile(null)}>
                Rimuovi
              </Button>
            </>
          ) : (
            <>
              <Upload className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground">Trascina un file .xml o .xml.p7m</p>
              <label className="mt-2">
                <Button size="sm" variant="outline" asChild>
                  <span>Sfoglia</span>
                </Button>
                <input type="file" accept=".xml,.p7m" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) setFile(f); }} />
              </label>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
          <Button disabled={!file || uploading} onClick={handleUpload}>
            {uploading ? "Caricamento..." : "Importa"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
