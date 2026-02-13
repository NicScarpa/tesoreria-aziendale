"use client";

import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { Lock, Plus, Upload, FileText, FileUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";

const tabs = [
  { label: "Situazione", href: "/fatture", disabled: false },
  { label: "Ricevute", href: "/fatture/ricevute", disabled: false },
  { label: "Emesse", href: "/fatture/emesse", disabled: false },
  { label: "Corrispettivi", href: "/fatture/corrispettivi", disabled: false },
  { label: "DDT", href: "/fatture/ddt", disabled: true },
  { label: "Preventivi", href: "/fatture/preventivi", disabled: true },
];

export default function FattureLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <nav className="inline-flex items-center gap-1 rounded-lg border border-[#e5e4e3] bg-white p-1">
          {tabs.map((tab) => {
            const isActive =
              tab.href === "/fatture"
                ? pathname === "/fatture"
                : pathname?.startsWith(tab.href);

            if (tab.disabled) {
              return (
                <span
                  key={tab.href}
                  className="flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium text-muted-foreground/50 cursor-not-allowed"
                >
                  {tab.label}
                  <Lock className="h-3 w-3" />
                </span>
              );
            }

            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  "rounded-md px-4 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-[#6672ff] text-white"
                    : "text-foreground hover:bg-muted"
                )}
              >
                {tab.label}
              </Link>
            );
          })}
        </nav>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="default" size="icon" className="h-[38px] w-[38px] rounded-full">
              <Plus className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-72 p-2">
            <DropdownMenuItem
              className="p-3 cursor-pointer"
              onClick={() => router.push("/fatture/import")}
            >
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-teal-50">
                  <Upload className="h-5 w-5 text-teal-600" />
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">Carica fatture</span>
                  <span className="text-xs text-muted-foreground">Importa più fatture in formato XML/P7M</span>
                </div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem
              className="p-3 cursor-pointer"
              onClick={() => router.push("/fatture/emesse")}
            >
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-50">
                  <FileText className="h-5 w-5" style={{ color: "#6672ff" }} />
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">Emetti fattura</span>
                  <span className="text-xs text-muted-foreground">Crea e invia una fattura elettronica</span>
                </div>
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem
              className="p-3 cursor-pointer"
              onClick={() => toast.info("Funzionalità in arrivo")}
            >
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-pink-50">
                  <FileUp className="h-5 w-5" style={{ color: "#f9567c" }} />
                </div>
                <div className="flex flex-col">
                  <span className="text-sm font-medium">Autofattura tramite PDF</span>
                  <span className="text-xs text-muted-foreground">Crea e emetti fatture in modo semplice dall&apos;autofattura</span>
                </div>
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      {children}
    </div>
  );
}
