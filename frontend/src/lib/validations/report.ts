import { z } from "zod";

export const createReportDefinitionSchema = z.object({
  nome: z.string().min(1, "Nome obbligatorio").max(255),
  descrizione: z.string().nullable().optional(),
  tipo: z
    .enum([
      "saldi_conti", "movimenti", "entrate_uscite", "riconciliazione",
      "scadenzario", "aging", "cash_flow", "pagamenti",
      "controparte", "personalizzato",
    ])
    .default("personalizzato"),
  formato_default: z.enum(["pdf", "xlsx", "csv"]).default("pdf"),
  parametri_default: z.record(z.unknown()).nullable().optional(),
  layout: z.record(z.unknown()).nullable().optional(),
});

export type CreateReportDefinitionInput = z.input<typeof createReportDefinitionSchema>;

export const generateReportSchema = z.object({
  formato: z.enum(["pdf", "xlsx", "csv"]).default("pdf"),
  parametri: z.record(z.unknown()).nullable().optional(),
});

export type GenerateReportInput = z.input<typeof generateReportSchema>;

export const createScheduleSchema = z.object({
  report_definition_id: z.string().uuid("Report obbligatorio"),
  nome: z.string().min(1, "Nome obbligatorio").max(255),
  frequenza: z.enum(["giornaliero", "settimanale", "mensile", "trimestrale"]),
  formato: z.enum(["pdf", "xlsx", "csv"]).default("pdf"),
  parametri: z.record(z.unknown()).nullable().optional(),
});

export type CreateScheduleInput = z.input<typeof createScheduleSchema>;
