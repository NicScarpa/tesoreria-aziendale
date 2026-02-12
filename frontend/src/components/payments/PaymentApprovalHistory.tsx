"use client";

import { Check, X, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { PaymentApproval, ApprovalAction } from "@/types/payment";

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const ACTION_CONFIG: Record<
  ApprovalAction,
  { label: string; color: string; icon: React.ElementType }
> = {
  approvata: {
    label: "Approvata",
    color: "bg-green-100 text-green-700",
    icon: Check,
  },
  rifiutata: {
    label: "Rifiutata",
    color: "bg-red-100 text-red-700",
    icon: X,
  },
  richiesta_modifica: {
    label: "Richiesta modifica",
    color: "bg-amber-100 text-amber-700",
    icon: AlertTriangle,
  },
};

interface PaymentApprovalHistoryProps {
  approvals: PaymentApproval[];
}

export function PaymentApprovalHistory({ approvals }: PaymentApprovalHistoryProps) {
  if (approvals.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Nessuna azione di approvazione registrata.
      </p>
    );
  }

  return (
    <div className="relative space-y-0">
      {/* Vertical line */}
      <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-gray-200" />

      {approvals.map((approval) => {
        const config = ACTION_CONFIG[approval.azione];
        const Icon = config.icon;

        return (
          <div key={approval.id} className="relative flex gap-4 pb-6 last:pb-0">
            {/* Timeline dot */}
            <div
              className={cn(
                "relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                config.color
              )}
            >
              <Icon className="h-4 w-4" />
            </div>

            {/* Content */}
            <div className="flex-1 pt-0.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium">
                  {approval.user_name || "Utente"}
                </span>
                <Badge variant="secondary" className={cn("text-[10px]", config.color)}>
                  {config.label}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {formatDate(approval.data_azione)}
                </span>
              </div>
              {approval.commento && (
                <p className="mt-1 text-sm text-muted-foreground">
                  {approval.commento}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
