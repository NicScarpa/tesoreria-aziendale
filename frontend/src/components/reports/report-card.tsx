"use client";

import {
  Wallet, List, ArrowUpDown, CheckCircle, Calendar, Clock,
  TrendingUp, CreditCard, Users, FileText, Star, StarOff,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { ReportDefinition, ReportType } from "@/types/report";
import { REPORT_FORMAT_LABELS } from "@/types/report";

const ICON_MAP: Record<ReportType, typeof FileText> = {
  saldi_conti: Wallet,
  movimenti: List,
  entrate_uscite: ArrowUpDown,
  riconciliazione: CheckCircle,
  scadenzario: Calendar,
  aging: Clock,
  cash_flow: TrendingUp,
  pagamenti: CreditCard,
  controparte: Users,
  personalizzato: FileText,
};

interface ReportCardProps {
  definition: ReportDefinition;
  onGenerate: (definition: ReportDefinition) => void;
  onTogglePreferito: (definition: ReportDefinition) => void;
}

export function ReportCard({ definition, onGenerate, onTogglePreferito }: ReportCardProps) {
  const Icon = ICON_MAP[definition.tipo] || FileText;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-primary/10 p-2">
              <Icon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-sm font-medium">{definition.nome}</CardTitle>
              {definition.is_system && (
                <Badge variant="secondary" className="mt-0.5 text-[10px]">
                  Sistema
                </Badge>
              )}
            </div>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onTogglePreferito(definition);
            }}
            className="text-muted-foreground hover:text-yellow-500 transition-colors"
          >
            {definition.is_preferito ? (
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            ) : (
              <StarOff className="h-4 w-4" />
            )}
          </button>
        </div>
      </CardHeader>
      <CardContent>
        {definition.descrizione && (
          <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
            {definition.descrizione}
          </p>
        )}
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            Formato: {REPORT_FORMAT_LABELS[definition.formato_default]}
          </span>
          <Button size="sm" onClick={() => onGenerate(definition)}>
            Genera
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
