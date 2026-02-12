"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  PAYMENT_STATUS_COLORS,
  PAYMENT_ORDER_STATUS_LABELS,
  type PaymentOrderStatus,
} from "@/types/payment";

interface PaymentStatusBadgeProps {
  stato: PaymentOrderStatus;
}

export function PaymentStatusBadge({ stato }: PaymentStatusBadgeProps) {
  return (
    <Badge
      variant="secondary"
      className={cn(
        "hover:bg-opacity-80",
        PAYMENT_STATUS_COLORS[stato]
      )}
    >
      {PAYMENT_ORDER_STATUS_LABELS[stato]}
    </Badge>
  );
}
