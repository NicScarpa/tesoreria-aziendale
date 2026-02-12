export type ReconciliationStatus = "unreconciled" | "partially_reconciled" | "reconciled";
export type ExpectedTransactionType = "expected_inflow" | "expected_outflow";
export type ExpectedDocumentType =
  | "sales_invoice"
  | "purchase_invoice"
  | "credit_note"
  | "debit_note"
  | "salary"
  | "tax"
  | "other";
export type ExpectedTransactionStatus = "open" | "partially_matched" | "matched" | "cancelled" | "expired";
export type ExpectedTransactionSource = "manual" | "invoice_import" | "schedule" | "sdi_sync";
export type ReconciliationType = "automatic" | "manual" | "suggested";
export type ReconciliationLineType = "transaction_match" | "expected_match" | "adjustment";

export interface ExpectedTransaction {
  id: string;
  company_id: string;
  bank_account_id: string | null;
  counterpart_name: string | null;
  counterpart_iban: string | null;
  type: ExpectedTransactionType;
  expected_amount: number;
  currency: string;
  due_date: string;
  description: string | null;
  reference_number: string | null;
  document_type: ExpectedDocumentType;
  status: ExpectedTransactionStatus;
  matched_amount: number;
  schedule_id: string | null;
  source: ExpectedTransactionSource;
  created_at: string;
  updated_at: string;
}

export interface ExpectedTransactionListResponse {
  items: ExpectedTransaction[];
  total: number;
  page: number;
  page_size: number;
  total_expected_amount: number;
  total_matched_amount: number;
}

export interface ReconciliationLine {
  id: string;
  reconciliation_id: string;
  transaction_id: string | null;
  expected_transaction_id: string | null;
  matched_amount: number;
  line_type: ReconciliationLineType;
  notes: string | null;
  created_at: string;
}

export interface Reconciliation {
  id: string;
  company_id: string;
  type: string;
  status: string;
  reconciliation_date: string;
  confirmed_by_user_id: string | null;
  confirmed_at: string | null;
  notes: string | null;
  matching_score: number | null;
  applied_rule: string | null;
  lines: ReconciliationLine[];
  created_at: string;
  updated_at: string;
}

export interface ReconciliationListResponse {
  items: Reconciliation[];
  total: number;
  page: number;
  page_size: number;
}

export interface MatchSuggestion {
  transaction_id: string | null;
  expected_transaction_id: string | null;
  score: number;
  match_type: string;
  matched_amount: number;
}

export interface DashboardData {
  unreconciled_transactions: number;
  open_expected: number;
  pending_suggestions: number;
  reconciliation_rate: number;
  expired_expected: number;
  total_unreconciled_amount: number;
  total_open_expected_amount: number;
}

export interface AutoMatchResult {
  total_matches: number;
  confirmed: number;
  suggested: number;
  matches: Reconciliation[];
}

export interface ReconciliationRule {
  id: string;
  company_id: string;
  name: string;
  description: string | null;
  match_amount: boolean;
  amount_tolerance: number;
  match_date: boolean;
  date_tolerance_days: number;
  match_description: boolean;
  match_counterpart: boolean;
  auto_confirm: boolean;
  min_confidence: number;
  priority: number;
  is_active: boolean;
  match_type: string;
  action: string;
  amount_tolerance_override: number | null;
  date_tolerance_override: number | null;
  reference_pattern: string | null;
  require_same_counterpart: boolean;
  times_applied: number;
  last_applied_at: string | null;
  confirmation_rate: number | null;
  created_at: string;
  updated_at: string;
}
