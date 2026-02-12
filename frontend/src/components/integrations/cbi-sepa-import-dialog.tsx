"use client";

import { useState, useRef } from "react";
import { Upload } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  accept: string;
  onImport: (file: File) => Promise<void>;
}

export function CBISEPAImportDialog({ open, onOpenChange, title, description, accept, onImport }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    try {
      await onImport(file);
      onOpenChange(false);
      setFile(null);
    } finally {
      setImporting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { onOpenChange(v); if (!v) setFile(null); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => inputRef.current?.click()}>
            <Upload className="h-4 w-4 mr-2" />
            {file ? file.name : "Seleziona File"}
          </Button>
          <input ref={inputRef} type="file" accept={accept} className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) setFile(f); }} />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
          <Button disabled={!file || importing} onClick={handleImport}>
            {importing ? "Elaborazione..." : "Importa"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
