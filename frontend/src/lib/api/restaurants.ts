// Typed client for /restaurants (restaurant_brand) — docs/API_CONTRACTS.md
// "Restaurants (`restaurant_brand`)".
import { apiFetch, toQueryString } from "./client";
import type { PaginatedResponse, PaginationParams } from "@/types/common";
import type { LocationSummary } from "@/types/location";
import type {
  CreateRestaurantInput,
  RestaurantBrand,
  UpdateRestaurantInput,
} from "@/types/restaurant";

/** GET /restaurants/{id} — public. Used by the SSR listing page. */
export async function getRestaurantById(id: number): Promise<RestaurantBrand> {
  return apiFetch<RestaurantBrand>(
    `/restaurants/${id}`,
    { method: "GET" },
    { revalidateSeconds: 60 }
  );
}

/**
 * FLAGGED CONTRACT GAP (see final report): frontend/CLAUDE.md's SSR listing
 * page pattern calls `getRestaurantBySlug(params.slug)` from
 * `/restaurant/[slug]/page.tsx`, but docs/API_CONTRACTS.md only documents
 * `GET /restaurants/{id}` with a numeric id — there is no dedicated
 * slug-lookup route. This assumes the backend's `{id}` path param can
 * resolve a slug string too (a common "id_or_slug" pattern); if that's not
 * actually true server-side, Architect/Backend Dev need to add a real
 * slug route (e.g. `GET /restaurants/by-slug/{slug}`) and this function
 * should be repointed at it. Not calling this a bug — it's a documented
 * open item to confirm.
 */
export async function getRestaurantBySlug(slug: string): Promise<RestaurantBrand> {
  return apiFetch<RestaurantBrand>(
    `/restaurants/${slug}`,
    { method: "GET" },
    { revalidateSeconds: 60 }
  );
}

/** GET /restaurants/{id}/locations — public, summary shape only. */
export async function getRestaurantLocations(
  id: number,
  params: PaginationParams = {}
): Promise<PaginatedResponse<LocationSummary>> {
  const query = toQueryString({
    page: params.page,
    page_size: params.page_size,
  });

  return apiFetch<PaginatedResponse<LocationSummary>>(
    `/restaurants/${id}/locations${query}`,
    { method: "GET" },
    { revalidateSeconds: 60 }
  );
}

/** POST /restaurants — auth: owner. */
export async function createRestaurant(
  input: CreateRestaurantInput,
  accessToken: string
): Promise<RestaurantBrand> {
  return apiFetch<RestaurantBrand>(
    "/restaurants",
    { method: "POST", body: JSON.stringify(input) },
    { accessToken }
  );
}

/** PATCH /restaurants/{id} — auth: owner (must own the brand) or admin. */
export async function updateRestaurant(
  id: number,
  input: UpdateRestaurantInput,
  accessToken: string
): Promise<RestaurantBrand> {
  return apiFetch<RestaurantBrand>(
    `/restaurants/${id}`,
    { method: "PATCH", body: JSON.stringify(input) },
    { accessToken }
  );
}

/**
 * DELETE /restaurants/{id} — auth: admin only. Returns 204; the DB
 * ON DELETE RESTRICT means this can 409 while locations still reference
 * the brand (docs/API_CONTRACTS.md).
 */
export async function deleteRestaurant(
  id: number,
  accessToken: string
): Promise<void> {
  return apiFetch<void>(
    `/restaurants/${id}`,
    { method: "DELETE" },
    { accessToken }
  );
}
