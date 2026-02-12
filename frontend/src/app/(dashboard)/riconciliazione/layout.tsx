"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { cn } from "@/lib/utils";

const tabs = [
  { label: "Dashboard", href: "/riconciliazione" },
  { label: "Manuale", href: "/riconciliazione/manuale" },
  { label: "Attese", href: "/riconciliazione/expected" },
  { label: "Storico", href: "/riconciliazione/storico" },
  { label: "Regole", href: "/riconciliazione/regole" },
];

export default function ReconciliationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="space-y-6">
      <nav className="flex border-b">
        {tabs.map((tab) => {
          const isActive =
            tab.href === "/riconciliazione"
              ? pathname === "/riconciliazione"
              : pathname?.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                isActive
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>
      {children}
    </div>
  );
}
