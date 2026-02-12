"use client";

import { Badge } from "@/components/ui/badge";
import type { ScheduleStatus } from "@/types/schedule";
import { SCHEDULE_STATUS_LABELS } from "@/types/schedule";

const STATUS_VARIANTS: Record<ScheduleStatus, "default" | "secondary" | "destructive" | "outline"> = {
  aperta: "default",
  parzialmente_pagata: "secondary",
  pagata: "outline",
  scaduta: "destructive",
  annullata: "secondary",
};

const STATUS_CLASSES: Record<ScheduleStatus, string> = {
  aperta: "bg-blue-100 text-blue-800 hover:bg-blue-100",
  parzialmente_pagata: "bg-amber-100 text-amber-800 hover:bg-amber-100",
  pagata: "bg-green-100 text-green-800 hover:bg-green-100",
  scaduta: "bg-red-100 text-red-800 hover:bg-red-100",
  annullata: "bg-gray-100 text-gray-500 hover:bg-gray-100",
};

export function ScheduleStatusBadge({ status }: { status: ScheduleStatus }) {
  return (
    <Badge variant={STATUS_VARIANTS[status]} className={STATUS_CLASSES[status]}>
      {SCHEDULE_STATUS_LABELS[status]}
    </Badge>
  );
}
