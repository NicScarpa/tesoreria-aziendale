"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import type { BankAccount } from "@/types/bank-account";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { PaymentWizard } from "@/components/payments/wizard/PaymentWizard";

export default function NuovoPagamentoPage() {
  const router = useRouter();

  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadBankAccounts() {
      try {
        const resp = await api.get<BankAccount[]>("/bank-accounts");
        setBankAccounts(resp.data);
      } catch {
        toast.error("Errore nel caricamento dei conti bancari");
      } finally {
        setLoading(false);
      }
    }
    loadBankAccounts();
  }, []);

  const handleComplete = (orderId: string) => {
    toast.success("Ordine di pagamento creato");
    router.push(`/pagamenti/${orderId}`);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => router.push("/pagamenti")}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            Pagamenti
          </Button>
        </div>
        <PageHeader
          title="Nuovo Pagamento"
          description="Crea un nuovo ordine di pagamento"
        />
        <LoadingState />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/pagamenti")}>
          <ArrowLeft className="h-4 w-4 mr-1" />
          Pagamenti
        </Button>
      </div>

      <PageHeader
        title="Nuovo Pagamento"
        description="Crea un nuovo ordine di pagamento"
      />

      <PaymentWizard
        bankAccounts={bankAccounts}
        onComplete={handleComplete}
      />
    </div>
  );
}
