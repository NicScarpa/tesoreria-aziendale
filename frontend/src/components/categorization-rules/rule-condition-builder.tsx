"use client";

import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { RuleCondition } from "@/types/categorization-rule";

const CONDITION_TYPES = [
  { value: "KEYWORDS", label: "Parole chiave" },
  { value: "TRANSACTION_TYPE", label: "Tipo transazione" },
  { value: "ACCOUNT", label: "Conto" },
];

const TX_TYPES = [
  { value: "credit_transfer", label: "Bonifico" },
  { value: "direct_debit", label: "Addebito diretto" },
  { value: "card_payment", label: "Carta" },
  { value: "cash", label: "Contante" },
  { value: "fee", label: "Commissione" },
  { value: "interest", label: "Interesse" },
  { value: "tax", label: "Tasse" },
  { value: "other", label: "Altro" },
];

interface Props {
  conditions: RuleCondition[];
  onChange: (conditions: RuleCondition[]) => void;
}

export function RuleConditionBuilder({ conditions, onChange }: Props) {
  const addCondition = () => {
    onChange([...conditions, { type: "KEYWORDS", value: [] }]);
  };

  const removeCondition = (index: number) => {
    onChange(conditions.filter((_, i) => i !== index));
  };

  const updateCondition = (index: number, updates: Partial<RuleCondition>) => {
    const next = [...conditions];
    next[index] = { ...next[index], ...updates };
    onChange(next);
  };

  return (
    <div className="space-y-2 mt-2">
      {conditions.map((cond, i) => (
        <div key={i} className="flex items-start gap-2 p-2 border rounded">
          <Select
            value={cond.type}
            onValueChange={(v) =>
              updateCondition(i, {
                type: v as RuleCondition["type"],
                value: v === "KEYWORDS" ? [] : "",
              })
            }
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CONDITION_TYPES.map((ct) => (
                <SelectItem key={ct.value} value={ct.value}>{ct.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex-1">
            {cond.type === "KEYWORDS" && (
              <Input
                placeholder="Parole chiave separate da virgola..."
                value={Array.isArray(cond.value) ? cond.value.join(", ") : cond.value}
                onChange={(e) => {
                  const keywords = e.target.value
                    .split(",")
                    .map((k) => k.trim())
                    .filter(Boolean);
                  updateCondition(i, { value: keywords });
                }}
              />
            )}
            {cond.type === "TRANSACTION_TYPE" && (
              <Select
                value={Array.isArray(cond.value) ? cond.value[0] : cond.value as string}
                onValueChange={(v) => updateCondition(i, { value: [v] })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona tipo..." />
                </SelectTrigger>
                <SelectContent>
                  {TX_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {cond.type === "ACCOUNT" && (
              <Input
                placeholder="ID conto..."
                value={cond.value as string}
                onChange={(e) => updateCondition(i, { value: e.target.value })}
              />
            )}
          </div>

          <Button variant="ghost" size="sm" className="h-9 w-9 p-0" onClick={() => removeCondition(i)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ))}

      <Button variant="outline" size="sm" onClick={addCondition} className="gap-1">
        <Plus className="h-4 w-4" />
        Aggiungi condizione
      </Button>
    </div>
  );
}
