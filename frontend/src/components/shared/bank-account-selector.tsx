"use client";

import { useState, useEffect } from "react";
import { Check, ChevronsUpDown, Landmark } from "lucide-react";
import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import type { BankAccount } from "@/types/bank-account";

interface Props {
  value: string | null;
  onChange: (accountId: string | null) => void;
  placeholder?: string;
  className?: string;
}

export function BankAccountSelector({
  value,
  onChange,
  placeholder = "Seleziona conto...",
  className,
}: Props) {
  const [open, setOpen] = useState(false);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);

  useEffect(() => {
    api
      .get<BankAccount[]>("/bank-accounts")
      .then((res) => setAccounts(res.data))
      .catch(() => {});
  }, []);

  const selected = accounts.find((a) => a.id === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("justify-between", className)}
        >
          {selected ? (
            <span className="flex items-center gap-2 truncate">
              <span
                className="h-3 w-3 rounded-full shrink-0"
                style={{ backgroundColor: selected.color || "#6b7280" }}
              />
              {selected.nickname || "Conto"}
            </span>
          ) : (
            <span className="flex items-center gap-2 text-muted-foreground">
              <Landmark className="h-4 w-4" />
              {placeholder}
            </span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[300px] p-0">
        <Command>
          <CommandInput placeholder="Cerca conto..." />
          <CommandList>
            <CommandEmpty>Nessun conto trovato.</CommandEmpty>
            <CommandGroup>
              {accounts.map((account) => (
                <CommandItem
                  key={account.id}
                  value={account.nickname || account.iban || account.id}
                  onSelect={() => {
                    onChange(account.id === value ? null : account.id);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === account.id ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <span
                    className="h-3 w-3 rounded-full shrink-0 mr-2"
                    style={{ backgroundColor: account.color || "#6b7280" }}
                  />
                  <div className="flex flex-col min-w-0">
                    <span className="truncate text-sm">
                      {account.nickname || "Conto"}
                    </span>
                    {account.iban && (
                      <span className="text-xs text-muted-foreground font-mono truncate">
                        {account.iban}
                      </span>
                    )}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
