// Typed client for /claim — docs/API_CONTRACTS.md "Claim flow (`/claim`)".
import { apiFetch } from "./client";
import type {
  ApproveClaimInput,
  ClaimResponse,
  CreateClaimInput,
  RejectClaimInput,
} from "@/types/claim";

/** POST /claim — auth: any authenticated Cognito user (the claimant). */
export async function submitClaim(
  input: CreateClaimInput,
  accessToken: string
): Promise<ClaimResponse> {
  return apiFetch<ClaimResponse>(
    "/claim",
    { method: "POST", body: JSON.stringify(input) },
    { accessToken }
  );
}

/** GET /claim/{id} — auth: the claimant (own claim) or admin (any claim). */
export async function getClaimById(
  id: number,
  accessToken: string
): Promise<ClaimResponse> {
  return apiFetch<ClaimResponse>(
    `/claim/${id}`,
    { method: "GET" },
    { accessToken }
  );
}

/** POST /claim/{id}/approve — auth: admin. */
export async function approveClaim(
  id: number,
  input: ApproveClaimInput,
  accessToken: string
): Promise<ClaimResponse> {
  return apiFetch<ClaimResponse>(
    `/claim/${id}/approve`,
    { method: "POST", body: JSON.stringify(input) },
    { accessToken }
  );
}

/** POST /claim/{id}/reject — auth: admin. */
export async function rejectClaim(
  id: number,
  input: RejectClaimInput,
  accessToken: string
): Promise<ClaimResponse> {
  return apiFetch<ClaimResponse>(
    `/claim/${id}/reject`,
    { method: "POST", body: JSON.stringify(input) },
    { accessToken }
  );
}
