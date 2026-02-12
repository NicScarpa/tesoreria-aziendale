import { z } from "zod";

export const conditionSchema = z.object({
  type: z.enum(["KEYWORDS", "ACCOUNT", "TRANSACTION_TYPE"]),
  value: z.union([z.string(), z.array(z.string())]),
});

export const createRuleSchema = z.object({
  name: z.string().nullable().optional(),
  direction: z.enum(["inflow", "outflow"]),
  category_id: z.string().uuid("Seleziona una categoria"),
  subcategory_id: z.string().uuid().nullable().optional(),
  conditions: z.array(conditionSchema).min(1, "Aggiungi almeno una condizione"),
  priority: z.number().int().default(0),
  is_active: z.boolean().default(true),
});

export type CreateRuleInput = z.infer<typeof createRuleSchema>;
