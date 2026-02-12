"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { InstitutionInfo } from "@/types/integration";

interface Props {
  institutions: InstitutionInfo[];
  selected: InstitutionInfo | null;
  onSelect: (inst: InstitutionInfo) => void;
}

export function BankInstitutionPicker({ institutions, selected, onSelect }: Props) {
  const [search, setSearch] = useState("");
  const filtered = institutions.filter((i) =>
    i.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-3">
      <Input placeholder="Cerca banca..." value={search} onChange={(e) => setSearch(e.target.value)} />
      <ScrollArea className="h-[300px]">
        <div className="grid grid-cols-2 gap-2">
          {filtered.map((inst) => (
            <Button
              key={inst.id}
              variant={selected?.id === inst.id ? "default" : "outline"}
              className="justify-start h-auto py-2 px-3"
              onClick={() => onSelect(inst)}
            >
              {inst.logo_url && <img src={inst.logo_url} alt="" className="h-5 w-5 mr-2 rounded" />}
              <span className="text-sm truncate">{inst.name}</span>
            </Button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
