"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Landmark,
  ArrowLeftRight,
  FileText,
  CalendarClock,
  CreditCard,
  TrendingUp,
  Link2,
  BarChart3,
  Plug,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import api from "@/lib/api";

const menuItems = [
  { label: "Dashboard", shortLabel: "Home", href: "/dashboard", icon: LayoutDashboard },
  { label: "Conti", shortLabel: "Conti", href: "/conti", icon: Landmark },
  { label: "Movimenti", shortLabel: "Movim.", href: "/movimenti", icon: ArrowLeftRight },
  { label: "Fatture", shortLabel: "Fatture", href: "/fatture", icon: FileText },
  { label: "Scadenzario", shortLabel: "Scad.", href: "/scadenzario", icon: CalendarClock, badgeKey: "scadute" as const },
  { label: "Pagamenti", shortLabel: "Pagam.", href: "/pagamenti", icon: CreditCard, badgeKey: "da_approvare" as const },
  { label: "Cash Flow", shortLabel: "Cashflow", href: "/cash-flow", icon: TrendingUp, badgeKey: "cashflow_alerts" as const },
  { label: "Riconciliazione", shortLabel: "Riconc.", href: "/riconciliazione", icon: Link2 },
  { label: "Report", shortLabel: "Report", href: "/report", icon: BarChart3 },
  { label: "Integrazioni", shortLabel: "Integ.", href: "/integrazioni", icon: Plug, badgeKey: "integrazioni" as const },
  { label: "Impostazioni", shortLabel: "Impost.", href: "/impostazioni", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const currentCompany = useAuthStore((s) => s.currentCompany);
  const [scaduteCount, setScaduteCount] = useState(0);
  const [daApprovareCount, setDaApprovareCount] = useState(0);
  const [cashflowAlertCount, setCashflowAlertCount] = useState(0);
  const [integrazioniCount, setIntegrazioniCount] = useState(0);

  useEffect(() => {
    let mounted = true;

    const fetchCount = async () => {
      try {
        const [schedResp, payResp, cfResp, intResp] = await Promise.all([
          api.get<{ totale_scadute: number }>("/schedules/summary"),
          api.get<{ totale_da_approvare: number }>("/payments/summary"),
          api.get<{ count: number }>("/cashflow/alerts/count"),
          api.get<{ total: number }>("/integrations/alerts-count").catch(() => ({ data: { total: 0 } })),
        ]);
        if (mounted) {
          setScaduteCount(schedResp.data.totale_scadute);
          setDaApprovareCount(payResp.data.totale_da_approvare);
          setCashflowAlertCount(cfResp.data.count);
          setIntegrazioniCount(intResp.data.total);
        }
      } catch {
        // Non-critical
      }
    };

    fetchCount();

    const handleVisibility = () => {
      if (document.visibilityState === "visible") fetchCount();
    };
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      mounted = false;
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, []);

  const companyInitials = currentCompany?.company_name
    ? currentCompany.company_name
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((chunk) => chunk[0])
        .join("")
        .toUpperCase()
    : "WS";

  return (
    <aside className="flex h-full w-[88px] flex-col border-r border-[#f2f2f2] bg-white">
      <div className="flex h-[72px] items-center justify-center border-b border-[#f2f2f2]">
        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-[#e5e4e3] bg-[#1a1a1a] text-[14px] font-semibold text-white">
          SB
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 px-1 py-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname?.startsWith(item.href);
          const badgeCount =
            item.badgeKey === "scadute" ? scaduteCount :
            item.badgeKey === "da_approvare" ? daApprovareCount :
            item.badgeKey === "cashflow_alerts" ? cashflowAlertCount :
            item.badgeKey === "integrazioni" ? integrazioniCount : 0;
          const showBadge = badgeCount > 0;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              className={cn(
                "group relative flex h-[70px] flex-col items-center justify-center gap-1 rounded-[8px] px-1 text-center text-[11px] leading-[14px] font-medium transition-colors",
                isActive
                  ? "bg-[#f5f6ff] text-[#6672ff]"
                  : "text-[#1a1a1a] hover:bg-[#f9f9f9]"
              )}
            >
              <Icon className="h-5 w-5" />
              <span className="line-clamp-2">{item.shortLabel}</span>
              {showBadge && (
                <span className="absolute top-2 right-2 flex min-w-[16px] items-center justify-center rounded-full bg-[#f75251] px-1 text-[9px] leading-[14px] font-bold text-white">
                  {badgeCount}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-[#f2f2f2] p-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#1a1a1a] text-[12px] font-semibold text-white">
          {companyInitials}
        </div>
      </div>
    </aside>
  );
}
