"use client";

import { useState, useRef } from "react";
import { FileSpreadsheet, Upload, CheckCircle, XCircle } from "lucide-react";
import { toast } from "sonner";
import { parseCBI, validateSEPA, importRendicontazione, importCAMT053 } from "@/lib/api/integrations";
import type { SEPAValidationResult, CBIParseResult, CAMT053ImportResult } from "@/types/integration";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type ImportType = "camt053" | "rendicontazione" | "pain002" | "validatore";

const IMPORT_CARDS: { type: ImportType; title: string; description: string; accept: string }[] = [
  { type: "camt053", title: "Estratto Conto (camt.053)", description: "Importa movimenti da file camt.053 SEPA", accept: ".xml" },
  { type: "rendicontazione", title: "Rendicontazione CBI", description: "Importa esiti da file rendicontazione CBI", accept: ".txt,.cbi" },
  { type: "pain002", title: "Esito SEPA (pain.002)", description: "Importa esiti pagamento da file pain.002", accept: ".xml" },
  { type: "validatore", title: "Validatore SEPA", description: "Valida un file SEPA XML", accept: ".xml" },
];

export default function CBISEPAPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeType, setActiveType] = useState<ImportType | null>(null);
  const [showDialog, setShowDialog] = useState(false);
  const [processing, setProcessing] = useState(false);

  // Results
  const [validationResult, setValidationResult] = useState<SEPAValidationResult | null>(null);
  const [cbiResult, setCbiResult] = useState<CBIParseResult | null>(null);
  const [camt053Result, setCamt053Result] = useState<CAMT053ImportResult | null>(null);
  const [genericResult, setGenericResult] = useState<string | null>(null);

  const handleCardClick = (type: ImportType) => {
    setActiveType(type);
    setValidationResult(null);
    setCbiResult(null);
    setCamt053Result(null);
    setGenericResult(null);
    setShowDialog(true);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !activeType) return;
    setProcessing(true);
    try {
      switch (activeType) {
        case "camt053": {
          const result = await importCAMT053(file);
          setCamt053Result(result);
          toast.success(`Importati ${result.transactions_imported} movimenti`);
          break;
        }
        case "rendicontazione": {
          const result = await parseCBI(file);
          setCbiResult(result);
          toast.success(`Parsificati ${result.records_parsed} record`);
          break;
        }
        case "pain002": {
          const result = await importRendicontazione(file);
          setGenericResult(`Importati ${result.records_imported} record`);
          toast.success("Import completato");
          break;
        }
        case "validatore": {
          const result = await validateSEPA(file);
          setValidationResult(result);
          break;
        }
      }
    } catch {
      toast.error("Errore nell'elaborazione del file");
    } finally {
      setProcessing(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const currentCard = IMPORT_CARDS.find((c) => c.type === activeType);

  return (
    <div className="space-y-6">
      <PageHeader title="CBI / SEPA" description="Importa e valida file nei formati bancari standard" />

      <div className="grid gap-4 md:grid-cols-2">
        {IMPORT_CARDS.map((card) => (
          <Card
            key={card.type}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => handleCardClick(card.type)}
          >
            <CardHeader className="flex flex-row items-center gap-3">
              <FileSpreadsheet className="h-8 w-8 text-primary" />
              <div>
                <CardTitle className="text-base">{card.title}</CardTitle>
                <CardDescription>{card.description}</CardDescription>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{currentCard?.title}</DialogTitle>
            <DialogDescription>{currentCard?.description}</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Button disabled={processing} onClick={() => fileInputRef.current?.click()}>
                <Upload className="h-4 w-4 mr-2" />
                {processing ? "Elaborazione..." : "Seleziona File"}
              </Button>
              <input ref={fileInputRef} type="file" accept={currentCard?.accept} className="hidden" onChange={handleFileSelect} />
            </div>

            {/* Validation Result */}
            {validationResult && (
              <Alert variant={validationResult.valid ? "default" : "destructive"}>
                {validationResult.valid ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                <AlertTitle>{validationResult.valid ? "File Valido" : "File Non Valido"}</AlertTitle>
                <AlertDescription>
                  {validationResult.file_type && <p>Tipo: {validationResult.file_type}</p>}
                  {validationResult.message_id && <p>Message ID: {validationResult.message_id}</p>}
                  {validationResult.errors.length > 0 && (
                    <ul className="mt-2 list-disc pl-4">
                      {validationResult.errors.map((err, i) => <li key={i} className="text-sm">{err}</li>)}
                    </ul>
                  )}
                </AlertDescription>
              </Alert>
            )}

            {/* CAMT053 Result */}
            {camt053Result && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Risultato Import</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Movimenti importati: <strong>{camt053Result.transactions_imported}</strong></div>
                  <div>Duplicati: <strong>{camt053Result.transactions_duplicated}</strong></div>
                  {camt053Result.account_iban && <div className="col-span-2">IBAN: {camt053Result.account_iban}</div>}
                </div>
              </div>
            )}

            {/* CBI Result */}
            {cbiResult && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Parsificati {cbiResult.records_parsed} record</p>
                {cbiResult.records.length > 0 && (
                  <div className="max-h-[200px] overflow-y-auto rounded border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Rif</TableHead>
                          <TableHead>Importo</TableHead>
                          <TableHead>Segno</TableHead>
                          <TableHead>Causale</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {cbiResult.records.slice(0, 10).map((r, i) => (
                          <TableRow key={i}>
                            <TableCell className="text-xs">{r.riferimento as string}</TableCell>
                            <TableCell className="text-xs">{r.importo as string}</TableCell>
                            <TableCell className="text-xs">{r.segno as string}</TableCell>
                            <TableCell className="text-xs">{r.causale as string}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            )}

            {/* Generic Result */}
            {genericResult && <p className="text-sm font-medium text-green-700">{genericResult}</p>}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>Chiudi</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
