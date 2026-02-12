"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Building2,
  Wallet,
  SlidersHorizontal,
  Landmark,
  Users,
  Puzzle,
  Bell,
  Tag,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const settingsMenu = [
  { label: "Dati aziendali", href: "/impostazioni/azienda", icon: Building2 },
  { label: "Tesoreria", href: "/impostazioni/tesoreria", icon: Wallet },
  { label: "Formato", href: "/impostazioni/preferenze", icon: SlidersHorizontal },
  { label: "Banche", href: "/impostazioni/banche", icon: Landmark },
  { label: "Team", href: "/impostazioni/team", icon: Users },
  { label: "Categorie", href: "/impostazioni/categorie", icon: Tag },
  { label: "Regole", href: "/impostazioni/regole", icon: Zap },
  { label: "Moduli", href: "/impostazioni/moduli", icon: Puzzle },
  { label: "Notifiche", href: "/impostazioni/notifiche", icon: Bell },
];

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="flex gap-6">
      <nav className="w-56 shrink-0 space-y-1">
        <h2 className="mb-4 text-lg font-semibold">Impostazioni</h2>
        {settingsMenu.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
}
