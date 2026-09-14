// Owner + manager portal dashboard — auth-gated per frontend/CLAUDE.md's
// "Auth-gated portal pages" pattern. Lists the signed-in owner's brands and
// locations via the owner-scoped `GET /restaurants` (docs/API_CONTRACTS.md,
// landed 2026-09-13), each location linking into its editor
// (`/portal/locations/{id}`).
//
// FLAGGED CONTRACT GAP (see this PR's description): `GET /restaurants` is
// "Auth: owner or admin" only — there is no manager path at all, and no
// other endpoint lets a manager discover which locations they're assigned
// to (the closest thing, `GET /locations/{id}/managers`, needs a location
// id up front, which is exactly what's missing). So a manager session
// cannot be listed here today; this page shows them a clear explanation
// instead of silently rendering nothing, and they can still reach a
// location editor directly if they have the link (see
// `/portal/locations/[id]/page.tsx`, which enforces access itself). A real
// fix needs a new backend endpoint (e.g. `GET /locations?assigned_to_me=true`
// or a manager-scoped branch of `GET /restaurants`) — flagged for
// Architect/Backend Dev, not built here.
import type { Metadata } from "next";
import { requireSession } from "@/lib/auth/guards";
import { ApiError } from "@/lib/api/client";
import { getMyRestaurants, getRestaurantLocations } from "@/lib/api/restaurants";
import BrandCard from "@/components/portal/BrandCard";
import InfoPanel from "@/components/ui/InfoPanel";
import type { LocationSummary } from "@/types/location";
import type { RestaurantBrand } from "@/types/restaurant";

export const metadata: Metadata = {
  title: "Owner Dashboard",
};

interface BrandWithLocations {
  brand: RestaurantBrand;
  locations: LocationSummary[];
  locationsError: string | null;
}

/**
 * `GET /restaurants` only returns a `location_count` per brand, not the
 * location rows — this fetches each brand's locations via the existing
 * public `GET /restaurants/{id}/locations` so each one can link to its
 * editor. Brands with `location_count === 0` skip the extra call.
 */
async function loadLocationsForBrand(brand: RestaurantBrand): Promise<BrandWithLocations> {
  if (brand.location_count === 0) {
    return { brand, locations: [], locationsError: null };
  }
  try {
    const page = await getRestaurantLocations(brand.id, { page: 1, page_size: 100 });
    return { brand, locations: page.results, locationsError: null };
  } catch (error) {
    return {
      brand,
      locations: [],
      locationsError:
        error instanceof ApiError
          ? error.message
          : "Could not load this brand's locations. Please try again.",
    };
  }
}

export default async function DashboardPage() {
  const session = await requireSession(["owner", "manager"]);

  if (session.role === "manager") {
    return (
      <main className="min-h-screen bg-brand-bg">
        <section className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
          <h1 className="font-display text-2xl font-bold text-brand-ink sm:text-3xl">
            Dashboard
          </h1>
          <p className="mt-2 text-sm text-brand-ink-muted">Signed in as manager.</p>

          <div className="mt-6">
            <InfoPanel
              title="No location list available for managers yet"
              body="There isn't a backend endpoint yet that lists which locations you're assigned to manage. Ask the owner who assigned you for a direct link to the location — you'll be able to open its editor at /portal/locations/{id} once you have the id."
            />
          </div>
        </section>
      </main>
    );
  }

  let brands: RestaurantBrand[] = [];
  let loadError: string | null = null;
  try {
    const page = await getMyRestaurants({ page: 1, page_size: 100 }, session.accessToken);
    brands = page.results;
  } catch (error) {
    loadError =
      error instanceof ApiError
        ? error.message
        : "Something went wrong loading your restaurants. Please try again.";
  }

  const brandsWithLocations = loadError
    ? []
    : await Promise.all(brands.map(loadLocationsForBrand));

  return (
    <main className="min-h-screen bg-brand-bg">
      <section className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <h1 className="font-display text-2xl font-bold text-brand-ink sm:text-3xl">Dashboard</h1>
        <p className="mt-2 text-sm text-brand-ink-muted">
          Your restaurant brands and locations. Select a location to edit its details, hours,
          photos, and managers.
        </p>

        <div className="mt-6">
          {loadError && <InfoPanel title="Couldn't load your restaurants" body={loadError} />}

          {!loadError && brands.length === 0 && (
            <InfoPanel
              title="No restaurants found"
              body="You don't have any restaurant brands yet. Claim an existing unclaimed listing from its public page, or create a new brand, to get started."
            />
          )}

          {!loadError && brandsWithLocations.length > 0 && (
            <div className="flex flex-col gap-5">
              {brandsWithLocations.map(({ brand, locations, locationsError }) => (
                <BrandCard
                  key={brand.id}
                  brand={brand}
                  locations={locations}
                  locationsError={locationsError}
                />
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
