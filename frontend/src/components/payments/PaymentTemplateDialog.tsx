"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, FileText, Trash2 } from "lucide-react";
import {
  createTemplateSchema,
  type CreateTemplateInput,
} from "@/lib/validations/payment";
import {
  listTemplates,
  createTemplate,
  applyTemplate,
  deleteTemplate,
} from "@/lib/api/payments";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  PAYMENT_ORDER_TYPE_LABELS,
  type PaymentTemplate,
  type PaymentOrder,
  type PaymentOrderType,
} from "@/types/payment";

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT");
}

interface PaymentTemplateDialogProps {
  open: boolean;
  onClose: () => void;
  mode: "create" | "apply";
  onApplied?: (order: PaymentOrder) => void;
}

export function PaymentTemplateDialog({
  open,
  onClose,
  mode,
  onApplied,
}: PaymentTemplateDialogProps) {
  const [templates, setTemplates] = useState<PaymentTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [applyDate, setApplyDate] = useState("");

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<CreateTemplateInput>({
    resolver: zodResolver(createTemplateSchema),
  });

  useEffect(() => {
    if (open && mode === "apply") {
      fetchTemplates();
    }
    if (!open) {
      reset();
      setSelectedTemplateId(null);
      setApplyDate("");
    }
  }, [open, mode, reset]);

  async function fetchTemplates() {
    setLoading(true);
    try {
      const data = await listTemplates();
      setTemplates(data);
    } catch {
      toast.error("Errore nel caricamento dei template");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateTemplate(data: CreateTemplateInput) {
    setSubmitting(true);
    try {
      await createTemplate(data);
      toast.success("Template creato con successo");
      reset();
      onClose();
    } catch {
      toast.error("Errore nella creazione del template");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleApplyTemplate() {
    if (!selectedTemplateId) {
      toast.error("Seleziona un template");
      return;
    }
    if (!applyDate) {
      toast.error("Inserisci la data di esecuzione");
      return;
    }

    setSubmitting(true);
    try {
      const order = await applyTemplate(selectedTemplateId, {
        data_esecuzione_richiesta: applyDate,
      });
      toast.success("Template applicato, ordine creato");
      onApplied?.(order);
      onClose();
    } catch {
      toast.error("Errore nell'applicazione del template");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteTemplate(id: string) {
    try {
      await deleteTemplate(id);
      setTemplates((prev) => prev.filter((t) => t.id !== id));
      if (selectedTemplateId === id) setSelectedTemplateId(null);
      toast.success("Template eliminato");
    } catch {
      toast.error("Errore nell'eliminazione del template");
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" ? "Salva come template" : "Applica template"}
          </DialogTitle>
        </DialogHeader>

        {mode === "create" ? (
          <form onSubmit={handleSubmit(handleCreateTemplate)} className="space-y-4">
            <div className="space-y-2">
              <Label>Nome template *</Label>
              <Input
                {...register("nome")}
                placeholder="Es: Bonifico fornitore ABC"
              />
              {errors.nome && (
                <p className="text-xs text-destructive">{errors.nome.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Tipo pagamento *</Label>
              <Select
                onValueChange={(v) => setValue("tipo", v as PaymentOrderType)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona tipo" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PAYMENT_ORDER_TYPE_LABELS).map(([key, label]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.tipo && (
                <p className="text-xs text-destructive">{errors.tipo.message}</p>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose}>
                Annulla
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Salvataggio...
                  </>
                ) : (
                  "Salva template"
                )}
              </Button>
            </DialogFooter>
          </form>
        ) : (
          <div className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : templates.length === 0 ? (
              <div className="p-8 text-center text-sm text-muted-foreground">
                Nessun template disponibile.
              </div>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {templates.map((t) => (
                  <div
                    key={t.id}
                    className={cn(
                      "flex items-center justify-between rounded-md border p-3 cursor-pointer transition-colors",
                      selectedTemplateId === t.id
                        ? "border-primary bg-primary/5"
                        : "hover:bg-muted/50"
                    )}
                    onClick={() => setSelectedTemplateId(t.id)}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">{t.nome}</p>
                        <p className="text-xs text-muted-foreground">
                          {PAYMENT_ORDER_TYPE_LABELS[t.tipo]} — Usato{" "}
                          {t.volte_utilizzato} {t.volte_utilizzato === 1 ? "volta" : "volte"}
                          {t.ultimo_utilizzo && (
                            <> — Ultimo: {formatDate(t.ultimo_utilizzo)}</>
                          )}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteTemplate(t.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {selectedTemplateId && (
              <div className="space-y-2">
                <Label>Data esecuzione *</Label>
                <Input
                  type="date"
                  value={applyDate}
                  onChange={(e) => setApplyDate(e.target.value)}
                />
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={onClose}>
                Annulla
              </Button>
              <Button
                onClick={handleApplyTemplate}
                disabled={submitting || !selectedTemplateId}
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Applicazione...
                  </>
                ) : (
                  "Applica template"
                )}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
