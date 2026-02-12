"use client";

import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export interface F24LineData {
  codice_tributo: string;
  rateazione: string;
  anno_riferimento: number;
  mese_riferimento: number | null;
  importo_debito: number;
  importo_credito: number;
}

// Extended data for INPS display: codice_sede = rateazione, causale = codice_tributo,
// periodo_da = anno_riferimento, periodo_a = mese_riferimento (repurposed)

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
    anno_riferimento: 0,
    mese_riferimento: null,
    importo_debito: 0,
    importo_credito: 0,
  };
}

interface F24SectionINPSProps {
  lines: F24LineData[];
  onChange: (lines: F24LineData[]) => void;
}

export function F24SectionINPS({ lines, onChange }: F24SectionINPSProps) {
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
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Codice Sede</TableHead>
              <TableHead>Causale</TableHead>
              <TableHead>Periodo Da</TableHead>
              <TableHead>Periodo A</TableHead>
              <TableHead className="text-right">Importo a Debito</TableHead>
              <TableHead className="text-right">Importo a Credito</TableHead>
              <TableHead className="w-[50px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {lines.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-sm text-muted-foreground py-6">
                  Nessuna riga. Clicca "Aggiungi riga" per iniziare.
                </TableCell>
              </TableRow>
            ) : (
              lines.map((line, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Input
                      value={line.rateazione}
                      onChange={(e) => updateRow(index, "rateazione", e.target.value)}
                      placeholder="0001"
                      className="h-8 w-20 font-mono"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      value={line.codice_tributo}
                      onChange={(e) => updateRow(index, "codice_tributo", e.target.value)}
                      placeholder="CXX"
                      className="h-8 w-20 font-mono"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="text"
                      value={line.anno_riferimento || ""}
                      onChange={(e) =>
                        updateRow(index, "anno_riferimento", parseInt(e.target.value) || 0)
                      }
                      placeholder="MM/AAAA"
                      className="h-8 w-24 font-mono"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="text"
                      value={line.mese_riferimento ?? ""}
                      onChange={(e) =>
                        updateRow(
                          index,
                          "mese_riferimento",
                          e.target.value ? parseInt(e.target.value) : null
                        )
                      }
                      placeholder="MM/AAAA"
                      className="h-8 w-24 font-mono"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="0.01"
                      value={line.importo_debito || ""}
                      onChange={(e) =>
                        updateRow(index, "importo_debito", parseFloat(e.target.value) || 0)
                      }
                      placeholder="0,00"
                      className="h-8 w-28 text-right"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="0.01"
                      value={line.importo_credito || ""}
                      onChange={(e) =>
                        updateRow(index, "importo_credito", parseFloat(e.target.value) || 0)
                      }
                      placeholder="0,00"
                      className="h-8 w-28 text-right"
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => removeRow(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
          {lines.length > 0 && (
            <TableFooter>
              <TableRow>
                <TableCell colSpan={4} className="font-semibold">
                  Subtotali INPS
                </TableCell>
                <TableCell className="text-right font-bold">
                  {formatCurrency(totalDebito)}
                </TableCell>
                <TableCell className="text-right font-bold">
                  {formatCurrency(totalCredito)}
                </TableCell>
                <TableCell />
              </TableRow>
            </TableFooter>
          )}
        </Table>
      </div>

      <Button variant="outline" size="sm" onClick={addRow}>
        <Plus className="mr-2 h-4 w-4" />
        Aggiungi riga
      </Button>
    </div>
  );
}
