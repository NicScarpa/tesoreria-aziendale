"use client";

import { AlertTriangle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

interface Props {
  count: number;
  onRenew?: () => void;
}

export function ConsentExpiryBanner({ count, onRenew }: Props) {
  if (count === 0) return null;

  return (
    <Alert className="border-amber-500 bg-amber-50 text-amber-800">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <span>
          {count} connessione/i con consenso in scadenza nei prossimi 14 giorni.
        </span>
        {onRenew && (
          <Button size="sm" variant="outline" className="ml-2 text-amber-700 border-amber-300" onClick={onRenew}>
            Rinnova
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}
