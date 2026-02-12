export type FlowDirection = "inflow" | "outflow";
export type TransactionStatus = "pending" | "booked" | "rejected";
export type TransactionType =
  | "credit_transfer"
  | "direct_debit"
  | "card_payment"
  | "cash"
  | "fee"
  | "interest"
  | "tax"
  | "other";
export type CategorizationSource = "manual" | "automatic" | "rule" | "import";
export type BatchStatus = "pending" | "processing" | "completed" | "failed" | "partial";

export interface Allocation {
  id: string;
  transaction_id: string;
  category_id: string;
  subcategory_id: string | null;
  amount: number;
  currency: string;
  percentage: number | null;
  category?: Category | null;
  subcategory?: Subcategory | null;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  company_id: string;
  bank_account_id: string;
  amount: number;
  currency: string;
  direction: FlowDirection;
  transaction_date: string;
  value_date: string | null;
  description: string | null;
  remittance_info: string | null;
  transaction_type: TransactionType;
  category_id: string | null;
  subcategory_id: string | null;
  categorization_source: CategorizationSource | null;
  counterpart_id: string | null;
  counterpart_name: string | null;
  counterpart_iban: string | null;
  status: TransactionStatus;
  verified: boolean;
  provider_transaction_id: string | null;
  hidden_at: string | null;
  notes: string | null;
  import_batch_id: string | null;
  reconciliation_status: ReconciliationStatus | null;
  reconciliation_id: string | null;
  category?: Category | null;
  subcategory?: Subcategory | null;
  allocations: Allocation[];
  bank_account_nickname: string | null;
  created_at: string;
  updated_at: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
}

export interface TransactionTotals {
  positive: number;
  negative: number;
}

export interface TransactionMetadata {
  total: number;
  totals: TransactionTotals;
  total_uncategorized: number;
}

export interface ImportBatch {
  id: string;
  status: BatchStatus;
  filename: string | null;
  total_records: number;
  imported_records: number;
  skipped_records: number;
  error_records: number;
  errors: Array<{ row: number; error: string }>;
  started_at: string | null;
  completed_at: string | null;
}

// Re-export for convenience
import type { Category, Subcategory } from "./category";
import type { ReconciliationStatus } from "./reconciliation";
export type { Category, Subcategory };
