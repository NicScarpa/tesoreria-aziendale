"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Loader2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { createPaymentOrder, addLine } from "@/lib/api/payments";
import { F24SectionErario, type F24LineData as ErarioLine } from "./F24SectionErario";
import { F24SectionINPS, type F24LineData as INPSLine } from "./F24SectionINPS";
import { F24_SECTION_LABELS, type F24SectionType } from "@/types/payment";
import type { BankAccount } from "@/types/bank-account";

// Re-export for generic section use
interface F24LineData {
  codice_tributo: string;
  rateazione: string;
  anno_riferimento: number;
  mese_riferimento: number | null;
  importo_debito: number;
  importo_credito: number;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

function emptyLine(): F24LineData {
  return {
    codice_tributo: "",
    rateazione: "",
    anno_riferimento: new Date().getFullYear(),
    mese_riferimento: null,
    importo_debito: 0,
    importo_credito: 0,
  };
}

// Generic section component for Regioni / IMU
function F24GenericSection({
  title,
  lines,
  onChange,
}: {
  title: string;
  lines: F24LineData[];
  onChange: (lines: F24LineData[]) => void;
}) {
  function addRow() {
    onChange([...lines, emptyLine()]);
  }

  function removeRow(index: number) {
    onChange(lines.filter((_, i) => i !== index));
  }

  function updateRow(index: number, field: keyof F24LineData, value: string | number | null) {
    const updated = lines.map((line, i) =>
      i === index ? { ...line, [field]: value } : line
    );
    onChange(updated);
  }

  const totalDebito = lines.reduce((sum, l) => sum + l.importo_debito, 0);
  const totalCredito = lines.reduce((sum, l) => sum + l.importo_credito, 0);

  return (
    <div className="space-y-3">
      {lines.length === 0 ? (
        <div className="rounded-md border p-6 text-center text-sm text-muted-foreground">
          Nessuna riga in {title}. Clicca "Aggiungi riga" per iniziare.
        </div>
      ) : (
        <div className="space-y-2">
          {lines.map((line, index) => (
            <div
              key={index}
              className="grid grid-cols-6 gap-2 items-end rounded-md border p-3"
            >
              <div className="space-y-1">
                <Label className="text-[10px]">Codice Tributo</Label>
                <Input
                  value={line.codice_tributo}
                  onChange={(e) => updateRow(index, "codice_tributo", e.target.value)}
                  placeholder="1001"
                  className="h-8 font-mono"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">Anno Rif.</Label>
                <Input
                  type="number"
                  value={line.anno_riferimento}
                  onChange={(e) =>
                    updateRow(index, "anno_riferimento", parseInt(e.target.value) || 0)
                  }
                  className="h-8"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">Debito</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={line.importo_debito || ""}
                  onChange={(e) =>
                    updateRow(index, "importo_debito", parseFloat(e.target.value) || 0)
                  }
                  placeholder="0,00"
                  className="h-8 text-right"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">Credito</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={line.importo_credito || ""}
                  onChange={(e) =>
                    updateRow(index, "importo_credito", parseFloat(e.target.value) || 0)
                  }
                  placeholder="0,00"
                  className="h-8 text-right"
                />
              </div>
              <div className="col-span-2 flex items-end justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive hover:text-destructive"
                  onClick={() => removeRow(index)}
                >
                  Rimuovi
                </Button>
              </div>
            </div>
          ))}
          <div className="flex justify-between items-center px-3 py-2 rounded-md bg-muted text-sm">
            <span className="font-semibold">Subtotali {title}</span>
            <div className="flex gap-6">
              <span>
                Debito: <strong>{formatCurrency(totalDebito)}</strong>
              </span>
              <span>
                Credito: <strong>{formatCurrency(totalCredito)}</strong>
              </span>
            </div>
          </div>
        </div>
      )}
      <Button variant="outline" size="sm" onClick={addRow}>
        Aggiungi riga
      </Button>
    </div>
  );
}

// --- Main F24Form ---

interface F24FormProps {
  onComplete: (orderId: string) => void;
  bankAccounts: BankAccount[];
}

export function F24Form({ onComplete, bankAccounts }: F24FormProps) {
  const [creating, setCreating] = useState(false);
  const [bankAccountId, setBankAccountId] = useState<string | null>(null);
  const [dataEsecuzione, setDataEsecuzione] = useState("");

  const [erarioLines, setErarioLines] = useState<F24LineData[]>([]);
  const [inpsLines, setInpsLines] = useState<F24LineData[]>([]);
  const [regioniLines, setRegioniLines] = useState<F24LineData[]>([]);
  const [imuLines, setImuLines] = useState<F24LineData[]>([]);

  const allLines = [
    ...erarioLines.map((l) => ({ ...l, sezione: "erario" as F24SectionType })),
    ...inpsLines.map((l) => ({ ...l, sezione: "inps" as F24SectionType })),
    ...regioniLines.map((l) => ({ ...l, sezione: "regioni" as F24SectionType })),
    ...imuLines.map((l) => ({ ...l, sezione: "imu_altri_enti" as F24SectionType })),
  ];

  const totalDebiti = allLines.reduce((sum, l) => sum + l.importo_debito, 0);
  const totalCrediti = allLines.reduce((sum, l) => sum + l.importo_credito, 0);
  const saldo = totalDebiti - totalCrediti;

  async function handleCreate() {
    if (allLines.length === 0) {
      toast.error("Inserisci almeno una riga F24");
      return;
    }
    if (!dataEsecuzione) {
      toast.error("Inserisci la data di esecuzione");
      return;
    }

    setCreating(true);
    try {
      const order = await createPaymentOrder({
        tipo: "f24",
        bank_account_id: bankAccountId,
        data_esecuzione_richiesta: dataEsecuzione,
        priorita: "normale",
        note: null,
      });

      for (const line of allLines) {
        const importo =
          line.importo_debito > line.importo_credito
            ? line.importo_debito - line.importo_credito
            : 0;

        await addLine(order.id, {
          beneficiario_nome: "Agenzia delle Entrate",
          importo: importo || line.importo_debito,
          valuta: "EUR",
          causale: `F24 - ${F24_SECTION_LABELS[line.sezione]} - ${line.codice_tributo}`,
          f24_sezione: line.sezione,
          f24_codice_tributo: line.codice_tributo,
          f24_rateazione: line.rateazione || null,
          f24_anno_riferimento: line.anno_riferimento,
          f24_mese_riferimento: line.mese_riferimento,
          f24_importo_debito: line.importo_debito,
          f24_importo_credito: line.importo_credito,
        });
      }

      toast.success("Modello F24 creato con successo");
      onComplete(order.id);
    } catch {
      toast.error("Errore nella creazione del modello F24");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Modello F24
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Conto bancario</Label>
              <Select
                value={bankAccountId ?? "none"}
                onValueChange={(v) =>
                  setBankAccountId(v === "none" ? null : v)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona conto" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Nessuno</SelectItem>
                  {bankAccounts.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.nickname || a.iban || a.id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Data esecuzione *</Label>
              <Input
                type="date"
                value={dataEsecuzione}
                onChange={(e) => setDataEsecuzione(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Sections */}
      <Card>
        <CardContent className="pt-6">
          <Tabs defaultValue="erario">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="erario">
                Erario
                {erarioLines.length > 0 && (
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({erarioLines.length})
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="inps">
                INPS
                {inpsLines.length > 0 && (
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({inpsLines.length})
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="regioni">
                Regioni
                {regioniLines.length > 0 && (
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({regioniLines.length})
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="imu">
                IMU / Altri
                {imuLines.length > 0 && (
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({imuLines.length})
                  </span>
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="erario" className="mt-4">
              <F24SectionErario lines={erarioLines} onChange={setErarioLines} />
            </TabsContent>

            <TabsContent value="inps" className="mt-4">
              <F24SectionINPS lines={inpsLines} onChange={setInpsLines} />
            </TabsContent>

            <TabsContent value="regioni" className="mt-4">
              <F24GenericSection
                title="Regioni"
                lines={regioniLines}
                onChange={setRegioniLines}
              />
            </TabsContent>

            <TabsContent value="imu" className="mt-4">
              <F24GenericSection
                title="IMU / Altri enti"
                lines={imuLines}
                onChange={setImuLines}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Totals */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-sm text-muted-foreground">Totale Debiti</p>
              <p className="text-xl font-bold text-red-600">
                {formatCurrency(totalDebiti)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Totale Crediti</p>
              <p className="text-xl font-bold text-green-600">
                {formatCurrency(totalCrediti)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Saldo</p>
              <p
                className={cn(
                  "text-xl font-bold",
                  saldo > 0 ? "text-red-600" : saldo < 0 ? "text-green-600" : "text-gray-600"
                )}
              >
                {formatCurrency(saldo)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex justify-end">
        <Button
          size="lg"
          onClick={handleCreate}
          disabled={creating || allLines.length === 0}
        >
          {creating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creazione in corso...
            </>
          ) : (
            "Crea modello F24"
          )}
        </Button>
      </div>
    </div>
  );
}
