import { z } from "zod";

export const createExpectedTransactionSchema = z.object({
  type: z.enum(["expected_inflow", "expected_outflow"]),
  expected_amount: z.number().positive("L'importo deve essere positivo"),
  due_date: z.string().min(1, "La data di scadenza è obbligatoria"),
  currency: z.string(),
  counterpart_name: z.string().optional(),
  counterpart_iban: z.string().optional(),
  bank_account_id: z.string().optional(),
  description: z.string().optional(),
  reference_number: z.string().optional(),
  document_type: z.enum([
    "sales_invoice", "purchase_invoice", "credit_note",
    "debit_note", "salary", "tax", "other",
  ]),
  source: z.string(),
});

export type CreateExpectedTransactionInput = z.infer<typeof createExpectedTransactionSchema>;

export const updateExpectedTransactionSchema = z.object({
  type: z.enum(["expected_inflow", "expected_outflow"]).optional(),
  expected_amount: z.number().positive().optional(),
  due_date: z.string().optional(),
  currency: z.string().optional(),
  counterpart_name: z.string().optional(),
  counterpart_iban: z.string().optional(),
  bank_account_id: z.string().optional(),
  description: z.string().optional(),
  reference_number: z.string().optional(),
  document_type: z.enum([
    "sales_invoice", "purchase_invoice", "credit_note",
    "debit_note", "salary", "tax", "other",
  ]).optional(),
});

export const createReconciliationRuleSchema = z.object({
  name: z.string().min(1, "Il nome è obbligatorio"),
  description: z.string().optional(),
  match_amount: z.boolean(),
  amount_tolerance: z.number().min(0),
  match_date: z.boolean(),
  date_tolerance_days: z.number().int().min(0),
  match_description: z.boolean(),
  match_counterpart: z.boolean(),
  auto_confirm: z.boolean(),
  min_confidence: z.number().min(0).max(1),
  priority: z.number().int(),
  is_active: z.boolean(),
  match_type: z.string(),
  action: z.string(),
  require_same_counterpart: z.boolean(),
});

export type CreateReconciliationRuleInput = z.infer<typeof createReconciliationRuleSchema>;
