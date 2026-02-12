"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { CalendarDays, Loader2 } from "lucide-react";
import api from "@/lib/api";
import { createFromSchedules } from "@/lib/api/payments";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { PaymentOrder } from "@/types/payment";
import type { BankAccount } from "@/types/bank-account";

interface Schedule {
  id: string;
  controparte_nome: string | null;
  importo_residuo: number;
  data_scadenza: string;
  descrizione: string | null;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT");
}

interface SchedulePickerDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: (order: PaymentOrder) => void;
  bankAccounts: BankAccount[];
}

export function SchedulePickerDialog({
  open,
  onClose,
  onCreated,
  bankAccounts,
}: SchedulePickerDialogProps) {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bankAccountId, setBankAccountId] = useState<string | null>(null);
  const [dataEsecuzione, setDataEsecuzione] = useState("");
  const [priorita, setPriorita] = useState<"normale" | "alta" | "urgente">("normale");

  useEffect(() => {
    if (!open) return;
    setSelected(new Set());
    setBankAccountId(null);
    setDataEsecuzione("");
    setPriorita("normale");
    fetchSchedules();
  }, [open]);

  async function fetchSchedules() {
    setLoading(true);
    try {
      const resp = await api.get<{ items: Schedule[] }>(
        "/schedules?tipo=passiva&stato=aperta"
      );
      setSchedules(resp.data.items ?? resp.data as unknown as Schedule[]);
    } catch {
      toast.error("Errore nel caricamento delle scadenze");
    } finally {
      setLoading(false);
    }
  }

  function toggleSelection(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function toggleAll() {
    if (selected.size === schedules.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(schedules.map((s) => s.id)));
    }
  }

  const totalSelected = schedules
    .filter((s) => selected.has(s.id))
    .reduce((sum, s) => sum + s.importo_residuo, 0);

  async function handleCreate() {
    if (selected.size === 0) {
      toast.error("Seleziona almeno una scadenza");
      return;
    }
    if (!dataEsecuzione) {
      toast.error("Inserisci la data di esecuzione");
      return;
    }

    setCreating(true);
    try {
      const order = await createFromSchedules({
        schedule_ids: Array.from(selected),
        bank_account_id: bankAccountId ?? undefined,
        data_esecuzione_richiesta: dataEsecuzione,
        priorita,
      });
      toast.success("Ordine di pagamento creato da scadenze");
      onCreated(order);
      onClose();
    } catch {
      toast.error("Errore nella creazione dell'ordine");
    } finally {
      setCreating(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5" />
            Crea pagamento da scadenze
          </DialogTitle>
        </DialogHeader>

        {/* Configuration */}
        <div className="grid grid-cols-3 gap-3">
          <div className="space-y-2">
            <Label>Data esecuzione *</Label>
            <Input
              type="date"
              value={dataEsecuzione}
              onChange={(e) => setDataEsecuzione(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Conto bancario</Label>
            <Select onValueChange={(v) => setBankAccountId(v === "none" ? null : v)}>
              <SelectTrigger>
                <SelectValue placeholder="Seleziona" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Nessuno</SelectItem>
                {bankAccounts.map((a) => (
                  <SelectItem key={a.id} value={a.id}>
                    {a.nickname || a.iban}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Priorita</Label>
            <Select
              defaultValue="normale"
              onValueChange={(v) => setPriorita(v as "normale" | "alta" | "urgente")}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="normale">Normale</SelectItem>
                <SelectItem value="alta">Alta</SelectItem>
                <SelectItem value="urgente">Urgente</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Schedule table */}
        <div className="rounded-md border mt-2">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : schedules.length === 0 ? (
            <div className="p-8 text-center text-sm text-muted-foreground">
              Nessuna scadenza aperta trovata.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40px]">
                    <Checkbox
                      checked={
                        schedules.length > 0 && selected.size === schedules.length
                      }
                      onCheckedChange={toggleAll}
                    />
                  </TableHead>
                  <TableHead>Controparte</TableHead>
                  <TableHead className="text-right">Importo residuo</TableHead>
                  <TableHead>Scadenza</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schedules.map((s) => (
                  <TableRow
                    key={s.id}
                    className="cursor-pointer"
                    onClick={() => toggleSelection(s.id)}
                  >
                    <TableCell>
                      <Checkbox
                        checked={selected.has(s.id)}
                        onCheckedChange={() => toggleSelection(s.id)}
                      />
                    </TableCell>
                    <TableCell className="font-medium">
                      {s.controparte_nome || s.descrizione || "-"}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(s.importo_residuo)}
                    </TableCell>
                    <TableCell>{formatDate(s.data_scadenza)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        {selected.size > 0 && (
          <div className="text-sm text-muted-foreground">
            {selected.size} {selected.size === 1 ? "scadenza selezionata" : "scadenze selezionate"}{" "}
            — Totale: <span className="font-semibold">{formatCurrency(totalSelected)}</span>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Annulla
          </Button>
          <Button onClick={handleCreate} disabled={creating || selected.size === 0}>
            {creating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creazione...
              </>
            ) : (
              "Crea ordine di pagamento"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
