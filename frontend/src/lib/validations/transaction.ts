import { z } from "zod";

export const csvMappingSchema = z.object({
  bank_account_id: z.string().min(1, "Seleziona un conto"),
  date_column: z.string().min(1, "Colonna data obbligatoria"),
  amount_column: z.string().min(1, "Colonna importo obbligatoria"),
  description_column: z.string().nullable().optional(),
  date_format: z.string().default("%d/%m/%Y"),
  decimal_separator: z.enum([",", "."]).default(","),
  csv_separator: z.enum([";", ",", "\t"]).default(";"),
});

export type CSVMappingInput = z.infer<typeof csvMappingSchema>;

export const updateTransactionSchema = z.object({
  category_id: z.string().uuid().nullable().optional(),
  subcategory_id: z.string().uuid().nullable().optional(),
  notes: z.string().nullable().optional(),
  verified: z.boolean().optional(),
  counterpart_name: z.string().nullable().optional(),
});

export type UpdateTransactionInput = z.infer<typeof updateTransactionSchema>;
