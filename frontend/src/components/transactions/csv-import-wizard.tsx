"use client";

import { useState, useCallback } from "react";
import { Upload, FileText, CheckCircle, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
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
} from "@/components/ui/dialog";
import { BankAccountSelector } from "@/components/shared/bank-account-selector";
import type { ImportBatch } from "@/types/transaction";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImported: () => void;
}

export function CSVImportWizard({ open, onOpenChange, onImported }: Props) {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [bankAccountId, setBankAccountId] = useState<string | null>(null);
  const [preview, setPreview] = useState<string[][]>([]);
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState({
    date_column: "",
    amount_column: "",
    description_column: "",
    date_format: "%d/%m/%Y",
    decimal_separator: ",",
    csv_separator: ";",
  });
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportBatch | null>(null);

  const parsePreview = useCallback((content: string, separator: string) => {
    const lines = content.split("\n").filter((l) => l.trim());
    const parsed = lines.slice(0, 11).map((line) => line.split(separator));
    if (parsed.length > 0) {
      setHeaders(parsed[0]);
      setPreview(parsed.slice(1, 11));
      // Auto-detect column mapping
      const h = parsed[0].map((h) => h.toLowerCase().trim());
      const dateIdx = h.findIndex((c) => c.includes("data") || c.includes("date"));
      const amountIdx = h.findIndex((c) => c.includes("importo") || c.includes("amount"));
      const descIdx = h.findIndex((c) => c.includes("descri") || c.includes("causale"));
      if (dateIdx >= 0) setMapping((m) => ({ ...m, date_column: parsed[0][dateIdx] }));
      if (amountIdx >= 0) setMapping((m) => ({ ...m, amount_column: parsed[0][amountIdx] }));
      if (descIdx >= 0) setMapping((m) => ({ ...m, description_column: parsed[0][descIdx] }));
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      parsePreview(text, mapping.csv_separator);
    };
    reader.readAsText(f);
  };

  const handleImport = async () => {
    if (!file || !bankAccountId) return;
    setImporting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("bank_account_id", bankAccountId);
      formData.append("date_column", mapping.date_column);
      formData.append("amount_column", mapping.amount_column);
      if (mapping.description_column) formData.append("description_column", mapping.description_column);
      formData.append("date_format", mapping.date_format);
      formData.append("decimal_separator", mapping.decimal_separator);
      formData.append("csv_separator", mapping.csv_separator);

      const resp = await api.post("/transactions/import", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(resp.data);
      setStep(4);
      onImported();
    } catch {
      toast.error("Errore durante l'importazione");
    } finally {
      setImporting(false);
    }
  };

  const reset = () => {
    setStep(1);
    setFile(null);
    setBankAccountId(null);
    setPreview([]);
    setHeaders([]);
    setMapping({
      date_column: "",
      amount_column: "",
      description_column: "",
      date_format: "%d/%m/%Y",
      decimal_separator: ",",
      csv_separator: ";",
    });
    setResult(null);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) reset();
        onOpenChange(v);
      }}
    >
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Importa movimenti CSV</DialogTitle>
        </DialogHeader>

        {/* Step indicators */}
        <div className="flex items-center gap-2 mb-4">
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              className={`h-2 flex-1 rounded-full ${
                s <= step ? "bg-primary" : "bg-muted"
              }`}
            />
          ))}
        </div>

        {/* Step 1: Upload */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Conto di destinazione</label>
              <BankAccountSelector
                value={bankAccountId}
                onChange={setBankAccountId}
                className="w-full mt-1"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Separatore CSV</label>
              <Select
                value={mapping.csv_separator}
                onValueChange={(v) => {
                  setMapping({ ...mapping, csv_separator: v });
                  if (file) {
                    const reader = new FileReader();
                    reader.onload = (ev) => parsePreview(ev.target?.result as string, v);
                    reader.readAsText(file);
                  }
                }}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value=";">Punto e virgola (;)</SelectItem>
                  <SelectItem value=",">Virgola (,)</SelectItem>
                  <SelectItem value="	">Tab</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="border-2 border-dashed rounded-lg p-8 text-center">
              <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground mb-2">
                Trascina un file CSV o clicca per selezionarlo
              </p>
              <Input
                type="file"
                accept=".csv,.txt"
                onChange={handleFileChange}
                className="max-w-xs mx-auto"
              />
              {file && (
                <p className="mt-2 text-sm flex items-center justify-center gap-1">
                  <FileText className="h-4 w-4" />
                  {file.name}
                </p>
              )}
            </div>

            <Button
              className="w-full"
              disabled={!file || !bankAccountId}
              onClick={() => setStep(2)}
            >
              Avanti
            </Button>
          </div>
        )}

        {/* Step 2: Mapping */}
        {step === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Mappa le colonne del file CSV ai campi del sistema.
            </p>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Colonna data *</label>
                <Select value={mapping.date_column} onValueChange={(v) => setMapping({ ...mapping, date_column: v })}>
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Seleziona..." />
                  </SelectTrigger>
                  <SelectContent>
                    {headers.map((h) => (
                      <SelectItem key={h} value={h}>{h}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Colonna importo *</label>
                <Select value={mapping.amount_column} onValueChange={(v) => setMapping({ ...mapping, amount_column: v })}>
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Seleziona..." />
                  </SelectTrigger>
                  <SelectContent>
                    {headers.map((h) => (
                      <SelectItem key={h} value={h}>{h}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Colonna descrizione</label>
                <Select
                  value={mapping.description_column || ""}
                  onValueChange={(v) => setMapping({ ...mapping, description_column: v })}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Opzionale" />
                  </SelectTrigger>
                  <SelectContent>
                    {headers.map((h) => (
                      <SelectItem key={h} value={h}>{h}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Formato data</label>
                <Select value={mapping.date_format} onValueChange={(v) => setMapping({ ...mapping, date_format: v })}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="%d/%m/%Y">GG/MM/AAAA</SelectItem>
                    <SelectItem value="%Y-%m-%d">AAAA-MM-GG</SelectItem>
                    <SelectItem value="%d-%m-%Y">GG-MM-AAAA</SelectItem>
                    <SelectItem value="%d.%m.%Y">GG.MM.AAAA</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Separatore decimali</label>
                <Select value={mapping.decimal_separator} onValueChange={(v) => setMapping({ ...mapping, decimal_separator: v })}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value=",">Virgola (1.234,56)</SelectItem>
                    <SelectItem value=".">Punto (1,234.56)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Preview table */}
            {preview.length > 0 && (
              <div className="border rounded overflow-x-auto max-h-48">
                <table className="text-xs w-full">
                  <thead>
                    <tr className="bg-muted">
                      {headers.map((h, i) => (
                        <th key={i} className="px-2 py-1 text-left">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.map((row, i) => (
                      <tr key={i} className="border-t">
                        {row.map((cell, j) => (
                          <td key={j} className="px-2 py-1 truncate max-w-[150px]">{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(1)}>Indietro</Button>
              <Button
                className="flex-1"
                disabled={!mapping.date_column || !mapping.amount_column}
                onClick={() => setStep(3)}
              >
                Avanti
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Confirm */}
        {step === 3 && (
          <div className="space-y-4">
            <div className="bg-muted/50 p-4 rounded-lg space-y-2 text-sm">
              <p><strong>File:</strong> {file?.name}</p>
              <p><strong>Righe:</strong> ~{preview.length}</p>
              <p><strong>Colonna data:</strong> {mapping.date_column}</p>
              <p><strong>Colonna importo:</strong> {mapping.amount_column}</p>
              {mapping.description_column && <p><strong>Colonna descrizione:</strong> {mapping.description_column}</p>}
              <p><strong>Formato data:</strong> {mapping.date_format}</p>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setStep(2)}>Indietro</Button>
              <Button className="flex-1" onClick={handleImport} disabled={importing}>
                {importing ? "Importazione in corso..." : "Importa"}
              </Button>
            </div>
          </div>
        )}

        {/* Step 4: Result */}
        {step === 4 && result && (
          <div className="space-y-4">
            <div className="text-center">
              {result.status === "completed" ? (
                <CheckCircle className="h-12 w-12 text-emerald-500 mx-auto" />
              ) : (
                <AlertCircle className="h-12 w-12 text-amber-500 mx-auto" />
              )}
              <h3 className="text-lg font-semibold mt-2">
                {result.status === "completed" ? "Importazione completata" : "Importazione parziale"}
              </h3>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-muted/50 p-3 rounded">
                <p className="text-muted-foreground">Totale righe</p>
                <p className="text-xl font-bold">{result.total_records}</p>
              </div>
              <div className="bg-emerald-50 p-3 rounded">
                <p className="text-muted-foreground">Importati</p>
                <p className="text-xl font-bold text-emerald-600">{result.imported_records}</p>
              </div>
              <div className="bg-amber-50 p-3 rounded">
                <p className="text-muted-foreground">Duplicati (skip)</p>
                <p className="text-xl font-bold text-amber-600">{result.skipped_records}</p>
              </div>
              <div className="bg-red-50 p-3 rounded">
                <p className="text-muted-foreground">Errori</p>
                <p className="text-xl font-bold text-red-600">{result.error_records}</p>
              </div>
            </div>

            {result.errors && result.errors.length > 0 && (
              <div className="border rounded p-3 max-h-32 overflow-y-auto">
                <p className="text-xs font-medium mb-1">Dettaglio errori:</p>
                {result.errors.map((err, i) => (
                  <p key={i} className="text-xs text-red-600">
                    Riga {err.row}: {err.error}
                  </p>
                ))}
              </div>
            )}

            <Button className="w-full" onClick={() => onOpenChange(false)}>
              Chiudi
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
