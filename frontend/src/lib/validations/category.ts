import { z } from "zod";

export const createCategorySchema = z.object({
  name: z.string().min(1, "Nome categoria obbligatorio"),
  color: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/, "Colore in formato #RRGGBB")
    .default("#6b7280"),
  sort_order: z.number().int().default(0),
});

export type CreateCategoryInput = z.infer<typeof createCategorySchema>;

export const updateCategorySchema = z.object({
  name: z.string().min(1).optional(),
  color: z
    .string()
    .regex(/^#[0-9a-fA-F]{6}$/, "Colore in formato #RRGGBB")
    .optional(),
  sort_order: z.number().int().optional(),
});

export type UpdateCategoryInput = z.infer<typeof updateCategorySchema>;

export const createSubcategorySchema = z.object({
  name: z.string().min(1, "Nome sottocategoria obbligatorio"),
});

export type CreateSubcategoryInput = z.infer<typeof createSubcategorySchema>;
