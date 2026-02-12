"use client";

import { Check, X, Ban } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  WORKFLOW_STEPS,
  PAYMENT_ORDER_STATUS_LABELS,
  TERMINAL_STATUSES,
  type PaymentOrderStatus,
} from "@/types/payment";

interface PaymentWorkflowBarProps {
  stato: PaymentOrderStatus;
}

export function PaymentWorkflowBar({ stato }: PaymentWorkflowBarProps) {
  const isTerminal = stato === "rifiutata" || stato === "annullata";
  const currentIndex = WORKFLOW_STEPS.indexOf(stato);

  return (
    <div className="w-full">
      <div className="flex items-center">
        {WORKFLOW_STEPS.map((step, index) => {
          const isCompleted = !isTerminal && currentIndex > index;
          const isCurrent = !isTerminal && stato === step;
          const isFuture = !isTerminal && currentIndex < index;

          return (
            <div key={step} className="flex items-center flex-1 last:flex-none">
              {/* Step circle */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-medium transition-colors",
                    isCompleted && "border-green-500 bg-green-500 text-white",
                    isCurrent && "border-blue-500 bg-blue-50 text-blue-600",
                    isFuture && "border-gray-300 bg-white text-gray-400",
                    isTerminal && "border-gray-300 bg-white text-gray-400"
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    index + 1
                  )}
                </div>
                <span
                  className={cn(
                    "mt-1 text-[10px] leading-tight text-center max-w-[70px]",
                    isCompleted && "text-green-600 font-medium",
                    isCurrent && "text-blue-600 font-semibold",
                    (isFuture || isTerminal) && "text-gray-400"
                  )}
                >
                  {PAYMENT_ORDER_STATUS_LABELS[step]}
                </span>
              </div>

              {/* Connector line */}
              {index < WORKFLOW_STEPS.length - 1 && (
                <div
                  className={cn(
                    "h-0.5 flex-1 mx-2 mt-[-16px]",
                    !isTerminal && currentIndex > index
                      ? "bg-green-500"
                      : "bg-gray-200"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Terminal state indicator */}
      {isTerminal && (
        <div className="mt-3 flex items-center gap-2">
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full",
              stato === "rifiutata" ? "bg-red-100" : "bg-gray-100"
            )}
          >
            {stato === "rifiutata" ? (
              <X className="h-4 w-4 text-red-600" />
            ) : (
              <Ban className="h-4 w-4 text-gray-500" />
            )}
          </div>
          <span
            className={cn(
              "text-sm font-semibold",
              stato === "rifiutata" ? "text-red-600" : "text-gray-500"
            )}
          >
            {PAYMENT_ORDER_STATUS_LABELS[stato]}
          </span>
        </div>
      )}
    </div>
  );
}
