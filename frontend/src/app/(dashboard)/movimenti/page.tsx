"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Upload, RefreshCw, FileSpreadsheet } from "lucide-react";
import { ExportButton } from "@/components/shared/export-button";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { TransactionMetadataBar } from "@/components/transactions/transaction-metadata-bar";
import {
  TransactionFiltersBar,
  defaultFilters,
  type TransactionFilters,
} from "@/components/transactions/transaction-filters";
import { TransactionTable } from "@/components/transactions/transaction-table";
import { TransactionDetailSheet } from "@/components/transactions/transaction-detail-sheet";
import { CSVImportWizard } from "@/components/transactions/csv-import-wizard";
import type { Transaction, TransactionListResponse, TransactionMetadata } from "@/types/transaction";
import type { Category } from "@/types/category";

export default function MovimentiPage() {
  const searchParams = useSearchParams();

  const { currentCompany } = useAuthStore();
  const userRole = currentCompany?.role;
  const canEdit = userRole === "owner" || userRole === "admin" || userRole === "editor";
  const isAdmin = userRole === "owner" || userRole === "admin";

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [metadata, setMetadata] = useState<TransactionMetadata | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [loading, setLoading] = useState(true);
  const [metadataLoading, setMetadataLoading] = useState(true);

  const [filters, setFilters] = useState<TransactionFilters>(() => {
    const f = { ...defaultFilters };
    const accountId = searchParams.get("bank_account_id");
    if (accountId) f.bank_account_id = accountId;
    return f;
  });

  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);

  const buildParams = useCallback(
    (forMetadata = false) => {
      const params = new URLSearchParams();
      if (filters.bank_account_id) params.set("bank_account_id", filters.bank_account_id);
      if (filters.date_from) params.set("date_from", filters.date_from);
      if (filters.date_to) params.set("date_to", filters.date_to);
      if (filters.amount_min) params.set("amount_min", filters.amount_min);
      if (filters.amount_max) params.set("amount_max", filters.amount_max);
      if (filters.direction) params.set("direction", filters.direction);
      if (filters.category_id) params.set("category_id", filters.category_id);
      if (filters.search) params.set("search", filters.search);
      if (filters.status) params.set("status", filters.status);
      if (filters.uncategorized) params.set("uncategorized", filters.uncategorized);
      if (filters.verified) params.set("verified", filters.verified);
      if (filters.counterpart_name) params.set("counterpart_name", filters.counterpart_name);
      if (!forMetadata) {
        params.set("page", page.toString());
        params.set("page_size", pageSize.toString());
      }
      return params.toString();
    },
    [filters, page, pageSize]
  );

  const loadTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await api.get<TransactionListResponse>(`/transactions?${buildParams()}`);
      setTransactions(resp.data.items);
      setTotal(resp.data.total);
    } catch {
      toast.error("Errore nel caricamento dei movimenti");
    } finally {
      setLoading(false);
    }
  }, [buildParams]);

  const loadMetadata = useCallback(async () => {
    setMetadataLoading(true);
    try {
      const resp = await api.get<TransactionMetadata>(`/transactions/metadata?${buildParams(true)}`);
      setMetadata(resp.data);
    } catch {
      // Non-critical
    } finally {
      setMetadataLoading(false);
    }
  }, [buildParams]);

  const loadCategories = useCallback(async () => {
    try {
      const resp = await api.get<Category[]>("/categories");
      setCategories(resp.data);
    } catch {
      // Non-critical
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    loadTransactions();
    loadMetadata();
  }, [loadTransactions, loadMetadata]);

  const reload = () => {
    loadTransactions();
    loadMetadata();
  };

  const handleToggleVerified = async (tx: Transaction) => {
    try {
      await api.patch(`/transactions/${tx.id}/verify`);
      reload();
    } catch {
      toast.error("Errore nella verifica");
    }
  };

  const handleRecategorize = async () => {
    try {
      const resp = await api.post("/transactions/recategorize");
      toast.success(`${resp.data.categorized_count} movimenti categorizzati`);
      reload();
    } catch {
      toast.error("Errore nella ricategorizzazione");
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Movimenti"
        description="Gestione movimenti bancari"
        actions={
          <div className="flex gap-2">
            {isAdmin && (
              <Button variant="outline" size="sm" onClick={handleRecategorize}>
                <RefreshCw className="h-4 w-4 mr-1" />
                Ricategorizza
              </Button>
            )}
            <ExportButton reportType="movimenti" label="Esporta" />
            {canEdit && (
              <>
                <Button size="sm" variant="outline" asChild>
                  <Link href="/integrazioni/cbi-sepa">
                    <FileSpreadsheet className="h-4 w-4 mr-1" />
                    Importa SEPA
                  </Link>
                </Button>
                <Button size="sm" onClick={() => setImportOpen(true)}>
                  <Upload className="h-4 w-4 mr-1" />
                  Importa CSV
                </Button>
              </>
            )}
          </div>
        }
      />

      <TransactionMetadataBar metadata={metadata} loading={metadataLoading} />

      <TransactionFiltersBar
        filters={filters}
        onChange={(f) => {
          setFilters(f);
          setPage(1);
        }}
        categories={categories}
      />

      {loading ? (
        <LoadingState />
      ) : (
        <>
          <TransactionTable
            transactions={transactions}
            onSelect={(tx) => {
              setSelectedTx(tx);
              setDetailOpen(true);
            }}
            onToggleVerified={canEdit ? handleToggleVerified : undefined}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {total} moviment{total === 1 ? "o" : "i"} totali
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  Precedente
                </Button>
                <span className="flex items-center text-sm px-2">
                  Pagina {page} di {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                >
                  Successiva
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      <TransactionDetailSheet
        transaction={selectedTx}
        open={detailOpen}
        onOpenChange={setDetailOpen}
        categories={categories}
        onUpdated={reload}
      />

      <CSVImportWizard
        open={importOpen}
        onOpenChange={setImportOpen}
        onImported={reload}
      />
    </div>
  );
}
