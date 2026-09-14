// Typed client for /locations (restaurant_location) and its sub-resources
// (hours, photos, managers) — docs/API_CONTRACTS.md "Locations
// (`restaurant_location`)" and "Location Managers (`location_manager`)".
import { apiFetch } from "./client";
import type {
  AssignLocationManagerInput,
  CreateLocationInput,
  CreatePhotoInput,
  LocationDetail,
  LocationManager,
  LocationManagersResponse,
  Photo,
  PhotoUploadUrlInput,
  PhotoUploadUrlResponse,
  UpdateLocationHoursInput,
  UpdateLocationHoursResponse,
  UpdateLocationInput,
  UpdatePhotoInput,
} from "@/types/location";

/** GET /locations/{id} — public. */
export async function getLocationById(id: number): Promise<LocationDetail> {
  return apiFetch<LocationDetail>(
    `/locations/${id}`,
    { method: "GET" },
    { revalidateSeconds: 60 }
  );
}

/** POST /locations — auth: owner (must own the parent brand). */
export async function createLocation(
  input: CreateLocationInput,
  accessToken: string
): Promise<LocationDetail> {
  return apiFetch<LocationDetail>(
    "/locations",
    { method: "POST", body: JSON.stringify(input) },
    { accessToken }
  );
}

/**
 * PATCH /locations/{id} — auth: owner (owns parent brand) or manager with
 * an active assignment for this location (checked server-side, never from
 * the JWT alone).
 */
export async function updateLocation(
  id: number,
  input: UpdateLocationInput,
  accessToken: string
): Promise<LocationDetail> {
  return apiFetch<LocationDetail>(
    `/locations/${id}`,
    { method: "PATCH", body: JSON.stringify(input) },
    { accessToken }
  );
}

/**
 * DELETE /locations/{id} — auth: owner (owns parent brand) or admin.
 * Soft delete (sets is_active=false) — see docs/API_CONTRACTS.md.
 */
export async function deleteLocation(
  id: number,
  accessToken: string
): Promise<void> {
  return apiFetch<void>(
    `/locations/${id}`,
    { method: "DELETE" },
    { accessToken }
  );
}

/** PUT /locations/{id}/hours — full week replacement. */
export async function updateLocationHours(
  id: number,
  input: UpdateLocationHoursInput,
  accessToken: string
): Promise<UpdateLocationHoursResponse> {
  return apiFetch<UpdateLocationHoursResponse>(
    `/locations/${id}/hours`,
    { method: "PUT", body: JSON.stringify(input) },
    { accessToken }
  );
}

/**
 * POST /locations/{id}/photos/upload-url — step 1 of the S3 presigned
 * upload flow (root CLAUDE.md media pattern: presigned URL, never through
 * Lambda). The client PUTs the file to `upload_url` directly, then calls
 * `createLocationPhoto` below with the same `s3_key`.
 */
export async function getLocationPhotoUploadUrl(
  id: number,
  input: PhotoUploadUrlInput,
  accessToken: string
): Promise<PhotoUploadUrlResponse> {
  return apiFetch<PhotoUploadUrlResponse>(
    `/locations/${id}/photos/upload-url`,
    { method: "POST", body: JSON.stringify(input) },
    { accessToken }
  );
}

/** POST /locations/{id}/photos — step 2, records the row after the S3 PUT succeeds. */
export async function createLocationPhoto(
  id: number,
  input: CreatePhotoInput,
  accessToken: string
): Promise<Photo> {
  return apiFetch<Photo>(
    `/locations/${id}/photos`,
    { method: "POST", body: JSON.stringify(input) },
    { accessToken }
  );
}

/** PATCH /locations/{id}/photos/{photo_id} — reorder or set as cover. */
export async function updateLocationPhoto(
  id: number,
  photoId: number,
  input: UpdatePhotoInput,
  accessToken: string
): Promise<Photo> {
  return apiFetch<Photo>(
    `/locations/${id}/photos/${photoId}`,
    { method: "PATCH", body: JSON.stringify(input) },
    { accessToken }
  );
}

/** DELETE /locations/{id}/photos/{photo_id} — hard row delete. */
export async function deleteLocationPhoto(
  id: number,
  photoId: number,
  accessToken: string
): Promise<void> {
  return apiFetch<void>(
    `/locations/${id}/photos/${photoId}`,
    { method: "DELETE" },
    { accessToken }
  );
}

/**
 * POST /locations/{id}/managers — auth: owner only (must own the parent
 * brand). No admin path, no manager-assigns-manager path — see
 * docs/API_CONTRACTS.md "POST /locations/{id}/managers".
 */
export async function assignLocationManager(
  id: number,
  input: AssignLocationManagerInput,
  accessToken: string
): Promise<LocationManager> {
  return apiFetch<LocationManager>(
    `/locations/${id}/managers`,
    { method: "POST", body: JSON.stringify(input) },
    { accessToken }
  );
}

/**
 * GET /locations/{id}/managers — auth: owner (owns parent brand), admin, or
 * a manager with an active assignment on this location. `activeOnly` is
 * forced true server-side for a manager caller regardless of what's passed
 * here (docs/API_CONTRACTS.md).
 */
export async function getLocationManagers(
  id: number,
  params: { activeOnly?: boolean } = {},
  accessToken: string
): Promise<LocationManagersResponse> {
  const query = params.activeOnly ? "?active_only=true" : "";
  return apiFetch<LocationManagersResponse>(
    `/locations/${id}/managers${query}`,
    { method: "GET" },
    { accessToken }
  );
}

/**
 * DELETE /locations/{id}/managers/{manager_id} — auth: owner (owns parent
 * brand) or admin. Soft-deactivate (is_active=false), idempotent — calling
 * again on an already-inactive row still returns 204.
 * `manager_id` is the assignment row's own PK (`location_manager.id`), not
 * the manager's `user_id`.
 */
export async function removeLocationManager(
  id: number,
  managerId: number,
  accessToken: string
): Promise<void> {
  return apiFetch<void>(
    `/locations/${id}/managers/${managerId}`,
    { method: "DELETE" },
    { accessToken }
  );
}
