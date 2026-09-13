// Types for POST /claim and its follow-ups, matching docs/API_CONTRACTS.md
// "Claim flow (`/claim`)" and docs/DECISIONS.md "Claim flow".

export type ClaimProofMethod =
  | "google_business_profile"
  | "phone_verification"
  | "document_upload";

export type ClaimStatus = "pending_review" | "approved" | "rejected";

/** Body for POST /claim. */
export interface CreateClaimInput {
  brand_id: number;
  /**
   * Required in practice for proof_method="phone_verification" when the
   * brand has more than one location (identifies which location's public
   * phone number is being called). Omit for a single-location brand or the
   * other two proof methods.
   */
  location_id?: number;
  proof_method: ClaimProofMethod;
  google_business_profile_url?: string | null;
  supporting_document_url?: string | null;
}

/** Response for POST /claim and GET /claim/{id}. */
export interface ClaimResponse {
  claim_id: number;
  brand_id: number;
  status: ClaimStatus;
  proof_method: ClaimProofMethod;
  submitted_at: string;
  /** submitted_at + 2 business days, computed, not stored. */
  sla_due_at: string;
  reviewed_at?: string | null;
  reviewer_notes?: string | null;
}

/** Body for POST /claim/{id}/approve. Every field optional. */
export interface ApproveClaimInput {
  reviewer_notes?: string;
}

/** Body for POST /claim/{id}/reject. reviewer_notes is required to reject. */
export interface RejectClaimInput {
  reviewer_notes: string;
}
