import { z } from "zod";

export const createPaymentOrderSchema = z.object({
  tipo: z.enum(["sepa_credit_transfer", "riba", "sdd", "f24", "bonifico_estero"], {
    message: "Seleziona il tipo di pagamento",
  }),
  bank_account_id: z.string().uuid().nullable().optional(),
  data_esecuzione_richiesta: z.string().min(1, "La data di esecuzione è obbligatoria"),
  valuta: z.string().default("EUR"),
  priorita: z.enum(["normale", "alta", "urgente"]).default("normale"),
  note: z.string().max(1000).nullable().optional(),
});

export type CreatePaymentOrderInput = z.infer<typeof createPaymentOrderSchema>;

export const updatePaymentOrderSchema = z.object({
  bank_account_id: z.string().uuid().nullable().optional(),
  data_esecuzione_richiesta: z.string().nullable().optional(),
  valuta: z.string().nullable().optional(),
  priorita: z.enum(["normale", "alta", "urgente"]).nullable().optional(),
  note: z.string().max(1000).nullable().optional(),
});

export type UpdatePaymentOrderInput = z.infer<typeof updatePaymentOrderSchema>;

export const createPaymentLineSchema = z.object({
  beneficiario_nome: z.string().min(1, "Il nome del beneficiario è obbligatorio").max(255),
  beneficiario_iban: z.string().max(34).nullable().optional(),
  beneficiario_bic: z.string().max(11).nullable().optional(),
  beneficiario_cf: z.string().max(16).nullable().optional(),
  beneficiario_indirizzo: z.string().max(500).nullable().optional(),
  importo: z.number().positive("L'importo deve essere positivo"),
  valuta: z.string(),
  causale: z.string().max(140, "La causale non può superare 140 caratteri").nullable().optional(),
  end_to_end_id: z.string().max(35).nullable().optional(),
  counterparty_id: z.string().uuid().nullable().optional(),
  schedule_id: z.string().uuid().nullable().optional(),
  // RiBa
  riba_numero_ricevuta: z.string().nullable().optional(),
  riba_data_scadenza: z.string().nullable().optional(),
  riba_piazza: z.string().nullable().optional(),
  riba_abi_banca_domiciliataria: z.string().nullable().optional(),
  riba_cab_banca_domiciliataria: z.string().nullable().optional(),
  // SDD
  sdd_mandate_id: z.string().nullable().optional(),
  sdd_mandate_date: z.string().nullable().optional(),
  sdd_mandate_type: z.enum(["core", "b2b"]).nullable().optional(),
  sdd_sequence_type: z.enum(["frst", "rcur", "fnal", "ooff"]).nullable().optional(),
  // F24
  f24_sezione: z.enum(["erario", "inps", "regioni", "imu_altri_enti"]).nullable().optional(),
  f24_codice_tributo: z.string().nullable().optional(),
  f24_rateazione: z.string().nullable().optional(),
  f24_anno_riferimento: z.number().int().nullable().optional(),
  f24_mese_riferimento: z.number().int().min(1).max(12).nullable().optional(),
  f24_importo_debito: z.number().min(0).nullable().optional(),
  f24_importo_credito: z.number().min(0).nullable().optional(),
  f24_codice_ente: z.string().nullable().optional(),
  f24_codice_sede: z.string().nullable().optional(),
});

export type CreatePaymentLineInput = z.infer<typeof createPaymentLineSchema>;

export const fromSchedulesSchema = z.object({
  schedule_ids: z.array(z.string().uuid()).min(1, "Seleziona almeno una scadenza"),
  bank_account_id: z.string().uuid().nullable().optional(),
  data_esecuzione_richiesta: z.string().min(1, "La data di esecuzione è obbligatoria"),
  priorita: z.enum(["normale", "alta", "urgente"]).default("normale"),
  note: z.string().max(1000).nullable().optional(),
});

export type FromSchedulesInput = z.infer<typeof fromSchedulesSchema>;

export const createTemplateSchema = z.object({
  nome: z.string().min(1, "Il nome è obbligatorio").max(255),
  tipo: z.enum(["sepa_credit_transfer", "riba", "sdd", "f24", "bonifico_estero"]),
  bank_account_id: z.string().uuid().nullable().optional(),
  dati_template: z.record(z.string(), z.unknown()).nullable().optional(),
});

export type CreateTemplateInput = z.infer<typeof createTemplateSchema>;

export const f24LineSchema = z.object({
  f24_sezione: z.enum(["erario", "inps", "regioni", "imu_altri_enti"], {
    message: "Seleziona la sezione",
  }),
  f24_codice_tributo: z.string().min(1, "Codice tributo obbligatorio").max(10),
  f24_rateazione: z.string().max(4).nullable().optional(),
  f24_anno_riferimento: z.number().int().min(2000).max(2100),
  f24_mese_riferimento: z.number().int().min(1).max(12).nullable().optional(),
  f24_importo_debito: z.number().min(0).default(0),
  f24_importo_credito: z.number().min(0).default(0),
  f24_codice_ente: z.string().max(10).nullable().optional(),
  f24_codice_sede: z.string().max(10).nullable().optional(),
});

export type F24LineInput = z.infer<typeof f24LineSchema>;
