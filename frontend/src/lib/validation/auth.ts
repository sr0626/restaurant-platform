// Client-side validation mirroring PATCH /auth/me (docs/API_CONTRACTS.md "Auth").
import { z } from "zod";

export const updateAuthMeSchema = z.object({
  full_name: z.string().trim().min(1, "Name is required").max(200),
  phone: z.string().trim().regex(/^\+?[1-9]\d{7,14}$/, "Enter a valid phone number"),
});

export type UpdateAuthMeFormValues = z.infer<typeof updateAuthMeSchema>;

/**
 * Sign-in form validation (frontend/src/components/auth/LoginForm.tsx).
 * The password rule mirrors the Cognito user pool's actual password policy
 * (infra/modules/cognito/main.tf `password_policy`: minimum_length = 8,
 * require_uppercase = true, require_numbers = true, require_symbols =
 * false) so an obviously-invalid attempt is caught before round-tripping to
 * Cognito. Cognito remains the source of truth for whether credentials are
 * actually correct — this is a client-side pre-check only.
 */
export const signInSchema = z.object({
  email: z
    .string()
    .trim()
    .min(1, "Email is required")
    .email("Enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Password must include an uppercase letter")
    .regex(/[0-9]/, "Password must include a number"),
});

export type SignInFormValues = z.infer<typeof signInSchema>;
