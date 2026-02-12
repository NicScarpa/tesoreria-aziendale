"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ReportParamsFormProps {
  tipo: string;
  parametri: Record<string, unknown>;
  onChange: (params: Record<string, unknown>) => void;
}

export function ReportParamsForm({ tipo, parametri, onChange }: ReportParamsFormProps) {
  const update = (key: string, value: unknown) => {
    onChange({ ...parametri, [key]: value });
  };

  const today = new Date().toISOString().split("T")[0];
  const thirtyDaysAgo = new Date(Date.now() - 30 * 86400000).toISOString().split("T")[0];

  // Common date range for most report types
  const showDateRange = [
    "movimenti", "entrate_uscite", "riconciliazione", "cash_flow", "pagamenti", "controparte",
  ].includes(tipo);

  return (
    <div className="space-y-3">
      {showDateRange && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Data inizio</Label>
              <Input
                type="date"
                value={(parametri.data_inizio as string) || thirtyDaysAgo}
                onChange={(e) => update("data_inizio", e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Data fine</Label>
              <Input
                type="date"
                value={(parametri.data_fine as string) || today}
                onChange={(e) => update("data_fine", e.target.value)}
              />
            </div>
          </div>
        </>
      )}

      {tipo === "saldi_conti" && (
        <div className="flex items-center justify-between">
          <Label className="text-sm">Includi conti chiusi</Label>
          <Switch
            checked={!!parametri.includi_conti_chiusi}
            onCheckedChange={(v) => update("includi_conti_chiusi", v)}
          />
        </div>
      )}

      {tipo === "scadenzario" && (
        <>
          <div className="space-y-1">
            <Label className="text-xs">Tipo scadenzario</Label>
            <Select
              value={(parametri.tipo_scadenzario as string) || "attiva"}
              onValueChange={(v) => update("tipo_scadenzario", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="attiva">Attivo (crediti)</SelectItem>
                <SelectItem value="passiva">Passivo (debiti)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center justify-between">
            <Label className="text-sm">Includi scadute</Label>
            <Switch
              checked={parametri.includi_scadute !== false}
              onCheckedChange={(v) => update("includi_scadute", v)}
            />
          </div>
        </>
      )}

      {tipo === "controparte" && (
        <div className="space-y-1">
          <Label className="text-xs">Nome controparte</Label>
          <Input
            placeholder="Es. ABC SRL"
            value={(parametri.controparte_nome as string) || ""}
            onChange={(e) => update("controparte_nome", e.target.value)}
          />
        </div>
      )}

      {tipo === "cash_flow" && (
        <>
          <div className="flex items-center justify-between">
            <Label className="text-sm">Includi scadenze</Label>
            <Switch
              checked={parametri.includi_scadenze !== false}
              onCheckedChange={(v) => update("includi_scadenze", v)}
            />
          </div>
          <div className="flex items-center justify-between">
            <Label className="text-sm">Includi ricorrenze</Label>
            <Switch
              checked={parametri.includi_ricorrenze !== false}
              onCheckedChange={(v) => update("includi_ricorrenze", v)}
            />
          </div>
        </>
      )}

      {tipo === "aging" && (
        <div className="space-y-1">
          <Label className="text-xs">Tipo</Label>
          <Select
            value={(parametri.tipo as string) || "entrambi"}
            onValueChange={(v) => update("tipo", v)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="entrambi">Crediti e Debiti</SelectItem>
              <SelectItem value="attiva">Solo Crediti</SelectItem>
              <SelectItem value="passiva">Solo Debiti</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}
    </div>
  );
}
