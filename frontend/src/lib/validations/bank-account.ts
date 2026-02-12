import { z } from "zod";

function validateIBAN(iban: string): boolean {
  const cleaned = iban.replace(/\s/g, "").toUpperCase();
  if (!/^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$/.test(cleaned)) return false;
  if (cleaned.startsWith("IT") && cleaned.length !== 27) return false;
  // Modulo 97 check with BigInt
  const rearranged = cleaned.slice(4) + cleaned.slice(0, 4);
  let numeric = "";
  for (const ch of rearranged) {
    if (/\d/.test(ch)) {
      numeric += ch;
    } else {
      numeric += (ch.charCodeAt(0) - 55).toString();
    }
  }
  return BigInt(numeric) % BigInt(97) === BigInt(1);
}

export const createBankAccountSchema = z.object({
  nickname: z.string().min(1, "Nome conto obbligatorio"),
  iban: z
    .string()
    .transform((v) => v.replace(/\s/g, "").toUpperCase())
    .refine(validateIBAN, "IBAN non valido")
    .nullable()
    .optional(),
  bic: z.string().nullable().optional(),
  account_number: z.string().nullable().optional(),
  currency: z.string().length(3, "Codice valuta: 3 caratteri").optional(),
  current_balance: z.number().nullable().optional(),
  available_balance: z.number().nullable().optional(),
  credit_limit: z.number().nullable().optional(),
  account_type: z
    .enum(["checking", "savings", "cash", "credit_card", "loan", "other"])
    .nullable()
    .optional(),
  color: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/, "Colore in formato #RRGGBB")
    .optional(),
  notes: z.string().nullable().optional(),
  is_default: z.boolean().optional(),
  bank_name: z.string().nullable().optional(),
});

export const updateBankAccountSchema = z.object({
  nickname: z.string().min(1).optional(),
  iban: z
    .string()
    .transform((v) => v.replace(/\s/g, "").toUpperCase())
    .refine(validateIBAN, "IBAN non valido")
    .nullable()
    .optional(),
  bic: z.string().nullable().optional(),
  account_number: z.string().nullable().optional(),
  currency: z.string().length(3).optional(),
  credit_limit: z.number().nullable().optional(),
  account_type: z
    .enum(["checking", "savings", "cash", "credit_card", "loan", "other"])
    .nullable()
    .optional(),
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/).optional(),
  notes: z.string().nullable().optional(),
  is_default: z.boolean().optional(),
  bank_name: z.string().nullable().optional(),
  ignore_balance: z.boolean().optional(),
});

export const updateBalanceSchema = z.object({
  current_balance: z.number().nullable().optional(),
  available_balance: z.number().nullable().optional(),
  notes: z.string().nullable().optional(),
});

export const createAccessSchema = z.object({
  user_id: z.string().uuid("ID utente non valido"),
  access_level: z.enum(["read", "write", "admin"]).default("read"),
});

export { validateIBAN };

export type CreateBankAccountInput = z.infer<typeof createBankAccountSchema>;
export type UpdateBankAccountInput = z.infer<typeof updateBankAccountSchema>;
export type UpdateBalanceInput = z.infer<typeof updateBalanceSchema>;
export type CreateAccessInput = z.infer<typeof createAccessSchema>;
