import { z } from "zod";

export const createScheduleSchema = z.object({
  tipo: z.enum(["attiva", "passiva"]),
  descrizione: z.string().min(1, "Descrizione obbligatoria").max(500),
  importo_totale: z.number().positive("L'importo deve essere positivo"),
  valuta: z.string().length(3).default("EUR"),
  data_scadenza: z.string().min(1, "Data scadenza obbligatoria"),
  data_emissione: z.string().nullable().optional(),
  tipo_documento: z.enum([
    "fattura_vendita", "fattura_acquisto", "nota_credito", "nota_debito",
    "stipendio", "tassa_f24", "contributo", "affitto", "utenza",
    "rata_prestito", "altro",
  ]).default("altro"),
  numero_documento: z.string().nullable().optional(),
  riferimento_documento: z.string().nullable().optional(),
  controparte_nome: z.string().nullable().optional(),
  controparte_iban: z.string().nullable().optional(),
  counterparty_id: z.string().uuid().nullable().optional(),
  bank_account_id: z.string().uuid().nullable().optional(),
  priorita: z.enum(["bassa", "normale", "alta", "urgente"]).default("normale"),
  metodo_pagamento: z.enum([
    "bonifico", "ri_ba", "sdd", "carta", "contanti", "f24", "altro",
  ]).nullable().optional(),
  categoria_id: z.string().uuid().nullable().optional(),
  note: z.string().nullable().optional(),
  is_ricorrente: z.boolean().default(false),
  ricorrenza_tipo: z.enum([
    "settimanale", "mensile", "bimestrale", "trimestrale", "semestrale", "annuale",
  ]).nullable().optional(),
  ricorrenza_fine: z.string().nullable().optional(),
});

export type CreateScheduleInput = z.input<typeof createScheduleSchema>;

export const updateScheduleSchema = z.object({
  descrizione: z.string().min(1).max(500).optional(),
  importo_totale: z.number().positive().optional(),
  valuta: z.string().length(3).optional(),
  data_scadenza: z.string().optional(),
  data_emissione: z.string().nullable().optional(),
  tipo_documento: z.enum([
    "fattura_vendita", "fattura_acquisto", "nota_credito", "nota_debito",
    "stipendio", "tassa_f24", "contributo", "affitto", "utenza",
    "rata_prestito", "altro",
  ]).optional(),
  numero_documento: z.string().nullable().optional(),
  riferimento_documento: z.string().nullable().optional(),
  controparte_nome: z.string().nullable().optional(),
  controparte_iban: z.string().nullable().optional(),
  bank_account_id: z.string().uuid().nullable().optional(),
  priorita: z.enum(["bassa", "normale", "alta", "urgente"]).optional(),
  metodo_pagamento: z.enum([
    "bonifico", "ri_ba", "sdd", "carta", "contanti", "f24", "altro",
  ]).nullable().optional(),
  note: z.string().nullable().optional(),
});

export type UpdateScheduleInput = z.infer<typeof updateScheduleSchema>;

export const createPaymentSchema = z.object({
  importo: z.number().positive("L'importo deve essere positivo"),
  data_pagamento: z.string().min(1, "Data pagamento obbligatoria"),
  metodo: z.enum([
    "bonifico", "ri_ba", "sdd", "carta", "contanti", "f24", "altro",
  ]).nullable().optional(),
  riferimento: z.string().nullable().optional(),
  note: z.string().nullable().optional(),
});

export type CreatePaymentInput = z.infer<typeof createPaymentSchema>;

export const createReminderSchema = z.object({
  giorni_prima: z.number().int().min(0).default(3),
  tipo: z.enum(["email", "in_app", "entrambi"]).default("in_app"),
  messaggio: z.string().nullable().optional(),
});

export type CreateReminderInput = z.input<typeof createReminderSchema>;
