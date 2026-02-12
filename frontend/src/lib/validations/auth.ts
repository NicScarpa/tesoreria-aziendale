import { z } from "zod";

export const loginSchema = z.object({
  email: z.email("Email non valida"),
  password: z.string().min(1, "Password obbligatoria"),
});

export const registerSchema = z.object({
  email: z.email("Email non valida"),
  password: z
    .string()
    .min(8, "Minimo 8 caratteri")
    .regex(/[A-Z]/, "Deve contenere almeno una maiuscola")
    .regex(/[a-z]/, "Deve contenere almeno una minuscola")
    .regex(/[0-9]/, "Deve contenere almeno un numero"),
  first_name: z.string().min(1, "Nome obbligatorio"),
  last_name: z.string().min(1, "Cognome obbligatorio"),
  company_name: z.string().min(1, "Nome azienda obbligatorio"),
});

export const forgotPasswordSchema = z.object({
  email: z.email("Email non valida"),
});

export const resetPasswordSchema = z.object({
  new_password: z
    .string()
    .min(8, "Minimo 8 caratteri")
    .regex(/[A-Z]/, "Deve contenere almeno una maiuscola")
    .regex(/[a-z]/, "Deve contenere almeno una minuscola")
    .regex(/[0-9]/, "Deve contenere almeno un numero"),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Le password non coincidono",
  path: ["confirm_password"],
});

export const changePasswordSchema = z.object({
  current_password: z.string().min(1, "Password attuale obbligatoria"),
  new_password: z.string().min(8, "Minimo 8 caratteri"),
});

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;
