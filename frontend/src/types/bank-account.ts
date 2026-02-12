export type AccountStatus = "active" | "inactive" | "hidden" | "closed" | "blocked";
export type AccountType = "checking" | "savings" | "cash" | "credit_card" | "loan" | "other";
export type BalanceSource = "manual" | "open_banking" | "import" | "calculated";
export type AccessLevel = "read" | "write" | "admin";

export interface BankAccount {
  id: string;
  company_id: string;
  bank_connection_id: string | null;
  nickname: string | null;
  iban: string | null;
  bic: string | null;
  account_number: string | null;
  currency: string;
  current_balance: number | null;
  available_balance: number | null;
  balance_date: string | null;
  credit_limit: number | null;
  status: AccountStatus;
  ignore_balance: boolean;
  hidden_at: string | null;
  allow_balance_change: boolean;
  provider_account_id: string | null;
  identifiers: unknown[] | null;
  last_synced_at: string | null;
  account_type: AccountType | null;
  color: string | null;
  notes: string | null;
  is_default: boolean;
  bank_name: string | null;
  bank_abi: string | null;
  bank_cab: string | null;
  created_at: string;
  updated_at: string;
}

export interface BankAccountSummary {
  count: number;
  total_current_balance: number;
  total_available_balance: number;
  difference: number;
  total_credit_limit: number;
}

export interface BankAccountBalance {
  id: string;
  bank_account_id: string;
  balance_date: string;
  current_balance: number | null;
  available_balance: number | null;
  source: BalanceSource;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BalanceChartPoint {
  date: string;
  current_balance: number | null;
  available_balance: number | null;
}

export interface BankAccountAccess {
  id: string;
  bank_account_id: string;
  user_id: string;
  user_email: string | null;
  user_name: string | null;
  access_level: AccessLevel;
  granted_by: string | null;
  created_at: string;
  updated_at: string;
}
