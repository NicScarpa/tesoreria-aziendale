export interface TreasurySettings {
  min_cash_threshold: number | null;
  critical_cash_threshold: number | null;
  advance_notice_days: number;
  auto_categorize: boolean;
  auto_reconcile: boolean;
  cashflow_update_mode: "manual" | "daily" | "realtime";
}

export interface DisplaySettings {
  date_format: string;
  decimal_separator: string;
  thousands_separator: string;
  timezone: string;
  first_day_of_week: number;
}

export interface CompanySettings {
  treasury_settings: TreasurySettings;
  display_settings: DisplaySettings;
}

export interface ReconciliationRule {
  id: string;
  company_id: string;
  name: string;
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
  created_at: string;
  updated_at: string;
}

export interface TeamMemberUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface TeamMember {
  id: string;
  user: TeamMemberUser;
  role: "owner" | "admin" | "editor" | "viewer";
  status: "active" | "invited" | "suspended" | "removed";
  invited_at: string | null;
  joined_at: string | null;
  invited_by_name: string | null;
  created_at: string;
}

export interface NotificationPreference {
  notification_type: string;
  in_app: boolean;
  email: boolean;
}

export interface ModuleConfig {
  key: string;
  label: string;
  description: string;
  enabled: boolean;
}
