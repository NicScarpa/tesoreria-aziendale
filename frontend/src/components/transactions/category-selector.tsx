"use client";

import { useState } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
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
import type { Category } from "@/types/category";

interface Props {
  categories: Category[];
  value: string | null;
  onChange: (categoryId: string | null) => void;
  className?: string;
}

export function CategorySelector({ categories, value, onChange, className }: Props) {
  const [open, setOpen] = useState(false);

  const selected = categories.find((c) => c.id === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("justify-between w-full", className)}
        >
          {selected ? (
            <span className="flex items-center gap-2 truncate">
              <span
                className="h-3 w-3 rounded-full shrink-0"
                style={{ backgroundColor: selected.color }}
              />
              {selected.name}
            </span>
          ) : (
            <span className="text-muted-foreground">Seleziona categoria...</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[250px] p-0">
        <Command>
          <CommandInput placeholder="Cerca categoria..." />
          <CommandList>
            <CommandEmpty>Nessuna categoria trovata.</CommandEmpty>
            <CommandGroup>
              <CommandItem
                value="__none__"
                onSelect={() => {
                  onChange(null);
                  setOpen(false);
                }}
              >
                <Check
                  className={cn("mr-2 h-4 w-4", !value ? "opacity-100" : "opacity-0")}
                />
                <span className="text-muted-foreground">Nessuna categoria</span>
              </CommandItem>
              {categories.map((cat) => (
                <CommandItem
                  key={cat.id}
                  value={cat.name}
                  onSelect={() => {
                    onChange(cat.id === value ? null : cat.id);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === cat.id ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <span
                    className="h-3 w-3 rounded-full shrink-0 mr-2"
                    style={{ backgroundColor: cat.color }}
                  />
                  {cat.name}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
