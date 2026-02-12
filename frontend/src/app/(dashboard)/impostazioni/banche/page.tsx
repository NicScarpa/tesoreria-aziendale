"use client";

import { Landmark } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

export default function BankConnectionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Connessioni bancarie</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Gestisci i collegamenti ai tuoi conti correnti
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Conti collegati</CardTitle>
          <CardDescription>
            Collega i tuoi conti correnti per importare automaticamente i
            movimenti bancari
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="rounded-full bg-muted p-4 mb-4">
              <Landmark className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium mb-2">
              Nessuna connessione bancaria configurata
            </h3>
            <p className="text-muted-foreground text-sm max-w-md mb-6">
              Collega i tuoi conti correnti tramite Open Banking (PSD2) per
              importare automaticamente i movimenti e sincronizzare i saldi in
              tempo reale.
            </p>
            <Button disabled title="Disponibile prossimamente">
              Collega conto
            </Button>
            <p className="text-muted-foreground text-xs mt-3">
              Disponibile prossimamente
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
