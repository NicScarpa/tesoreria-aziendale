import type { Category, Subcategory } from "./category";

export interface RuleCondition {
  type: "KEYWORDS" | "ACCOUNT" | "TRANSACTION_TYPE";
  value: string | string[];
}

export interface CategorizationRule {
  id: string;
  company_id: string;
  name: string | null;
  direction: "inflow" | "outflow";
  action_type: string;
  category_id: string;
  subcategory_id: string | null;
  conditions: RuleCondition[];
  priority: number;
  is_active: boolean;
  category?: Category | null;
  subcategory?: Subcategory | null;
  created_at: string;
  updated_at: string;
}
