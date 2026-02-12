"use client";

import { useRouter } from "next/navigation";
import {
  CheckCircle, AlertTriangle, CreditCard, Upload, Bell, Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { QuickActionItem } from "@/types/dashboard";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  "check-circle": CheckCircle,
  "alert-triangle": AlertTriangle,
  "credit-card": CreditCard,
  upload: Upload,
  bell: Bell,
  zap: Zap,
};

interface Props {
  data: QuickActionItem[];
}

export function QuickActionsWidget({ data }: Props) {
  const router = useRouter();

  if (data.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <Zap className="h-4 w-4" />
          Azioni Rapide
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {data.map((action) => {
            const Icon = ICON_MAP[action.icona] || Zap;

            return (
              <Button
                key={action.azione}
                variant="outline"
                size="sm"
                className="w-full justify-start gap-2 text-left h-auto py-2"
                onClick={() => router.push(action.link)}
              >
                <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="text-sm font-medium">{action.titolo}</p>
                  <p className="text-xs text-muted-foreground truncate">{action.descrizione}</p>
                </div>
              </Button>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
