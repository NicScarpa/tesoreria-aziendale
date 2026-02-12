"use client";

import { useRouter } from "next/navigation";
import { Upload, Calendar, CreditCard, Bell } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { it } from "date-fns/locale";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AttivitaRecenteItem } from "@/types/dashboard";

const TYPE_ICONS = {
  import: Upload,
  schedule: Calendar,
  payment: CreditCard,
  alert: Bell,
};

const TYPE_COLORS = {
  import: "bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400",
  schedule: "bg-purple-100 text-purple-600 dark:bg-purple-950 dark:text-purple-400",
  payment: "bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400",
  alert: "bg-amber-100 text-amber-600 dark:bg-amber-950 dark:text-amber-400",
};

interface Props {
  data: AttivitaRecenteItem[];
}

export function ActivityTimeline({ data }: Props) {
  const router = useRouter();

  if (data.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">Attivita Recenti</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative space-y-3">
          {data.map((item, index) => {
            const Icon = TYPE_ICONS[item.tipo] || Bell;
            const colorClass = TYPE_COLORS[item.tipo] || TYPE_COLORS.alert;

            return (
              <button
                key={index}
                onClick={() => item.link && router.push(item.link)}
                className="flex w-full items-start gap-3 rounded-lg p-2 hover:bg-muted/50 transition-colors text-left"
              >
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${colorClass}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm truncate">{item.descrizione}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(item.data), { addSuffix: true, locale: it })}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
