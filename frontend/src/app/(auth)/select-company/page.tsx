"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { Building2 } from "lucide-react";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function SelectCompanyPage() {
  const router = useRouter();
  const { companies, setCurrentCompany } = useAuthStore();

  function handleSelect(company: (typeof companies)[0]) {
    setCurrentCompany(company);
    router.replace("/dashboard");
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40">
      <div className="w-full max-w-lg space-y-4 px-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Seleziona azienda</h1>
          <p className="mt-1 text-muted-foreground">
            Scegli l&apos;azienda con cui lavorare.
          </p>
        </div>
        <div className="space-y-3">
          {companies.map((c) => (
            <Card
              key={c.company_id}
              className="cursor-pointer transition-colors hover:bg-accent"
              onClick={() => handleSelect(c)}
            >
              <CardHeader className="flex-row items-center gap-4 space-y-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <Building2 className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-base">{c.company_name}</CardTitle>
                  <CardDescription className="capitalize">{c.role}</CardDescription>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
