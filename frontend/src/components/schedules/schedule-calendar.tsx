"use client";

import { useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ScheduleCalendarDay } from "@/types/schedule";
import { SCHEDULE_TYPE_LABELS } from "@/types/schedule";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(value);
}

interface ScheduleCalendarProps {
  days: ScheduleCalendarDay[];
  month: number;
  year: number;
  onDayClick?: (day: ScheduleCalendarDay) => void;
}

export function ScheduleCalendar({ days, month, year, onDayClick }: ScheduleCalendarProps) {
  const calendarGrid = useMemo(() => {
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);
    const startDow = (firstDay.getDay() + 6) % 7; // Monday = 0
    const totalDays = lastDay.getDate();

    const dayMap = new Map<string, ScheduleCalendarDay>();
    for (const d of days) {
      dayMap.set(d.data, d);
    }

    const cells: { day: number | null; date: string | null; data: ScheduleCalendarDay | null }[] = [];

    // Empty cells before first day
    for (let i = 0; i < startDow; i++) {
      cells.push({ day: null, date: null, data: null });
    }

    for (let d = 1; d <= totalDays; d++) {
      const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      cells.push({ day: d, date: dateStr, data: dayMap.get(dateStr) || null });
    }

    return cells;
  }, [days, month, year]);

  const weekDays = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"];
  const today = new Date().toISOString().split("T")[0];

  return (
    <div>
      <div className="grid grid-cols-7 gap-px bg-gray-200 rounded-lg overflow-hidden">
        {weekDays.map((wd) => (
          <div key={wd} className="bg-gray-50 p-2 text-center text-xs font-medium text-muted-foreground">
            {wd}
          </div>
        ))}
        {calendarGrid.map((cell, i) => (
          <div
            key={i}
            className={cn(
              "bg-white min-h-[80px] p-1.5 text-sm",
              !cell.day && "bg-gray-50",
              cell.date === today && "ring-2 ring-primary ring-inset",
              cell.data && "cursor-pointer hover:bg-gray-50",
            )}
            onClick={() => cell.data && onDayClick?.(cell.data)}
          >
            {cell.day && (
              <>
                <span className={cn("text-xs", cell.date === today && "font-bold text-primary")}>
                  {cell.day}
                </span>
                {cell.data && (
                  <div className="mt-0.5 space-y-0.5">
                    {cell.data.scadenze.slice(0, 3).map((s) => (
                      <div
                        key={s.id}
                        className={cn(
                          "text-[10px] leading-tight px-1 py-0.5 rounded truncate",
                          s.tipo === "attiva" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
                        )}
                      >
                        {formatCurrency(s.importo_residuo)}
                      </div>
                    ))}
                    {cell.data.scadenze.length > 3 && (
                      <span className="text-[10px] text-muted-foreground">
                        +{cell.data.scadenze.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
