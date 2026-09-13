// Typed client for /auth — docs/API_CONTRACTS.md "Auth (`/auth`)".
// Not one of the four files explicitly named in the task, but /auth/me is
// part of the Phase 1 endpoint contract too, so it's covered here for
// completeness (root CLAUDE.md "All API calls go through typed functions").
import { apiFetch } from "./client";
import type { AuthMe, UpdateAuthMeInput } from "@/types/auth";

/** GET /auth/me — auth: any authenticated user. */
export async function getCurrentUser(accessToken: string): Promise<AuthMe> {
  return apiFetch<AuthMe>(
    "/auth/me",
    { method: "GET" },
    { accessToken }
  );
}

/** PATCH /auth/me — auth: owner. Always scoped to the authenticated caller. */
export async function updateCurrentUser(
  input: UpdateAuthMeInput,
  accessToken: string
): Promise<AuthMe["owner_account"]> {
  return apiFetch<AuthMe["owner_account"]>(
    "/auth/me",
    { method: "PATCH", body: JSON.stringify(input) },
    { accessToken }
  );
}
