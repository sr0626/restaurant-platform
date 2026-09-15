"use server";

// Server Actions backing the admin listings management UI
// (AdminListingsPanel.tsx) — same "keep the Cognito access token
// server-side" rationale as admin/claims/actions.ts. Every action
// independently re-checks `role === "admin"` from the verified session
// (not just from the page's own `requireSession` gate) since a Server
// Action is a real network endpoint Next.js exposes, callable on its own.
//
// Both actions call real, already-documented endpoints
// (docs/API_CONTRACTS.md "DELETE /restaurants/{id}" and
// "DELETE /locations/{id}") — no new backend endpoint was needed for
// moderation itself.
import { ApiError } from "@/lib/api/client";
import { deleteLocation } from "@/lib/api/locations";
import { deleteRestaurant } from "@/lib/api/restaurants";
import { getServerSession } from "@/lib/auth/session";

export type ListingActionResult = { ok: true } | { ok: false; error: string };

async function requireAdminAccessToken(): Promise<
  { ok: true; accessToken: string } | { ok: false; error: string }
> {
  const session = await getServerSession();
  if (!session) {
    return { ok: false, error: "Your session has expired. Please sign in again." };
  }
  if (session.role !== "admin") {
    return { ok: false, error: "Only admins can manage listings." };
  }
  return { ok: true, accessToken: session.accessToken };
}

/**
 * DELETE /restaurants/{id} — auth: admin only. Hard delete. The database's
 * `ON DELETE RESTRICT` on `restaurant_location.brand_id` means this 409s
 * while the brand still has any (active or inactive) locations — surfaced
 * here as-is rather than swallowed, so the admin knows to remove/reassign
 * locations first (docs/API_CONTRACTS.md "DELETE /restaurants/{id}").
 */
export async function deleteRestaurantAction(brandId: number): Promise<ListingActionResult> {
  const admin = await requireAdminAccessToken();
  if (!admin.ok) return admin;

  try {
    await deleteRestaurant(brandId, admin.accessToken);
    return { ok: true };
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 404) {
        return { ok: false, error: `No restaurant found with id #${brandId}.` };
      }
      if (error.status === 409) {
        return {
          ok: false,
          error:
            "This restaurant still has locations attached — remove or reassign them before deleting the listing.",
        };
      }
      return { ok: false, error: error.message };
    }
    return { ok: false, error: "Something went wrong. Please try again." };
  }
}

/**
 * DELETE /locations/{id} — auth: owner (owns parent brand) or admin, here
 * always called as admin. Soft delete: sets `is_active=false`, does not
 * remove the row (docs/API_CONTRACTS.md "DELETE /locations/{id}"). There
 * is no reactivation endpoint in the current contract (`PATCH
 * /locations/{id}` has no `is_active` field) — deactivating here is a
 * one-way moderation action until that gap is closed.
 */
export async function deactivateLocationAction(locationId: number): Promise<ListingActionResult> {
  const admin = await requireAdminAccessToken();
  if (!admin.ok) return admin;

  try {
    await deleteLocation(locationId, admin.accessToken);
    return { ok: true };
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 404) {
        return { ok: false, error: `No location found with id #${locationId}.` };
      }
      return { ok: false, error: error.message };
    }
    return { ok: false, error: "Something went wrong. Please try again." };
  }
}
