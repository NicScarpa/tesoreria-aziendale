"use client";

import { Pencil, Trash2, Play } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { CategorizationRule } from "@/types/categorization-rule";

const DIRECTION_LABELS: Record<string, string> = {
  inflow: "Entrata",
  outflow: "Uscita",
};

interface Props {
  rules: CategorizationRule[];
  onEdit: (rule: CategorizationRule) => void;
  onDelete: (rule: CategorizationRule) => void;
  onTest: (rule: CategorizationRule) => void;
  canEdit?: boolean;
  canDelete?: boolean;
}

export function RuleList({ rules, onEdit, onDelete, onTest, canEdit, canDelete }: Props) {
  return (
    <div className="space-y-2">
      {rules.map((rule) => (
        <div
          key={rule.id}
          className="flex items-center gap-3 p-3 border rounded-lg hover:bg-muted/50"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium truncate">{rule.name || "Regola senza nome"}</span>
              <Badge variant="outline" className="text-xs">
                {DIRECTION_LABELS[rule.direction] || rule.direction}
              </Badge>
              {!rule.is_active && (
                <Badge variant="secondary" className="text-xs">Disattivata</Badge>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
              {rule.category && (
                <span className="flex items-center gap-1">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: rule.category.color }}
                  />
                  {rule.category.name}
                </span>
              )}
              <span>Priorità: {rule.priority}</span>
              <span>
                {rule.conditions.length} condizion{rule.conditions.length === 1 ? "e" : "i"}
              </span>
            </div>
          </div>

          <div className="flex gap-1">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => onTest(rule)} title="Testa regola">
              <Play className="h-4 w-4" />
            </Button>
            {canEdit && (
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => onEdit(rule)}>
                <Pencil className="h-4 w-4" />
              </Button>
            )}
            {canDelete && (
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-red-500" onClick={() => onDelete(rule)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      ))}

      {rules.length === 0 && (
        <div className="text-center py-8 text-sm text-muted-foreground">
          Nessuna regola di categorizzazione configurata.
        </div>
      )}
    </div>
  );
}
