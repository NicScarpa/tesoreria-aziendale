"use client";

import { useReducer, useState } from "react";
import { toast } from "sonner";
import { ArrowLeft, ChevronRight, Loader2, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { createPaymentOrder, addLine } from "@/lib/api/payments";
import { StepConfig, type WizardConfig } from "./StepConfig";
import { StepLines } from "./StepLines";
import { StepReview } from "./StepReview";
import type {
  PaymentOrderLine,
  PaymentOrderType,
  PaymentPriority,
} from "@/types/payment";
import type { CreatePaymentLineInput } from "@/lib/validations/payment";
import type { BankAccount } from "@/types/bank-account";

// --- Reducer ---

interface WizardState {
  step: 1 | 2 | 3;
  config: WizardConfig;
  lines: PaymentOrderLine[];
}

type WizardAction =
  | { type: "SET_STEP"; step: 1 | 2 | 3 }
  | { type: "SET_CONFIG"; config: WizardConfig }
  | { type: "ADD_LINE"; line: PaymentOrderLine }
  | { type: "REMOVE_LINE"; index: number }
  | { type: "UPDATE_LINE"; index: number; line: PaymentOrderLine }
  | { type: "RESET" };

const initialConfig: WizardConfig = {
  tipo: "sepa_credit_transfer",
  bank_account_id: null,
  data_esecuzione_richiesta: "",
  priorita: "normale",
  note: "",
};

function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "SET_STEP":
      return { ...state, step: action.step };
    case "SET_CONFIG":
      return { ...state, config: action.config };
    case "ADD_LINE":
      return { ...state, lines: [...state.lines, action.line] };
    case "REMOVE_LINE":
      return {
        ...state,
        lines: state.lines.filter((_, i) => i !== action.index),
      };
    case "UPDATE_LINE":
      return {
        ...state,
        lines: state.lines.map((l, i) => (i === action.index ? action.line : l)),
      };
    case "RESET":
      return { step: 1, config: initialConfig, lines: [] };
    default:
      return state;
  }
}

// --- Step definitions ---

const STEPS = [
  { number: 1 as const, label: "Configurazione" },
  { number: 2 as const, label: "Righe" },
  { number: 3 as const, label: "Riepilogo" },
];

// --- Component ---

interface PaymentWizardProps {
  onComplete: (orderId: string) => void;
  bankAccounts: BankAccount[];
}

export function PaymentWizard({ onComplete, bankAccounts }: PaymentWizardProps) {
  const [state, dispatch] = useReducer(wizardReducer, {
    step: 1,
    config: initialConfig,
    lines: [],
  });
  const [creating, setCreating] = useState(false);

  function handleNext() {
    if (state.step === 1) {
      if (!state.config.data_esecuzione_richiesta) {
        toast.error("Inserisci la data di esecuzione richiesta");
        return;
      }
      dispatch({ type: "SET_STEP", step: 2 });
    } else if (state.step === 2) {
      dispatch({ type: "SET_STEP", step: 3 });
    }
  }

  function handleBack() {
    if (state.step === 2) dispatch({ type: "SET_STEP", step: 1 });
    else if (state.step === 3) dispatch({ type: "SET_STEP", step: 2 });
  }

  function handleAddLine(data: CreatePaymentLineInput) {
    const line: PaymentOrderLine = {
      id: crypto.randomUUID(),
      payment_order_id: "",
      beneficiario_nome: data.beneficiario_nome,
      beneficiario_iban: data.beneficiario_iban ?? null,
      beneficiario_bic: data.beneficiario_bic ?? null,
      beneficiario_cf: data.beneficiario_cf ?? null,
      beneficiario_indirizzo: data.beneficiario_indirizzo ?? null,
      importo: data.importo,
      valuta: data.valuta ?? "EUR",
      causale: data.causale ?? null,
      end_to_end_id: data.end_to_end_id ?? null,
      stato: "inclusa",
      counterparty_id: data.counterparty_id ?? null,
      schedule_id: data.schedule_id ?? null,
      riba_numero_ricevuta: data.riba_numero_ricevuta ?? null,
      riba_data_scadenza: data.riba_data_scadenza ?? null,
      riba_piazza: data.riba_piazza ?? null,
      riba_abi_banca_domiciliataria: data.riba_abi_banca_domiciliataria ?? null,
      riba_cab_banca_domiciliataria: data.riba_cab_banca_domiciliataria ?? null,
      sdd_mandate_id: data.sdd_mandate_id ?? null,
      sdd_mandate_date: data.sdd_mandate_date ?? null,
      sdd_mandate_type: data.sdd_mandate_type ?? null,
      sdd_sequence_type: data.sdd_sequence_type ?? null,
      f24_sezione: data.f24_sezione ?? null,
      f24_codice_tributo: data.f24_codice_tributo ?? null,
      f24_rateazione: data.f24_rateazione ?? null,
      f24_anno_riferimento: data.f24_anno_riferimento ?? null,
      f24_mese_riferimento: data.f24_mese_riferimento ?? null,
      f24_importo_debito: data.f24_importo_debito ?? null,
      f24_importo_credito: data.f24_importo_credito ?? null,
      f24_codice_ente: data.f24_codice_ente ?? null,
      f24_codice_sede: data.f24_codice_sede ?? null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    dispatch({ type: "ADD_LINE", line });
  }

  async function handleCreate() {
    setCreating(true);
    try {
      // 1. Create the order
      const order = await createPaymentOrder({
        tipo: state.config.tipo,
        bank_account_id: state.config.bank_account_id,
        data_esecuzione_richiesta: state.config.data_esecuzione_richiesta,
        priorita: state.config.priorita,
        note: state.config.note || null,
      });

      // 2. Add lines one by one
      for (const line of state.lines) {
        await addLine(order.id, {
          beneficiario_nome: line.beneficiario_nome,
          beneficiario_iban: line.beneficiario_iban,
          beneficiario_bic: line.beneficiario_bic,
          beneficiario_cf: line.beneficiario_cf,
          beneficiario_indirizzo: line.beneficiario_indirizzo,
          importo: line.importo,
          valuta: line.valuta,
          causale: line.causale,
          end_to_end_id: line.end_to_end_id,
          counterparty_id: line.counterparty_id,
          schedule_id: line.schedule_id,
          riba_numero_ricevuta: line.riba_numero_ricevuta,
          riba_data_scadenza: line.riba_data_scadenza,
          riba_piazza: line.riba_piazza,
          riba_abi_banca_domiciliataria: line.riba_abi_banca_domiciliataria,
          riba_cab_banca_domiciliataria: line.riba_cab_banca_domiciliataria,
          sdd_mandate_id: line.sdd_mandate_id,
          sdd_mandate_date: line.sdd_mandate_date,
          sdd_mandate_type: line.sdd_mandate_type,
          sdd_sequence_type: line.sdd_sequence_type,
          f24_sezione: line.f24_sezione,
          f24_codice_tributo: line.f24_codice_tributo,
          f24_rateazione: line.f24_rateazione,
          f24_anno_riferimento: line.f24_anno_riferimento,
          f24_mese_riferimento: line.f24_mese_riferimento,
          f24_importo_debito: line.f24_importo_debito,
          f24_importo_credito: line.f24_importo_credito,
          f24_codice_ente: line.f24_codice_ente,
          f24_codice_sede: line.f24_codice_sede,
        });
      }

      toast.success("Ordine di pagamento creato con successo");
      dispatch({ type: "RESET" });
      onComplete(order.id);
    } catch {
      toast.error("Errore nella creazione dell'ordine di pagamento");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Step indicators */}
      <div className="flex items-center justify-center gap-2">
        {STEPS.map((s, index) => (
          <div key={s.number} className="flex items-center">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium border-2 transition-colors",
                  state.step === s.number &&
                    "border-primary bg-primary text-primary-foreground",
                  state.step > s.number &&
                    "border-green-500 bg-green-500 text-white",
                  state.step < s.number &&
                    "border-gray-300 bg-white text-gray-400"
                )}
              >
                {state.step > s.number ? (
                  <Check className="h-4 w-4" />
                ) : (
                  s.number
                )}
              </div>
              <span
                className={cn(
                  "text-sm",
                  state.step === s.number
                    ? "font-semibold text-foreground"
                    : "text-muted-foreground"
                )}
              >
                {s.label}
              </span>
            </div>
            {index < STEPS.length - 1 && (
              <div
                className={cn(
                  "mx-4 h-0.5 w-12",
                  state.step > s.number ? "bg-green-500" : "bg-gray-200"
                )}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step content */}
      <Card>
        <CardContent className="pt-6">
          {state.step === 1 && (
            <StepConfig
              config={state.config}
              onChange={(config) => dispatch({ type: "SET_CONFIG", config })}
              bankAccounts={bankAccounts}
            />
          )}
          {state.step === 2 && (
            <StepLines
              lines={state.lines}
              tipo={state.config.tipo}
              onAddLine={handleAddLine}
              onRemoveLine={(index) =>
                dispatch({ type: "REMOVE_LINE", index })
              }
              bankAccounts={bankAccounts}
            />
          )}
          {state.step === 3 && (
            <StepReview
              config={state.config}
              lines={state.lines}
              bankAccounts={bankAccounts}
            />
          )}
        </CardContent>
      </Card>

      {/* Navigation buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={state.step === 1}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Indietro
        </Button>
        <div className="flex gap-2">
          {state.step < 3 ? (
            <Button onClick={handleNext}>
              Avanti
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={handleCreate} disabled={creating}>
              {creating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creazione in corso...
                </>
              ) : (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Crea ordine di pagamento
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
