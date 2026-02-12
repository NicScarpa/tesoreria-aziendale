"use client";

import { useState, useCallback } from "react";
import { Upload, FileText } from "lucide-react";
import { toast } from "sonner";
import { uploadBatch } from "@/lib/api/integrations";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function InvoiceBatchUploadDialog({ open, onOpenChange, onSuccess }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const newFiles = Array.from(e.dataTransfer.files).filter(
      (f) => f.name.endsWith(".xml") || f.name.endsWith(".p7m") || f.name.endsWith(".zip")
    );
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      const result = await uploadBatch(files);
      toast.success(`Batch completato: ${result.fatture_importate} importate`);
      onOpenChange(false);
      setFiles([]);
      onSuccess();
    } catch {
      toast.error("Errore nel batch import");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) setFiles([]); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Carica Multiple Fatture</DialogTitle>
        </DialogHeader>

        <div
          className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <Upload className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground mb-2">Trascina file .xml, .p7m o .zip</p>
          <label>
            <Button size="sm" variant="outline" asChild>
              <span>Sfoglia</span>
            </Button>
            <input type="file" accept=".xml,.p7m,.zip" multiple className="hidden" onChange={(e) => {
              if (e.target.files) setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
            }} />
          </label>
        </div>

        {files.length > 0 && (
          <div className="space-y-1 max-h-[200px] overflow-y-auto">
            {files.map((f, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="flex-1 truncate">{f.name}</span>
                <span className="text-xs text-muted-foreground">{(f.size / 1024).toFixed(1)} KB</span>
                <Button size="sm" variant="ghost" className="h-6 w-6 p-0" onClick={() => setFiles((prev) => prev.filter((_, idx) => idx !== i))}>
                  &times;
                </Button>
              </div>
            ))}
          </div>
        )}

        {uploading && <Progress value={50} className="h-2" />}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
          <Button disabled={files.length === 0 || uploading} onClick={handleUpload}>
            {uploading ? "Caricamento..." : `Importa ${files.length} file`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
