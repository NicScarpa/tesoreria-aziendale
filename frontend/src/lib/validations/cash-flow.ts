import { z } from "zod";

export const createForecastSchema = z.object({
  nome: z.string().min(1, "Nome obbligatorio").max(255),
  descrizione: z.string().nullable().optional(),
  data_inizio: z.string().min(1, "Data inizio obbligatoria"),
  data_fine: z.string().min(1, "Data fine obbligatoria"),
  tipo: z.enum(["base", "ottimistico", "pessimistico", "personalizzato"]).default("base"),
  bank_account_ids: z.array(z.string().uuid()).nullable().optional(),
  includi_scadenze: z.boolean().default(true),
  includi_pagamenti: z.boolean().default(true),
  includi_ricorrenze: z.boolean().default(true),
  includi_stime_storiche: z.boolean().default(false),
});

export type CreateForecastInput = z.input<typeof createForecastSchema>;

export const updateForecastSchema = z.object({
  nome: z.string().min(1).max(255).optional(),
  descrizione: z.string().nullable().optional(),
  stato: z.enum(["bozza", "attiva", "archiviata"]).optional(),
});

export type UpdateForecastInput = z.infer<typeof updateForecastSchema>;

export const createScenarioSchema = z.object({
  nome: z.string().min(1, "Nome obbligatorio").max(255),
  descrizione: z.string().nullable().optional(),
  tipo_aggiustamento: z.enum(["aggiunta", "rimozione", "modifica_importo", "spostamento_data"]),
  data_originale: z.string().nullable().optional(),
  data_modificata: z.string().nullable().optional(),
  importo_originale: z.number().nullable().optional(),
  importo_modificato: z.number().nullable().optional(),
  tipo_movimento: z.enum(["entrata", "uscita"]).nullable().optional(),
  categoria: z.string().nullable().optional(),
});

export type CreateScenarioInput = z.input<typeof createScenarioSchema>;
