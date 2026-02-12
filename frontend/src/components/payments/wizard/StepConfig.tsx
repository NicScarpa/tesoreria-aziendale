"use client";

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
import {
  PAYMENT_ORDER_TYPE_LABELS,
  PAYMENT_PRIORITY_LABELS,
  type PaymentOrderType,
  type PaymentPriority,
} from "@/types/payment";
import type { BankAccount } from "@/types/bank-account";

export interface WizardConfig {
  tipo: PaymentOrderType;
  bank_account_id: string | null;
  data_esecuzione_richiesta: string;
  priorita: PaymentPriority;
  note: string;
}

interface StepConfigProps {
  config: WizardConfig;
  onChange: (config: WizardConfig) => void;
  bankAccounts: BankAccount[];
}

export function StepConfig({ config, onChange, bankAccounts }: StepConfigProps) {
  function update(partial: Partial<WizardConfig>) {
    onChange({ ...config, ...partial });
  }

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Label>Tipo pagamento *</Label>
        <Select
          value={config.tipo}
          onValueChange={(v) => update({ tipo: v as PaymentOrderType })}
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
      </div>

      <div className="space-y-2">
        <Label>Conto bancario</Label>
        <Select
          value={config.bank_account_id ?? "none"}
          onValueChange={(v) =>
            update({ bank_account_id: v === "none" ? null : v })
          }
        >
          <SelectTrigger>
            <SelectValue placeholder="Seleziona conto" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Nessuno</SelectItem>
            {bankAccounts.map((a) => (
              <SelectItem key={a.id} value={a.id}>
                {a.nickname || a.iban || a.id}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Data esecuzione richiesta *</Label>
          <Input
            type="date"
            value={config.data_esecuzione_richiesta}
            onChange={(e) => update({ data_esecuzione_richiesta: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Priorita</Label>
          <Select
            value={config.priorita}
            onValueChange={(v) => update({ priorita: v as PaymentPriority })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(PAYMENT_PRIORITY_LABELS).map(([key, label]) => (
                <SelectItem key={key} value={key}>
                  {label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-2">
        <Label>Note</Label>
        <Textarea
          value={config.note}
          onChange={(e) => update({ note: e.target.value })}
          placeholder="Note aggiuntive per l'ordine di pagamento..."
          rows={3}
        />
      </div>
    </div>
  );
}
