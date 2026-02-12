"use client";

import type { DashboardData, DashboardWidget, WidgetType } from "@/types/dashboard";
import { BalanceSummaryWidget } from "./BalanceSummaryWidget";
import { CashFlowMiniWidget } from "./CashFlowMiniWidget";
import { IncomeExpenseWidget } from "./IncomeExpenseWidget";
import { ScheduleWidget } from "./ScheduleWidget";
import { ReconciliationDonut } from "./ReconciliationDonut";
import { PaymentPendingWidget } from "./PaymentPendingWidget";
import { AlertWidget } from "./AlertWidget";
import { ActivityTimeline } from "./ActivityTimeline";
import { QuickActionsWidget } from "./QuickActionsWidget";

interface Props {
  data: DashboardData;
  widgets: DashboardWidget[];
}

export function DashboardGrid({ data, widgets }: Props) {
  const visibleWidgets = widgets
    .filter((w) => w.visibile)
    .sort((a, b) => a.posizione - b.posizione);

  // Separate full-width widgets from grid widgets
  const fullWidthTypes: WidgetType[] = ["saldo_totale", "cash_flow_mini"];
  const fullWidthWidgets = visibleWidgets.filter((w) => fullWidthTypes.includes(w.widget_type));
  const gridWidgets = visibleWidgets.filter((w) => !fullWidthTypes.includes(w.widget_type));

  const renderWidget = (widget: DashboardWidget) => {
    const key = widget.widget_type;

    switch (key) {
      case "saldo_totale":
        return <BalanceSummaryWidget data={data.saldi} />;
      case "cash_flow_mini":
        return <CashFlowMiniWidget data={data.cash_flow} />;
      case "entrate_uscite":
        return <IncomeExpenseWidget data={data.entrate_uscite} />;
      case "scadenze":
        return <ScheduleWidget data={data.scadenze} />;
      case "riconciliazione":
        return <ReconciliationDonut data={data.riconciliazione} />;
      case "pagamenti_pendenti":
        return <PaymentPendingWidget data={data.pagamenti} />;
      case "alert":
        return <AlertWidget data={data.alert} />;
      case "attivita_recenti":
        return <ActivityTimeline data={data.attivita_recenti} />;
      case "azioni_rapide":
        return <QuickActionsWidget data={data.quick_actions} />;
      case "saldi_per_conto":
        // Already shown in BalanceSummaryWidget
        return null;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Full-width widgets */}
      {fullWidthWidgets.map((widget) => (
        <div key={widget.widget_type}>
          {renderWidget(widget)}
        </div>
      ))}

      {/* Grid widgets */}
      <div className="grid gap-4 md:grid-cols-2">
        {gridWidgets.map((widget) => {
          const rendered = renderWidget(widget);
          if (!rendered) return null;
          return (
            <div key={widget.widget_type}>
              {rendered}
            </div>
          );
        })}
      </div>
    </div>
  );
}
