"use client";

import { cn } from "@/lib/utils";
import type { ConfidenceLevel } from "@/types/cash-flow";
import { CONFIDENCE_LABELS, CONFIDENCE_COLORS } from "@/types/cash-flow";

interface ConfidenceBadgeProps {
  level: ConfidenceLevel;
  className?: string;
}

export function ConfidenceBadge({ level, className }: ConfidenceBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        CONFIDENCE_COLORS[level],
        className
      )}
    >
      {CONFIDENCE_LABELS[level]}
    </span>
  );
}
