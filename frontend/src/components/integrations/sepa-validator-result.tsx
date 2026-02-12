"use client";

import { CheckCircle, XCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { SEPAValidationResult } from "@/types/integration";

interface Props {
  result: SEPAValidationResult;
}

export function SEPAValidatorResult({ result }: Props) {
  return (
    <Alert variant={result.valid ? "default" : "destructive"}>
      {result.valid ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
      <AlertTitle>{result.valid ? "File Valido" : "File Non Valido"}</AlertTitle>
      <AlertDescription>
        {result.file_type && <p className="text-sm">Tipo: {result.file_type}</p>}
        {result.message_id && <p className="text-sm">Message ID: {result.message_id}</p>}
        {result.errors.length > 0 && (
          <ul className="mt-2 list-disc pl-4">
            {result.errors.map((err, i) => (
              <li key={i} className="text-sm">{err}</li>
            ))}
          </ul>
        )}
      </AlertDescription>
    </Alert>
  );
}
