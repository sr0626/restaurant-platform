// Client-side validation for the claim flow form (frontend/CLAUDE.md
// Phase 1 scope: "Claim flow UI"), mirroring POST /claim's body shape in
// docs/API_CONTRACTS.md exactly — this schema validates in the browser
// before the typed function in /lib/api/claim.ts ever sends the request;
// the backend re-validates independently, this is not a substitute for
// server-side checks.
import { z } from "zod";

export const claimProofMethodSchema = z.enum([
  "google_business_profile",
  "phone_verification",
  "document_upload",
]);

export const createClaimSchema = z
  .object({
    brand_id: z.number().int().positive(),
    location_id: z.number().int().positive().optional(),
    proof_method: claimProofMethodSchema,
    google_business_profile_url: z.string().url().nullable().optional(),
    supporting_document_url: z.string().nullable().optional(),
  })
  .superRefine((value, ctx) => {
    if (
      value.proof_method === "google_business_profile" &&
      !value.google_business_profile_url
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["google_business_profile_url"],
        message: "A Google Business Profile URL is required for this proof method.",
      });
    }
    if (
      value.proof_method === "document_upload" &&
      !value.supporting_document_url
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["supporting_document_url"],
        message: "A supporting document upload is required for this proof method.",
      });
    }
  });

export type CreateClaimFormValues = z.infer<typeof createClaimSchema>;

export const rejectClaimSchema = z.object({
  reviewer_notes: z.string().min(1, "Reviewer notes are required to reject a claim."),
});

export const approveClaimSchema = z.object({
  reviewer_notes: z.string().optional(),
});
