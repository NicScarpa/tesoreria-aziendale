"use client";

import { Badge } from "@/components/ui/badge";
import type { SchedulePriority } from "@/types/schedule";
import { PRIORITY_LABELS } from "@/types/schedule";

const PRIORITY_CLASSES: Record<SchedulePriority, string> = {
  bassa: "bg-gray-100 text-gray-600 hover:bg-gray-100",
  normale: "bg-blue-50 text-blue-600 hover:bg-blue-50",
  alta: "bg-orange-100 text-orange-700 hover:bg-orange-100",
  urgente: "bg-red-100 text-red-700 hover:bg-red-100",
};

export function PriorityBadge({ priority }: { priority: SchedulePriority }) {
  if (priority === "normale") return null;
  return (
    <Badge variant="outline" className={PRIORITY_CLASSES[priority]}>
      {PRIORITY_LABELS[priority]}
    </Badge>
  );
}
