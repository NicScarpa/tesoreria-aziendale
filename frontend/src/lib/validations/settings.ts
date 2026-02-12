import { z } from "zod";

function luhnCheck(vat: string): boolean {
  let total = 0;
  for (let i = 0; i < vat.length; i++) {
    let d = parseInt(vat[i], 10);
    if (i % 2 === 1) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    total += d;
  }
  return total % 10 === 0;
}

export const companySchema = z.object({
  name: z.string().min(1, "Nome azienda obbligatorio"),
  vat_number: z
    .string()
    .regex(/^\d{11}$/, "P.IVA: 11 cifre")
    .refine(luhnCheck, "P.IVA non valida (checksum)")
    .nullable()
    .optional(),
  tax_number: z
    .string()
    .regex(/^[A-Z0-9]{16}$/i, "Codice fiscale: 16 caratteri alfanumerici")
    .transform((v) => v.toUpperCase())
    .nullable()
    .optional(),
  country: z.string().length(2, "Codice paese: 2 caratteri").optional(),
  address: z.string().nullable().optional(),
  fiscal_regime: z.string().max(10).nullable().optional(),
  group_vat_number: z.string().max(20).nullable().optional(),
  city: z.string().max(100).nullable().optional(),
  postal_code: z.string().max(10).nullable().optional(),
  province_code: z.string().max(5).nullable().optional(),
  certified_email: z.email("PEC non valida").nullable().optional(),
  destination_code: z
    .string()
    .regex(/^[A-Z0-9]{7}$/i, "Codice SDI: 7 caratteri")
    .transform((v) => v.toUpperCase())
    .nullable()
    .optional(),
  default_currency: z.string().length(3).optional(),
});

export const treasurySettingsSchema = z.object({
  min_cash_threshold: z.number().nullable(),
  critical_cash_threshold: z.number().nullable(),
  advance_notice_days: z.number().int().min(1).max(90),
  auto_categorize: z.boolean(),
  auto_reconcile: z.boolean(),
  cashflow_update_mode: z.enum(["manual", "daily", "realtime"]),
});

export const displaySettingsSchema = z.object({
  date_format: z.string(),
  decimal_separator: z.string(),
  thousands_separator: z.string(),
  timezone: z.string(),
  first_day_of_week: z.number().int().min(0).max(6),
});

export const reconciliationRuleSchema = z.object({
  name: z.string().min(1, "Nome obbligatorio"),
  match_amount: z.boolean(),
  amount_tolerance: z.number().min(0),
  match_date: z.boolean(),
  date_tolerance_days: z.number().int().min(0),
  match_description: z.boolean(),
  match_counterpart: z.boolean(),
  auto_confirm: z.boolean(),
  min_confidence: z.number().min(0).max(1),
  priority: z.number().int().min(0),
  is_active: z.boolean(),
});

export const inviteMemberSchema = z.object({
  email: z.email("Email non valida"),
  role: z.enum(["viewer", "editor", "admin"]),
});

export const transferOwnershipSchema = z.object({
  target_user_id: z.string().uuid(),
  password: z.string().min(1, "Password obbligatoria"),
});

export type CompanyInput = z.infer<typeof companySchema>;
export type TreasurySettingsInput = z.infer<typeof treasurySettingsSchema>;
export type DisplaySettingsInput = z.infer<typeof displaySettingsSchema>;
export type ReconciliationRuleInput = z.infer<typeof reconciliationRuleSchema>;
export type InviteMemberInput = z.infer<typeof inviteMemberSchema>;
export type TransferOwnershipInput = z.infer<typeof transferOwnershipSchema>;
