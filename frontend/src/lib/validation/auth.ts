// Client-side validation mirroring PATCH /auth/me (docs/API_CONTRACTS.md "Auth").
import { z } from "zod";

export const updateAuthMeSchema = z.object({
  full_name: z.string().trim().min(1, "Name is required").max(200),
  phone: z.string().trim().regex(/^\+?[1-9]\d{7,14}$/, "Enter a valid phone number"),
});

export type UpdateAuthMeFormValues = z.infer<typeof updateAuthMeSchema>;
