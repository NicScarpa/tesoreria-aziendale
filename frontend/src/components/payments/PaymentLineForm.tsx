"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  createPaymentLineSchema,
  type CreatePaymentLineInput,
} from "@/lib/validations/payment";
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
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PaymentOrderType, PaymentOrderLine } from "@/types/payment";

interface PaymentLineFormProps {
  open: boolean;
  onClose: () => void;
  tipo: PaymentOrderType;
  onSubmit: (data: CreatePaymentLineInput) => void;
  defaultValues?: Partial<PaymentOrderLine>;
}

export function PaymentLineForm({
  open,
  onClose,
  tipo,
  onSubmit,
  defaultValues,
}: PaymentLineFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<CreatePaymentLineInput>({
    resolver: zodResolver(createPaymentLineSchema),
    defaultValues: {
      beneficiario_nome: defaultValues?.beneficiario_nome ?? "",
      beneficiario_iban: defaultValues?.beneficiario_iban ?? null,
      beneficiario_bic: defaultValues?.beneficiario_bic ?? null,
      beneficiario_cf: defaultValues?.beneficiario_cf ?? null,
      importo: defaultValues?.importo ?? 0,
      valuta: defaultValues?.valuta ?? "EUR",
      causale: defaultValues?.causale ?? null,
      end_to_end_id: defaultValues?.end_to_end_id ?? null,
      // RiBa
      riba_numero_ricevuta: defaultValues?.riba_numero_ricevuta ?? null,
      riba_data_scadenza: defaultValues?.riba_data_scadenza ?? null,
      riba_piazza: defaultValues?.riba_piazza ?? null,
      riba_abi_banca_domiciliataria: defaultValues?.riba_abi_banca_domiciliataria ?? null,
      riba_cab_banca_domiciliataria: defaultValues?.riba_cab_banca_domiciliataria ?? null,
      // SDD
      sdd_mandate_id: defaultValues?.sdd_mandate_id ?? null,
      sdd_mandate_date: defaultValues?.sdd_mandate_date ?? null,
      sdd_mandate_type: defaultValues?.sdd_mandate_type ?? null,
      sdd_sequence_type: defaultValues?.sdd_sequence_type ?? null,
      // F24
      f24_sezione: defaultValues?.f24_sezione ?? null,
      f24_codice_tributo: defaultValues?.f24_codice_tributo ?? null,
      f24_rateazione: defaultValues?.f24_rateazione ?? null,
      f24_anno_riferimento: defaultValues?.f24_anno_riferimento ?? null,
      f24_mese_riferimento: defaultValues?.f24_mese_riferimento ?? null,
      f24_importo_debito: defaultValues?.f24_importo_debito ?? null,
      f24_importo_credito: defaultValues?.f24_importo_credito ?? null,
      f24_codice_ente: defaultValues?.f24_codice_ente ?? null,
      f24_codice_sede: defaultValues?.f24_codice_sede ?? null,
    },
  });

  const showSEPA = tipo === "sepa_credit_transfer" || tipo === "bonifico_estero";
  const showRiBa = tipo === "riba";
  const showSDD = tipo === "sdd";
  const showF24 = tipo === "f24";

  const isEditing = !!defaultValues?.id;

  function handleFormSubmit(data: CreatePaymentLineInput) {
    onSubmit(data);
    reset();
    onClose();
  }

  function handleCancel() {
    reset();
    onClose();
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleCancel()}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Modifica riga di pagamento" : "Nuova riga di pagamento"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          {/* Common fields */}
          <div className="space-y-2">
            <Label>Beneficiario *</Label>
            <Input
              {...register("beneficiario_nome")}
              placeholder="Nome beneficiario"
            />
            {errors.beneficiario_nome && (
              <p className="text-xs text-destructive">{errors.beneficiario_nome.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label>Importo *</Label>
              <Input
                type="number"
                step="0.01"
                {...register("importo", { valueAsNumber: true })}
                placeholder="0,00"
              />
              {errors.importo && (
                <p className="text-xs text-destructive">{errors.importo.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Valuta</Label>
              <Input {...register("valuta")} defaultValue="EUR" />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Causale</Label>
            <Textarea
              {...register("causale")}
              placeholder="Descrizione del pagamento"
              rows={2}
            />
            {errors.causale && (
              <p className="text-xs text-destructive">{errors.causale.message}</p>
            )}
          </div>

          {/* SEPA / Bonifico Estero fields */}
          {showSEPA && (
            <>
              <div className="border-t pt-4">
                <p className="text-sm font-semibold mb-3">Dati SEPA</p>
              </div>
              <div className="space-y-2">
                <Label>IBAN beneficiario</Label>
                <Input
                  {...register("beneficiario_iban")}
                  placeholder="IT60X0542811101000000123456"
                  className="font-mono"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>BIC</Label>
                  <Input
                    {...register("beneficiario_bic")}
                    placeholder="BPPIITRRXXX"
                    className="font-mono"
                  />
                </div>
                <div className="space-y-2">
                  <Label>End-to-End ID</Label>
                  <Input
                    {...register("end_to_end_id")}
                    placeholder="Riferimento univoco"
                  />
                </div>
              </div>
            </>
          )}

          {/* RiBa fields */}
          {showRiBa && (
            <>
              <div className="border-t pt-4">
                <p className="text-sm font-semibold mb-3">Dati RiBa</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Numero ricevuta</Label>
                  <Input {...register("riba_numero_ricevuta")} />
                </div>
                <div className="space-y-2">
                  <Label>Data scadenza</Label>
                  <Input type="date" {...register("riba_data_scadenza")} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Piazza</Label>
                <Input {...register("riba_piazza")} placeholder="Localita di pagamento" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>ABI banca domiciliataria</Label>
                  <Input
                    {...register("riba_abi_banca_domiciliataria")}
                    placeholder="00000"
                    className="font-mono"
                  />
                </div>
                <div className="space-y-2">
                  <Label>CAB banca domiciliataria</Label>
                  <Input
                    {...register("riba_cab_banca_domiciliataria")}
                    placeholder="00000"
                    className="font-mono"
                  />
                </div>
              </div>
            </>
          )}

          {/* SDD fields */}
          {showSDD && (
            <>
              <div className="border-t pt-4">
                <p className="text-sm font-semibold mb-3">Dati SDD</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Mandate ID</Label>
                  <Input {...register("sdd_mandate_id")} placeholder="ID mandato" />
                </div>
                <div className="space-y-2">
                  <Label>Data mandato</Label>
                  <Input type="date" {...register("sdd_mandate_date")} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Tipo mandato</Label>
                  <Select
                    onValueChange={(v) =>
                      setValue("sdd_mandate_type", v as "core" | "b2b")
                    }
                    defaultValue={defaultValues?.sdd_mandate_type ?? undefined}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="core">CORE</SelectItem>
                      <SelectItem value="b2b">B2B</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Tipo sequenza</Label>
                  <Select
                    onValueChange={(v) =>
                      setValue(
                        "sdd_sequence_type",
                        v as "frst" | "rcur" | "fnal" | "ooff"
                      )
                    }
                    defaultValue={defaultValues?.sdd_sequence_type ?? undefined}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="frst">Prima (FRST)</SelectItem>
                      <SelectItem value="rcur">Ricorrente (RCUR)</SelectItem>
                      <SelectItem value="fnal">Finale (FNAL)</SelectItem>
                      <SelectItem value="ooff">Una tantum (OOFF)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>IBAN debitore</Label>
                <Input
                  {...register("beneficiario_iban")}
                  placeholder="IBAN del debitore"
                  className="font-mono"
                />
              </div>
            </>
          )}

          {/* F24 fields */}
          {showF24 && (
            <>
              <div className="border-t pt-4">
                <p className="text-sm font-semibold mb-3">Dati F24</p>
              </div>
              <div className="space-y-2">
                <Label>Sezione</Label>
                <Select
                  onValueChange={(v) =>
                    setValue(
                      "f24_sezione",
                      v as "erario" | "inps" | "regioni" | "imu_altri_enti"
                    )
                  }
                  defaultValue={defaultValues?.f24_sezione ?? undefined}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleziona sezione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="erario">Erario</SelectItem>
                    <SelectItem value="inps">INPS</SelectItem>
                    <SelectItem value="regioni">Regioni</SelectItem>
                    <SelectItem value="imu_altri_enti">IMU / Altri enti</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Codice tributo</Label>
                  <Input
                    {...register("f24_codice_tributo")}
                    placeholder="Es: 1001"
                    className="font-mono"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Rateazione</Label>
                  <Input
                    {...register("f24_rateazione")}
                    placeholder="Es: 0101"
                    className="font-mono"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Anno riferimento</Label>
                  <Input
                    type="number"
                    {...register("f24_anno_riferimento", { valueAsNumber: true })}
                    placeholder="2026"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Mese riferimento</Label>
                  <Input
                    type="number"
                    min={1}
                    max={12}
                    {...register("f24_mese_riferimento", { valueAsNumber: true })}
                    placeholder="1-12"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Importo a debito</Label>
                  <Input
                    type="number"
                    step="0.01"
                    {...register("f24_importo_debito", { valueAsNumber: true })}
                    placeholder="0,00"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Importo a credito</Label>
                  <Input
                    type="number"
                    step="0.01"
                    {...register("f24_importo_credito", { valueAsNumber: true })}
                    placeholder="0,00"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Codice ente</Label>
                  <Input {...register("f24_codice_ente")} />
                </div>
                <div className="space-y-2">
                  <Label>Codice sede</Label>
                  <Input {...register("f24_codice_sede")} />
                </div>
              </div>
            </>
          )}

          <DialogFooter className="pt-4">
            <Button type="button" variant="outline" onClick={handleCancel}>
              Annulla
            </Button>
            <Button type="submit">
              {isEditing ? "Salva modifiche" : "Aggiungi riga"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
