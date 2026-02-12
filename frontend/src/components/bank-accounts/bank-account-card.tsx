"use client";

import Link from "next/link";
import { MoreHorizontal, Eye, EyeOff, Pencil, Trash2, Star, Plug } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { maskIBAN } from "@/lib/iban";
import type { BankAccount } from "@/types/bank-account";

function formatCurrency(value: number | null, currency = "EUR"): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency }).format(value);
}

const STATUS_LABELS: Record<string, string> = {
  active: "Attivo",
  inactive: "Inattivo",
  hidden: "Nascosto",
  closed: "Chiuso",
  blocked: "Bloccato",
};

const STATUS_VARIANTS: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  active: "default",
  inactive: "secondary",
  hidden: "outline",
  closed: "destructive",
  blocked: "destructive",
};

const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  checking: "Conto corrente",
  savings: "Risparmio",
  cash: "Cassa",
  credit_card: "Carta di credito",
  loan: "Prestito",
  other: "Altro",
};

interface Props {
  account: BankAccount;
  onEdit?: (account: BankAccount) => void;
  onHide?: (account: BankAccount) => void;
  onDelete?: (account: BankAccount) => void;
  onUpdateBalance?: (account: BankAccount) => void;
  canEdit?: boolean;
  canDelete?: boolean;
}

export function BankAccountCard({
  account,
  onEdit,
  onHide,
  onDelete,
  onUpdateBalance,
  canEdit = false,
  canDelete = false,
}: Props) {
  return (
    <Card className="relative overflow-hidden">
      <div
        className="absolute left-0 top-0 bottom-0 w-1"
        style={{ backgroundColor: account.color || "#6b7280" }}
      />
      <CardContent className="pt-6 pl-5">
        <div className="flex items-start justify-between">
          <Link href={`/conti/${account.id}`} className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold truncate">
                {account.nickname || "Conto senza nome"}
              </h3>
              {account.is_default && (
                <Star className="h-4 w-4 text-amber-500 fill-amber-500 shrink-0" />
              )}
            </div>
            {account.iban && (
              <p className="text-sm text-muted-foreground font-mono">
                {maskIBAN(account.iban)}
              </p>
            )}
            {account.bank_name && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {account.bank_name}
              </p>
            )}
          </Link>
          {(canEdit || canDelete) && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {canEdit && (
                  <>
                    <DropdownMenuItem onClick={() => onEdit?.(account)}>
                      <Pencil className="h-4 w-4 mr-2" />
                      Modifica
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onUpdateBalance?.(account)}>
                      <TrendingUpIcon className="h-4 w-4 mr-2" />
                      Aggiorna saldo
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onHide?.(account)}>
                      {account.hidden_at ? (
                        <>
                          <Eye className="h-4 w-4 mr-2" />
                          Mostra
                        </>
                      ) : (
                        <>
                          <EyeOff className="h-4 w-4 mr-2" />
                          Nascondi
                        </>
                      )}
                    </DropdownMenuItem>
                  </>
                )}
                {canDelete && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      variant="destructive"
                      onClick={() => onDelete?.(account)}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Elimina
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        <div className="mt-4 flex items-end justify-between">
          <div>
            <p className="text-xs text-muted-foreground">Saldo contabile</p>
            <p className="text-xl font-bold">
              {formatCurrency(account.current_balance, account.currency)}
            </p>
            {account.available_balance !== null && account.available_balance !== account.current_balance && (
              <p className="text-xs text-muted-foreground">
                Disponibile: {formatCurrency(account.available_balance, account.currency)}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {account.bank_connection_id && (
              <Badge variant="outline" className="text-xs gap-1 text-emerald-700 border-emerald-300 bg-emerald-50">
                <Plug className="h-3 w-3" />
                Open Banking
              </Badge>
            )}
            {account.account_type && (
              <Badge variant="outline" className="text-xs">
                {ACCOUNT_TYPE_LABELS[account.account_type] || account.account_type}
              </Badge>
            )}
            <Badge variant={STATUS_VARIANTS[account.status] || "outline"}>
              {STATUS_LABELS[account.status] || account.status}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Simple inline icon to avoid extra import
function TrendingUpIcon({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
      <polyline points="16 7 22 7 22 13" />
    </svg>
  );
}
